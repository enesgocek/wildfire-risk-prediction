"""Audit existing image evidence for retrospective cover review, never label admission."""

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "first": (
        "preevent_image_windows_v1/20261023T152456Z_e03ae61d",
        "a3d1378c3f13a2b1947b045aaa2f296426bdfb4246861160aa83adf3caa6a5f8",
    ),
    "alternatives": (
        "preevent_date_comparison_v1/20261023T154219Z_144befb7",
        "f50778b9bd1a344c35336273fb46d19258481dc50676a692682e8772bd8b468d",
    ),
}
FLAGS = (
    "cloud_cirrus_fraction",
    "cloud_shadow_fraction",
    "dark_or_cast_shadow_fraction",
    "nodata_defective_fraction",
    "unclassified_fraction",
    "snow_ice_fraction",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Timezone required")
    return result.astimezone(UTC)


def main():
    pins, rows = {}, []

    def pin(path, expected):
        require(sha(path) == expected, "Changed evidence: " + path.name)
        pins[path.relative_to(ROOT).as_posix()] = expected

    for role, (relative, digest) in SOURCES.items():
        folder = BASE / relative
        pin(folder / "readback.json", digest)
        report = json.loads((folder / "readback.json").read_text(encoding="utf-8"))
        for name, expected in sorted(report["artifact_sha256"].items()):
            if not name.endswith("/receipt.json"):
                continue
            path = folder / name
            pin(path, expected)
            item = json.loads(path.read_text(encoding="utf-8"))
            for band, asset in item["assets"].items():
                pin(path.parent / (band + ".tif"), asset["sha256"])
            t = utc(item["prediction_utc"])
            acquired = utc(item["acquired_utc"])
            generated = utc(item["product_generated_utc"])
            require(2018 <= t.year <= 2023, "Training-only evidence")
            require(0 < (t - acquired).total_seconds() <= 60 * 86400, "Pre-T 60-day contract")
            require(generated >= acquired, "Generation before acquisition")
            quality = item["quality"]
            counts = quality["scl_counts"]
            require(sum(counts.values()) == quality["support_pixel_centres"], "SCL count total")
            require(quality["support_pixel_centres"] > 0, "Empty support")
            require(all(0 <= quality[k] <= 1 for k in FLAGS), "Invalid fractions")
            for flag in ("quality_threshold_accepted", "habitat_accepted", "fire_label_accepted"):
                require(quality[flag] is False, "No existing admission supported")
            require(item["historical_available_at_verified"] is False, "Availability state changed")
            rows.append(
                {
                    "detection_id": item["detection_id"],
                    "item_id": item["item_id"],
                    "role": role,
                    "receipt_path": path.relative_to(ROOT).as_posix(),
                    "prediction_utc": t.isoformat(),
                    "acquired_utc": acquired.isoformat(),
                    "product_generated_utc": generated.isoformat(),
                    "days_before_prediction": (t - acquired).total_seconds() / 86400,
                    "product_generated_after_prediction": generated > t,
                    "historical_availability": "unverified",
                    "historical_predictor_use_permitted": False,
                    "retrospective_image_context_present": True,
                    "quality_flags_present": [k for k in FLAGS if quality[k] > 0],
                    "zero_cloud_cirrus_count": counts["8"] + counts["9"] + counts["10"] == 0,
                    "zero_all_selected_quality_flags": all(quality[k] == 0 for k in FLAGS),
                    "quality_sufficient_for_cover_admission": None,
                    "natural_vs_managed_cover_verified": False,
                    "habitat_admission": "undecided",
                    "target": None,
                }
            )
    keys = {(r["detection_id"], r["item_id"]) for r in rows}
    require(len(rows) == len(keys) == 37, "Expected 37 point-image pairs")
    require(Counter(r["role"] for r in rows) == {"first": 25, "alternatives": 12}, "Coverage")
    points = []
    for identity in sorted({r["detection_id"] for r in rows}):
        subset = [r for r in rows if r["detection_id"] == identity]
        require(len({r["prediction_utc"] for r in subset}) == 1, "Conflicting cutoff")
        require(len({r["acquired_utc"][:10] for r in subset}) == len(subset), "Repeated date")
        points.append(
            {
                "detection_id": identity,
                "image_dates": len(subset),
                "has_zero_cloud_cirrus_date": any(r["zero_cloud_cirrus_count"] for r in subset),
                "has_zero_all_selected_quality_flags_date": any(
                    r["zero_all_selected_quality_flags"] for r in subset
                ),
                "has_generated_before_or_at_T_date": any(
                    not r["product_generated_after_prediction"] for r in subset
                ),
                "natural_vs_managed_cover_verified": False,
                "next_evidence_requirement": (
                    "documented_land_use_or_interpretable_cover_evidence_at_relevant_time"
                ),
                "habitat_admission": "undecided",
                "target": None,
            }
        )
    require(len(points) == 25, "Expected 25 points")
    summary = {
        "points": 25,
        "point_image_pairs": 37,
        "point_image_pairs_generated_after_T": sum(
            r["product_generated_after_prediction"] for r in rows
        ),
        "unique_source_items": len({r["item_id"] for r in rows}),
        "historical_availability_verified": 0,
        "points_with_multiple_dates": sum(r["image_dates"] > 1 for r in points),
        "points_with_zero_cloud_cirrus_date": sum(r["has_zero_cloud_cirrus_date"] for r in points),
        "points_with_zero_all_selected_quality_flags_date": sum(
            r["has_zero_all_selected_quality_flags_date"] for r in points
        ),
        "points_with_any_generated_before_or_at_T_date": sum(
            r["has_generated_before_or_at_T_date"] for r in points
        ),
        "accepted_natural_cover_points": 0,
    }
    pin(Path(__file__), sha(Path(__file__)))
    result = {
        "version": "habitat_temporal_evidence_audit_v1",
        "summary": summary,
        "image_evidence": rows,
        "point_requirements": points,
        "source_sha256": pins,
        "quality_flags_are_not_admission_thresholds": True,
        "historical_availability_is_distinct_from_generation_time": True,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    folder = (
        BASE
        / "habitat_temporal_evidence_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    folder.mkdir(parents=True, exist_ok=False)
    path = folder / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback mismatch")
    for name, expected in list(pins.items()):
        pin(ROOT / name, expected)
    print(folder.relative_to(ROOT), sha(path), "PINS", len(pins))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
