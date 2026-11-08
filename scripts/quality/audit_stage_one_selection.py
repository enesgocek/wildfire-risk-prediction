"""Compare nominal observation diagnostics across the full event candidate frame."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
EVENTS = BASE / "full_event_sensitivity_v1/20261022T204358Z_820d043d"
OBS = BASE / "observation_materialization_v1/20261014T145638Z_c0881064"
CALENDAR = BASE / "pu_calendar_observation_v1/20261108T010353Z_12368f01"
PINS = {
    EVENTS / "readback.json": "40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86",
    OBS
    / "accepted_readback.json": "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    CALENDAR / "readback.json": "e9c7ee3a1cda77371467ecf36d0dc6ddf3615aefe9134f1b7544325ed477129b",
}
KEYS = ["grid_id", "prediction_timestamp_utc"]
CATEGORY = "review_category"
NO_CANDIDATE = "no_candidate_in_nine_settings"
SEASONS = ("DJF", "MAM", "JJA", "SON")
PRESENT = "obs_product_present"
LAND = "obs_land_nominal_input_no_residual"
GAP = "obs_nominal_land_center_longest_envelope_gap_seconds"
CLOUD = "obs_cloud"
OBS_METRICS = [
    "zero_selected_land_centers",
    "land_center_gap_at_least_12h",
    "cloud_centers_present",
]
SUMMARY_COUNTS = ["rows", "product_present", *OBS_METRICS]
OBS_COLUMNS = [
    *KEYS,
    PRESENT,
    LAND,
    GAP,
    CLOUD,
    "obs_daily_observation_status",
    "obs_negative_label_permitted",
    "obs_target_window_alignment",
]


def verify(path, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    require(actual == expected, f"Input digest: {path.relative_to(ROOT)}")
    return path


def read_report(path):
    return json.loads(verify(path, PINS[path]).read_bytes())


def candidate_rows(event_report):
    file = verify(
        EVENTS / "candidate_units.csv", event_report["artifact_sha256"]["candidate_units.csv"]
    )
    candidates = pd.read_csv(
        file,
        usecols=[*KEYS, CATEGORY, "target", "positive_label_permitted", "negative_label_permitted"],
    )
    require(
        len(candidates) == event_report["candidate_cell_day_union"] == 7610
        and candidates[CATEGORY].value_counts().to_dict() == event_report["category_counts"]
        and not candidates.duplicated(KEYS).any()
        and candidates.target.isna().all()
        and candidates.positive_label_permitted.eq(False).all()
        and candidates.negative_label_permitted.eq(False).all(),
        "Frozen candidate frame",
    )
    candidates["month"] = candidates[KEYS[1]].str[:7]
    return candidates[[*KEYS, CATEGORY, "month"]]


def compare_month(report, month_candidates, provinces, calendar_days):
    month = report["month"]
    file = verify(OBS / month / "observations.csv.gz", report["table_sha256"])
    observed = pd.read_csv(file, usecols=OBS_COLUMNS)
    days = [day for day in calendar_days if day.startswith(month)]
    expected_stamps = {day + "T00:00:00+00:00" for day in days}
    observed["province"] = observed.grid_id.map(provinces)
    require(
        len(observed) == report["rows"] == len(days) * len(provinces)
        and not observed.duplicated(KEYS).any()
        and set(observed[KEYS[1]]) == expected_stamps
        and observed.province.notna().all()
        and observed.obs_daily_observation_status.eq("unknown").all()
        and observed.obs_negative_label_permitted.eq(False).all()
        and observed.obs_target_window_alignment.eq("boundary_timing_unresolved").all(),
        f"Nominal observation frame: {month}",
    )
    joined = observed.merge(
        month_candidates[[*KEYS, CATEGORY]], on=KEYS, how="left", validate="one_to_one"
    )
    require(joined[CATEGORY].notna().sum() == len(month_candidates), f"Candidate match: {month}")
    joined[CATEGORY] = joined[CATEGORY].fillna(NO_CANDIDATE)
    present = joined[PRESENT].eq(True)
    require(
        present.sum() == report["rows_with_product"]
        and joined.loc[~present, [LAND, GAP, CLOUD]].isna().all().all()
        and joined.loc[present, [LAND, GAP, CLOUD]].notna().all().all(),
        f"Missing source remains separate: {month}",
    )
    joined["rows"] = 1
    joined["product_present"] = present
    joined["zero_selected_land_centers"] = present & joined[LAND].eq(0)
    joined["land_center_gap_at_least_12h"] = present & joined[GAP].ge(12 * 3600)
    joined["cloud_centers_present"] = present & joined[CLOUD].gt(0)
    totals = joined.groupby(["province", CATEGORY], sort=True)[SUMMARY_COUNTS].sum().reset_index()
    totals["year"] = int(month[:4])
    totals["season"] = SEASONS[(int(month[-2:]) % 12) // 3]
    return totals


def compare_candidate_mix(by_stratum):
    """Standardize the comparison group to the candidates' observed stratum mix."""
    strata = ["province", "year", "season"]
    candidate = by_stratum.loc[by_stratum[CATEGORY].ne(NO_CANDIDATE)]
    candidate = candidate.groupby(strata)[SUMMARY_COUNTS].sum()
    candidate = candidate.loc[candidate.product_present.gt(0)]
    other = by_stratum.loc[by_stratum[CATEGORY].eq(NO_CANDIDATE)].set_index(strata)
    other = other.reindex(candidate.index)
    require(other.product_present.gt(0).all(), "Comparison support in each candidate stratum")
    weight = candidate.product_present / candidate.product_present.sum()
    observed_rates = candidate[OBS_METRICS].div(candidate.product_present, axis=0)
    comparison_rates = other[OBS_METRICS].div(other.product_present, axis=0)
    return {
        "strata": len(candidate),
        "candidate_product_rows": int(candidate.product_present.sum()),
        "candidate_rates": observed_rates.mul(weight, axis=0).sum().to_dict(),
        "no_candidate_rates_at_candidate_mix": comparison_rates.mul(weight, axis=0).sum().to_dict(),
        "strata_with_lower_candidate_rate": (observed_rates < comparison_rates).sum().to_dict(),
    }


