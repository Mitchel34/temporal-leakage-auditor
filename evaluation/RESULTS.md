# Synthetic evaluation results

On **2026-10-07**, the fixed **12 fixtures / 48 rows** passed all **13 checks**
on **Python 3.14.7, macOS (Darwin), arm64**. These checks compare exact ordered
findings with independently declared truth, verify unchanged input, and
reconcile aggregate counts. The protocol returned 86 numeric metrics.

These results cover the declared synthetic predicates. They do not establish
real-world sensitivity, model quality, or large-input scalability.

## Aggregate counts

The unit is `(fixture, rule, row_id)`. Only training rows are eligible for label
overlap. Precision and recall are ratios of the counts below.

| Rule | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `late_feature` | 3 | 0 | 0 | 45 | 1.0 | 1.0 |
| `label_overlap` | 3 | 0 | 0 | 21 | 1.0 | 1.0 |
| `cross_split_duplicate` | 6 | 0 | 0 | 42 | 1.0 | 1.0 |

## Fixture counts

Each cell is **TP / FP / FN / TN**. TP and FP were measured. FN and TN
are derived from those measurements and the literal positives and eligible
units in [TRUTH.md](TRUTH.md). The derived counts reconcile exactly with the
aggregate counts returned by the evaluation.

| Fixture | Late feature | Label overlap | Cross-split duplicate |
| --- | --- | --- | --- |
| F01 | 1 / 0 / 0 / 3 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |
| F02 | 1 / 0 / 0 / 3 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |
| F03 | 1 / 0 / 0 / 3 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |
| F04 | 0 / 0 / 0 / 4 | 1 / 0 / 0 / 1 | 0 / 0 / 0 / 4 |
| F05 | 0 / 0 / 0 / 4 | 1 / 0 / 0 / 1 | 0 / 0 / 0 / 4 |
| F06 | 0 / 0 / 0 / 4 | 1 / 0 / 0 / 1 | 0 / 0 / 0 / 4 |
| F07 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 2 / 0 / 0 / 2 |
| F08 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 2 / 0 / 0 / 2 |
| F09 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 2 / 0 / 0 / 2 |
| F10 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |
| F11 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |
| F12 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 2 | 0 / 0 / 0 / 4 |

[RESULTS.json](RESULTS.json) contains every fixture's counts and ratios.
Precision or recall with a zero denominator is `null`, including all-negative
fixture/rule combinations; undefined ratios are never replaced with 1.

## Resources and method

The reviewed, standard-library evaluation ran in one local compute process
with one supervisor. The runner used direct-child `wait4` accounting.

| Quantity | Observed or charged value | Interpretation |
| --- | ---: | --- |
| Charged CPU | 10.0 seconds | Full conservative reservation; no refund. |
| Observed CPU before final closeout | 0.079592 seconds | Child plus supervisor; a lower bound excluding final receipt and database closeout. |
| Runner wall time | 0.094976 seconds | Includes supervision through child termination accounting; excludes final receipt and database closeout. |
| Memory | 58,261,504 bytes | Sum of child and supervisor high-water marks; not simultaneous RSS. |

The operational budgets were 10 CPU seconds, 30 wall seconds, and 256 MiB
of memory. Operational memory sampling can overshoot and is not a hard
containment guarantee. No external service was used. This single tiny run
is functional verification, not a repeated-run timing or scalability study.

## Exact source and reproduction

The evaluated bundle was assembled from the unchanged detector, fixture
definitions, and protocol; their SHA-256 hashes are in RESULTS.json.

```text
f4c475f10acd297f1087f093d649267e7f7bbab3c641dfcb8b2b78df8ebfda36
```

Follow [the reproduction instructions](README.md) to build the same bundle
and run its small deterministic protocol. The plain reproduction command
reproduces predicates and counts; it does not recreate the supervised
resource measurement. The runner name, digest, and measurement method are
recorded in RESULTS.json.
