"""Prepare a detection-independent, unlabelled review sample from the audited calendar."""

import hashlib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from audit_pu_calendar_observation import OBS, OBS_COLUMNS, SEASONS
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.water_scope import build_water_scope

FRAME = BASE / "pu_calendar_observation_v1/20261108T010353Z_12368f01"
FRAME_RECEIPT_SHA = "e9c7ee3a1cda77371467ecf36d0dc6ddf3615aefe9134f1b7544325ed477129b"
STATIC = ROOT / "data/interim/landscape/v1/grid_static.csv"
STATIC_SHA = "bd9b2a27e6234d97e41df11dac59fb7bc82242ef282ff60ac75d83cbc3fb0f82"
SEED = 20261108
SCOPE = ["province", "year", "season"]
LAND, GAP = OBS_COLUMNS[-2:]
FRACTIONS = ["forest_fraction", "shrub_fraction", "agriculture_fraction"]
PARTITION = [*SCOPE, "cover_context", "source_sensors", "observation_context"]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def classify(table, source_days):
    present = table.obs_product_present
    require(
        present.eq(table.source_sensors.ne("missing")).all()
        and table.obs_daily_observation_status.eq("unknown").all()
        and table.obs_negative_label_permitted.eq(False).all()
        and table.obs_target_window_alignment.eq("boundary_timing_unresolved").all()
        and table.prediction_day_utc.isin(source_days).all()
        and table.loc[~present, OBS_COLUMNS[-3:]].isna().all().all()
        and table.loc[present, OBS_COLUMNS[-3:]].notna().all().all(),
        "Observation scope, measured values and source gaps",
    )
    table["observation_context"] = np.select(
        [~present, table[LAND].eq(0), table[GAP].ge(43200)],
        ["missing_product", "no_selected_land_center", "land_gap_ge_12h"],
        default="land_gap_lt_12h",
    )
    return table


def top(table, keys, rank):
    return table.loc[table.groupby(keys, sort=True)[rank].idxmin()]


def contrasts(table):
    woody = table.cover_context.eq("forest_shrub_mapped")
    include = table.water_scope_included
    groups = {
        "mapped_water_only": ~include,
        "no_mapped_forest_shrub": include & ~woody,
        "woody_no_selected_land_center": woody
        & table.observation_context.eq("no_selected_land_center"),
        "woody_gap_ge_12h": woody & table.observation_context.eq("land_gap_ge_12h"),
        "source_snpp_only": include & table.source_sensors.eq("SNPP"),
        "source_n20_only": include & table.source_sensors.eq("N20"),
    }
    for group, mask in groups.items():
        yield top(table.loc[mask], ["province"], "contrast_rank").assign(contrast=group)
    missing = table.loc[woody & table.observation_context.eq("missing_product")]
    yield top(missing, ["province", "prediction_day_utc"], "contrast_rank").assign(
        contrast="woody_missing_product"
    )


def publish(path, table):
    table = table.drop(columns=["base_rank", "contrast_rank"]).reset_index(drop=True)
    table["target"] = np.nan
    table["habitat_decision"] = "undecided"
    table.to_csv(path, index=False, mode="x", encoding="utf-8-sig")
    readback = pd.read_csv(path)
    pd.testing.assert_frame_equal(table, readback, check_dtype=False)
    return digest(path)


