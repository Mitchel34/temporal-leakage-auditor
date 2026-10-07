# Verification status

Current evidence covers **41 ordinary local tests**, all passing on **Python
3.14.7**, and the documented source-tree CLI examples. No child processes are
created by the test suite. The declared Python 3.10 minimum remains untested.

Reproduce the behavior checks:

```sh
python3 -B -m unittest discover -s tests -v
```

Verified demo outcomes:

| Input / output | Exit code | Findings |
| --- | ---: | ---: |
| `examples/clean.csv` / JSON | 0 | 0 |
| `examples/leaky.csv` / JSON | 1 | 4 |
| `examples/leaky.json` / Markdown | 1 | 4 |

The four leaky findings comprise one late feature, one label overlap, and two
cross-split duplicate occurrences. These are small usage checks, not a measured
precision/recall evaluation.

An independent review identified error paths for large JSON integers, delayed
output failures, and closed streams. Regression tests cover their corrections.
An initial test also caught acceptance of `24:00:00` by a permissive timestamp
parser; explicit calendar-component validation now enforces the contract.

The **twelve-fixture primary evaluation passed** on Python 3.14.7. All 13 checks
passed across 48 synthetic rows. Exact findings matched independently declared
truth, inputs remained unchanged, and aggregate counts reconciled. See
[the measured results](../evaluation/RESULTS.md) for per-fixture counts,
source hashes, and resource-accounting methods.

The evaluation conservatively charged the full 10 CPU seconds reserved. Observed
CPU before final closeout was 0.079592 seconds, which is a lower bound rather than
complete end-to-end usage. Reported memory was 58,261,504 bytes, the sum of process
high-water marks rather than simultaneous RSS. Memory control was operational,
not a hard containment guarantee.

Clean offline installation also **passed**. An existing Python 3.11.13 build
toolchain produced the original package's wheel without a package index,
dependency downloads, or isolated build-dependency installation. The wheel was
installed into a fresh Python 3.14.7 virtual environment using its locally
bundled `ensurepip` support. The installed import path was inside that virtual
environment, and both package and distribution versions were 0.1.0.

From outside the source tree, the installed CLI returned 0 with no findings for
the clean CSV and 1 with four findings for each leaky CSV/JSON input. All nine
build/install/verification steps returned their expected exit codes. See
[INSTALLATION.md](INSTALLATION.md) for reproduction commands and
[INSTALLATION.json](INSTALLATION.json) for sanitized evidence and the tested wheel
hash. Python 3.11.13 was used only for building; it was not qualified as a runtime.

**Remote publication verification is pending.** No complete remote delivery,
scalability, or real-world detection-performance claim is made.
