"""Prepare separate conditional source proposals; never mutate the accepted S/U package."""

import csv
import json
import socket
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from prepare_satellite_pu_cover import (
    CGLS,
    CGLS_SHA,
    CORINE,
    CORINE_SHA,
    LEGEND,
    LEGEND_SHA,
    context,
    sample_centers,
)
from pyproj import Geod, network

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POINTS = BASE / "mesogeos_reference_pilot_run_v1/20261124T231948Z_e9a7e57e"
AUDIT = BASE / "mesogeos_reference_pilot_audit_v1/20261124T233152Z_7d080df8"
COVER = BASE / "satellite_PU_cover_v1/20261120T003942Z_3f82694d"
CELLS = BASE / "cell_cover_scope_v1/20261119T002103Z_099cd518"
OLD = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
DECISION = ROOT / "configs/mesogeos_candidate_review_v1.json"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def table(path, records):
    fields = list(dict.fromkeys(k for row in records for k in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def history_counts(frame, timestamp, longitude, latitude):
    """Nearby earlier observations are context, not a proof of same physical event."""
    delta = (frame.timestamp - timestamp).dt.total_seconds().to_numpy() / 3600
    keep = (delta >= -72) & (delta <= 24)
    near = frame.loc[keep]
    dt = delta[keep]
    _, _, distances = Geod(ellps="WGS84").inv(
        np.full(len(near), longitude),
        np.full(len(near), latitude),
        near.longitude.to_numpy(float),
        near.latitude.to_numpy(float),
    )
    result = []
    for radius in (500, 1000, 2000):
        within = np.asarray(distances) <= radius
        for gap in (24, 48, 72):
            result.append(
                {
                    "distance_m": radius,
                    "history_hours": gap,
                    "earlier_VIIRS_centers": int(np.sum(within & (dt >= -gap) & (dt < 0))),
                    "simultaneous_VIIRS_centers": int(np.sum(within & (dt == 0))),
                    "later_24h_VIIRS_centers": int(np.sum(within & (dt > 0) & (dt <= 24))),
                }
            )
    return result


def deny_network(*args, **kwargs):
    raise RuntimeError("Offline context review")


def main():
    pins = {}

    def pin(path, expected=None):
        value = digest(path)
        require(expected is None or value == expected, "Frozen input hash")
        pins[path] = value
        return path

    decision = json.loads(pin(DECISION).read_bytes())
    require(
        decision["selected_direction"]
        == "A_prepare_separate_noisy_S_proposals_after_context_checks",
        "Researcher decision",
    )
    audit = json.loads(
        pin(AUDIT / "readback.json", decision["reference_audit_sha256"]).read_bytes()
    )
    pin(POINTS / "readback.json", audit["first_stage_receipt_sha256"])
    for name, expected in audit["artifact_sha256"].items():
        pin(AUDIT / name, expected)
    first = json.loads((POINTS / "readback.json").read_bytes())
    pin(POINTS / "point_context_review.csv", first["artifact_sha256"]["point_context_review.csv"])
    for folder, expected in (
        (COVER, "ae771636b7c230afe7b9603b00f266eab3a3a3fa408a56f9b765a27f6da34900"),
        (CELLS, "1831e4d0f67789883d9d98f636c6df23194609dbf53a3f74b127ab8c68993f59"),
        (OLD, "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366"),
    ):
        receipt = json.loads(pin(folder / "readback.json", expected).read_bytes())
        names = {
            COVER: "historical_center_context.csv",
            CELLS: "cell_map_comparison.csv",
            OLD: "inspection_memberships.csv",
        }
        name = names[folder]
        pin(folder / name, receipt["artifact_sha256"][name])
    pin(CGLS, CGLS_SHA)
    pin(CORINE, CORINE_SHA)
    pin(LEGEND, LEGEND_SHA)
    for path in (
        Path(__file__),
        Path(__file__).with_name("prepare_satellite_pu_cover.py"),
        ROOT / "src/wildfire_risk_prediction/target_admission.py",
        ROOT / "src/wildfire_risk_prediction/landscape.py",
    ):
        pin(path)
    socket.create_connection = deny_network
    network.set_network_enabled(False)
    links = [
        r
        for r in rows(AUDIT / "native_date_context_lookup.csv")
        if r["calendar_lookup_only"] != "existing_S_context"
    ]
    require(len(links) == decision["review_cases"] == 32, "Exact newly approved review subset")
    points = {r["source_record_index"]: r for r in rows(POINTS / "point_context_review.csv")}
    selected = [points[r["source_record_index"]] for r in links]
    require(
        all(r["YEAR"] in {"2018", "2019", "2020", "2021", "2022"} for r in selected),
        "Open years only",
    )
    cells = {r["grid_id"]: r for r in rows(CELLS / "cell_map_comparison.csv")}
    frame = pd.read_csv(COVER / "historical_center_context.csv")
    frame["timestamp"] = pd.to_datetime(frame.detection_timestamp_utc, utc=True)
    require(
        len(frame) == 28396 and frame.timestamp.dt.year.between(2018, 2022).all(),
        "Frozen fit-only VIIRS inventory",
    )
    legend = json.loads(LEGEND.read_bytes())["legend"]
    lon = np.array([float(r["native_point_lon"]) for r in selected])
    lat = np.array([float(r["native_point_lat"]) for r in selected])
    maps = {
        "cgls2017": sample_centers(CGLS, lon, lat),
        "corine2018": sample_centers(CORINE, lon, lat, legend=legend),
    }
    cases, scenarios = [], []
    for i, (point, link) in enumerate(zip(selected, links, strict=True)):
        grid = link["grid_candidate"]
        cell = cells.get(grid)
        source_time = pd.Timestamp(point["acquisition_utc_candidate_if_FIRMS_fields_preserved"])
        candidate = {
            "source_record_index": point["source_record_index"],
            "source_id": point["id"],
            "native_year": point["YEAR"],
            "native_date": point["IGNITION_D"],
            "source_province": point["PROVINCE"],
            "grid_candidate": grid,
            "previous_lookup_context": link["calendar_lookup_only"],
            "conditional_acquisition_utc": source_time.isoformat(),
            "cell_present_in_AOI": cell is not None,
            "water_scope_included": cell is not None and cell["water_scope_included"] == "True",
            "cell_2017_forest_fraction": float(cell["forest_fraction"]) if cell else None,
            "cell_2017_shrub_fraction": float(cell["shrub_fraction"]) if cell else None,
            "cell_2018_woody_fraction_of_AOI": float(cell["clc_woody_fraction_of_aoi"])
            if cell
            else None,
            "clock_semantics_accepted": False,
            "new_event_verified": False,
            "event_date_cover_verified": False,
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "existing_SU_modified": False,
        }
        for key, scheme in (("cgls2017", "CGLS2017"), ("corine2018", "CORINE2018")):
            sample = maps[key][i]
            candidate.update({key + "_" + k: v for k, v in sample.items()})
            candidate[key + "_point_context"] = context(sample["class_code"], scheme)
        dates = []
        for clock, shift in (
            ("preserved_MODIS_UTC_if_lineage_correct", 0),
            ("minus_3h_stress_only_not_claimed_local_time", 3),
        ):
            stamp = source_time - pd.Timedelta(hours=shift)
            window = detection_windows(pd.Series([stamp.isoformat()])).iloc[0]
            prediction = window.prediction_timestamp_utc
            dates.append(prediction.isoformat())
            window_allowed = prediction.year in range(
                2018, 2023
            ) and window.target_end_inclusive_utc < pd.Timestamp("2023-01-01", tz="UTC")
            for item in history_counts(frame, stamp, lon[i], lat[i]):
                item.update(
                    {
                        "source_id": point["id"],
                        "source_record_index": point["source_record_index"],
                        "clock_assumption": clock,
                        "conditional_prediction_timestamp_utc": prediction.isoformat(),
                        "window_in_fit_review_period": window_allowed,
                        "lookback_source_period_complete": stamp
                        - pd.Timedelta(hours=item["history_hours"])
                        >= pd.Timestamp("2018-01-01", tz="UTC"),
                        "no_earlier_VIIRS_center_is_observed_absence": False,
                        "conditional_S_proposal_only": bool(
                            window_allowed
                            and candidate["water_scope_included"]
                            and candidate["cgls2017_point_context"] == "forest_shrub"
                            and item["earlier_VIIRS_centers"] == 0
                            and stamp - pd.Timedelta(hours=item["history_hours"])
                            >= pd.Timestamp("2018-01-01", tz="UTC")
                        ),
                        "proposal_assumptions": (
                            "source_clock_preserved;historical_center_proxy;"
                            "no_observed_prior_is_only_a_noisy_newness_proxy"
                        ),
                        "accepted_S_assignment": False,
                        "target": None,
                        "accepted_L_membership": None,
                        "negative_label_permitted": False,
                    }
                )
                scenarios.append(item)
        candidate["conditional_target_day_stable_under_3h_stress"] = len(set(dates)) == 1
        cases.append(candidate)
    require(
        len(cases) == 32 and len(scenarios) == 576,
        "All cases and both clocks/nine scenarios retained",
    )
    out = (
        BASE
        / "mesogeos_candidate_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    table(out / "case_context.csv", cases)
    table(out / "conditional_S_proposals.csv", scenarios)
    # Re-open saved tables rather than using only the in-memory producer counts.
    saved, saved_scenarios = (
        rows(out / "case_context.csv"),
        rows(out / "conditional_S_proposals.csv"),
    )
    require(len({r["source_record_index"] for r in saved}) == 32, "Unique persisted source cases")
    require(
        all(
            not r["target"]
            and not r["accepted_L_membership"]
            and r["negative_label_permitted"] == "False"
            for r in saved_scenarios
        ),
        "No accepted labels",
    )
    summary = []
    for clock in decision["clock_sensitivity"]:
        for radius in decision["distance_sensitivity_m"]:
            for gap in decision["history_sensitivity_hours"]:
                part = [
                    r
                    for r in saved_scenarios
                    if r["clock_assumption"] == clock
                    and int(r["distance_m"]) == radius
                    and int(r["history_hours"]) == gap
                ]
                require(len(part) == 32, "Every source case in every assumption")
                summary.append(
                    {
                        "clock": clock,
                        "distance_m": radius,
                        "history_hours": gap,
                        "conditional_proposals": sum(
                            r["conditional_S_proposal_only"] == "True" for r in part
                        ),
                        "with_earlier_VIIRS_context": sum(
                            int(r["earlier_VIIRS_centers"]) > 0 for r in part
                        ),
                        "with_later_24h_VIIRS_context": sum(
                            int(r["later_24h_VIIRS_centers"]) > 0 for r in part
                        ),
                    }
                )
    require(
        all(digest(p) == h for p, h in pins.items()), "Input closure including unchanged old S/U"
    )
    result = {
        "status": "32_case_conditional_proposals_prepared_not_membership_acceptance",
        "analysis_date": "2026-11-25",
        "case_count": len(saved),
        "scenario_rows": len(saved_scenarios),
        "source_year_counts": dict(Counter(r["native_year"] for r in saved)),
        "source_province_counts": dict(Counter(r["source_province"] for r in saved)),
        "cgls2017_point_context_counts": dict(Counter(r["cgls2017_point_context"] for r in saved)),
        "corine2018_point_context_counts": dict(
            Counter(r["corine2018_point_context"] for r in saved)
        ),
        "two_map_woody_rows": sum(
            r["cgls2017_point_context"] == r["corine2018_point_context"] == "forest_shrub"
            for r in saved
        ),
        "conditional_day_stable_rows": sum(
            r["conditional_target_day_stable_under_3h_stress"] == "True" for r in saved
        ),
        "water_scope_rows": sum(r["water_scope_included"] == "True" for r in saved),
        "scenario_summary": summary,
        "new_S_assignments_or_Y_or_L": False,
        "new_models": False,
        "final_merge": False,
        "scientific_values_2023_to_2025_opened": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(out.relative_to(ROOT).as_posix())
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"input_sha256", "artifact_sha256", "scenario_summary"}
            },
            ensure_ascii=False,
        )
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
