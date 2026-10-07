# Provenance

All source, documentation, examples, and fixture definitions were written for
this project. No external dataset or third-party source code is included.

The demo uses invented IDs and dates. The twelve evaluation fixtures use an
explicit public cutoff, integer offsets, four invented rows per case, and seed
1729 for row ordering. No parameters came from real observations or private
records. An independent reviewer prepared the fixture generator and literal
truth before inspecting the detector. See [TRUTH.md](../evaluation/TRUTH.md).

Runtime dependencies are Python standard-library modules. `setuptools` is a
declared build-tool requirement only; it is not vendored or installed by the
application. There are no hosted jobs, workflows, service calls, or telemetry.

No license has been selected for this project. This document describes origin;
it does not grant a license.
