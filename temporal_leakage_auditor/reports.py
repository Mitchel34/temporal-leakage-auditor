"""Deterministic reports without machine or execution metadata."""

import html
import json

from .core import RULES


def make_report(rows, cutoff, findings):
    return {
        "schema_version": 1,
        "cutoff": cutoff,
        "rows": {
            "total": len(rows),
            "train": sum(row["split"] == "train" for row in rows),
            "validation": sum(row["split"] == "validation" for row in rows),
        },
        "summary": {
            "finding_count": len(findings),
            "affected_row_count": len({f["row_ids"][0] for f in findings}),
            "by_rule": {rule: sum(f["rule"] == rule for f in findings) for rule in RULES},
        },
        "findings": findings,
    }


def render_json(report):
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True,
                      allow_nan=False) + "\n"


def _markdown_cell(value):
    # Encode HTML and Markdown punctuation so an identifier stays table text.
    punctuation = "\\`*_{}[]()#+-.!|"
    return "".join(f"&#{ord(c)};" if c in punctuation else html.escape(c, quote=True)
                   for c in value)


def render_markdown(report):
    lines = ["# Temporal Leakage Audit", "", "Cutoff: " + report["cutoff"], "",
             f"Rows: {report['rows']['total']} "
             f"({report['rows']['train']} train, {report['rows']['validation']} validation)",
             "", f"Findings: {report['summary']['finding_count']}; "
             f"affected rows: {report['summary']['affected_row_count']}",
             "", "| Rule | Findings |", "| --- | ---: |"]
    for rule in RULES:
        lines.append(f"| {rule} | {report['summary']['by_rule'][rule]} |")
    lines.append("")
    if report["findings"]:
        lines.extend(["| Rule | Row ID | Severity | Reason | Repair |",
                      "| --- | --- | --- | --- | --- |"])
        for finding in report["findings"]:
            values = [finding["rule"], finding["row_ids"][0], finding["severity"],
                      finding["reason"], finding["repair"]]
            lines.append("| " + " | ".join(_markdown_cell(v) for v in values) + " |")
    else:
        lines.append("No declared-rule findings were found.")
    lines.extend(["", "A clean report is not proof of leakage-free modeling."])
    return "\n".join(lines) + "\n"
