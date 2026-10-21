"""Compare FIRMS deliveries as multisets; never infer physical event identity."""

import csv
import re
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

FIELDS = (
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_t31",
    "frp",
    "daynight",
    "type",
)
NUMERIC = {"latitude", "longitude", "brightness", "scan", "track", "bright_t31", "frp"}
KEY = ("satellite", "acq_date", "acq_time", "latitude", "longitude")


def canonical(field, value):
    value = value.strip()
    if field in NUMERIC:
        try:
            number = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Invalid FIRMS numeric value") from exc
        if not number.is_finite():
            raise ValueError("Nonfinite FIRMS value")
        return str(number.normalize()) if number else "0"
    if field == "acq_time":
        if not re.fullmatch(r"[0-9]{1,4}", value):
            raise ValueError("Invalid acquisition time")
        value = value.zfill(4)
        if int(value[:2]) > 23 or int(value[2:]) > 59:
            raise ValueError("Invalid acquisition time")
    return value


def read_delivery(stream, start, end, sensor, *, allow_later=False):
    """Read training rows only; later old rows are date-filtered before field parsing."""
    reader = csv.DictReader(stream)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("Unexpected FIRMS header")
    rows, raw_rows, ordered = Counter(), Counter(), []
    outside = 0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed FIRMS row")
        day = row["acq_date"]
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError("Noncanonical acquisition date")
        if not start <= day <= end:
            if allow_later and "2024-01-01" <= day <= "2024-12-31":
                outside += 1
                continue
            raise ValueError("Unexpected delivery period")
        values = tuple(canonical(k, row[k]) for k in FIELDS)
        entry = dict(zip(FIELDS, values, strict=True))
        if entry["satellite"] != sensor or entry["version"] != "2":
            raise ValueError("Unexpected sensor or collection")
        if entry["instrument"] not in {"VIIRS", "SNPP"}:
            raise ValueError("Unexpected instrument")
        if entry["type"] not in {"0", "1", "2", "3"}:
            raise ValueError("Unexpected Type")
        if entry["confidence"] not in {"l", "n", "h"} or entry["daynight"] not in {"D", "N"}:
            raise ValueError("Unexpected confidence/daynight")
        if not -90 <= Decimal(entry["latitude"]) <= 90:
            raise ValueError("Invalid latitude")
        if not -180 <= Decimal(entry["longitude"]) <= 180:
            raise ValueError("Invalid longitude")
        rows[values] += 1
        raw_rows[tuple(row[k] for k in FIELDS)] += 1
        ordered.append(values)
    if not rows:
        raise ValueError("Empty training delivery")
    return {"rows": rows, "raw": raw_rows, "ordered": ordered, "later_rows_skipped": outside}


def grouped(rows, fields):
    indexes = [FIELDS.index(k) for k in fields]
    groups = defaultdict(Counter)
    for row, count in rows.items():
        groups[tuple(row[i] for i in indexes)][row] += count
    return groups


def compare(old, new):
    """Keep multiplicity, separate changed unique keys from ambiguous groups."""
    before, after = old["rows"], new["rows"]
    left, right = grouped(before, KEY), grouped(after, KEY)
    shared = left.keys() & right.keys()
    changes, transitions = Counter(), Counter()
    changed_unique = ambiguous_shared = 0
    for key in shared:
        a, b = left[key], right[key]
        if a == b:
            continue
        if a.total() == b.total() == 1:
            changed_unique += 1
            x, y = next(iter(a)), next(iter(b))
            for i, field in enumerate(FIELDS):
                if x[i] != y[i]:
                    changes[field] += 1
            transitions[f"{x[FIELDS.index('type')]}->{y[FIELDS.index('type')]}"] += 1
        else:
            ambiguous_shared += 1
    removed, added = before - after, after - before
    # These residual projection overlaps are diagnostics, never accepted matches.
    projections = {}
    for label, fields in (
        ("same_sensor_time_possible_coordinate_change", ("satellite", "acq_date", "acq_time")),
        ("same_sensor_coordinates_possible_time_change", ("satellite", "latitude", "longitude")),
    ):
        a, b = grouped(removed, fields), grouped(added, fields)
        projections[label] = len(a.keys() & b.keys())
    return {
        "old_rows": before.total(),
        "new_rows": after.total(),
        "old_later_rows_date_filtered": old["later_rows_skipped"],
        "canonical_multiset_equal": before == after,
        "text_field_multiset_equal": old["raw"] == new["raw"],
        "canonical_row_order_equal": old["ordered"] == new["ordered"],
        "unchanged_full_rows": (before & after).total(),
        "removed_or_changed_full_rows": removed.total(),
        "added_or_changed_full_rows": added.total(),
        "old_unique_detection_keys": len(left),
        "new_unique_detection_keys": len(right),
        "removed_detection_keys": len(left.keys() - right.keys()),
        "added_detection_keys": len(right.keys() - left.keys()),
        "changed_unique_detection_keys": changed_unique,
        "changed_fields_at_unique_keys": dict(sorted(changes.items())),
        "type_transitions_at_changed_unique_keys": dict(sorted(transitions.items())),
        "ambiguous_changed_shared_keys": ambiguous_shared,
        "old_duplicate_key_groups": sum(c.total() > 1 for c in left.values()),
        "new_duplicate_key_groups": sum(c.total() > 1 for c in right.values()),
        "old_duplicate_full_rows_excess": before.total() - len(before),
        "new_duplicate_full_rows_excess": after.total() - len(after),
        "unpaired_residual_projection_overlaps": projections,
    }


def categories(delivery):
    result = {}
    for field in ("type", "confidence", "version", "instrument", "daynight", "acq_date"):
        counts = Counter()
        index = FIELDS.index(field)
        for row, count in delivery["rows"].items():
            value = row[index][:4] if field == "acq_date" else row[index]
            counts[value] += count
        result["year" if field == "acq_date" else field] = dict(sorted(counts.items()))
    return result