def main():
    event, observation, calendar = (read_report(path) for path in PINS)
    candidates = candidate_rows(event)
    frame = json.loads(verify(CALENDAR / "frame.json", calendar["frame_sha256"]).read_bytes())
    require(frame["constructed_without_event_selection"] is True, "Independent calendar frame")
    months = {entry["month"]: entry for entry in observation["reports"]}
    require(len(months) == len(observation["reports"]) == 72, "72 training months")
    require(set(months) == {day[:7] for day in frame["prediction_days_utc"]}, "Training scope")
    require(set(candidates.month) <= set(months), "Candidates within observation calendar")
    parts = [
        compare_month(
            months[month],
            candidates.loc[candidates.month.eq(month)],
            frame["grid_primary_provinces"],
            frame["prediction_days_utc"],
        )
        for month in sorted(months)
    ]
    combined = pd.concat(parts, ignore_index=True)
    by_stratum = combined.groupby(["province", "year", "season", CATEGORY], as_index=False)[
        SUMMARY_COUNTS
    ].sum()
    totals = combined.groupby(CATEGORY)[SUMMARY_COUNTS].sum()
    require(
        totals.rows.sum() == frame["rows_before_eligibility"] == 6351709
        and totals.loc[NO_CANDIDATE, "rows"] == 6351709 - len(candidates)
        and totals.drop(index=NO_CANDIDATE).rows.to_dict() == event["category_counts"],
        "Complete calendar partition",
    )
    report = {
        "scope": "training_nominal_observation_selection_diagnostic",
        "inputs_sha256": {
            path.relative_to(ROOT).as_posix(): digest for path, digest in PINS.items()
        },
        "candidate_input_sha256": event["artifact_sha256"]["candidate_units.csv"],
        "observation_tables_checked": len(months),
        "calendar_frame_sha256": calendar["frame_sha256"],
        "by_category": totals.reset_index().to_dict("records"),
        "by_province_year_season_category": by_stratum.to_dict("records"),
        "comparison_at_candidate_province_year_season_mix": compare_candidate_mix(by_stratum),
        "target_admission": specification(),
    }
    out = BASE / "stage_one_selection_v1" / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    out.mkdir(parents=True)
    file = out / "readback.json"
    file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(file.read_bytes()) == report, "Output roundtrip")
    print(file.relative_to(ROOT).as_posix())
    print(hashlib.sha256(file.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
