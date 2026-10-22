"""Audit the 21 linked candidates' cover and retained public-reference context."""

import csv
import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import rasterio

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.point_cover_context import sample_centers

ROOT = Path(__file__).resolve().parents[2]
LINK = "outputs/reports/dataset/event_observation_link_v1/20261022T205236Z_797195a6"
EVENT = "outputs/reports/dataset/full_event_sensitivity_v1/20261022T204358Z_820d043d"
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
HABITAT = "outputs/reports/habitat/review_v1/20261009T235212Z_3c2c021b"
REFERENCE = "outputs/reports/dataset/independent_reference_plan_v1/20261015T145033Z_81f53320"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline case context; web research recorded separately")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    pins = {}

    def retain(name, expected=None):
        p = ROOT / name
        require(
            p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT), "Local input"
        )
        actual = sha(p)
        require(expected is None or actual == expected, "Input pin")
        pins[name] = actual
        return p

    def report(folder, expected):
        return json.loads(retain(folder + "/readback.json", expected).read_text())

    link = report(LINK, "9b4be7d301436840819d3a9d90ece3a5ede5f6bd257c364ef7d5cc9cc08cf6bf")
    event = report(EVENT, "40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86")
    graph = json.loads(
        retain(
            GRAPH + "/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    cases = pd.read_csv(
        retain(
            LINK + "/pilot_evidence_links.csv", link["artifact_sha256"]["pilot_evidence_links.csv"]
        ),
        float_precision="round_trip",
    )
    cases = cases.loc[cases.first_candidate_present_in_catalog_union].copy()
    require(len(cases) == 21 and cases.target.isna().all(), "Fixed unlabelled linked cases")
    habitat = pd.read_csv(
        retain(
            HABITAT + "/cells.csv",
            "76ab3a1dc632be7764548699342aaa3d933166e4d0ccb0d51ad3ea2df92ba14a",
        ),
        float_precision="round_trip",
    )
    require(habitat.grid_id.is_unique and habitat.reference_year.eq(2017).all(), "2017 cell map")
    hfields = [
        "grid_id",
        "reference_year",
        "forest_fraction",
        "shrub_fraction",
        "herbaceous_fraction",
        "agriculture_fraction",
        "urban_fraction",
        "water_fraction",
        "covered_area_km2",
        "aoi_area_km2",
        "habitat_eligibility",
    ]
    cases = cases.merge(habitat[hfields], on="grid_id", validate="many_to_one", how="left")
    require(
        cases.reference_year.notna().all() and cases.habitat_eligibility.eq("undecided").all(),
        "Cover context available, habitat not admitted",
    )
    detail = pd.read_csv(
        retain(
            EVENT + "/component_cell_evidence.csv",
            event["artifact_sha256"]["component_cell_evidence.csv"],
        )
    )
    detail = detail.merge(
        cases[["grid_id", "prediction_timestamp_utc"]],
        on=["grid_id", "prediction_timestamp_utc"],
        validate="many_to_one",
    )
    occurrences = []
    for scenario, group in detail.groupby("scenario"):
        assignments = pd.read_csv(
            retain(
                f"data/interim/event_grouping/{scenario}_assignments.csv",
                graph["artifact_sha256"][scenario]["assignments_sha256"],
            )
        )
        assignments["first_detection_utc"] = pd.to_datetime(
            assignments.timestamp, utc=True, format="ISO8601"
        ).map(pd.Timestamp.isoformat)
        selected = group[
            ["candidate_component_id", "grid_id", "first_detection_utc", "prediction_timestamp_utc"]
        ].rename(columns={"candidate_component_id": "cluster_id"})
        joined = selected.merge(
            assignments,
            on=["cluster_id", "grid_id", "first_detection_utc"],
            how="left",
            validate="one_to_many",
            indicator=True,
        )
        require(joined["_merge"].eq("both").all(), "Every first-cell time has source witnesses")
        joined["scenario"] = scenario
        occurrences.append(joined.drop(columns="_merge"))
    witnesses = pd.concat(occurrences, ignore_index=True)
    ids = set(witnesses.detection_id)
    source = retain("data/interim/firms_combined_candidates_2018_2024.csv", graph["source_sha256"])
    selected_rows = []
    skipped_validation = 0
    with source.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            year = row["detection_timestamp_utc"][:4]
            require(year in {str(y) for y in range(2018, 2025)}, "Source period")
            if year == "2024":
                skipped_validation += 1
                continue
            if row["detection_id"] in ids:
                selected_rows.append(
                    {
                        k: row[k]
                        for k in (
                            "detection_id",
                            "grid_id",
                            "detection_timestamp_utc",
                            "longitude",
                            "latitude",
                        )
                    }
                )
    points = pd.DataFrame(selected_rows)
    require(
        set(points.detection_id) == ids and points.detection_id.is_unique, "Exact source points"
    )
    points["longitude"] = points.longitude.astype(float)
    points["latitude"] = points.latitude.astype(float)
    points["source_time"] = pd.to_datetime(
        points.detection_timestamp_utc, utc=True, format="ISO8601"
    ).map(pd.Timestamp.isoformat)
    identity = witnesses.merge(
        points[["detection_id", "grid_id", "source_time"]],
        on=["detection_id", "grid_id"],
        validate="many_to_one",
    )
    require(identity.first_detection_utc.eq(identity.source_time).all(), "Source time match")
    raster = retain(
        "data/raw/landcover/landcover_copernicus_2017.tif",
        "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    )
    with rasterio.open(raster) as dataset:
        sampled = sample_centers(points, dataset)
        raster_info = {
            "crs": dataset.crs.to_string(),
            "resolution": list(dataset.res),
            "nodata": dataset.nodata,
            "band_count": dataset.count,
        }
        # A separate direct pixel read verifies sample values at saved row/column positions.
        for row in sampled.itertuples():
            if pd.notna(row.reference_map_row):
                value = dataset.read(
                    1,
                    window=(
                        (int(row.reference_map_row), int(row.reference_map_row) + 1),
                        (int(row.reference_map_column), int(row.reference_map_column) + 1),
                    ),
                    masked=True,
                )[0, 0]
                require(int(value) == row.center_cover_code_2017, "Independent pixel read")
    case_points = witnesses.merge(sampled, on=["detection_id", "grid_id"], validate="many_to_one")
    unique_case_points = case_points.drop_duplicates(
        ["grid_id", "prediction_timestamp_utc", "detection_id"]
    )
    context = (
        unique_case_points.groupby(["grid_id", "prediction_timestamp_utc"])
        .agg(
            unique_first_detection_points=("detection_id", "size"),
            first_point_cover_groups_json=(
                "center_cover_group_2017",
                lambda x: json.dumps(sorted(set(x))),
            ),
        )
        .reset_index()
    )
    cases = cases.merge(context, on=["grid_id", "prediction_timestamp_utc"], validate="one_to_one")
    reference = report(
        REFERENCE, "20e6d42f35c4c7310ef34f980dcb80de589fcc73b839d4daa93cb7185ce40e06"
    )
    records = pd.read_csv(
        retain(
            REFERENCE + "/institutional_context_records.csv",
            reference["artifact_sha256"]["institutional_context_records.csv"],
        ),
        dtype=str,
    )
    cases["retained_context_same_reported_date_count"] = (
        cases.target_day.map(records.reported_date.value_counts()).fillna(0).astype(int)
    )
    cases["independent_event_identity_proven"] = False
    cases["habitat_eligibility_accepted"] = False
    sources = retain("docs/research/candidate_context_sources_2026-10-23.json")
    source_review = json.loads(sources.read_text(encoding="utf-8"))
    require(source_review["accepted_incident_matches"] == 0, "No invented web matches")
    for name in (
        "scripts/quality/review_linked_candidate_context.py",
        "src/wildfire_risk_prediction/point_cover_context.py",
        "src/wildfire_risk_prediction/landscape.py",
        "src/wildfire_risk_prediction/target_admission.py",
    ):
        retain(name)
    out = (
        ROOT
        / "outputs/reports/dataset/linked_candidate_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("case_cover_reference_context.csv", cases),
        ("first_point_cover.csv", sampled),
        ("scenario_first_point_witnesses.csv", case_points),
    ):
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            pd.read_csv(path, float_precision="round_trip"),
            check_dtype=False,
        )
        artifacts[name] = sha(path)
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, "Inputs unchanged")
    path = out / "input_manifest.json"
    path.write_text(json.dumps(pins, indent=2) + "\n")
    artifacts[path.name] = sha(path)
    result = {
        "version": "linked_candidate_context_v1",
        "client_date": "2026-10-23",
        "status": "cover_and_reference_context_only_not_forest_fire_acceptance",
        "cases": len(cases),
        "case_scenario_components": len(detail),
        "scenario_point_witnesses": len(witnesses),
        "unique_source_points": len(sampled),
        "point_reference_cover_counts": {
            str(k): int(v) for k, v in sampled.center_cover_group_2017.value_counts().items()
        },
        "case_reference_cover_sets": {
            str(k): int(v) for k, v in cases.first_point_cover_groups_json.value_counts().items()
        },
        "retained_context_records": len(records),
        "cases_sharing_retained_context_reported_date": int(
            cases.retained_context_same_reported_date_count.gt(0).sum()
        ),
        "accepted_independent_incident_matches": 0,
        "raster": raster_info,
        "reference_year": 2017,
        "validation_rows_date_filtered": skipped_validation,
        "final_test_accessed": False,
        "point_cover_is_fire_truth": False,
        "current_year_cover_verified": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "rows_excluded": 0,
        "final_merge_performed": False,
        "network_requests_in_this_script": 0,
        "web_search_recorded_separately": True,
        "input_count": len(pins),
        "artifact_sha256": artifacts,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    require(json.loads(path.read_text()) == result, "JSON readback")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "report_sha256": sha(path),
                "all_input_hashes_unchanged": True,
                "csv_content_roundtrip_passed": True,
                "scientific_acceptance_granted": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(result, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(path))


if __name__ == "__main__":
    main()
