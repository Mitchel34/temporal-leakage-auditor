"""Small in-process behavior checks; no benchmark, installation, or subprocess."""

import copy
import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from temporal_leakage_auditor.cli import main
from temporal_leakage_auditor.core import RULES, audit_rows
from temporal_leakage_auditor.inputs import (
    FIELDS, InputError, load_rows, parse_rows, parse_timestamp, validate_rows,
)
from temporal_leakage_auditor.reports import make_report, render_json, render_markdown

CUTOFF_TEXT = "2025-01-15T00:00:00Z"
CUTOFF, CANONICAL = parse_timestamp(CUTOFF_TEXT)


def raw_rows():
    return [
        {"row_id": "train-one", "observation_id": "obs-one", "entity_id": "person",
         "split": "train", "prediction_time": "2025-01-14T00:00:00Z",
         "feature_available_time": "2025-01-14T00:00:00Z",
         "label_end_time": CUTOFF_TEXT},
        {"row_id": "validation-one", "observation_id": "obs-two", "entity_id": "person",
         "split": "validation", "prediction_time": CUTOFF_TEXT,
         "feature_available_time": CUTOFF_TEXT, "label_end_time": CUTOFF_TEXT},
    ]


def pairs(findings):
    return [(f["rule"], f["row_ids"][0]) for f in findings]


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.rows = validate_rows(raw_rows(), CUTOFF)

    def test_equality_empty_intervals_and_repeated_entities_are_clean(self):
        self.assertEqual(audit_rows(self.rows, CUTOFF), [])

    def test_late_feature_microsecond_boundary_in_either_split(self):
        for index in (0, 1):
            for delta in (-1, 0, 1, 1000000, 86400000000):
                with self.subTest(index=index, delta=delta):
                    rows = copy.deepcopy(self.rows)
                    rows[index]["feature_available_time"] = rows[index]["prediction_time"] + delta
                    expected = [("late_feature", rows[index]["row_id"])] if delta > 0 else []
                    self.assertEqual(pairs(audit_rows(rows, CUTOFF)), expected)

    def test_label_cutoff_boundary_and_validation_labels(self):
        for delta in (-1, 0, 1, 1000000, 86400000000):
            with self.subTest(delta=delta):
                rows = copy.deepcopy(self.rows)
                rows[0]["label_end_time"] = CUTOFF + delta
                rows[1]["label_end_time"] = CUTOFF + 86400000000
                expected = [("label_overlap", "train-one")] if delta > 0 else []
                self.assertEqual(pairs(audit_rows(rows, CUTOFF)), expected)

    def test_duplicate_marks_all_occurrences_in_both_splits(self):
        self.rows[1]["observation_id"] = self.rows[0]["observation_id"]
        extra = dict(self.rows[0], row_id="another-train")
        self.rows.append(extra)
        self.assertEqual(pairs(audit_rows(self.rows, CUTOFF)), [
            ("cross_split_duplicate", "another-train"),
            ("cross_split_duplicate", "train-one"),
            ("cross_split_duplicate", "validation-one"),
        ])

    def test_duplicate_within_one_split_is_outside_rule(self):
        self.rows.append(dict(self.rows[0], row_id="other-train"))
        self.assertEqual(audit_rows(self.rows, CUTOFF), [])

    def test_simultaneous_rules_stable_order_and_no_input_mutation(self):
        self.rows[0]["feature_available_time"] += 1
        self.rows[0]["label_end_time"] += 1
        self.rows[1]["observation_id"] = self.rows[0]["observation_id"]
        before = copy.deepcopy(self.rows)
        findings = audit_rows(self.rows, CUTOFF)
        self.assertEqual(pairs(findings), [("late_feature", "train-one"),
            ("label_overlap", "train-one"), ("cross_split_duplicate", "train-one"),
            ("cross_split_duplicate", "validation-one")])
        self.assertEqual(findings, audit_rows(list(reversed(self.rows)), CUTOFF))
        self.assertEqual(self.rows, before)
        self.assertEqual(len(pairs(findings)), len(set(pairs(findings))))
        for finding in findings:
            self.assertEqual(set(finding), {"rule", "row_ids", "severity", "reason", "repair"})
            self.assertEqual(finding["severity"], "error")
            self.assertTrue(finding["reason"] and finding["repair"])

    def test_observation_identity_is_case_sensitive(self):
        self.rows[0]["observation_id"] = "Observation"
        self.rows[1]["observation_id"] = "observation"
        self.assertEqual(audit_rows(self.rows, CUTOFF), [])


