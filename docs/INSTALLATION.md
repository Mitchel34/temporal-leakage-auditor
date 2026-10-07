# Offline installation and verification

Clean installation of version **0.1.0 passed on Python 3.14.7** on 2026-10-07.
The package was imported from a fresh virtual environment, and its installed CLI
ran from outside the source tree. The runtime uses only Python's standard library.

## Available tools

The verified build used tools already installed locally:

| Tool | Version | Role |
| --- | --- | --- |
| Python | 3.11.13 | Build the wheel. |
| setuptools | 80.9.0 | Existing build backend; the project declares setuptools >=68. |
| wheel | 0.45.1 | Existing wheel build support. |
| pip | 25.1.1 | Build-toolchain pip. |
| Python | 3.14.7 | Fresh installation and runtime checks. |

Python 3.14.7 supplied local `venv`/`ensurepip` support. No build dependencies or
runtime dependencies were downloaded. Python 3.11.13 was used for building only;
this does not establish runtime compatibility on that version. The declared
Python >=3.10 minimum also remains untested.

## Reproduce the offline procedure

Start in the project source directory. These POSIX-shell commands assume the
existing build tools are available through `python3.11`, and `python3.14` has
working local `venv`/`ensurepip` support. Adjust the interpreter names for your
installed tools. If those prerequisites are unavailable, this offline route
cannot install or download them for you. Source-tree usage remains available as
shown in the project README.

Copy only the package, its packaging metadata, and the synthetic examples into a
fresh temporary working directory:

```sh
install_work="$(mktemp -d)"
mkdir -p "$install_work/source/temporal_leakage_auditor" \
  "$install_work/wheels" "$install_work/fixtures" "$install_work/outside"
cp pyproject.toml "$install_work/source/"
cp temporal_leakage_auditor/*.py "$install_work/source/temporal_leakage_auditor/"
cp examples/clean.csv examples/leaky.csv examples/leaky.json "$install_work/fixtures/"
```

Build with the existing toolchain, then create a fresh target environment and
install the resulting wheel. `--no-index`, `--no-deps`, and
`--no-build-isolation` keep the build dependent on the already available tools.

```sh
python3.11 -B -I -m pip --isolated --disable-pip-version-check wheel \
  --no-index --no-deps --no-build-isolation --no-cache-dir \
  --wheel-dir "$install_work/wheels" "$install_work/source"

python3.14 -B -I -m venv "$install_work/venv"

"$install_work/venv/bin/python" -B -I -m pip --isolated \
  --disable-pip-version-check install --no-index --no-deps --no-cache-dir \
  "$install_work/wheels/temporal_leakage_auditor-0.1.0-py3-none-any.whl"
```

Move outside both the project checkout and the copied source. Verify that Python
imports the installed package from the virtual environment and that both version
declarations agree:

```sh
cd "$install_work/outside"

"$install_work/venv/bin/python" -B -I -c '
import importlib.metadata as metadata
import pathlib
import sys
import temporal_leakage_auditor as auditor
assert sys.prefix != sys.base_prefix
assert pathlib.Path(auditor.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
assert auditor.__version__ == "0.1.0"
assert metadata.version("temporal-leakage-auditor") == "0.1.0"
print(auditor.__version__)
'

"$install_work/venv/bin/python" -B -I \
  "$install_work/venv/bin/temporal-leakage-auditor" --version
```

Run the installed console entry point against the copied synthetic examples:

```sh
"$install_work/venv/bin/python" -B -I \
  "$install_work/venv/bin/temporal-leakage-auditor" \
  "$install_work/fixtures/clean.csv" --input-format csv \
  --cutoff 2025-01-15T00:00:00Z

"$install_work/venv/bin/python" -B -I \
  "$install_work/venv/bin/temporal-leakage-auditor" \
  "$install_work/fixtures/leaky.csv" --input-format csv \
  --cutoff 2025-01-15T00:00:00Z

"$install_work/venv/bin/python" -B -I \
  "$install_work/venv/bin/temporal-leakage-auditor" \
  "$install_work/fixtures/leaky.json" --input-format json \
  --cutoff 2025-01-15T00:00:00Z
```

The leaky examples intentionally return exit code **1** to signal findings.
Account for that expected code when using a shell with `set -e`.

## Verified outcomes

| Installed input | Exit code | Findings |
| --- | ---: | ---: |
| Clean CSV | 0 | 0 |
| Leaky CSV | 1 | 4 |
| Leaky JSON | 1 | 4 |

All nine tool steps returned their expected exit codes: inspect the existing
toolchain, build, create the environment, install, verify import identity, verify
the CLI version, and run the three demos. The tested wheel SHA-256 is:

```text
2c26af33f70b3852fc93ff3f34dd3f008a5189e8c692dc641eda2620940b05f3
```

This digest identifies the tested artifact. A separate build can produce a
different archive digest because of build timestamps; byte-for-byte reproducible
wheel builds were not tested. [INSTALLATION.json](INSTALLATION.json) records the
sanitized tool versions, original package source hashes, and observed outcomes.

Installation verification establishes these local behaviors. It does not verify
other Python versions or establish remote publication. No license grant or hosted
workflow is included.
