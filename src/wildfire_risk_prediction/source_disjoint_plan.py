"""Key/membership-only feasibility for a proposed frozen-score evaluation."""

from datetime import datetime

import pandas as pd

from .feature_join import require

GROUPS = (
    "original_source_calendar",
    "exclude_any_same_key_satellite_proposal",
    "absent_from_four_province_calendar",
)
SLICES = (
    "all_same_grid_month",
    "gap_1_to_3_days",
    "gap_4_to_30_days",
    "other_day_before_source_day",
    "other_day_after_source_day",
)


def inventory(records):
    require(
        len({(r["cohort"], r["grid"], r["time"]) for r in records}) == len(records),
        "Unique cohort/cell/day keys",
    )
    require(
        all(datetime.fromisoformat(r["time"]).year == 2022 for r in records),
        "Only existing 2022 key inventory",
    )
    four = {(r["grid"], r["time"]): r for r in records if r["cohort"] == "four_province"}
    mersin = [r for r in records if r["cohort"] == "separate_Mersin"]
    require(all(r["flags"] in (0, 511) for r in mersin), "Fixed original Mersin source membership")
    rows = []
    for source in mersin:
        if not source["flags"]:
            continue
        shared = four.get((source["grid"], source["time"]))
        category = (
            "absent_from_four_calendar"
            if shared is None
            else "same_key_satellite_proposal"
            if shared["flags"]
            else "same_key_unassigned"
        )
        controls = [
            r
            for r in mersin
            if r["eligible"]
            and not r["flags"]
            and r["grid"] == source["grid"]
            and r["time"][:7] == source["time"][:7]
        ]
        deltas = (
            [
                (datetime.fromisoformat(r["time"]) - datetime.fromisoformat(source["time"])).days
                for r in controls
            ]
            if source["eligible"]
            else []
        )
        rows.append(
            {
                "grid_id": source["grid"],
                "prediction_timestamp_utc": source["time"],
                "exact_key_category": category,
                "primary_eligible": source["eligible"],
                "original_source_scenarios": source["flags"].bit_count(),
                "four_province_source_scenarios": shared["flags"].bit_count() if shared else 0,
                "planned_pairs_all_same_grid_month": len(deltas),
                "planned_pairs_gap_1_to_3_days": sum(1 <= abs(d) <= 3 for d in deltas),
                "planned_pairs_gap_4_to_30_days": sum(4 <= abs(d) <= 30 for d in deltas),
                "planned_pairs_other_day_before_source_day": sum(d < 0 for d in deltas),
                "planned_pairs_other_day_after_source_day": sum(d > 0 for d in deltas),
            }
        )
    return pd.DataFrame(rows)


def group_mask(anchors, group):
    require(group in GROUPS, "Proposed source subset")
    if group == GROUPS[0]:
        return pd.Series(True, index=anchors.index)
    return (
        anchors.exact_key_category.ne("same_key_satellite_proposal")
        if group == GROUPS[1]
        else anchors.exact_key_category.eq("absent_from_four_calendar")
    )


def support(anchors):
    rows = []
    for group in GROUPS:
        selected = anchors.loc[group_mask(anchors, group)]
        for section in SLICES:
            column = "planned_pairs_" + section
            rows.append(
                {
                    "source_group": group,
                    "slice": section,
                    "all_source_anchors": len(selected),
                    "eligible_source_anchors": int(selected.primary_eligible.sum()),
                    "contributing_source_anchors": int(selected[column].gt(0).sum()),
                    "planned_comparison_pairs_per_model_scenario": int(selected[column].sum()),
                    "contributing_cells": selected.loc[selected[column].gt(0), "grid_id"].nunique(),
                }
            )
    return pd.DataFrame(rows)
