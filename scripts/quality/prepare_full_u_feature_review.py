"""Materialize the unchanged four-province U sample for inspection, never labels or fitting."""

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import geopandas as gpd
import pandas as pd
import prepare_source_pu_feature_review as source_review

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.feature_readiness import inspect_day
from wildfire_risk_prediction.target_admission import specification

ROOT, BASE = source_review.ROOT, source_review.BASE
U = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/U_key_sample.csv"
U_SHA = "fd77c27454083e45f625e7e94ef0a14e5ace7d65636cace59b92261666c4d19f"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
PROVINCES = ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
PREVIEW = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1/readback.json"
PREVIEW_SHA = "ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405"


def province_support(grid, provinces):
    """Positive-area memberships; a boundary touch alone is not province support."""
    join.require(
        grid.crs is not None
        and grid.crs.to_epsg() == 6933
        and provinces.crs is not None
        and provinces.crs.to_epsg() == 6933,
        "Explicit equal-area geometries",
    )
    join.require(grid.grid_id.is_unique and provinces.GAUL1_NAME.is_unique, "Unique geometries")
    result = []
    for row in provinces.itertuples():
        overlap = grid.geometry.intersection(row.geometry).area
        for idx in grid.index[overlap.gt(0)]:
            result.append(
                {
                    "grid_id": grid.loc[idx, "grid_id"],
                    "province": row.GAUL1_NAME,
                    "intersection_area_m2": float(overlap.loc[idx]),
                    "fraction_of_grid_aoi_area": float(
                        overlap.loc[idx] / grid.loc[idx].geometry.area
                    ),
                }
            )
    support = pd.DataFrame(result)
    join.require(
        set(support.grid_id) == set(grid.grid_id), "Every selected cell has province support"
    )
    return support.sort_values(["grid_id", "province"]).reset_index(drop=True)


def inspection_table(sample, features, support):
    join.require(
        not sample.duplicated(join.KEYS).any()
        and not features.duplicated(join.KEYS).any()
        and set(map(tuple, sample[join.KEYS].to_numpy()))
        == set(map(tuple, features[join.KEYS].to_numpy())),
        "Exact original U keys without inner-join losses",
    )
    join.require(
        sample.target.isna().all()
        and sample.daily_observation_status.eq("unknown").all()
        and sample.review_role.eq("U_unknown_not_negative").all(),
        "No U negative labels",
    )
    join.require(features.columns.tolist() == join.KEYS + join.feature_names(), "Only feature X")
    metadata = sample.copy()
    names = support.groupby("grid_id").province.agg(lambda x: "|".join(sorted(x)))
    metadata["province_support"] = metadata.grid_id.map(names)
    join.require(metadata.province_support.notna().all(), "No unmatched province metadata")
    result = metadata.merge(features, on=join.KEYS, how="left", validate="one_to_one", sort=False)
    fields = join.feature_names()
    result["missing_feature_count"] = result[fields].isna().sum(axis=1)
    join.require(len(result) == len(sample) and result.target.isna().all(), "Inspection only")
    return result


