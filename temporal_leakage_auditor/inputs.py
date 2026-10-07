"""Strict CSV/JSON parsing and explicit UTC semantics."""

import csv
import io
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

FIELDS = (
    "row_id", "observation_id", "entity_id", "split", "prediction_time",
    "feature_available_time", "label_end_time",
)
TIME_FIELDS = ("prediction_time", "feature_available_time", "label_end_time")
TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z"
)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class InputError(ValueError):
    """An expected input-contract failure with a safe, deterministic message."""


def parse_timestamp(value, location="cutoff"):
    """Normalize an unambiguous UTC timestamp without floating-point rounding."""
    if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
        raise InputError(location + ": expected UTC timestamp ending in Z")
    try:
        fraction = value[20:-1] if len(value) > 20 else ""
        instant = datetime(int(value[0:4]), int(value[5:7]), int(value[8:10]),
                           int(value[11:13]), int(value[14:16]), int(value[17:19]),
                           int(fraction.ljust(6, "0")), tzinfo=timezone.utc)
    except ValueError:
        raise InputError(location + ": invalid calendar date or time") from None
    delta = instant - EPOCH
    micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    # strftime's year padding is platform-dependent for years before 1000.
    canonical = (
        f"{instant.year:04d}-{instant.month:02d}-{instant.day:02d}T"
        f"{instant.hour:02d}:{instant.minute:02d}:{instant.second:02d}."
        f"{instant.microsecond:06d}Z"
    )
    return micros, canonical


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("JSON contains a duplicate object key")
        result[key] = value
    return result


def _bad_constant(value):
    raise InputError("JSON contains a nonstandard numeric constant")


def parse_rows(text, input_format):
    if input_format == "json":
        try:
            rows = json.loads(text, object_pairs_hook=_json_object,
                              parse_constant=_bad_constant)
        except InputError:
            raise
        except (ValueError, RecursionError):
            raise InputError("invalid JSON document") from None
        if not isinstance(rows, list):
            raise InputError("JSON input must be an array of row objects")
        return rows
    if input_format != "csv":
        raise InputError("input format must be csv or json")
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
        if header is None or len(header) != len(FIELDS) or set(header) != set(FIELDS):
            raise InputError("CSV header must contain exactly the seven required fields")
        rows = []
        for position, values in enumerate(reader, 1):
            if len(values) != len(header):
                raise InputError(f"row {position}: wrong number of CSV cells")
            rows.append(dict(zip(header, values)))
        return rows
    except csv.Error:
        raise InputError("invalid CSV document") from None


def validate_rows(raw_rows, cutoff):
    """Validate the whole input before any detection or output."""
    if not isinstance(raw_rows, list) or not raw_rows:
        raise InputError("input must contain at least one row in each split")
    rows, row_ids, splits = [], set(), set()
    for position, raw in enumerate(raw_rows, 1):
        location = f"row {position}"
        if not isinstance(raw, dict) or set(raw) != set(FIELDS):
            raise InputError(location + ": expected exactly the seven required fields")
        if any(not isinstance(raw[field], str) for field in FIELDS):
            raise InputError(location + ": all field values must be strings")
        for field in ("row_id", "observation_id", "entity_id"):
            value = raw[field]
            if (not value or value != value.strip()
                    or any(unicodedata.category(c) in ("Cc", "Cf", "Cs", "Zl", "Zp")
                           for c in value)):
                raise InputError(location + ": invalid identifier in " + field)
        if raw["row_id"] in row_ids:
            raise InputError(location + ": duplicate row_id")
        row_ids.add(raw["row_id"])
        split = raw["split"]
        if split not in ("train", "validation"):
            raise InputError(location + ": split must be train or validation")
        splits.add(split)
        row = dict(raw)
        for field in TIME_FIELDS:
            row[field] = parse_timestamp(raw[field], location + ": " + field)[0]
        if row["label_end_time"] < row["prediction_time"]:
            raise InputError(location + ": label end precedes prediction")
        if split == "train" and row["prediction_time"] >= cutoff:
            raise InputError(location + ": training prediction must precede cutoff")
        if split == "validation" and row["prediction_time"] < cutoff:
            raise InputError(location + ": validation prediction precedes cutoff")
        rows.append(row)
    if splits != {"train", "validation"}:
        raise InputError("input must contain at least one row in each split")
    return rows


def load_rows(path, input_format, cutoff):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        raise InputError("input file is unreadable or is not UTF-8") from None
    return validate_rows(parse_rows(text, input_format), cutoff)