def main():
    pins = {}

    def retain(path, expected=None):
        actual = digest(path)
        require(expected is None or actual == expected, "Input digest")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    audit = read_json(retain(FRAME / "readback.json", FRAME_RECEIPT_SHA))
    frame = read_json(retain(FRAME / "frame.json", audit["frame_sha256"]))
    grid_provinces = frame["grid_primary_provinces"]
    source_days = audit["nominal_source_days"]
    require(
        frame["constructed_without_event_selection"] is True
        and frame["eligible_unlabelled_training_pool_accepted"] is False
        and list(source_days) == frame["prediction_days_utc"]
        and len(source_days) == 2191
        and len(grid_provinces) == 2899
        and audit["daily_observation_status"] == "unknown"
        and audit["positive_label_permitted"] is False
        and audit["negative_label_permitted"] is False,
        "Audited calendar and closed acceptance gates",
    )
    static = pd.read_csv(retain(STATIC, STATIC_SHA), float_precision="round_trip")
    policy = read_json(retain(ROOT / "configs/water_scope_v1.json"))
    cells = build_water_scope(static, list(grid_provinces), policy).merge(
        static[["grid_id", *FRACTIONS]], on="grid_id", validate="one_to_one"
    )
    cells["province"] = cells.grid_id.map(grid_provinces)
    require(cells.province.notna().all() and cells.province.nunique() == 4, "Province grid keys")
    cells["cover_context"] = np.select(
        [~cells.water_scope_included, cells.forest_shrub_fraction.gt(0)],
        ["mapped_water_only", "forest_shrub_mapped"],
        default="no_forest_shrub_mapped",
    )

    base, examples, partition = [], [], Counter()
    for entry in audit["months"]:
        month = entry["month"]
        path = OBS / month / "observations.csv.gz"
        table = pd.read_csv(
            retain(path, entry["source_sha256"][path.relative_to(ROOT).as_posix()]),
            usecols=OBS_COLUMNS,
        ).rename(columns={"obs_nominal_granule_day": "prediction_day_utc"})
        table = table.sort_values(["prediction_day_utc", "grid_id"], ignore_index=True)
        days = [day for day in source_days if day.startswith(month + "-")]
        require(
            2018 <= int(month[:4]) <= 2023
            and table.prediction_day_utc.tolist() == np.repeat(days, len(cells)).tolist()
            and table.grid_id.tolist() == sorted(grid_provinces) * len(days)
            and table.prediction_timestamp_utc.eq(
                table.prediction_day_utc + "T00:00:00+00:00"
            ).all(),
            "Exact training month keys",
        )
        table = table.merge(cells, on="grid_id", validate="many_to_one", sort=False)
        table["source_sensors"] = table.prediction_day_utc.map(
            {day: "+".join(source_days[day]) if source_days[day] else "missing" for day in days}
        )
        table["year"] = int(month[:4])
        table["season"] = SEASONS[int(month[5:7]) % 12 // 3]
        table = classify(table, days)
        partition.update(table.groupby(PARTITION).size().to_dict())
        rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
        table["base_rank"] = rng.random(len(table))
        table["contrast_rank"] = rng.random(len(table))
        base.append(top(table.loc[table.water_scope_included], SCOPE, "base_rank"))
        examples.extend(contrasts(table))

    denominators, counts = Counter(), Counter()
    for key, n in partition.items():
        province, year, season, cover, _, obs = key
        if cover != "mapped_water_only":
            denominators[province, year, season] += n
        counts[obs] += n
    total = audit["counts"]["all"]
    require(
        sum(counts.values()) == frame["rows_before_eligibility"]
        and counts["missing_product"] == total["missing_product"]
        and counts["no_selected_land_center"] == total["product_rows"] - total["with_land_centers"],
        "Population totals reconcile",
    )
    core = top(pd.concat(base, ignore_index=True), SCOPE, "base_rank").sort_values(SCOPE)
    require(len(core) == len(denominators) == 96, "One sample per province/year/season")
    core["stratum_rows"] = [
        denominators[key] for key in core[SCOPE].itertuples(index=False, name=None)
    ]
    core["inclusion_probability"] = 1 / core.stratum_rows
    example_keys = ["province", "contrast"]
    pool = pd.concat(examples, ignore_index=True)
    # The two missing dates have distinct review slots in each province.
    pool["review_slot_day"] = pool.prediction_day_utc.where(
        pool.contrast.eq("woody_missing_product"), "any"
    )
    example_keys.append("review_slot_day")
    review = top(pool, example_keys, "contrast_rank").sort_values(example_keys)
    water_provinces = set(cells.loc[~cells.water_scope_included, "province"])
    review_counts = review.groupby("province").size().to_dict()
    require(
        review_counts == {p: 7 + int(p in water_provinces) for p in cells.province.unique()}
        and set(review.loc[review.contrast.eq("mapped_water_only"), "province"]) == water_provinces,
        "Diagnostic slots present wherever supported by source",
    )
    keys = ["grid_id", "prediction_day_utc"]
    require(not core.duplicated(keys).any(), "Unique base sample units")

    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "pu_calendar_sample_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    hashes = {
        "sample.csv": publish(out / "sample.csv", core),
        "contrasts.csv": publish(out / "contrasts.csv", review),
    }
    retain(Path(__file__).resolve())
    report = {
        "seed": SEED,
        "source_sha256": pins,
        "output_sha256": hashes,
        "stratification": SCOPE,
        "population_rows": sum(counts.values()),
        "water_scope_rows": sum(denominators.values()),
        "core_rows": len(core),
        "contrast_slots": len(review),
        "distinct_contrast_rows": len(review.drop_duplicates(keys)),
        "overlap_core_contrast": len(core[keys].merge(review[keys].drop_duplicates())),
        "partition": [
            dict(zip(PARTITION, k, strict=True), rows=n) for k, n in sorted(partition.items())
        ],
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "training_pool_accepted": False,
        "final_merge_performed": False,
    }
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
