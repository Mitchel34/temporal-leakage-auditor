# Input and output contract, version 1

`python3 -m temporal_leakage_auditor INPUT --cutoff TIMESTAMP --input-format {csv,json}
[--format {json,markdown}]` reads a UTF-8 file. JSON is the default output format.
Output goes to stdout; diagnostics go to stderr. Exit codes are 0 for a clean
audit, 1 for findings, and 2 for invalid arguments/input or output failures.

## Validation

CSV requires a header. JSON requires an array of objects. Both require exactly
`row_id`, `observation_id`, `entity_id`, `split`, `prediction_time`,
`feature_available_time`, and `label_end_time`; every value is a string.
Additional payload/feature columns must be removed explicitly before auditing.

Reject empty input, a missing split, duplicate CSV headers or JSON object keys,
uneven CSV records, malformed CSV/JSON, non-string fields, missing/extra fields,
duplicate `row_id` values, and undefined split names. Empty CSV records are not
silently skipped. A UTF-8 byte-order mark is not part of the accepted header or
JSON syntax. Validation completes before any audit output.

IDs are nonempty, case-sensitive Unicode scalar strings without leading/trailing
whitespace. Unicode control/format characters, surrogate code points, and line or
paragraph separators are rejected. IDs are not case-folded or Unicode-normalized.
Repeated `entity_id` values are legal. Same-split observation duplicates are legal
input and are not flagged by the cross-split rule.

Times use `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`, with one to six fractional digits if a
fraction is present. Only ASCII digits are allowed. Valid years are 0001–9999,
hours 00–23, minutes/seconds 00–59, and valid calendar dates. All time comparisons
use integer UTC microseconds, with no floating-point rounding.

The cutoff is mandatory and never inferred. Every training prediction must be
strictly before cutoff; every validation prediction must be at or after it.
`label_end_time >= prediction_time` is required. An empty half-open label interval
is allowed. Availability later than prediction is a finding, not an input error.

## Rules

1. `late_feature`: availability is strictly after prediction, in either split.
2. `label_overlap`: a training row's half-open label interval ends strictly after
   cutoff. An end equal to cutoff is clean. Validation rows are ineligible.
3. `cross_split_duplicate`: an observation ID appears in both splits. Every
   occurrence on both sides is marked, regardless of its temporal distance.

Each finding has exactly `rule`, `row_ids` (one-element array), `severity` (`error`),
`reason`, and `repair`. Findings are sorted by the rule order above, then Unicode
lexical `row_id` order. Repeated emissions for the same rule/row are not allowed.

## Reports

JSON has exactly `schema_version` (1), `cutoff` (UTC with six fractional digits),
`rows` (`total`, `train`, `validation`), `summary` (`finding_count`,
`affected_row_count`, `by_rule` containing all three rule IDs), and `findings`.
Object keys are sorted, indentation is two spaces, non-ASCII text is escaped,
numbers are finite, and the document ends in one newline. No runtime timestamps,
file paths, machine identities, or randomness enter an audit report.

Markdown contains the same counts and findings, with identifiers escaped as
table text. It includes the limitation that a clean report does not prove a
leakage-free model. A stream failure can leave partial bytes at the destination;
that is an output failure with exit code 2, not a successful report. Malformed
input produces no partial audit.

The importable `core.audit_rows()` expects already-validated normalized rows;
use the CLI/input layer for untrusted CSV/JSON. The detector never changes its
input. It uses linear lookup storage and sorts findings; no scalability benchmark
has been claimed.
