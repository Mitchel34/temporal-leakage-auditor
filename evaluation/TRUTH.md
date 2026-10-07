# Synthetic fixture definitions and literal truth

These twelve small cases are original synthetic inputs. Their expected findings
are declared below and literally in `fixtures.py`; they are not calculated by a
detector. This document specifies expected behavior, not measured results.

`fixture_cases(seed=1729)` returns cases in order F01 through F12. Each case has
exactly `fixture_id`, `cutoff`, `rows`, and `truth`. Each case is a separate input
with four rows named `t1`, `t2`, `v1`, and `v2`. The seed changes only row order
using a local random-number generator. Repeated calls with the same seed and
interpreter produce the same order, without changing global random state.
Changing the seed does not change identities, timestamps, or truth.

## Baseline and representation

The cutoff is `2025-01-15T00:00:00.000000Z`, or **1736899200000000** integer UTC
microseconds since `1970-01-01T00:00:00Z`. One second is 1000000 microseconds;
one day is 86400000000 microseconds. All arithmetic is integer arithmetic.

Each normalized row has exactly seven fields: `row_id`, `observation_id`,
`entity_id`, `split`, `prediction_time`, `feature_available_time`, and
`label_end_time`. The first four are strings; the last three are integer UTC
microseconds. The CSV/JSON interface uses timestamp strings, so these normalized
rows are intended for the pure detector after the parsing boundary.

| Row | Split | Prediction relative to cutoff | Baseline label end |
| --- | --- | --- | --- |
| `t1` | `train` | −3 days | prediction +1 day |
| `t2` | `train` | −2 days | prediction +1 day |
| `v1` | `validation` | +2 days | prediction +1 day |
| `v2` | `validation` | +3 days | prediction +1 day |

Baseline feature availability equals prediction. Baseline observation and entity
IDs are distinct for all four rows, respectively `observation_` and `entity_`
followed by the row ID. All fields remain at baseline unless changed below.

## Exact expected findings

Findings are ordered by `late_feature`, `label_overlap`,
`cross_split_duplicate`, then lexical row ID. Each listed pair must occur
exactly once; an empty list means there must be no findings.

| Fixture | Modification | Literal positive `(rule, row_id)` pairs |
| --- | --- | --- |
| F01 | `t1` feature availability = prediction +1 microsecond | `[('late_feature', 't1')]` |
| F02 | `v1` feature availability = prediction +1 second | `[('late_feature', 'v1')]` |
| F03 | `t2` feature availability = prediction +1 day | `[('late_feature', 't2')]` |
| F04 | `t1` label end = cutoff +1 microsecond | `[('label_overlap', 't1')]` |
| F05 | `t1` label end = cutoff +1 second | `[('label_overlap', 't1')]` |
| F06 | `t1` label end = cutoff +1 day | `[('label_overlap', 't1')]` |
| F07 | Duplicate pair at cutoff ±1 microsecond, as defined below | `[('cross_split_duplicate', 't1'), ('cross_split_duplicate', 'v1')]` |
| F08 | Duplicate pair at cutoff ±1 second, as defined below | `[('cross_split_duplicate', 't1'), ('cross_split_duplicate', 'v1')]` |
| F09 | Duplicate pair at cutoff ±1 day, as defined below | `[('cross_split_duplicate', 't1'), ('cross_split_duplicate', 'v1')]` |
| F10 | `t1` label end = cutoff; `v1` prediction and availability = cutoff; `v1` label end = cutoff +1 day | `[]` |
| F11 | All four entity IDs = `entity_shared`; observation IDs remain distinct | `[]` |
| F12 | Both training label ends = cutoff −1 microsecond; all four feature times = prediction −1 microsecond | `[]` |

For F07–F09, `t1` and `v1` share `observation_shared`. For the declared positive
offset, set `t1` prediction and feature availability to cutoff minus the offset
and its label end to cutoff. Set `v1` prediction and feature availability to
cutoff plus the offset and its label end to its new prediction plus one day.
The two entity IDs stay distinct. These offsets vary the examples; the duplicate
rule itself has no temporal-distance threshold.

The label convention is `[prediction_time, label_end_time)`. Ending exactly at
cutoff is clean, and feature availability exactly at prediction is clean.
Validation predictions may equal cutoff. Repeated entity identity by itself is
not a finding.

## Accounting

The unit is `(fixture, rule, row_id)`. In each fixture, four rows are eligible
for `late_feature`, two training rows for `label_overlap`, and four rows for
`cross_split_duplicate`. Validation rows are not label-overlap true negatives.

| Rule | Eligible units across 12 cases | Literal positive units | Literal negative units |
| --- | ---: | ---: | ---: |
| `late_feature` | 48 | 3 | 45 |
| `label_overlap` | 24 | 3 | 21 |
| `cross_split_duplicate` | 48 | 6 | 42 |

For an observed TP and FP count, derive FN as literal positives minus TP, and
TN as eligible units minus literal positives minus FP. Undefined precision or
recall is `null`. Correct classification would yield TP/FP/FN/TN of 3/0/0/45,
3/0/0/21, and 6/0/0/42 respectively. These are expected counts, not an evaluation
claim. Compare exact ordered findings and reject duplicate, unknown, or
ineligible emissions before scoring; set equality alone can hide duplicates.

These small synthetic cases demonstrate declared predicate boundaries. They do
not measure real-world sensitivity, validate timestamp provenance, inspect
feature lineage, or establish that a model is free of temporal leakage.
