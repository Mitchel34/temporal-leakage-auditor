"""Tiny scoring-contract checks with hand-declared outputs, not an evaluation."""

import copy
import unittest

from evaluation.protocol import score_fixture


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.case = {"rows": [{"row_id": "t", "split": "train"},
                              {"row_id": "v", "split": "validation"}],
                     "truth": [("late_feature", "t")]}
        self.finding = {"rule": "late_feature", "row_ids": ["t"],
                        "severity": "error", "reason": "Reason", "repair": "Repair"}

    def test_counts_include_missed_and_false_findings(self):
        exact, counts = score_fixture([dict(self.finding, row_ids=["v"])], self.case)
        self.assertFalse(exact)
        self.assertEqual(counts["late_feature"], {"tp": 0, "fp": 1, "fn": 1, "tn": 0})
        self.assertEqual(counts["label_overlap"], {"tp": 0, "fp": 0, "fn": 0, "tn": 1})

    def test_exactness_preserves_emission_order(self):
        case = copy.deepcopy(self.case)
        case["truth"].append(("cross_split_duplicate", "v"))
        second = dict(self.finding, rule="cross_split_duplicate", row_ids=["v"])
        self.assertTrue(score_fixture([self.finding, second], case)[0])
        self.assertFalse(score_fixture([second, self.finding], case)[0])

    def test_duplicate_emissions_rejected_before_set_scoring(self):
        with self.assertRaises(ValueError):
            score_fixture([self.finding, self.finding], self.case)

    def test_unknown_and_ineligible_emissions_rejected(self):
        for finding in (dict(self.finding, rule="unknown"),
                        dict(self.finding, row_ids=["missing"]),
                        dict(self.finding, rule="label_overlap", row_ids=["v"]),
                        dict(self.finding, row_ids=["t", "v"]),
                        dict(self.finding, repair="")):
            with self.subTest(finding=finding), self.assertRaises(ValueError):
                score_fixture([finding], self.case)

    def test_exact_result_and_denominators(self):
        exact, counts = score_fixture([self.finding], self.case)
        self.assertTrue(exact)
        self.assertEqual(counts["late_feature"], {"tp": 1, "fp": 0, "fn": 0, "tn": 1})
        self.assertEqual(counts["cross_split_duplicate"], {"tp": 0, "fp": 0, "fn": 0, "tn": 2})


if __name__ == "__main__":
    unittest.main()
