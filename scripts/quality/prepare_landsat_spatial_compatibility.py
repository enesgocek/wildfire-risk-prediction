"""Select a small spatial compatibility proposal offline; never download or execute it."""

import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from shapely.geometry import shape

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"


def main():
    geometry_path = ROOT / "data/interim/grid_aoi_parts.geojson"
    province_path = (
        ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
    )
    reference_path = ROOT / "data/interim/vegetation/full_grid_v1/2022-07-01_b64/snapshots.csv"
    features = json.loads(geometry_path.read_bytes())["features"]
    provinces = json.loads(province_path.read_bytes())["features"]
    eligible = {}
    with reference_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            if row["snapshot_cutoff_utc"] != "2022-07-01T00:00:00+00:00":
                raise ValueError("Unexpected reference period")
            if all(
                row[f] and math.isfinite(float(row[f]))
                for f in ("ndvi_median_mean", "ndmi_median_mean")
            ):
                eligible.setdefault(row["grid_id"], set()).add(int(row["window_days"]))
    selected = []
    for province in sorted(provinces, key=lambda f: f["properties"]["GAUL1_NAME"]):
        area = shape(province["geometry"])
        pool = sorted(
            f["properties"]["grid_id"]
            for f in features
            if f["properties"]["aoi_fraction"] >= 0.9
            and eligible.get(f["properties"]["grid_id"]) == {30, 60}
            and area.covers(shape(f["geometry"]).representative_point())
        )
        if not pool:
            raise ValueError("No comparable sample in province")
        selected.append(
            {
                "province": province["properties"]["GAUL1_NAME"],
                "grid_id": pool[len(pool) // 2],
                "eligible_pool_size": len(pool),
            }
        )
    if len(selected) != 4 or len({r["grid_id"] for r in selected}) != 4:
        raise ValueError("Distinct four-province sample")
    proposal = {
        "version": "landsat_spatial_compatibility_proposal_v1",
        "prepared_date": "2026-11-25",
        "execute_authorized": False,
        "purpose": "quantify_spatial_method_difference_before_any_full_2024_production",
        "sample_selection": (
            "per_province_upper_median_lexical_grid_id_among_"
            "AOI_fraction_ge_0.9_and_two_finite_old_windows"
        ),
        "sample_is_representative_or_independent_fire_validation": False,
        "samples": selected,
        "cutoff_UTC": "2022-07-01T00:00:00+00:00",
        "windows_days": [30, 60],
        "window": "[T-window,T)",
        "source_collection": "landsat-c2-l2",
        "platform": "landsat-8",
        "tier": "T1",
        "asset_keys": ["red", "nir08", "swir16", "qa_pixel", "qa_radsat"],
        "reflectance_scale": 0.0000275,
        "reflectance_offset": -0.2,
        "reflectance_bounds": [0, 1],
        "QA_excluded_mask": 191,
        "QA_RADSAT_required": 0,
        "composite": "pixelwise_index_median_then_exact_planar_AOI_weighted_mean",
        "candidate_grid": "EPSG6933_30m_global_origin_zero_unverified_against_old_EE_grid",
        "max_seconds_from_first_network_attempt": 900,
        "max_cumulative_response_body_bytes": 268435456,
        "max_HTTP_attempts": 2048,
        "max_unique_scenes": 40,
        "incomplete_or_over_budget_scene_lists_are_not_valid_features": True,
        "retry_rate_limit_or_authentication_bypass": False,
        "numeric_equivalence_threshold_accepted": None,
        "method_acceptance_full_2024_production_or_model_prediction": False,
        "scientific_values_2023_2024_2025": False,
        "new_training_labels_or_final_merge": False,
        "paid_compute_subscription_or_GCP": False,
        "reference_input_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in (geometry_path, province_path, reference_path)
        },
    }
    out = (
        BASE
        / "landsat_spatial_compatibility_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "proposal.json"
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "status": "offline_proposal_prepared_execution_not_authorized",
        "proposal_sha256": digest(path),
        "producer_sha256": digest(Path(__file__)),
        "samples": selected,
        "network_training_prediction_or_merge": False,
    }
    (out / "readback.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
