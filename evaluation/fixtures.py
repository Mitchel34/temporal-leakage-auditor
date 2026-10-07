"""Small synthetic cases with literal, independently declared expected findings.

The timestamps are normalized integer UTC microseconds. The seed changes only
row order; it cannot change a case's timestamps, identities, or literal truth.
This module does not import, inspect, or call a detector.
"""

import random


CUTOFF = 1736899200000000
SECOND = 1000000
DAY = 86400000000

# Literal declarations, already in rule order and then lexical row-ID order.
# Keep expected findings independent of case construction and detector output.
FIXTURE_TRUTH = (
    ("F01", (("late_feature", "t1"),)),
    ("F02", (("late_feature", "v1"),)),
    ("F03", (("late_feature", "t2"),)),
    ("F04", (("label_overlap", "t1"),)),
    ("F05", (("label_overlap", "t1"),)),
    ("F06", (("label_overlap", "t1"),)),
    ("F07", (("cross_split_duplicate", "t1"), ("cross_split_duplicate", "v1"))),
    ("F08", (("cross_split_duplicate", "t1"), ("cross_split_duplicate", "v1"))),
    ("F09", (("cross_split_duplicate", "t1"), ("cross_split_duplicate", "v1"))),
    ("F10", ()),
    ("F11", ()),
    ("F12", ()),
)


def baseline_rows():
    """Return fresh baseline rows keyed by their stable occurrence IDs."""
    rows = {}
    for row_id, split, day_offset in (
        ("t1", "train", -3),
        ("t2", "train", -2),
        ("v1", "validation", 2),
        ("v2", "validation", 3),
    ):
        prediction = CUTOFF + day_offset * DAY
        rows[row_id] = {
            "row_id": row_id,
            "observation_id": "observation_" + row_id,
            "entity_id": "entity_" + row_id,
            "split": split,
            "prediction_time": prediction,
            "feature_available_time": prediction,
            "label_end_time": prediction + DAY,
        }
    return rows


def fixture_cases(seed=1729):
    """Return F01 through F12 with fresh row dictionaries and literal truth.

    Each dictionary contains exactly ``fixture_id``, ``cutoff``, ``rows``, and
    ``truth``. Each case is a separate four-row input. Truth is a list of
    ``(rule, row_id)`` tuples. No expected finding is calculated from row values.
    A local PRNG leaves the caller's global random state unchanged.
    """
    rng = random.Random(seed)
    cases = []
    for fixture_id, truth in FIXTURE_TRUTH:
        rows = baseline_rows()
        t1 = rows["t1"]
        t2 = rows["t2"]
        v1 = rows["v1"]

        if fixture_id == "F01":
            t1["feature_available_time"] = t1["prediction_time"] + 1
        elif fixture_id == "F02":
            v1["feature_available_time"] = v1["prediction_time"] + SECOND
        elif fixture_id == "F03":
            t2["feature_available_time"] = t2["prediction_time"] + DAY
        elif fixture_id == "F04":
            t1["label_end_time"] = CUTOFF + 1
        elif fixture_id == "F05":
            t1["label_end_time"] = CUTOFF + SECOND
        elif fixture_id == "F06":
            t1["label_end_time"] = CUTOFF + DAY
        elif fixture_id in ("F07", "F08", "F09"):
            offset = {"F07": 1, "F08": SECOND, "F09": DAY}[fixture_id]
            t1["observation_id"] = "observation_shared"
            v1["observation_id"] = "observation_shared"
            t1["prediction_time"] = CUTOFF - offset
            t1["feature_available_time"] = CUTOFF - offset
            t1["label_end_time"] = CUTOFF
            v1["prediction_time"] = CUTOFF + offset
            v1["feature_available_time"] = CUTOFF + offset
            v1["label_end_time"] = CUTOFF + offset + DAY
        elif fixture_id == "F10":
            t1["label_end_time"] = CUTOFF
            v1["prediction_time"] = CUTOFF
            v1["feature_available_time"] = CUTOFF
            v1["label_end_time"] = CUTOFF + DAY
        elif fixture_id == "F11":
            for row in rows.values():
                row["entity_id"] = "entity_shared"
        elif fixture_id == "F12":
            t1["label_end_time"] = CUTOFF - 1
            t2["label_end_time"] = CUTOFF - 1
            for row in rows.values():
                row["feature_available_time"] = row["prediction_time"] - 1

        ordered_rows = list(rows.values())
        rng.shuffle(ordered_rows)
        cases.append({
            "fixture_id": fixture_id,
            "cutoff": CUTOFF,
            "rows": ordered_rows,
            "truth": list(truth),
        })
    return cases
