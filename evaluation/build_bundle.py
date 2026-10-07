"""Combine exact reviewed source files without executing the evaluation.

The generated single-file entry point has no imports of arbitrary local modules.
Each original source is embedded verbatim with its relative path and SHA-256.
"""

import argparse
import ast
import hashlib
from pathlib import Path

SOURCES = ("temporal_leakage_auditor/core.py", "evaluation/fixtures.py",
           "evaluation/protocol.py")


def bundle_text(root):
    pieces = ["# Generated from the exact source files below. Do not edit.\n"]
    for relative in SOURCES:
        data = (root / relative).read_bytes()
        text = data.decode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        pieces.append(f"\n# Source: {relative}\n# SHA-256: {digest}\n{text}\n")
    pieces.append("\ndef evaluate():\n    return evaluate_with(audit_rows, fixture_cases)\n")
    output = "".join(pieces)
    ast.parse(output)
    if len(output.encode("utf-8")) > 128 * 1024:
        raise ValueError("Evaluation source exceeds 128 KiB")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new output file; existing files are refused")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    text = bundle_text(root)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
