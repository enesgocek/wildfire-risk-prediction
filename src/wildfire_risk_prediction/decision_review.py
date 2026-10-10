"""Diagnostic support intersections and purposive cases; never select habitat or events."""

import json

import numpy as np

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.habitat_review import THRESHOLDS
from wildfire_risk_prediction.target_admission import detection_windows
from wildfire_risk_prediction.weather_policy import AREA_TOLERANCE

VERSION = "dataset_decision_review_v1"
EVENT_FLAGS = [
    "temporal_chain_review",
    "spatial_chain_review",
    "multi_grid_first_detection_review",
    "calendar_year_crossing_review",
    "period_start_context_missing",
    "period_end_context_missing",
]


def support_intersection(habitat, coverage):
    require(
        not habitat.empty
        and habitat.grid_id.is_unique
        and coverage.grid_id.is_unique
        and habitat.grid_id.notna().all()
        and coverage.grid_id.notna().all()
        and set(habitat.grid_id) == set(coverage.grid_id),
        "Support grid identities",
    )
    require(
        habitat.habitat_eligibility.eq("undecided").all()
        and habitat.negative_label_permitted.eq(False).all(),
        "Habitat still undecided",
    )  # noqa: E712
    values = coverage[["training_min_coverage", "training_max_coverage"]]
    require(
        np.isfinite(values.to_numpy()).all()
        and values.ge(0).all().all()
        and values.le(1).all().all()
        and coverage.training_min_coverage.le(coverage.training_max_coverage).all(),
        "Weather coverage range",
    )
    require(
        np.allclose(
            coverage.training_min_coverage, coverage.training_max_coverage, rtol=0, atol=1e-12
        ),
        "This review requires invariant training support",
    )
    table = habitat.merge(coverage, on="grid_id", validate="one_to_one")
    minimum = table.training_min_coverage
    table["weather_support_group"] = np.where(
        minimum.eq(0), "none", np.where(minimum.ge(1 - AREA_TOLERANCE), "full", "partial")
    )
    groups = []
    for name in ["none", "partial", "full"]:
        part = table.loc[table.weather_support_group.eq(name)]
        groups.append(
            {
                "support_group": name,
                "cells": len(part),
                "aoi_area_km2": float(part.aoi_area_km2.sum()),
                "forest_class_area_km2": float(
                    (part.forest_fraction * part.covered_area_km2).sum()
                ),
                "shrub_class_area_km2": float((part.shrub_fraction * part.covered_area_km2).sum()),
                "natural_class_area_km2": float(
                    (part.natural_vegetation_fraction * part.covered_area_km2).sum()
                ),
            }
        )
    scenarios = []
    for measure in ["forest_fraction", "forest_shrub_fraction", "natural_vegetation_fraction"]:
        for threshold in THRESHOLDS:
            selected = table[measure].ge(threshold)
            scenarios.append(
                {
                    "measure": measure,
                    "threshold_inclusive": threshold,
                    "cells": int(selected.sum()),
                    **{
                        f"weather_{group}_cells": int(
                            (selected & table.weather_support_group.eq(group)).sum()
                        )
                        for group in ["none", "partial", "full"]
                    },
                }
            )
    require(sum(g["cells"] for g in groups) == len(table), "Support partitions")
    return table.sort_values("grid_id").reset_index(drop=True), groups, scenarios


def habitat_cases(table):
    """Retain every water/support flag; add three ranked examples per explicit review question."""
    reasons = {}

    def pick(rows, reason):
        for grid in rows.grid_id:
            reasons.setdefault(grid, set()).add(reason)

    pick(table.loc[table.water_only_flag], "water_only_map_class")
    pick(table.loc[table.terrain_area_review_flag], "terrain_area_review")
    for group in ["none", "partial"]:
        pick(
            table.loc[table.weather_support_group.eq(group)]
            .sort_values(["natural_vegetation_fraction", "grid_id"], ascending=[False, True])
            .head(3),
            f"natural_cover_with_weather_{group}",
        )
    mixed = table.loc[table.forest_fraction.gt(0) & table.agriculture_fraction.gt(0)].copy()
    mixed["joint_fraction"] = mixed[["forest_fraction", "agriculture_fraction"]].min(axis=1)
    pick(
        mixed.sort_values(["joint_fraction", "grid_id"], ascending=[False, True]).head(3),
        "mixed_forest_agriculture",
    )
    result = table.loc[table.grid_id.isin(reasons)].copy()
    result["selection_reasons_json"] = result.grid_id.map(lambda g: json.dumps(sorted(reasons[g])))
    result["sampling"] = "purposive_review_not_representative"
    return result.sort_values("grid_id").reset_index(drop=True)


def event_cases(catalog):
    """At most one extreme per question plus one unflagged reference; no scenario selected."""
    require(catalog.cluster_id.is_unique and not catalog.empty, "Case catalog identities")
    require(catalog.event_status.eq("exploratory_cluster_only").all(), "Exploratory case input")
    window = detection_windows(catalog.first_detection_utc)
    frame = catalog.copy()
    frame["training_window_boundary_review"] = window.training_window_boundary_review
    reasons = {}
    questions = [
        ("temporal_chain_review", "duration_hours"),
        ("spatial_chain_review", "max_distance_from_canonical_first_m"),
        ("multi_grid_first_detection_review", "earliest_grid_count"),
        ("calendar_year_crossing_review", "duration_hours"),
        ("period_start_context_missing", "duration_hours"),
        ("period_end_context_missing", "duration_hours"),
        ("training_window_boundary_review", "duration_hours"),
    ]
    for reason, rank in questions:
        rows = frame.loc[frame[reason]].sort_values([rank, "cluster_id"], ascending=[False, True])
        if len(rows):
            reasons.setdefault(rows.iloc[0].cluster_id, set()).add(reason)
    plain = frame.loc[~frame[EVENT_FLAGS + ["training_window_boundary_review"]].any(axis=1)]
    if len(plain):
        key = plain.sort_values(["first_detection_utc", "cluster_id"]).iloc[0].cluster_id
        reasons.setdefault(key, set()).add("unflagged_reference_not_confirmed_fire")
    result = frame.loc[frame.cluster_id.isin(reasons)].copy()
    result["selection_reasons_json"] = result.cluster_id.map(
        lambda g: json.dumps(sorted(reasons[g]))
    )
    result["sampling"] = "purposive_review_not_representative"
    return result.sort_values("cluster_id").reset_index(drop=True)
