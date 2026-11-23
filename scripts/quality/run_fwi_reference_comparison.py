"""Approved small retrospective FWI/frozen-score comparison; no model loading or fitting."""

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

from wildfire_risk_prediction import fwi_reference as fwi
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/fwi_reference_comparison_execution_v1.json"
PLAN = BASE / "fwi_reference_comparison_plan_v1/20261123T002128Z_66578e13/readback.json"
CLOCK = BASE / "fwi_increment_interpretation_v1/20261123T002508Z_5c7204e9/readback.json"
SCORES = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"
NETCDF = ROOT / "data/raw/external/cems_fwi_pilot_v1/ff72cf1a14e9faea5681118fe8888717.nc"
GRID = ROOT / "data/aoi/grid_5km.geojson"
KEYS = ["grid_id", "prediction_timestamp_utc"]
SCORE = "fixed_linear_source_score_not_fire_probability"


def validate(config):
    require(
        config["decision_source"]
        == "user_continue_in_response_to_specific_A_FWI_reference_proposal"
        and config["proposal_sha256"] == digest(PLAN)
        and config["purpose"] == "exploratory_retrospective_reference_not_operational_backtest"
        and config["target_dates"] == ["2022-06-02", "2022-06-30"]
        and config["nominal_FWI_calendar_lag_days"] == 1
        and config["local_limit_seconds"] == 900,
        "Specific continuation, bounded dates and retrospective reference direction",
    )
    require(
        all(
            config[k] is False
            for k in (
                "new_model_fitting_authorized",
                "hyperparameter_or_production_scenario_selection_authorized",
                "new_2023_2024_2025_scientific_values_authorized",
                "new_download_or_cloud_authorized",
                "new_Y_or_accepted_L_authorized",
                "negative_label_permitted",
                "risk_probability_or_validated_colors_authorized",
                "final_merge_permitted",
                "actual_operational_latency_verified",
                "strict_before_target_forcing_proven",
            )
        )
        and config["daily_observation_status"] == "unknown",
        "No widening to fitting, labels, closed years, operational proof or merge",
    )


