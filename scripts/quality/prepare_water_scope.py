"""Offline mapped-water scope and training-only impact readback."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.water_scope import (
    attach_water_scope,
    build_water_scope,
    retain_water_scope,
)

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = "outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2"
PILOT = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed/review.json"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline water scope preparation")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular scope input")
        digest = sha(path)
        require(expected is None or digest == expected, "Scope input hash changed")
        pins[name] = digest
        return path

    def read_report(name, expected):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    policy = json.loads(retained("configs/water_scope_v1.json").read_text(encoding="utf-8"))
    static = pd.read_csv(
        retained(
            "data/interim/landscape/v1/grid_static.csv",
            "bd9b2a27e6234d97e41df11dac59fb7bc82242ef282ff60ac75d83cbc3fb0f82",
        ),
        float_precision="round_trip",
    )
    retained(
        "data/interim/landscape/v1/manifest.json",
        "8fad7a76759baeebe0342dbe67343f7f02be4d86af64dece22956939c2c2e1bb",
    )
    support_report = read_report(
        SUPPORT + "/readback.json",
        "ad0567e829719d4b2b45cb7b696ce4442c8fc083268a670c4696b1bd642aa5a9",
    )
    support = pd.read_csv(
        retained(
            SUPPORT + "/support_cells.csv", support_report["artifact_sha256"]["support_cells.csv"]
        ),
        float_precision="round_trip",
    )
    scope = build_water_scope(static, support.grid_id, policy)
    scope = scope.merge(
        support[["grid_id", "weather_support_group", "water_only_flag"]],
        on="grid_id",
        validate="one_to_one",
    )
    scope["previous_water_only_flag_agrees"] = scope.water_only_flag.eq(~scope.water_scope_included)
    scope = scope.drop(columns="water_only_flag")
    pilot_report = read_report(
        PILOT + "/readback.json",
        "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037",
    )
    # Preserve all original pilot forms and observations, not just the selected rows.
    pilot_files = {
        name: retained(PILOT + "/" + name, digest)
        for name, digest in pilot_report["artifact_sha256"].items()
    }
    pilot = pd.read_csv(pilot_files["random_grid_days.csv"], float_precision="round_trip")
    require(len(pilot) == 400 and pilot.target.isna().all(), "Unlabelled pilot")
    dates = pd.to_datetime(pilot.prediction_timestamp_utc, utc=True, errors="raise")
    require(dates.dt.year.between(2018, 2023).all(), "Training pilot only")
    annotated = attach_water_scope(pilot, scope)
    selected = retain_water_scope(pilot, scope)
    pd.testing.assert_frame_equal(annotated[pilot.columns], pilot)
    pd.testing.assert_frame_equal(
        selected[pilot.columns], pilot.loc[annotated.water_scope_included]
    )

    graph = read_report(GRAPH, "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e")
    # A single assignment inventory supplies detection keys, not an accepted graph rule.
    assignments = pd.read_csv(
        retained(
            "data/interim/event_grouping/d500m_t24h_assignments.csv",
            graph["artifact_sha256"]["d500m_t24h"]["assignments_sha256"],
        )
    ).drop(columns="cluster_id")
    times = pd.to_datetime(assignments.timestamp, utc=True, errors="raise")
    require(
        len(assignments) == 30295
        and assignments.detection_id.is_unique
        and times.dt.year.between(2018, 2023).all(),
        "Unique training detection inventory",
    )
    inventory = attach_water_scope(assignments, scope)
    excluded_detections = inventory.loc[~inventory.water_scope_included]

    for name in (
        "src/wildfire_risk_prediction/water_scope.py",
        "src/wildfire_risk_prediction/landscape.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "scripts/quality/prepare_water_scope.py",
        PROTECTED,
    ):
        retained(name)
    protected = json.loads((ROOT / PROTECTED).read_text(encoding="utf-8"))
    for name, digest in protected.items():
        retained(name, digest)

    numerical = pd.DataFrame(
        [
            {
                "diagnostic_water_isclose_atol": tolerance,
                "cells_flagged": int(
                    np.isclose(scope.water_fraction, 1, atol=tolerance, rtol=0).sum()
                ),
                "extra_cells_vs_applied_rule": int(
                    (
                        np.isclose(scope.water_fraction, 1, atol=tolerance, rtol=0)
                        & scope.water_scope_included
                    ).sum()
                ),
                "selected": False,
            }
            for tolerance in (0, 1e-12, 1e-9, 1e-6)
        ]
    )
    # Context for a later decision only; no vegetation threshold is applied.
    sensitivity = []
    for threshold in (0.01, 0.10, 0.25, 0.50, 0.75):
        for group in ("retained_mixed", "retained_no_water"):
            group_mask = scope.water_scope_reason.eq(group)
            above = group_mask & scope.forest_shrub_fraction.ge(threshold)
            sensitivity.append(
                {
                    "group": group,
                    "exploratory_forest_shrub_fraction_at_least": threshold,
                    "group_cells": int(group_mask.sum()),
                    "cells_at_or_above": int(above.sum()),
                    "cells_below": int((group_mask & ~above).sum()),
                    "selected": False,
                }
            )
    training_days = len(pd.date_range("2018-01-01", "2023-12-31", freq="D"))
    excluded = ~scope.water_scope_included
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/water_scope_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("grid_water_scope.csv", scope),
        ("pilot_water_scope.csv", annotated),
        ("excluded_training_detections.csv", excluded_detections),
        ("numerical_water_diagnostics.csv", numerical),
        ("mixed_scope_sensitivity.csv", pd.DataFrame(sensitivity)),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        reread = pd.read_csv(path, float_precision="round_trip")
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), reread, check_dtype=False)
        artifacts[name] = sha(path)
    result = {
        "status": "researcher_water_scope_applied_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "policy": policy,
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "cells_total": len(scope),
        "cells_excluded_map_water": int(excluded.sum()),
        "cells_retained_for_further_eligibility_review": int((~excluded).sum()),
        "cell_groups": scope.water_scope_reason.value_counts().to_dict(),
        "excluded_aoi_area_km2": float(scope.loc[excluded, "aoi_area_m2"].sum() / 1e6),
        "excluded_raster_covered_area_km2": float(scope.loc[excluded, "covered_area_km2"].sum()),
        "previous_water_flag_agreement": bool(scope.previous_water_only_flag_agrees.all()),
        "training_days": training_days,
        "training_grid_days_before": len(scope) * training_days,
        "training_grid_days_excluded_by_scope": int(excluded.sum()) * training_days,
        "training_grid_days_retained_by_scope": int((~excluded).sum()) * training_days,
        "pilot_rows_before": len(pilot),
        "pilot_rows_retained": len(selected),
        "training_candidate_detections_reviewed": len(inventory),
        "training_candidate_detections_in_excluded_cells": len(excluded_detections),
        "protected_inputs_verified": len(protected),
        "source_rows_deleted": 0,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "mixed_cell_threshold_selected": None,
        "event_scenario_selected": None,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "2017 discrete map water is not independently verified historical water truth",
            "Retained means passing only the water rule, not accepted habitat or label evidence",
            "Grid-day impact is the full 2191-day Cartesian domain, not eligible labelled rows",
            "Thermal candidate detections are not independent fires or accepted positive labels",
            "Pilot is annotated without resampling; original inclusion weights are unchanged",
            "Full feature/observation artifacts unchanged; downstream consumers must apply scope",
        ],
    }
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Scope report readback")
    require(
        all(sha(out / name) == digest for name, digest in artifacts.items()), "Artifact closure"
    )
    closure = {
        "status": "passed",
        "report_sha256": sha(path),
        "input_files_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    (out / "completion_readback.json").write_text(
        json.dumps(closure, indent=2) + "\n", encoding="utf-8"
    )
    print("Water scope result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
