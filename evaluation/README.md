# Reproducible evaluation protocol

The primary evaluation is the twelve four-row cases in [TRUTH.md](TRUTH.md).
Expected labels are literal and independent of detector decisions. No large
scaling case is part of this primary protocol.

`protocol.evaluate_with(detector, cases_factory)` checks exact ordered findings,
duplicate/unknown/ineligible emissions, unchanged input, and aggregate truth.
The detector is the same `core.audit_rows()` used by the CLI.

Prepare a self-contained source file without executing an evaluation:

```sh
python3 evaluation/build_bundle.py evaluation/bundle.py
```

The builder embeds the exact bytes of `core.py`, `fixtures.py`, and `protocol.py`,
with relative source names and SHA-256 hashes. It refuses to overwrite an existing
file, validates syntax, and enforces a 128 KiB source-size limit. Its `evaluate()`
entry point returns named Boolean checks and numeric metrics. No detector logic
is reimplemented in the bundle. The bundle imports only the standard library and
its evaluation function performs no filesystem, network, or subprocess operations.

For an independently authorized local reproduction of that tiny protocol:

```sh
python3 -c 'import json, runpy; m = runpy.run_path("evaluation/bundle.py"); print(json.dumps(m["evaluate"](), indent=2, sort_keys=True))'
```

This plain reproduction command does not provide process supervision, memory
containment, or a measured resource receipt. A reported evaluation must identify
the exact source hash, Python version, command/runner, outcomes, and measurement
method. The initial supervised evaluation passed all 13 checks across 12 fixtures
and 48 rows on Python 3.14.7. See [RESULTS.md](RESULTS.md) for its measured counts,
source hash, resource-accounting method, and limitations, and [STATUS.md](STATUS.md)
for the remaining verification work.

## Counts and ratios

The unit is `(fixture, rule, row_id)`. All four rows are eligible for feature and
duplicate rules; only two training rows are eligible for label overlap.
Return per-fixture/per-rule measured TP and FP (72 metrics), aggregate TP/FP/FN/TN
for three rules (12), fixture count, and row count: **86 metrics** in total.

For each published fixture/rule, derive FN = literal positives − TP and
TN = eligible rows − literal positives − FP. Publish all four counts. Precision
is TP/(TP+FP), recall is TP/(TP+FN); an undefined ratio is `null`. Do not replace an
undefined ratio with 1. The literal counts needed for derivation are in TRUTH.md.

Keep full resource measurement separate from predicate counts. State whether CPU
is measured or conservatively charged, whether wall time includes supervision,
and whether memory is simultaneous RSS or a sum of process high-water marks.
Operational sampling can overshoot; it is not a hard memory guarantee.
