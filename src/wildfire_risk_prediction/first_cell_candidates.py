"""Keep every recorded earliest cell under an exploratory component, never a fire ID."""

import json

import pandas as pd

from wildfire_risk_prediction.feature_join import require


def candidate_cells(components, policy):
    """Expand first-cell sets without selecting a grouping or admitting targets.

    Scenario-qualified component IDs are local review keys. They cannot justify
    complete event membership for fold admission or physical event counts.
    """
    require(
        policy["version"] == "first_cell_candidates_v1"
        and policy["method"] == "all_recorded_earliest_cells"
        and policy["candidate_identity"] == "existing_scenario_component_id"
        and policy["grouping_scenario_selected"] is None
        and policy["daily_observation_status"] == "unknown"
        and all(
            policy[name] is False
            for name in (
                "independent_event_identity_accepted",
                "positive_label_permitted",
                "negative_label_permitted",
                "final_merge_authorized",
            )
        ),
        "Candidate-only policy; all scientific admission gates remain closed",
    )
    require(
        len(components) > 0
        and components.cluster_id.notna().all()
        and components.cluster_id.is_unique
        and components.target.isna().all(),
        "Unique unlabelled components",
    )
    rows = []
    for component in components.sort_values("cluster_id").itertuples():
        require(
            isinstance(component.scenario, str)
            and component.scenario
            and component.cluster_id.startswith(component.scenario + "_"),
            "Scenario-qualified component key",
        )
        first = pd.Timestamp(component.first_detection_utc)
        require(
            not pd.isna(first)
            and first.tzinfo is not None
            and first.utcoffset().total_seconds() == 0
            and 2018 <= first.year <= 2023,
            "Training UTC first time",
        )
        cells = json.loads(component.earliest_grid_ids_json)
        require(
            isinstance(cells, list)
            and len(cells) > 0
            and all(isinstance(cell, str) and cell for cell in cells)
            and len(set(cells)) == len(cells) == component.earliest_grid_count,
            "Exact distinct recorded first-cell set",
        )
        for cell in sorted(cells):
            rows.append(
                {
                    "scenario": component.scenario,
                    "candidate_component_id": component.cluster_id,
                    "grid_id": cell,
                    "first_detection_utc": first.isoformat(),
                    "first_cell_count": len(cells),
                    "policy_version": policy["version"],
                    "event_identity_accepted": False,
                    "event_membership_complete": False,
                    "target": None,
                }
            )
    return pd.DataFrame(rows)
