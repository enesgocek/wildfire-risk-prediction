"""Inventory existing satellite candidate keys for a possible PU route, never assign L or Y."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from prepare_full_u_feature_review import GRID, PROVINCES, U_SHA, U, province_support
from prepare_source_pu_feature_review import review_key

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "full_event_sensitivity_v1/20261022T204358Z_820d043d/readback.json"
PARENT_SHA = "40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86"
GRID_SHA = "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
PROVINCES_SHA = "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb"
WATER = BASE / "water_scope_v1/20261014T185242Z_f2e469bd/grid_water_scope.csv"
WATER_SHA = "5ab988c0b59a51a92763187359bb84588929f95926d827d6e5d177a8aa329946"


def fit_units(rows):
    kept, boundary, other_role = [], [], 0
    seen = set()
    for row in rows:
        # Only time metadata is read for 2023 calibration rows.
        stamp = row["prediction_timestamp_utc"]
        if stamp[:4] not in {str(y) for y in range(2018, 2023)}:
            other_role += 1
            continue
        if stamp[:10] == "2022-12-31":
            boundary.append({"grid_id": row["grid_id"], "prediction_timestamp_utc": stamp})
            continue
        key = review_key(row["grid_id"], stamp)
        require(key not in seen, "Unique candidate cell-day")
        seen.add(key)
        require(
            row["target"] == ""
            and all(
                row[f] == "False"
                for f in (
                    "event_identity_accepted",
                    "event_membership_complete",
                    "positive_label_permitted",
                    "negative_label_permitted",
                )
            ),
            "All catalogue candidates remain unadmitted",
        )
        item = dict(row)
        item["weak_positive_membership"] = None
        item["target"] = None
        item["source_semantics"] = "retrospective_component_first_key_not_verified_new_fire"
        kept.append(item)
    return kept, boundary, other_role


def u_context(u_rows, candidates):
    index = {(x["grid_id"], x["prediction_timestamp_utc"]): x for x in candidates}
    result, seen = [], set()
    for row in u_rows:
        key = review_key(row["grid_id"], row["prediction_timestamp_utc"])
        require(
            key not in seen
            and row["target"] == ""
            and row["daily_observation_status"] == "unknown",
            "Same unknown U",
        )
        seen.add(key)
        found = index.get(key)
        result.append(
            {
                **row,
                "catalogue_first_candidate_context_present": found is not None,
                "candidate_setting_support": int(found["scenarios_with_candidate"]) if found else 0,
                "context_is_fire_label": False,
                "candidate_overlap_removed": False,
            }
        )
    return result


def main():
    pins = {
        PARENT: PARENT_SHA,
        GRID: GRID_SHA,
        PROVINCES: PROVINCES_SHA,
        U: U_SHA,
        WATER: WATER_SHA,
    }
    require(all(digest(p) == h for p, h in pins.items()), "Original candidate, U and scope pins")
    parent = json.loads(PARENT.read_bytes())
    path = PARENT.parent / "candidate_units.csv"
    pins[path] = parent["artifact_sha256"][path.name]
    require(digest(path) == pins[path], "Original all-scenario candidate inventory")
    with path.open(encoding="utf-8", newline="") as stream:
        candidates, boundary, other_role = fit_units(csv.DictReader(stream))
    require(
        len(candidates) + len(boundary) + other_role == 7610,
        "All original candidates accounted for",
    )
    with U.open(encoding="utf-8", newline="") as stream:
        context = u_context(list(csv.DictReader(stream)), candidates)
    require(len(context) == 2048, "Original full U retained")
    water = pd.read_csv(WATER)
    retained = set(water.loc[water.water_scope_included, "grid_id"])
    require(len(retained) == 2889, "Same water scope")
    grid = gpd.read_file(GRID).to_crs(6933)
    support = province_support(grid, gpd.read_file(PROVINCES).to_crs(6933))
    names = support.groupby("grid_id").province.agg(lambda x: "|".join(sorted(x)))
    for row in candidates:
        row["water_scope_retained"] = row["grid_id"] in retained
        row["province_area_support"] = names.loc[row["grid_id"]]
    out = (
        BASE
        / "satellite_PU_inventory_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(candidates).to_csv(out / "candidate_key_inventory.csv", index=False)
    pd.DataFrame(context).to_csv(out / "unchanged_U_candidate_context.csv", index=False)
    provinces = {}
    for province in sorted(support.province.unique()):
        rows = [r for r in candidates if province in r["province_area_support"].split("|")]
        provinces[province] = {
            "candidate_keys": len(rows),
            "water_scope_retained": sum(r["water_scope_retained"] for r in rows),
            "year_counts": dict(Counter(r["prediction_timestamp_utc"][:4] for r in rows)),
        }
    report = {
        "status": "satellite_noisy_PU_direction_inventory_only_no_L_or_Y",
        "parent_2018_2023_key_union": 7610,
        "fit_2018_2022_keys": len(candidates),
        "2022_year_end_keys_preserved_in_parent": boundary,
        "calibration_role_keys_not_inspected_beyond_time_metadata": other_role,
        "fit_categories": dict(Counter(r["review_category"] for r in candidates)),
        "fit_water_scope_outside_keys_preserved": sum(
            not r["water_scope_retained"] for r in candidates
        ),
        "province_membership_counts_may_overlap": provinces,
        "U_keys_retained": len(context),
        "U_keys_with_candidate_context": sum(
            r["catalogue_first_candidate_context_present"] for r in context
        ),
        "U_keys_without_context_are_verified_negative": False,
        "overlapping_U_keys_removed_or_relabeled": False,
        "new_graphs_or_lineage_runs": False,
        "cached_first_key_is_causal_lineage_birth": False,
        "new_L_or_Y_memberships": 0,
        "model_trained": False,
        "primary_24h_new_forest_shrub_fire_target_changed": False,
        "satellite_PU_method_selected": False,
        "scenario_selected": None,
        "main_method_accepted": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {
            n: digest(out / n)
            for n in ("candidate_key_inventory.csv", "unchanged_U_candidate_context.csv")
        },
    }
    require(all(digest(p) == h for p, h in pins.items()), "Original inputs unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(
        "fit_candidate_keys",
        len(candidates),
        "U_candidate_overlaps",
        report["U_keys_with_candidate_context"],
    )
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
