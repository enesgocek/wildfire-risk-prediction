"""Attach existing map evidence to the frozen fit-only protocol, without cover filtering."""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROTOCOL = BASE / "source_conditioned_pu_protocol_v1/20261119T200942Z_3bc1ded8/readback.json"
PROTOCOL_SHA = "c22b246a5f93563115a193de7022d63accdabb18938ac5a635f4916ff3951df9"
REFERENCE = BASE / "mersin_joint_reference_v1/20261118T140734Z_19b35a6d/readback.json"
REFERENCE_SHA = "20c458af72b4a77e69d9e4713acfe91bbeaaaac2322165fa6e2a4fe248bcf5bc"
FOREST_SHRUB = {311, 312, 313, 322, 323, 324}


def attach_cover(cases, reference_rows):
    selected = {x["archive_row"]: x for x in cases if x["diagnostic_focus"]}
    require(len(selected) == sum(x["diagnostic_focus"] for x in cases), "Unique focused source key")
    result = {}
    for old in reference_rows:
        # Filter metadata before looking at class/pixel/context values, including 2023.
        if str(old["year"]) not in {str(y) for y in range(2018, 2023)}:
            continue
        key = old["archive_row"]
        if key not in selected:
            continue
        current = selected[key]
        require(not current["researcher_retained_outside_L"], "Preserve retention decision")
        require(
            current["target"] is None and current["membership"] == "review_unassigned",
            "No target admission",
        )
        require(int(old["year"]) == current["year"], "Same source year")
        require(
            [old["grid_id"]] == current["conditional_center_grid_ids"], "Same source center cell"
        )
        require(key not in result, "Unique source-to-map evidence key")
        code = old["corine_2018_center_code"]
        context = (
            "forest_shrub"
            if code in FOREST_SHRUB
            else "unmapped"
            if code is None
            else "agriculture"
            if 200 <= code < 300
            else "other"
        )
        require(context == old["center_context"], "Map legend group agrees with existing receipt")
        item = {
            "archive_row": key,
            "year": current["year"],
            "grid_id": old["grid_id"],
            "corine_2018_center_code": code,
            "map_center_context": context,
            "circle_pixel_center_samples": {},
            "membership": "review_unassigned",
            "target": None,
            "event_date_cover_verified": False,
            "map_context_is_fire_type": False,
        }
        for radius in (250, 1000):
            counts = {
                name: old[f"{name}_{radius}m"]
                for name in (
                    "sampled_pixels",
                    "mapped_pixels",
                    "forest_shrub_pixels",
                    "agriculture_pixels",
                )
            }
            require(
                all(type(n) is int and n >= 0 for n in counts.values()),
                "Nonnegative integer map counts",
            )
            require(
                counts["sampled_pixels"] > 0
                and counts["mapped_pixels"] <= counts["sampled_pixels"]
                and counts["forest_shrub_pixels"] + counts["agriculture_pixels"]
                <= counts["mapped_pixels"],
                "Map support partition",
            )
            item["circle_pixel_center_samples"][str(radius)] = counts
        result[key] = item
    require(
        set(result) == set(selected), "All focused rows have prior map evidence; no silent subset"
    )
    return [result[k] for k in sorted(result)]


def summarize(rows):
    return {
        "source_rows": len(rows),
        "center_context_counts": dict(
            sorted(Counter(x["map_center_context"] for x in rows).items())
        ),
        "forest_shrub_centers_with_agriculture_samples": {
            str(radius): sum(
                x["map_center_context"] == "forest_shrub"
                and x["circle_pixel_center_samples"][str(radius)]["agriculture_pixels"] > 0
                for x in rows
            )
            for radius in (250, 1000)
        },
        "agriculture_centers_with_forest_shrub_samples": {
            str(radius): sum(
                x["map_center_context"] == "agriculture"
                and x["circle_pixel_center_samples"][str(radius)]["forest_shrub_pixels"] > 0
                for x in rows
            )
            for radius in (250, 1000)
        },
        "incomplete_map_support": {
            str(radius): sum(
                x["circle_pixel_center_samples"][str(radius)]["mapped_pixels"]
                < x["circle_pixel_center_samples"][str(radius)]["sampled_pixels"]
                for x in rows
            )
            for radius in (250, 1000)
        },
    }


def main():
    pins = {PROTOCOL: PROTOCOL_SHA, REFERENCE: REFERENCE_SHA}
    require(all(digest(p) == h for p, h in pins.items()), "Frozen protocol and prior map evidence")
    protocol = json.loads(PROTOCOL.read_bytes())
    pins.update({ROOT / p: h for p, h in protocol["input_sha256"].items()})
    require(
        all(digest(p) == h for p, h in pins.items()), "Source, prior L/U and scope remain unchanged"
    )
    reference = json.loads(REFERENCE.read_bytes())
    rows = attach_cover(protocol["cases"], reference["reference_units"])
    require(len(rows) == 380, "Same diagnostic focus")
    result = {
        "status": "prior_map_evidence_attached_to_fit_source_review_not_habitat_acceptance",
        "summary": summarize(rows),
        "rows": rows,
        "source_rows_outside_focus_retained_in_parent": 44,
        "map_basis": "CORINE_2018_prior_pixel_center_sampling_not_new_area_measurement",
        "map_groups": {
            "forest_shrub_CLC_codes": sorted(FOREST_SHRUB),
            "agriculture_CLC_interval": [200, 300],
        },
        "prior_map_production_inputs_sha256": reference["inputs_sha256"],
        "current_raster_recomputed": False,
        "future_source_context_values_used": False,
        "cover_filter_applied": False,
        "local_habitat_policy_accepted": False,
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "label_noise_rate_estimated": False,
        "features_joined_for_training": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "source_conditioned_cover_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Saved map evidence roundtrip")
    require(all(digest(p) == h for p, h in pins.items()), "All inputs preserved at closure")
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(result["summary"]))
    print("PASS fit_only_prior_cover_evidence; no habitat acceptance, L, labels or training")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
