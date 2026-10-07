# Temporal Leakage Auditor

An offline Python CLI that audits declared temporal metadata in training and
validation splits. It explains late feature availability, training label windows
that overlap validation, and observation IDs reused across splits.

The runtime uses only Python's standard library. It does not train a model,
contact a service, infer missing timestamps, or modify your data.

**Local verification complete:** behavior tests, the synthetic evaluation, and
clean offline installation passed. Remote publication verification is pending.

## Try the demo

From the source directory with Python 3.10 or later:

```sh
python3 -m temporal_leakage_auditor examples/leaky.csv \
  --input-format csv --cutoff 2025-01-15T00:00:00Z

python3 -m temporal_leakage_auditor examples/leaky.json \
  --input-format json --cutoff 2025-01-15T00:00:00Z --format markdown

python3 -m temporal_leakage_auditor examples/clean.csv \
  --input-format csv --cutoff 2025-01-15T00:00:00Z
```

The leaky demo should report four findings: a late feature and an overlapping
label for `train-a`, plus a cross-split duplicate for both `train-a` and
`validation-a`. Its exit code is **1**, indicating findings, not a parsing failure.
The clean example should return **0**. Malformed input or an output error returns
**2** and a short diagnostic on stderr.

Use shell redirection to save a JSON or Markdown report. Input format is explicit;
there is no URL or stdin mode. `--help` and `--version` require no input file.

## Input

CSV headers and JSON row objects must contain exactly these seven fields; all
input values are strings:

| Field | Meaning |
| --- | --- |
| `row_id` | Unique row occurrence; findings refer to this ID. |
| `observation_id` | Stable observation identity, compared across splits. |
| `entity_id` | Entity identity; repetition is allowed. |
| `split` | `train` or `validation`. |
| `prediction_time` | When the prediction would be made. |
| `feature_available_time` | When all represented features were available. |
| `label_end_time` | Exclusive end of the label interval. |

Timestamps must be UTC, for example `2025-01-15T00:00:00Z` or
`2025-01-15T00:00:00.000001Z`. Offsets, naive times, leap seconds, `24:00:00`, and
precision beyond six fractional digits are rejected. Both splits must be present.
Training predictions precede the explicit cutoff; validation predictions are at
or after it. Label ends cannot precede prediction times.

The detector treats label windows as **half-open**: `[prediction_time, label_end_time)`.
A feature available exactly at prediction is allowed. A training label ending
exactly at cutoff is allowed. Confirm these conventions match your label semantics.

See [the full contract](docs/SPEC.md) for validation and output details.

## What the findings mean

| Rule | Trigger | Suggested response |
| --- | --- | --- |
| `late_feature` | Availability is later than prediction. | Use only available features or change prediction time. |
| `label_overlap` | A training label ends after validation begins. | Exclude the overlapping row or move the split boundary. |
| `cross_split_duplicate` | An observation ID occurs in both splits. | Keep the observation in one split and verify stable identity. |

Each rule emits one finding per affected row. A row can have several findings.
Ordering is deterministic: the rules above, then lexical row ID. JSON and Markdown
contain the same audit information; JSON is intended for downstream tooling.

## Verification and status

```sh
python3 -B -m unittest discover -s tests -v
```

All **41 tests passed on Python 3.14.7**. The tests use tiny in-process examples,
including exact temporal boundaries,
invalid input, deterministic reports, and scoring-error checks. They create no
subprocesses. The [twelve-fixture protocol](evaluation/TRUTH.md) was prepared
independently of the detector. Its local evaluation passed all **13 checks
across 12 fixtures and 48 rows**. [Measured results](evaluation/RESULTS.md) report
the confusion counts and resource-accounting limits. These synthetic results do
not estimate real-world detection performance.

Source-tree execution has no third-party runtime dependency. Packaging metadata
and **clean offline installation are verified on Python 3.14.7**. The installed
package was imported from a fresh virtual environment, and its CLI reproduced the
clean and leaky examples from outside the source tree. See
[installation instructions and evidence](docs/INSTALLATION.md).

Building a distribution requires an existing compatible setuptools toolchain;
the runtime has no third-party dependencies. The declared Python 3.10 minimum
remains untested. Using Python 3.11.13 to build the wheel does not establish
runtime compatibility on that version.

## Limits

A clean audit is **not proof of leakage-free modeling**. The tool trusts the
provided timestamps and IDs. It does not inspect feature lineage, preprocessing
fit history, target encoding, undocumented publication delays, or data provenance.
One availability time summarizes all features in a row. Same-split duplicates and
entity/group contamination are outside these three rules. Synthetic cases verify
declared predicates, not real-world sensitivity or model quality.

Inputs and findings are held in memory; large-file scalability has not been
measured. Original synthetic examples and their provenance are documented in
[PROVENANCE.md](docs/PROVENANCE.md). No license grant has been selected.
