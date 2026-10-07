"""Pure detector over validated rows with integer UTC microsecond timestamps.

The CLI and the reproducible evaluation use these same predicates. Validation
and timestamp parsing belong to the input layer; this module performs no I/O.
"""

RULES = ("late_feature", "label_overlap", "cross_split_duplicate")
DETAILS = {
    "late_feature": (
        "Feature availability is later than prediction time.",
        "Use features available at prediction time or move prediction later.",
    ),
    "label_overlap": (
        "The training label interval extends beyond the validation cutoff.",
        "Remove the overlapping training row or use a cutoff after its label ends.",
    ),
    "cross_split_duplicate": (
        "This observation ID occurs in both training and validation.",
        "Keep each observation in one split; verify that observation IDs are stable.",
    ),
}


def audit_rows(rows, cutoff):
    """Return one finding per rule/row, in fixed rule order then lexical row ID.

    Preconditions: the input layer validated unique row IDs, split membership,
    prediction/cutoff ordering, and nonnegative half-open label intervals.
    Repeated entity IDs do not imply a finding. Input rows are never modified.
    """
    train_ids = {r["observation_id"] for r in rows if r["split"] == "train"}
    validation_ids = {
        r["observation_id"] for r in rows if r["split"] == "validation"
    }
    shared_ids = train_ids & validation_ids
    affected = {rule: [] for rule in RULES}
    for row in rows:
        if row["feature_available_time"] > row["prediction_time"]:
            affected["late_feature"].append(row["row_id"])
        if row["split"] == "train" and row["label_end_time"] > cutoff:
            affected["label_overlap"].append(row["row_id"])
        if row["observation_id"] in shared_ids:
            affected["cross_split_duplicate"].append(row["row_id"])
    findings = []
    for rule in RULES:
        reason, repair = DETAILS[rule]
        for row_id in sorted(affected[rule]):
            findings.append({
                "rule": rule,
                "row_ids": [row_id],
                "severity": "error",
                "reason": reason,
                "repair": repair,
            })
    return findings
