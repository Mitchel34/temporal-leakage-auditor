"""Pure evaluation protocol. Combining sources supplies detector and fixtures.

Expected labels come exclusively from the independently declared fixture truth.
This module performs no filesystem access and never executes on import.
"""

EVAL_RULES = ("late_feature", "label_overlap", "cross_split_duplicate")


def score_fixture(findings, case):
    """Validate emissions before computing row-level confusion counts."""
    eligible = {
        rule: {r["row_id"] for r in case["rows"]
               if rule != "label_overlap" or r["split"] == "train"}
        for rule in EVAL_RULES
    }
    if not isinstance(findings, list):
        raise ValueError("Findings must be a list")
    observed = []
    for finding in findings:
        if (not isinstance(finding, dict)
                or set(finding) != {"rule", "row_ids", "severity", "reason", "repair"}
                or finding["rule"] not in EVAL_RULES
                or not isinstance(finding["row_ids"], list)
                or len(finding["row_ids"]) != 1
                or not isinstance(finding["row_ids"][0], str)
                or finding["row_ids"][0] not in eligible[finding["rule"]]
                or finding["severity"] != "error"
                or not isinstance(finding["reason"], str) or not finding["reason"]
                or not isinstance(finding["repair"], str) or not finding["repair"]):
            raise ValueError("Invalid, unknown, or ineligible finding")
        observed.append((finding["rule"], finding["row_ids"][0]))
    if len(observed) != len(set(observed)):
        raise ValueError("Duplicate finding emissions")
    truth = case["truth"]
    if len(truth) != len(set(truth)) or any(
            rule not in EVAL_RULES or row_id not in eligible[rule]
            for rule, row_id in truth):
        raise ValueError("Invalid literal truth")
    counts = {}
    for rule in EVAL_RULES:
        positive = {row_id for truth_rule, row_id in truth if truth_rule == rule}
        predicted = {row_id for actual_rule, row_id in observed if actual_rule == rule}
        tp = len(positive & predicted)
        fp = len(predicted - positive)
        fn = len(positive) - tp
        tn = len(eligible[rule]) - len(positive) - fp
        counts[rule] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    return observed == truth, counts


def evaluate_with(detector, cases_factory):
    """Run the twelve predeclared cases, with 86 finite numeric metrics."""
    cases = cases_factory(seed=1729)
    if [case["fixture_id"] for case in cases] != [f"F{i:02d}" for i in range(1, 13)]:
        raise ValueError("Expected exactly the twelve declared fixtures")
    totals = {rule: {key: 0 for key in ("tp", "fp", "fn", "tn")} for rule in EVAL_RULES}
    checks, metrics = [], {}
    for case in cases:
        before = [dict(row) for row in case["rows"]]
        findings = detector(case["rows"], case["cutoff"])
        exact, counts = score_fixture(findings, case)
        checks.append({"name": case["fixture_id"] + " exact ordered findings and unchanged input",
                       "passed": exact and case["rows"] == before})
        for rule in EVAL_RULES:
            for key in ("tp", "fp", "fn", "tn"):
                totals[rule][key] += counts[rule][key]
            for key in ("tp", "fp"):
                metrics[case["fixture_id"].lower() + "_" + rule + "_" + key] = counts[rule][key]
    for rule in EVAL_RULES:
        for key in ("tp", "fp", "fn", "tn"):
            metrics[rule + "_" + key] = totals[rule][key]
    metrics["fixture_count"] = len(cases)
    metrics["row_count"] = sum(len(case["rows"]) for case in cases)
    expected = {"late_feature": {"tp": 3, "fp": 0, "fn": 0, "tn": 45},
                "label_overlap": {"tp": 3, "fp": 0, "fn": 0, "tn": 21},
                "cross_split_duplicate": {"tp": 6, "fp": 0, "fn": 0, "tn": 42}}
    checks.append({"name": "Aggregate declared truth and eligibility counts",
                   "passed": totals == expected and metrics["row_count"] == 48})
    return {"checks": checks, "metrics": metrics}