def main():
    started = monotonic()
    store = source_review.SOURCE_FEATURES
    pins = {
        source_review.PROTOCOL: source_review.PROTOCOL_SHA,
        U: U_SHA,
        PREVIEW: PREVIEW_SHA,
        store / "readback.json": source_review.FEATURE_REPORT_SHA,
        Path(source_review.__file__): digest(Path(source_review.__file__)),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Pinned U and source review")
    parent = json.loads(source_review.PROTOCOL.read_bytes())
    feature_report = json.loads((store / "readback.json").read_bytes())
    preview = json.loads(PREVIEW.read_bytes())
    pins.update({ROOT / p: h for p, h in parent["input_sha256"].items()})
    for name in ("verified_daily_files.csv", "input_manifest.json"):
        pins[store / name] = feature_report["artifact_sha256"][name]
    for name in ("features.csv", "inspection.csv", "source_case_mapping.json"):
        pins[PREVIEW.parent / name] = preview["artifact_sha256"][name]
    join.require(all(digest(p) == h for p, h in pins.items()), "Current frozen parents")
    sample = pd.read_csv(U, float_precision="round_trip")
    with U.open(encoding="utf-8-sig", newline="") as stream:
        sources, keys, mapping = source_review.collect_keys(
            parent["cases"], list(csv.DictReader(stream))
        )
    join.require(
        len(keys) == len(sample) == 2048
        and len(sources) == 374
        and len(mapping) == 380
        and not sources.intersection(keys),
        "Unchanged U sample and source keys",
    )
    days, by_day = defaultdict(set), defaultdict(dict)
    for grid, stamp in keys:
        days[stamp[:10]].add(grid)
    with (store / "verified_daily_files.csv").open(encoding="utf-8", newline="") as stream:
        for entry in csv.DictReader(stream):
            if entry["day"] in days:
                join.require(entry["kind"] not in by_day[entry["day"]], "Unique daily index")
                by_day[entry["day"]][entry["kind"]] = entry
    join.require(
        set(by_day) == set(days)
        and all(set(v) == {"features", "provenance"} for v in by_day.values()),
        "Both parts for all original U days",
    )
    old_pins = json.loads((store / "input_manifest.json").read_bytes())
    pins[source_review.STATIC] = old_pins[source_review.STATIC.relative_to(ROOT).as_posix()]
    for name in (
        "feature_join",
        "feature_partition",
        "feature_readiness",
        "landscape",
        "weather_policy",
    ):
        path = ROOT / f"src/wildfire_risk_prediction/{name}.py"
        pins[path] = old_pins.get(path.relative_to(ROOT).as_posix(), digest(path))
    join.require(all(digest(p) == h for p, h in pins.items()), "Source/checker identities")
    static = parse_csv(source_review.STATIC.read_bytes())
    rows, provenance, checks = [], [], []
    for number, day in enumerate(sorted(days), 1):
        tables = {}
        for kind in ("features", "provenance"):
            entry = by_day[day][kind]
            path, full = source_review.selected_file(ROOT, entry, day, kind)
            pins[path] = entry["sha256"]
            tables[kind] = full.loc[full.grid_id.isin(days[day])].copy()
        checks.append(
            inspect_day(
                tables["features"],
                tables["provenance"],
                sorted(days[day]),
                day,
                static.loc[static.grid_id.isin(days[day])],
            )
        )
        rows.append(tables["features"])
        provenance.append(tables["provenance"])
        if number % 100 == 0:
            print(f"FOUR PROVINCE U FEATURE DAYS {number}/{len(days)}", flush=True)
    features = pd.concat(rows, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    qa = pd.concat(provenance, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    join.require(len(features) == len(qa) == 2048, "Every U key retained exactly once")
    grid = gpd.read_file(GRID).to_crs(6933)
    support = province_support(
        grid.loc[grid.grid_id.isin(sample.grid_id)], gpd.read_file(PROVINCES).to_crs(6933)
    )
    inspection = inspection_table(sample, features, support)
    old_features = parse_csv((PREVIEW.parent / "features.csv").read_bytes())
    old_u = (
        old_features.set_index(join.KEYS)
        .loc[sorted(keys.intersection(map(tuple, old_features[join.KEYS].to_numpy())))]
        .reset_index()
    )
    join.require(len(old_u) == 503, "Same Mersin slice as before")
    pd.testing.assert_frame_equal(
        features.set_index(join.KEYS).loc[old_u.set_index(join.KEYS).index].reset_index(),
        old_u,
        check_dtype=False,
        check_exact=True,
    )
    out = (
        BASE
        / "full_U_feature_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    artifacts = {}
    for name, frame in (
        ("features.csv", features),
        ("provenance.csv", qa),
        ("inspection.csv", inspection),
        ("grid_province_support.csv", support),
    ):
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(path.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[name] = digest(path)
    profiles = {}
    for province in sorted(support.province.unique()):
        cells = set(support.loc[support.province.eq(province), "grid_id"])
        selected = {(g, t) for g, t in keys if g in cells}
        profiles[province] = source_review.describe(features, selected)
    report = {
        "status": "unchanged_four_province_U_features_inspectable_not_labeled_dataset",
        "U_keys": 2048,
        "unique_U_cells": int(sample.grid_id.nunique()),
        "days_read": len(days),
        "daily_files_hash_verified": 2 * len(days),
        "feature_columns": join.feature_names(),
        "all_U_profile": source_review.describe(features, keys),
        "province_profiles_positive_area_memberships_can_overlap": profiles,
        "U_keys_in_multiple_provinces": int(inspection.province_support.str.contains("\\|").sum()),
        "source_records_preserved_in_existing_parent": 380,
        "source_keys_preserved_in_existing_parent": 374,
        "prior_Mersin_U_features_exactly_reproduced": 503,
        "joint_missingness_checks": checks,
        "sampling_unchanged": True,
        "new_sampling_or_imputation": False,
        "source_Mersin_and_other_province_U_used_to_fit_model": False,
        "province_context_is_model_input": False,
        "model_trained": False,
        "new_L_or_Y_labels": 0,
        "all_U_keys_are_unknown_not_negative": True,
        "operational_publication_availability_verified": False,
        "full_daily_2889_cell_score_panel_created": False,
        "risk_bands_or_final_merge_created": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged at closure")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    join.require(json.loads(path.read_bytes()) == report, "Report readback")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print(
        "Complete 27-feature rows", report["all_U_profile"]["complete_27_feature_rows"], flush=True
    )
    print(
        "PASS unchanged_U_review_only; no fire labels, fitting, risk colors or final merge",
        flush=True,
    )
    print("readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
