"""Describe a separate 2022 Mersin-source calendar diagnostic; no extraction, scoring or fit."""

import calendar
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
OLD = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1"
PARTITION = BASE / "conditional_rank_partition_v1/20261119T210609Z_511e5d9f"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"


def main():
    pins = {
        OLD / "readback.json": "ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405",
        PARTITION
        / "readback.json": "c2ffa568ec7138c734b71a70d5091ba1ca1de46c38e67d58dd90fcd00eb1a391",
        CALENDAR
        / "readback.json": "b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040",
    }
    require(
        all(digest(p) == h for p, h in pins.items()), "Frozen source role and calendar metadata"
    )
    old, partition, current = [
        json.loads((p / "readback.json").read_bytes()) for p in (OLD, PARTITION, CALENDAR)
    ]
    for folder, report in ((OLD, old), (CALENDAR, current)):
        pins.update({folder / name: h for name, h in report["artifact_sha256"].items()})
    require(all(digest(p) == h for p, h in pins.items()), "Current original X and role files")
    roles = pd.DataFrame(partition["proposed_key_partitions"])
    held = roles.loc[roles.proposed_partition.eq("proposed_assessment_2022")].copy()
    source = held.loc[held.review_population.eq("source_center_hypothesis")]
    other = held.loc[held.review_population.eq("U_geographic_slice")]
    require(len(source) == 81 and len(other) == 87, "Original 81 source/87 unknown 2022 keys")
    require(
        not source.prediction_timestamp_utc.str[:10]
        .eq("2022-05-27")
        .where(source.grid_id.eq("E6933_5K_V1_C642_R876"), False)
        .any(),
        "Protected WF1538 key remains excluded",
    )
    names = [
        f
        for f in old["feature_columns"]
        if f.startswith(("temperature_", "dewpoint_", "wind_", "soil_", "rain_", "vegetation_"))
    ]
    features = parse_csv((OLD / "features.csv").read_bytes())
    complete = set(
        features.loc[features[names].notna().all(axis=1), KEYS].itertuples(index=False, name=None)
    )
    source_keys = set(source[KEYS].itertuples(index=False, name=None))
    other_keys = set(other[KEYS].itertuples(index=False, name=None))
    exact_pairs = [
        (a, b)
        for a in source_keys & complete
        for b in other_keys & complete
        if a[0] == b[0] and a[1][:7] == b[1][:7]
    ]
    strata = sorted({(g, t[:7]) for g, t in source_keys})
    proposed = set()
    for grid, month in strata:
        year, number = map(int, month.split("-"))
        require(year == 2022, "Only existing exploratory 2022 source months")
        for day in range(1, calendar.monthrange(year, number)[1] + 1):
            stamp = f"{month}-{day:02d}T00:00:00+00:00"
            if stamp[:10] != "2022-12-31":
                proposed.add((grid, stamp))
    snapshot = CALENDAR / current["snapshot_directory"]
    current_roles = parse_csv((snapshot / "review_roles.csv").read_bytes())
    available = set(current_roles[KEYS].itertuples(index=False, name=None)) | set(
        features[KEYS].itertuples(index=False, name=None)
    )
    out = (
        BASE
        / "cross_source_calendar_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(sorted(proposed), columns=KEYS).to_csv(
        out / "proposed_2022_source_calendar_keys.csv", index=False
    )
    result = {
        "status": "cross_source_calendar_metadata_proposal_only_no_new_X_or_scoring",
        "source_2022_keys": len(source_keys),
        "original_U_2022_keys_preserved": len(other_keys),
        "complete_dynamic_source_keys": len(source_keys & complete),
        "complete_dynamic_U_keys": len(other_keys & complete),
        "original_same_grid_month_complete_pairs": len(exact_pairs),
        "source_keys_with_original_comparator": len({a for a, _ in exact_pairs}),
        "source_grid_year_months": len(strata),
        "proposed_calendar_keys": len(proposed),
        "keys_with_existing_X_in_review_snapshots": len(proposed & available),
        "keys_needing_local_X_preparation": len(proposed - available),
        "source_anchor_days_preserved": source_keys <= proposed,
        "prospective_sample_is_population_or_independent_true_fire_test": False,
        "source_coordinate_time_semantics_verified": False,
        "original_U_or_weights_changed": False,
        "new_models_fitted": 0,
        "new_scores_or_Y_or_accepted_L_created": 0,
        "new_scientific_daily_files_read": 0,
        "feature_preparation_authorized_by_this_proposal": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {
            "proposed_2022_source_calendar_keys.csv": digest(
                out / "proposed_2022_source_calendar_keys.csv"
            )
        },
        "producer_sha256": digest(Path(__file__)),
    }
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Original source records and feature snapshots unchanged",
    )
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(json.dumps({k: v for k, v in result.items() if isinstance(v, int)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