def main():
    started = monotonic()
    decision = json.loads(CONFIG.read_bytes())
    validate(decision)
    pins = {
        CONFIG: digest(CONFIG),
        PLAN: "d8326d3bd0b54a5b95cdf66e5309b6e6138e7b49f6a06574ba8c37f26b67bdbf",
        CLOCK: "befa8ecc8e7da5dbc580aa379530ba3ea0426879f2b5411c74a525b86e236ea3",
        NETCDF: "e6b57e8ecbd5836f141eb6d0cbd17dc283d6569bb194c5496861d4ba8e5f5a8e",
        GRID: "5695da5111855daa6696b22d213a8ab340e24e561cec3c222ad7152af3de9abe",
        SCORES
        / "readback.json": "a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9",
        Path(fwi.__file__): digest(Path(fwi.__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Pinned existing inputs")
    original = json.loads((SCORES / "readback.json").read_bytes())
    frames = {}
    for name, sha in original["artifact_sha256"].items():
        if not name.endswith("_source_calendar_scores.csv"):
            continue
        p = SCORES / name
        require(digest(p) == sha, "Frozen score CSV unchanged")
        pins[p] = sha
        frame = pd.read_csv(p)
        frame = (
            frame.loc[frame.prediction_timestamp_utc.str[:10].between("2022-06-02", "2022-06-30")]
            .sort_values(KEYS)
            .reset_index(drop=True)
        )
        require(
            len(frame) == 203 and not frame.duplicated(KEYS).any(), "Exact unique proposed keys"
        )
        require(
            frame.target.isna().all()
            and frame.accepted_L_membership.isna().all()
            and frame.daily_observation_status.eq("unknown").all(),
            "Unknown, unlabelled rows",
        )
        frames[name.split("_source_calendar")[0]] = frame
    require(len(frames) == 9, "All nine existing scores without selection")
    first = next(iter(frames.values()))
    for frame in frames.values():
        pd.testing.assert_frame_equal(
            frame.drop(columns=[SCORE]), first.drop(columns=[SCORE]), check_exact=True
        )
    # Protect stored models without unpickling or recalculating their scores.
    for name, sha in original["input_sha256"].items():
        if name.endswith("pairwise_linear.joblib"):
            pins[ROOT / name] = sha
    require(all(digest(p) == h for p, h in pins.items()), "Original model file identities")
    grid = json.loads(GRID.read_bytes())
    geometries = {r["properties"]["grid_id"]: r for r in grid["features"]}
    project = Transformer.from_crs(4326, 6933, always_xy=True, allow_ballpark=False).transform
    geographic = Transformer.from_crs(6933, 4326, always_xy=True, allow_ballpark=False).transform
    mappings, values = [], {}
    with rasterio.open(NETCDF) as dataset:
        require(
            dataset.count == 30
            and dataset.shape == (21, 49)
            and dataset.res == (0.25, 0.25)
            and dataset.scales == (1.0,) * 30
            and dataset.offsets == (0.0,) * 30,
            "Known native pilot grid and units",
        )
        xs = np.array([dataset.xy(0, c)[0] for c in range(dataset.width)])
        ys = np.array([dataset.xy(r, 0)[1] for r in range(dataset.height)])
        for grid_id in sorted(first.grid_id.unique()):
            feature = geometries[grid_id]
            properties = feature["properties"]
            require(
                properties["grid_crs"] == "EPSG:6933" and properties["cell_size_m"] == 5000,
                "Original grid identity",
            )
            polygon = transform(project, shape(feature["geometry"]))
            centroid = polygon.centroid
            expected = (properties["column"] * 5000 + 2500, properties["row"] * 5000 + 2500)
            require(
                abs(centroid.x - expected[0]) < 0.01 and abs(centroid.y - expected[1]) < 0.01,
                "Independent ID/geometry center",
            )
            lon, lat = geographic(centroid.x, centroid.y)
            node = fwi.nearest_node(lon, lat, xs, ys)
            # Independent all-node spherical haversine computation validates geodesic selection.
            candidates = []
            for row, y in enumerate(ys):
                for col, x in enumerate(xs):
                    z = (
                        math.sin(math.radians(y - lat) / 2) ** 2
                        + math.cos(math.radians(y))
                        * math.cos(math.radians(lat))
                        * math.sin(math.radians(x - lon) / 2) ** 2
                    )
                    distance = 2 * fwi.SOURCE_RADIUS_M * math.asin(math.sqrt(min(1, z)))
                    candidates.append((distance, row, col))
            independent = min(candidates)
            require(
                independent[1:] == (node["native_row"], node["native_column"])
                and abs(independent[0] - node["distance_on_source_sphere_m"]) < 1e-6,
                "Independent nearest node",
            )
            mappings.append(
                {
                    "grid_id": grid_id,
                    "projected_center_x_m": centroid.x,
                    "projected_center_y_m": centroid.y,
                    "center_longitude_WGS84": lon,
                    "center_latitude_WGS84": lat,
                    **node,
                }
            )
        for stamp in sorted(first.prediction_timestamp_utc.unique()):
            band, nominal_day = fwi.lagged_band(stamp)
            require(
                dataset.tags(band)["NETCDF_DIM_valid_time"]
                == str(int(datetime.fromisoformat(nominal_day).replace(tzinfo=UTC).timestamp())),
                "Exact prior nominal calendar day",
            )
            raster = dataset.read(band, masked=True)
            for node in mappings:
                values[(node["grid_id"], stamp)] = fwi.sample_preserving_missing(
                    raster, node["native_row"], node["native_column"]
                )
            require(
                monotonic() - started < decision["local_limit_seconds"], "Bounded local execution"
            )
    combined = first.drop(columns=[SCORE]).copy()
    combined["FWI_previous_nominal_day"] = [
        fwi.lagged_band(s)[1] for s in combined.prediction_timestamp_utc
    ]
    combined["FWI_retrospective_reference_not_probability"] = [
        values[k] for k in combined[KEYS].itertuples(index=False, name=None)
    ]
    for scenario, frame in frames.items():
        combined[scenario + "_frozen_source_score"] = frame[SCORE]
    variants = {"previous_day_FWI": combined.FWI_retrospective_reference_not_probability.to_numpy()}
    variants.update({name: frame[SCORE].to_numpy() for name, frame in frames.items()})
    support = np.logical_and.reduce([np.isfinite(x) for x in variants.values()])
    combined["common_reference_and_all_nine_scores_finite"] = support
    source = combined.original_source_record_key_present.to_numpy()
    a, b = fwi.matched_pairs(combined.grid_id, combined.prediction_timestamp_utc, source, support)
    independent_pairs = {
        (i, j)
        for i in range(len(combined))
        for j in range(len(combined))
        if support[i]
        and support[j]
        and source[i]
        and not source[j]
        and combined.grid_id.iloc[i] == combined.grid_id.iloc[j]
        and combined.prediction_timestamp_utc.iloc[i][:7]
        == combined.prediction_timestamp_utc.iloc[j][:7]
    }
    require(
        len(a) > 0 and set(zip(a, b, strict=True)) == independent_pairs,
        "Independent exact common pair identities",
    )
    dates = pd.to_datetime(combined.prediction_timestamp_utc, utc=True)
    gaps = (
        dates.iloc[a].reset_index(drop=True) - dates.iloc[b].reset_index(drop=True)
    ).dt.total_seconds().to_numpy() / 86400
    masks = {
        "all_same_grid_month": np.ones(len(a), dtype=bool),
        "other_before_source": gaps > 0,
        "other_after_source": gaps < 0,
        "gap_1_to_3_days": np.abs(gaps) <= 3,
        "gap_4_to_30_days": np.abs(gaps) >= 4,
    }
    metrics, per_grid = [], []
    for name, score in variants.items():
        for label, mask in masks.items():
            result = fwi.pair_credit(score, a[mask], b[mask])
            if result["pairs"]:
                scalar = (
                    sum(
                        1 if score[i] > score[j] else 0.5 if score[i] == score[j] else 0
                        for i, j in zip(a[mask], b[mask], strict=True)
                    )
                    / result["pairs"]
                )
                require(result["auxiliary_pair_AUC"] == scalar, "Independent scalar credit")
            metrics.append({"variant": name, "slice": label, **result})
        for grid_id in sorted(combined.grid_id.unique()):
            mask = combined.grid_id.to_numpy()[a] == grid_id
            per_grid.append(
                {"variant": name, "grid_id": grid_id, **fwi.pair_credit(score, a[mask], b[mask])}
            )
    require(all(digest(p) == h for p, h in pins.items()), "All original files unchanged")
    out = (
        BASE
        / "fwi_reference_comparison_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    combined.to_csv(out / "common_calendar_review.csv", index=False)
    pd.DataFrame(mappings).to_csv(out / "native_node_mapping.csv", index=False)
    pd.DataFrame(metrics).to_csv(out / "matched_reference_metrics.csv", index=False)
    pd.DataFrame(per_grid).to_csv(out / "per_cell_reference_metrics.csv", index=False)
    pd.DataFrame(
        {
            "source_row": a,
            "other_row_not_true_negative": b,
            "source_grid": combined.grid_id.to_numpy()[a],
            "source_timestamp": combined.prediction_timestamp_utc.to_numpy()[a],
            "other_timestamp": combined.prediction_timestamp_utc.to_numpy()[b],
        }
    ).to_csv(out / "common_pairs.csv", index=False)
    summary = {
        "status": "bounded_retrospective_FWI_reference_comparison_complete_not_fire_validation",
        "decision": decision,
        "calendar_keys": len(combined),
        "common_finite_keys": int(support.sum()),
        "missing_reference_keys_retained": int((~np.isfinite(variants["previous_day_FWI"])).sum()),
        "source_keys_before_support": int(source.sum()),
        "source_keys_on_common_support": int((source & support).sum()),
        "common_pairs": len(a),
        "native_nodes_selected": len({(r["native_row"], r["native_column"]) for r in mappings}),
        "maximum_center_to_native_node_m": max(r["distance_on_source_sphere_m"] for r in mappings),
        "all_seven_same_node_under_WGS84_distance": all(
            r["same_nearest_node_using_WGS84_distance"] for r in mappings
        ),
        "metrics": metrics,
        "new_models_fitted_or_loaded": 0,
        "closed_year_values_opened": False,
        "Y_or_accepted_L_created": 0,
        "negative_label_permitted": False,
        "final_merge_performed": False,
        "operational_time_validity_proven": False,
        "source_is_true_fire_validation": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.glob("*.csv")},
        "producer_sha256": digest(Path(__file__)),
        "elapsed_seconds": monotonic() - started,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print(
        pd.DataFrame(metrics).query("slice == 'all_same_grid_month'").to_string(index=False),
        flush=True,
    )


if __name__ == "__main__":
    main()
