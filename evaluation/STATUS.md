# Evaluation status

The twelve primary synthetic fixtures were evaluated on **2026-10-07** with
**Python 3.14.7**. All **13 checks passed** across **48 rows**. Measured findings
matched the independently declared truth. [RESULTS.md](RESULTS.md) and
[RESULTS.json](RESULTS.json) contain aggregate and per-fixture counts, defined
precision/recall ratios, exact source hashes, and resource-accounting limitations.

The literal truth in [TRUTH.md](TRUTH.md) remains the predeclared specification;
the result files contain measurements and explicitly identified derivations.
No real-world detection performance or large-input scalability is claimed.

Small ordinary behavior checks are separate from the formal fixture evaluation.
Clean offline installation passed in a fresh Python 3.14.7 virtual environment;
see [installation verification](../docs/INSTALLATION.md). Compatibility with other
Python versions remains unverified. Remote publication verification is pending,
and no remote delivery is claimed.
