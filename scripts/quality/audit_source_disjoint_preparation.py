"""Check proposal counts from original CSV exports without the planning helper."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PLAN = BASE / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
KEYS = ["grid_id", "prediction_timestamp_utc"]


def main():
    receipt = json.loads((PLAN / "readback.json").read_bytes())
    pins = {ROOT / name: sha for name, sha in receipt["input_sha256"].items()}
    pins.update({PLAN / name: sha for name, sha in receipt["artifact_sha256"].items()})
    reference = json.loads((REVIEW / "readback.json").read_bytes())
    if (
        digest(REVIEW / "readback.json")
        != "4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e"
    ):
        raise ValueError("Original review receipt")
    overlap_path = REVIEW / "Mersin_source_anchor_overlap.csv"
    pins[overlap_path] = reference["artifact_sha256"][overlap_path.name]
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("All original and proposal bytes")
    anchors = pd.read_csv(overlap_path)
    flag_columns = [c for c in anchors if c.startswith("S_candidate_context_")]
    anchors["exact_key_category"] = [
        "same_key_satellite_proposal"
        if has_proposal
        else "same_key_unassigned"
        if shared
        else "absent_from_four_calendar"
        for shared, has_proposal in zip(
            anchors.also_in_four_province_calendar,
            anchors[flag_columns].eq(True).any(axis=1),
            strict=True,
        )
    ]
    columns = KEYS + ["primary_weather_and_dynamic_15_eligible"]
    days = pd.read_csv(RUN / "d1000m_t24h/separate_Mersin_scores.csv", usecols=columns)
    anchor_keys = set(anchors[KEYS].itertuples(index=False, name=None))
    other = days.loc[
        days.primary_weather_and_dynamic_15_eligible
        & ~days[KEYS].apply(tuple, axis=1).isin(anchor_keys)
    ].copy()
    anchors = anchors.merge(days, on=KEYS, how="left", validate="one_to_one")
    anchors["primary_eligible"] = anchors.primary_weather_and_dynamic_15_eligible
    for name in (
        "all_same_grid_month",
        "gap_1_to_3_days",
        "gap_4_to_30_days",
        "other_day_before_source_day",
        "other_day_after_source_day",
    ):
        anchors["planned_pairs_" + name] = 0
    for i, row in anchors.iterrows():
        if not row.primary_eligible:
            continue
        controls = other.loc[
            other.grid_id.eq(row.grid_id)
            & other.prediction_timestamp_utc.str[:7].eq(row.prediction_timestamp_utc[:7])
        ]
        offsets = (
            pd.to_datetime(controls.prediction_timestamp_utc, utc=True)
            - pd.Timestamp(row.prediction_timestamp_utc)
        ).dt.days
        values = [
            len(offsets),
            int(offsets.abs().between(1, 3).sum()),
            int(offsets.abs().between(4, 30).sum()),
            int(offsets.lt(0).sum()),
            int(offsets.gt(0).sum()),
        ]
        for name, value in zip(
            [c for c in anchors if c.startswith("planned_pairs_")], values, strict=True
        ):
            anchors.loc[i, name] = value
    planned = pd.read_csv(PLAN / "source_anchor_inventory.csv")
    selected_columns = (
        KEYS
        + ["exact_key_category", "primary_eligible"]
        + [c for c in anchors if c.startswith("planned_pairs_")]
    )
    pd.testing.assert_frame_equal(
        planned[selected_columns].sort_values(KEYS).reset_index(drop=True),
        anchors[selected_columns].sort_values(KEYS).reset_index(drop=True),
        check_dtype=False,
        check_exact=True,
    )
    counts = pd.read_csv(PLAN / "planned_support.csv")
    if len(counts) != 15 or counts.duplicated(["source_group", "slice"]).any():
        raise ValueError("All three nested groups and five slices")
    for row in counts.itertuples():
        eligible = anchors
        if row.source_group == "exclude_any_same_key_satellite_proposal":
            eligible = anchors.loc[anchors.exact_key_category.ne("same_key_satellite_proposal")]
        elif row.source_group == "absent_from_four_province_calendar":
            eligible = anchors.loc[anchors.exact_key_category.eq("absent_from_four_calendar")]
        elif row.source_group != "original_source_calendar":
            raise ValueError("Unknown proposed group")
        c = "planned_pairs_" + row.slice
        expected = (
            len(eligible),
            int(eligible.primary_eligible.sum()),
            int(eligible[c].gt(0).sum()),
            int(eligible[c].sum()),
            eligible.loc[eligible[c].gt(0), "grid_id"].nunique(),
        )
        actual = (
            row.all_source_anchors,
            row.eligible_source_anchors,
            row.contributing_source_anchors,
            row.planned_comparison_pairs_per_model_scenario,
            row.contributing_cells,
        )
        if actual != expected:
            raise ValueError("Independent planned support")
    out = (
        BASE
        / "source_disjoint_preparation_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "original_csv_key_membership_plan_audit_passed",
        "anchors": len(anchors),
        "support_rows": len(counts),
        "performance_evaluation_run": False,
        "new_model_or_prediction_calls": 0,
        "true_fire_validation": False,
        "proposal_readback_sha256": digest(PLAN / "readback.json"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