class TimestampTests(unittest.TestCase):
    def test_fractional_normalization_and_exact_microseconds(self):
        self.assertEqual(CANONICAL, "2025-01-15T00:00:00.000000Z")
        self.assertEqual(parse_timestamp("2025-01-15T00:00:00.000001Z")[0], CUTOFF + 1)
        self.assertEqual(parse_timestamp("2025-01-15T00:00:00.1Z")[1],
                         "2025-01-15T00:00:00.100000Z")

    def test_year_padding_and_dates_before_epoch(self):
        self.assertEqual(parse_timestamp("0001-01-01T00:00:00Z")[1],
                         "0001-01-01T00:00:00.000000Z")
        self.assertEqual(parse_timestamp("1969-12-31T23:59:59.999999Z")[0], -1)
        self.assertEqual(parse_timestamp("2024-02-29T00:00:00Z")[1],
                         "2024-02-29T00:00:00.000000Z")

    def test_ambiguous_or_invalid_timestamps_rejected(self):
        invalid = ["2025-01-15", "2025-01-15 00:00:00Z", "2025-01-15T00:00:00",
                   "2025-01-15T00:00:00+00:00", "2025-01-15T00:00:00z",
                   "2025-01-15T00:00:00.Z", "2025-01-15T00:00:00.0000001Z",
                   "2025-02-29T00:00:00Z", "2025-01-15T24:00:00Z",
                   "2025-01-15T00:00:60Z", "0000-01-01T00:00:00Z", 123,
                   " " + CUTOFF_TEXT, CUTOFF_TEXT + "\n"]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(InputError):
                parse_timestamp(value)


class InputTests(unittest.TestCase):
    def assert_invalid_change(self, field, value):
        rows = raw_rows()
        rows[0][field] = value
        with self.assertRaises(InputError):
            validate_rows(rows, CUTOFF)

    def test_empty_and_single_split_rejected(self):
        for rows in ([], raw_rows()[:1], raw_rows()[1:]):
            with self.subTest(rows=rows), self.assertRaises(InputError):
                validate_rows(rows, CUTOFF)

    def test_fields_must_be_exact_and_string_valued(self):
        for value in (None, 1, True, [], {}):
            with self.subTest(value=value):
                self.assert_invalid_change("entity_id", value)
        for change in ("missing", "extra"):
            rows = raw_rows()
            if change == "missing":
                del rows[0]["entity_id"]
            else:
                rows[0]["unexpected"] = "value"
            with self.assertRaises(InputError):
                validate_rows(rows, CUTOFF)

    def test_invalid_row_types_rejected(self):
        for value in (None, [], "row", 4):
            with self.subTest(value=value), self.assertRaises(InputError):
                validate_rows([value, raw_rows()[1]], CUTOFF)

    def test_identifiers_reject_controls_whitespace_and_surrogates(self):
        for value in ("", " leading", "trailing ", "line\nbreak", "tab\t", "\x00",
                      "\ud800", "\udfff", "invisible\u200b", "bidi\u202e", "a\u2028b"):
            for field in ("row_id", "observation_id", "entity_id"):
                with self.subTest(field=field, value=repr(value)):
                    self.assert_invalid_change(field, value)

    def test_unicode_scalar_identifiers_are_valid(self):
        rows = raw_rows()
        rows[0]["row_id"] = "観測-é-😀"
        self.assertEqual(validate_rows(rows, CUTOFF)[0]["row_id"], "観測-é-😀")

    def test_duplicate_row_and_unknown_splits_rejected(self):
        rows = raw_rows()
        rows[1]["row_id"] = rows[0]["row_id"]
        with self.assertRaises(InputError):
            validate_rows(rows, CUTOFF)
        for split in ("test", "Train", "train "):
            self.assert_invalid_change("split", split)

    def test_temporal_ordering_is_validated(self):
        self.assert_invalid_change("label_end_time", "2025-01-13T00:00:00Z")
        self.assert_invalid_change("prediction_time", CUTOFF_TEXT)
        rows = raw_rows()
        rows[1]["prediction_time"] = "2025-01-14T23:59:59.999999Z"
        with self.assertRaises(InputError):
            validate_rows(rows, CUTOFF)

    def test_late_feature_is_a_finding_not_malformed_input(self):
        rows = raw_rows()
        rows[0]["feature_available_time"] = "2025-01-16T00:00:00Z"
        self.assertEqual(len(validate_rows(rows, CUTOFF)), 2)

    def test_json_shape_duplicate_keys_constants_and_syntax(self):
        for text in ('{}', 'null', '"rows"', '[{"row_id":"a","row_id":"b"}]',
                     '[NaN]', '[Infinity]', '[', '{broken}'):
            with self.subTest(text=text), self.assertRaises(InputError):
                parse_rows(text, "json")

    def test_lone_surrogate_from_json_is_rejected(self):
        rows = raw_rows()
        rows[0]["row_id"] = "\ud800"
        with self.assertRaises(InputError):
            validate_rows(parse_rows(json.dumps(rows), "json"), CUTOFF)

    def test_huge_json_integer_is_rejected_without_traceback(self):
        # Python versions with a digit cap fail at parse time; others reject the
        # resulting non-object row during normal validation.
        with self.assertRaises(InputError):
            validate_rows(parse_rows("[" + "9" * 5000 + "]", "json"), CUTOFF)

    def test_csv_header_row_lengths_and_quoting(self):
        header = ",".join(FIELDS)
        invalid = ["", header.replace("entity_id", "row_id"), header + ",extra",
                   header + "\nshort,row", header + '\n"unterminated', header + "\n\n"]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(InputError):
                parse_rows(text, "csv")

    def test_csv_json_parity_and_header_order(self):
        rows = raw_rows()
        rows[0]["entity_id"] = 'entity, with "quotes"'
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(reversed(FIELDS)))
        writer.writeheader()
        writer.writerows(rows)
        self.assertEqual(validate_rows(parse_rows(stream.getvalue(), "csv"), CUTOFF),
                         validate_rows(parse_rows(json.dumps(rows), "json"), CUTOFF))

    def test_unreadable_and_invalid_utf8_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for mode in ("missing", "invalid_utf8"):
                if mode == "invalid_utf8":
                    path.write_bytes(b"\xff")
                with self.subTest(mode=mode), self.assertRaises(InputError):
                    load_rows(path, "json", CUTOFF)


