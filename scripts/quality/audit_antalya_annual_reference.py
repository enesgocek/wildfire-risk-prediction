"""Conditional 2018 source-point context; a year-only reference cannot assign a day."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "docs/research/antalya_annual_reference_2026-11-19.json"
HALF_STEPS = (Decimal("0.005"), Decimal("0.01"))


def inspect_rows(rows, *, date_field, year, longitude, latitude, source_role):
    """Filter date metadata first; never infer an incident date from a nearby detection."""
    require(type(year) is int and 2018 <= year <= 2022, "Fit-role reference year required")
    require(source_role == "reported_central_feature_record", "Aggregate centers are not records")
    lon, lat = Decimal(str(longitude)), Decimal(str(latitude))
    require(lon.is_finite() and lat.is_finite(), "Finite source-coordinate interpretation")
    require(20 <= lon <= 40 and 30 <= lat <= 45, "Conditional geographic interpretation")
    counts = [Counter() for _ in HALF_STEPS]
    year_rows = 0
    for row in rows:
        # Later data roles and other years are skipped before coordinate access.
        stamp = row[date_field]
        if not stamp.startswith(f"{year}-"):
            continue
        datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        year_rows += 1
        x, y = Decimal(row["longitude"]), Decimal(row["latitude"])
        require(x.is_finite() and y.is_finite(), "Finite retained coordinates")
        for step, tally in zip(HALF_STEPS, counts, strict=True):
            if abs(x - lon) <= step and abs(y - lat) <= step:
                tally[stamp[:10]] += 1
    return {
        "scientific_value_year": year,
        "year_rows_examined": year_rows,
        "conditional_boxes": [
            {
                "half_step_degrees": str(step),
                "bounds_lon_lat": [
                    str(lon - step),
                    str(lat - step),
                    str(lon + step),
                    str(lat + step),
                ],
                "interpretation": "decimal_rounding_hypothesis"
                if i == 0
                else "quantization_sensitivity_only",
                "is_total_location_error_bound": False,
                "matched_detection_rows": sum(tally.values()),
                "matched_catalogue_dates": dict(sorted(tally.items())),
                "dates_are_source_event_dates": False,
            }
            for i, (step, tally) in enumerate(zip(HALF_STEPS, counts, strict=True))
        ],
        "source_event_day": None,
        "target": None,
        "same_physical_event_verified": False,
        "negative_label_permitted": False,
    }


def main():
    notes = json.loads(NOTES.read_bytes())
    for relative, expected in notes["input_sha256"].items():
        require(digest(ROOT / relative) == expected, "Input identity: " + relative)
    point = notes["conditional_2018_point"]
    require(point["year"] == 2018, "This source review is limited to 2018")
    require(point["source_event_day"] is None, "Year-only source retained")
    require(point["crs_verified"] is False, "Geographic CRS remains a hypothesis")
    for key in (
        "positive_label_permitted",
        "negative_label_permitted",
        "training_authorized",
        "final_merge_permitted",
    ):
        require(notes[key] is False, "Closed scientific permission")
    contexts = {}
    for name, item in notes["catalogues"].items():
        with (ROOT / item["path"]).open(encoding="utf-8-sig", newline="") as stream:
            contexts[name] = inspect_rows(
                csv.DictReader(stream),
                date_field=item["date_field"],
                year=2018,
                longitude=point["longitude_hypothesis"],
                latitude=point["latitude_hypothesis"],
                source_role=point["role"],
            )
    report = {
        "status": "conditional_annual_source_point_checked_no_day_or_label_admitted",
        "source_notes_sha256": digest(NOTES),
        "producer_sha256": digest(Path(__file__)),
        "verified_input_sha256": notes["input_sha256"],
        "source_pdf_pages": 16,
        "source_visually_reviewed_pages": [3, 10, 11],
        "review_by": "assistant_not_researcher_or_independent_expert",
        "conditional_source_point": point,
        "catalogue_contexts": contexts,
        "source_event_day": None,
        "target": None,
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "prior_possible_L_proposals_changed": False,
        "U_sample_changed": False,
        "same_physical_event_verified": False,
        "new_correspondence_started": False,
        "source_semantics_automatically_verified": False,
        "model_trained": False,
        "final_merge_performed": False,
        "target_admission": specification(),
        "validation_or_final_test_scientific_values_opened": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/antalya_annual_reference_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Report readback")
    print(out.relative_to(ROOT).as_posix())
    print("PASS bounded_annual_context; no incident day, labels, recall or observation acceptance")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
