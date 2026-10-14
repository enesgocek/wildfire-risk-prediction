"""Training-only review selection; observations and exploratory cases are not labels."""

import hashlib
import json
import re

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, utc_times
from wildfire_risk_prediction.observation_table import DIAGNOSTICS
from wildfire_risk_prediction.target_admission import detection_windows

VERSION = "label_evidence_review_v1"
KEYS = ["grid_id", "prediction_timestamp_utc"]
STRATA = ["year", "quarter", "geography_stratum", "signal_stratum"]
SEED = "label-review-pilot-v1-seed42"
REVIEW_FIELDS = [
    "reviewer_id",
    "reviewed_at_utc",
    "evidence_reference",
    "evidence_time_utc",
    "independent_of_firms_viirs",
    "event_interpretation",
    "first_cell_assessment",
    "habitat_assessment",
    "observation_sufficiency_assessment",
    "uncertainty_reason",
    "notes",
]


def geography(grid_ids):
    """Four equal-width grid-column sectors, west to east; explicitly not provinces."""
    ids = sorted(grid_ids)
    require(ids and len(ids) == len(set(ids)), "Unique sampling grid")
    pattern = re.compile(r"E6933_5K_V1_C(\d+)_R(\d+)")
    matches = [pattern.fullmatch(i) for i in ids]
    require(all(matches), "Known equal-area grid identifiers")
    columns = np.array([int(m.group(1)) for m in matches])
    low, high = int(columns.min()), int(columns.max())
    bands = np.minimum((columns - low) * 4 // (high - low + 1), 3) + 1
    return pd.DataFrame(
        {
            "grid_id": ids,
            "grid_column": columns,
            "geography_stratum": [f"west_east_sector_{i}" for i in bands],
        }
    )


def classify(frame, grid):
    """Mutually exclusive sampling signals; no fire/no-fire or observation verdict."""
    require(not frame.empty and not frame.duplicated(KEYS).any(), "Unique grid-day frame")
    times = utc_times(frame.prediction_timestamp_utc)
    require(
        times.notna().all()
        and times.dt.year.between(2018, 2023).all()
        and times.eq(times.dt.normalize()).all(),
        "Training midnight keys only",
    )
    boolean(frame.obs_product_present, "Source product flag")
    boolean(frame.obs_negative_label_permitted, "Negative gate")
    require(
        frame.obs_negative_label_permitted.eq(False).all()
        and frame.obs_daily_observation_status.eq("unknown").all()
        and frame.obs_target_window_alignment.eq("boundary_timing_unresolved").all(),
        "Closed scientific observation gates",
    )
    present = frame.obs_product_present
    require(
        frame.loc[~present, ["obs_" + x for x in DIAGNOSTICS]].isna().all().all(),
        "Absent products retain missing diagnostic values",
    )
    thermal = frame[["obs_nominal_confidence_fire", "obs_high_confidence_fire"]]
    require(
        np.isfinite(thermal.loc[present].to_numpy()).all()
        and thermal.loc[present].ge(0).all().all(),
        "Finite thermal counters",
    )
    result = frame.copy()
    result["year"] = times.dt.year
    result["quarter"] = times.dt.quarter
    mapping = grid.set_index("grid_id").geography_stratum
    require(mapping.index.is_unique, "Unique geography keys")
    result["geography_stratum"] = result.grid_id.map(mapping)
    require(result.geography_stratum.notna().all(), "Sampling geography covers each cell")
    result["signal_stratum"] = np.where(
        ~present,
        "source_product_absent",
        np.where(
            thermal.sum(axis=1).gt(0),
            "thermal_center_present",
            "product_present_no_selected_thermal_center",
        ),
    )
    result["sampling_rank_sha256"] = [
        hashlib.sha256(f"{SEED}|{g}|{t}".encode()).hexdigest()
        for g, t in zip(result.grid_id, times.map(pd.Timestamp.isoformat), strict=True)
    ]
    return result


def smallest(frame, per_stratum):
    require(isinstance(per_stratum, int) and 1 <= per_stratum <= 10, "Bounded pilot allocation")
    return (
        frame.sort_values(["sampling_rank_sha256"] + KEYS)
        .groupby(STRATA, sort=True, dropna=False)
        .head(per_stratum)
        .sort_values(STRATA + ["sampling_rank_sha256"] + KEYS)
        .reset_index(drop=True)
    )


def finalize_sample(candidates, population, per_stratum):
    require(
        not population.duplicated(STRATA).any() and population.population_n.gt(0).all(),
        "Positive stratum population counts",
    )
    sample = smallest(candidates, per_stratum).merge(population, on=STRATA, validate="many_to_one")
    sample["sample_n"] = sample.groupby(STRATA).grid_id.transform("size")
    require(
        sample.sample_n.eq(np.minimum(per_stratum, sample.population_n)).all()
        and len(sample.groupby(STRATA)) == len(population),
        "Every nonempty stratum sampled",
    )
    sample["inclusion_fraction"] = sample.sample_n / sample.population_n
    sample["expansion_weight"] = sample.population_n / sample.sample_n
    sample["review_unit_id"] = [
        f"random:{g}:{t[:10]}"
        for g, t in zip(sample.grid_id, sample.prediction_timestamp_utc, strict=True)
    ]
    sample["selection_purpose"] = "stratified_grid_day_pilot_not_reviewed"
    sample["target"] = pd.NA
    return sample


def event_requests(cases, members):
    """Retain all tied first cells, and distinguish nominal detection day from candidate T."""
    require(
        not cases.empty and not cases.duplicated(["scenario", "cluster_id"]).any(),
        "Unique event-scenario cases",
    )
    require(cases.event_status.eq("exploratory_cluster_only").all(), "Exploratory cases only")
    boolean(cases.negative_label_permitted, "Case negative gate")
    require(cases.negative_label_permitted.eq(False).all(), "No admitted event labels")
    windows = detection_windows(cases.first_detection_utc)
    members = members.copy()
    # The retained member CSV uses pandas' space-separated UTC display format.
    # Normalize that separator in memory; keep the accepted CSV bytes unchanged.
    members["time"] = utc_times(members.detection_timestamp_utc.str.replace(" ", "T", n=1))
    require(
        members.time.notna().all() and members.time.dt.year.between(2018, 2023).all(),
        "Training case members",
    )
    require(
        not members.duplicated(["scenario", "cluster_id", "detection_id"]).any(),
        "Unique case-member keys",
    )
    groups = members.groupby(["scenario", "cluster_id"])
    require(
        set(groups.groups) == set(zip(cases.scenario, cases.cluster_id, strict=True)),
        "Exact case-member group coverage",
    )
    records = []
    for i, case in cases.iterrows():
        group = groups.get_group((case.scenario, case.cluster_id))
        first = pd.Timestamp(case.first_detection_utc)
        ids = json.loads(case.earliest_grid_ids_json)
        actual = sorted(group.loc[group.time.eq(group.time.min()), "grid_id"].unique())
        require(
            isinstance(ids, list)
            and ids == actual
            and len(group) == case.detection_count
            and group.time.min() == first,
            "All first cells match retained member evidence",
        )
        start = windows.loc[i, "prediction_timestamp_utc"]
        require(
            pd.Timestamp(case.candidate_prediction_timestamp_utc) == start,
            "Candidate prediction window matches right-inclusive midnight rule",
        )
        for grid_id in ids:
            for role, day in (
                ("first_detection_nominal_day", first.normalize()),
                ("candidate_prediction_day", start),
            ):
                records.append(
                    {
                        "review_unit_id": f"event:{case.scenario}:{case.cluster_id}",
                        "scenario": case.scenario,
                        "cluster_id": case.cluster_id,
                        "grid_id": grid_id,
                        "first_detection_utc": first.isoformat(),
                        "candidate_prediction_timestamp_utc": start.isoformat(),
                        "observation_lookup_timestamp_utc": day.isoformat(),
                        "lookup_role": role,
                        "lookup_in_training_calendar": 2018 <= day.year <= 2023,
                        "training_window_boundary_review": bool(
                            windows.loc[i, "training_window_boundary_review"]
                        ),
                    }
                )
    return pd.DataFrame(records)


def attach_events(requests, observations):
    require(not observations.duplicated(KEYS).any(), "Unique lookup observations")
    lookup = observations.rename(
        columns={"prediction_timestamp_utc": "observation_lookup_timestamp_utc"}
    )
    linked = requests.merge(
        lookup,
        on=["grid_id", "observation_lookup_timestamp_utc"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    require(
        linked._merge.eq("both").eq(linked.lookup_in_training_calendar).all(),
        "Every training lookup matched; out-of-calendar lookup remains explicit",
    )
    linked["lookup_status"] = np.where(
        linked._merge.eq("both"), "matched_nominal_day_diagnostics", "outside_training_calendar"
    )
    linked["exact_target_window_coverage_proven"] = False
    linked["target"] = pd.NA
    return linked.drop(columns="_merge")


def blank_reviews(unit_ids, kind):
    require(len(unit_ids) == len(set(unit_ids)), "Unique human review units")
    result = pd.DataFrame(
        {"review_unit_id": list(unit_ids), "review_kind": kind, "review_status": "not_reviewed"}
    )
    for field in REVIEW_FIELDS:
        result[field] = pd.NA
    return result
