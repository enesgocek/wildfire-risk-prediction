"""Cross-scenario review evidence for the fixed pilot; never assigns binary targets."""

import json

import pandas as pd

from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_review import audit_sample
from wildfire_risk_prediction.target_admission import review_catalog

SCENARIOS = tuple(f"d{d}m_t{t}h" for d in (500, 1000, 2000) for t in (24, 48, 72))
FLAGS = [
    "temporal_chain_review",
    "spatial_chain_review",
    "multi_grid_first_detection_review",
    "calendar_year_crossing_review",
    "period_start_context_missing",
    "period_end_context_missing",
    "training_window_boundary_review",
]
VERSION = "label_protocol_review_v1"


def compare_catalogs(sample, catalogs, grid_ids):
    """Match all tied first cells, distinguish presence agreement from membership agreement."""
    audit_sample(sample)
    require(
        sample.window_daily_observation_status.eq("unknown").all()
        and not sample.window_negative_label_permitted.any()
        and not sample.window_positive_label_permitted.any(),
        "Closed window label gates",
    )
    require(set(catalogs) == set(SCENARIOS), "All nine catalog scenarios required")
    ids = set(grid_ids)
    require(set(sample.grid_id) <= ids, "Known pilot grid")
    key_times = utc_times(sample.prediction_timestamp_utc).map(pd.Timestamp.isoformat)
    long_rows, global_rows = [], []
    for scenario in SCENARIOS:
        catalog = catalogs[scenario]
        validated, _ = review_catalog(catalog)
        stamps = utc_times(catalog.candidate_prediction_timestamp_utc).map(pd.Timestamp.isoformat)
        by_key = {}
        for index, row in catalog.iterrows():
            cells = json.loads(row.earliest_grid_ids_json)
            require(set(cells) <= ids, "Known first-cell grid")
            flags = [flag for flag in FLAGS if bool(validated.loc[index, flag])]
            entry = {
                "cluster_id": row.cluster_id,
                "membership_sha256": row.membership_sha256,
                "flags": flags,
            }
            stamp = stamps.loc[index]
            for cell in cells:
                by_key.setdefault((cell, stamp), []).append(entry)
        global_rows.append(
            {
                "scenario": scenario,
                "exploratory_clusters": len(catalog),
                "candidate_first_cell_window_keys": len(by_key),
                "multi_first_cell_clusters": int(catalog.earliest_grid_count.gt(1).sum()),
                "clusters_with_review_flags": int(validated[FLAGS].any(axis=1).sum()),
                "scenario_selected": False,
            }
        )
        for row, stamp in zip(sample.itertuples(), key_times, strict=True):
            matches = by_key.get((row.grid_id, stamp), [])
            flags = sorted({flag for item in matches for flag in item["flags"]})
            long_rows.append(
                {
                    "review_unit_id": row.review_unit_id,
                    "grid_id": row.grid_id,
                    "prediction_timestamp_utc": row.prediction_timestamp_utc,
                    "scenario": scenario,
                    "candidate_cluster_first_cell_matches": len(matches),
                    "matched_cluster_ids_json": json.dumps(
                        sorted(x["cluster_id"] for x in matches)
                    ),
                    "matched_membership_set_json": json.dumps(
                        sorted(x["membership_sha256"] for x in matches)
                    ),
                    "review_flags_json": json.dumps(flags),
                }
            )
    long = pd.DataFrame(long_rows)
    rows = []
    for row in sample.itertuples():
        group = long.loc[long.review_unit_id.eq(row.review_unit_id)]
        present = group.candidate_cluster_first_cell_matches.gt(0)
        variants = group.matched_membership_set_json.nunique()
        if not present.any():
            state = "no_candidate_in_any_scenario"
        elif not present.all():
            state = "candidate_in_some_scenarios"
        elif variants > 1:
            state = "all_scenarios_match_memberships_differ"
        else:
            state = "all_scenarios_match_memberships_equal"
        flags = sorted({f for value in group.review_flags_json for f in json.loads(value)})
        if not row.water_scope_included:
            route = "outside_water_scope_audit_only"
        elif row.window_incomplete_packet_set:
            route = "source_packet_review"
        elif row.window_boundary_scan_present:
            route = "boundary_time_review"
        elif state in ("candidate_in_some_scenarios", "all_scenarios_match_memberships_differ"):
            route = "event_scenario_disagreement_review"
        elif present.any():
            route = "catalog_first_candidate_review"
        elif row.window_loaded_definite_thermal_present:
            route = "thermal_without_catalog_first_candidate_review"
        elif row.window_loaded_nominal_land_center_definite_count == 0:
            route = "no_nominal_land_center_review"
        else:
            route = "background_observation_review"
        rows.append(
            {
                "review_unit_id": row.review_unit_id,
                "catalog_match_state": state,
                "scenarios_with_candidate": int(present.sum()),
                "candidate_match_count_min": int(group.candidate_cluster_first_cell_matches.min()),
                "candidate_match_count_max": int(group.candidate_cluster_first_cell_matches.max()),
                "matched_membership_set_variants": variants,
                "catalog_review_flags_json": json.dumps(flags),
                "proposed_review_route": route,
                "route_is_label_admission": False,
                "protocol_status": "draft_unaccepted",
                "protocol_review_version": VERSION,
            }
        )
    output = sample.merge(
        pd.DataFrame(rows), on="review_unit_id", validate="one_to_one", sort=False
    )
    pd.testing.assert_frame_equal(output[sample.columns], sample.reset_index(drop=True))
    require(
        output.target.isna().all() and output.window_target.isna().all(), "Targets stay unassigned"
    )
    return output, long, pd.DataFrame(global_rows)