class ReportsAndCliTests(unittest.TestCase):
    def run_cli(self, rows, *extra):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            code = main([str(path), "--cutoff", CUTOFF_TEXT, "--input-format", "json", *extra],
                        stdout=out, stderr=err)
            return code, out.getvalue(), err.getvalue()

    def test_clean_exit_and_canonical_report(self):
        code, output, errors = self.run_cli(raw_rows())
        self.assertEqual((code, errors), (0, ""))
        result = json.loads(output)
        self.assertEqual(result["cutoff"], CANONICAL)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["summary"]["by_rule"], dict.fromkeys(RULES, 0))
        self.assertEqual(set(result), {"schema_version", "cutoff", "rows", "summary", "findings"})
        self.assertEqual(output, render_json(result))

    def test_findings_exit_counts_and_input_order_invariance(self):
        rows = raw_rows()
        rows[0]["feature_available_time"] = "2025-01-14T00:00:00.000001Z"
        rows[0]["label_end_time"] = "2025-01-15T00:00:00.000001Z"
        first = self.run_cli(rows)
        self.assertEqual(first, self.run_cli(list(reversed(rows))))
        code, output, errors = first
        self.assertEqual((code, errors), (1, ""))
        result = json.loads(output)
        self.assertEqual(result["summary"]["finding_count"], 2)
        self.assertEqual(result["summary"]["affected_row_count"], 1)

    def test_later_invalid_row_produces_no_partial_audit(self):
        rows = raw_rows()
        rows[0]["feature_available_time"] = "2025-01-16T00:00:00Z"
        rows[1]["entity_id"] = "\ud800"
        code, output, error = self.run_cli(rows)
        self.assertEqual((code, output), (2, ""))
        self.assertEqual(error, "error: row 2: invalid identifier in entity_id\n")

    def test_argument_error_has_no_audit(self):
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(main([], stdout=out, stderr=err), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertTrue(err.getvalue().startswith("error:"))

    def test_markdown_escapes_identifier_injection_once(self):
        rows = raw_rows()
        rows[0]["row_id"] = '<script>|`[link](target)\\#😀'
        rows[0]["feature_available_time"] = "2025-01-14T00:00:01Z"
        code, output, error = self.run_cli(rows, "--format", "markdown")
        self.assertEqual((code, error), (1, ""))
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;&#124;&#96;&#91;link&#93;", output)
        self.assertNotIn("&&#35;", output)
        self.assertIn("Findings: 1; affected rows: 1", output)
        self.assertIn("A clean report is not proof", output)

    def test_clean_markdown_and_json_unicode_encoding(self):
        rows = raw_rows()
        code, output, errors = self.run_cli(rows, "--format", "markdown")
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("No declared-rule findings were found.", output)
        rows[0]["row_id"] = "観測"
        rows[0]["feature_available_time"] = "2025-01-14T00:00:01Z"
        output = self.run_cli(rows)[1]
        self.assertTrue(output.isascii())
        self.assertEqual(json.loads(output)["findings"][0]["row_ids"], ["観測"])

    def test_output_error_returns_two(self):
        class BrokenStream:
            def write(self, text):
                raise OSError("do not expose private output details")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(raw_rows()), encoding="utf-8")
            errors = io.StringIO()
            code = main([str(path), "--cutoff", CUTOFF_TEXT, "--input-format", "json"],
                        stdout=BrokenStream(), stderr=errors)
            self.assertEqual(code, 2)
            self.assertEqual(errors.getvalue(), "error: output stream is unavailable\n")

    def test_buffered_flush_error_returns_two(self):
        class FailsOnFlush(io.StringIO):
            def flush(self):
                raise OSError("private sink detail")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(raw_rows()), encoding="utf-8")
            errors = io.StringIO()
            code = main([str(path), "--cutoff", CUTOFF_TEXT, "--input-format", "json"],
                        stdout=FailsOnFlush(), stderr=errors)
            self.assertEqual(code, 2)
            self.assertEqual(errors.getvalue(), "error: output stream is unavailable\n")

    def test_closed_output_and_diagnostic_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(raw_rows()), encoding="utf-8")
            closed = io.StringIO()
            closed.close()
            errors = io.StringIO()
            args = [str(path), "--cutoff", CUTOFF_TEXT, "--input-format", "json"]
            self.assertEqual(main(args, stdout=closed, stderr=errors), 2)
            self.assertEqual(errors.getvalue(), "error: output stream is unavailable\n")
            self.assertEqual(main([], stdout=io.StringIO(), stderr=closed), 2)

    def test_failed_default_output_is_closed_before_shutdown(self):
        class FailsOnFlush(io.StringIO):
            def flush(self):
                raise OSError("sink failed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(raw_rows()), encoding="utf-8")
            sink = FailsOnFlush()
            with contextlib.redirect_stdout(sink):
                code = main([str(path), "--cutoff", CUTOFF_TEXT, "--input-format", "json"],
                            stderr=io.StringIO())
            self.assertEqual(code, 2)
            self.assertTrue(sink.closed)

    def test_help_version_use_checked_injected_output(self):
        for flag in ("--help", "-h", "-hh", "--version"):
            with self.subTest(flag=flag):
                out, err = io.StringIO(), io.StringIO()
                self.assertEqual(main([flag], stdout=out, stderr=err), 0)
                self.assertTrue(out.getvalue())
                self.assertEqual(err.getvalue(), "")
                out.close()
                self.assertEqual(main([flag], stdout=out, stderr=err), 2)

    def test_help_version_flush_failures_and_default_diagnostic_cleanup(self):
        class FailsOnFlush(io.StringIO):
            def flush(self):
                raise OSError("buffer failed")
        for flag in ("--help", "-hh", "--version"):
            with self.subTest(flag=flag), contextlib.redirect_stdout(FailsOnFlush()) as sink:
                self.assertEqual(main([flag], stderr=io.StringIO()), 2)
                self.assertTrue(sink.closed)
        with contextlib.redirect_stderr(FailsOnFlush()) as sink:
            self.assertEqual(main([], stdout=io.StringIO()), 2)
            self.assertTrue(sink.closed)


if __name__ == "__main__":
    unittest.main()
