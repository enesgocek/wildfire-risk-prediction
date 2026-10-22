"""Record the chosen cover direction and describe nearby map classes at fixed pilot points."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import rasterio

from wildfire_risk_prediction.cover_neighborhood import describe_neighborhoods
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PARENT = "outputs/reports/dataset/linked_candidate_context_v1/20261022T210339Z_23e2e5a4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline reference-map neighborhoods")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained input",
        )
        actual = sha(path)
        require(expected is None or expected == actual, "Input fingerprint")
        pins[name] = actual
        return path

    parent = json.loads(
        retain(
            PARENT + "/readback.json",
            "58363f7e1640af945195ecf9d13144a5ec4951fb259a30816274c12956710de8",
        ).read_text()
    )
    policy = json.loads(retain("configs/habitat_scope_direction_v1.json").read_text())
    require(
        policy["primary_research_cover_groups"] == ["forest", "shrub"]
        and policy["decision_source"] == "explicit_user_selection_forest_and_shrub"
        and policy["automatic_exclusion_authorized"] is False
        and policy["positive_label_permitted"] is False
        and policy["negative_label_permitted"] is False
        and policy["point_neighborhood_radius_selected_m"] is None,
        "Direction only, no chosen point filter",
    )
    points = pd.read_csv(
        retain(
            PARENT + "/first_point_cover.csv", parent["artifact_sha256"]["first_point_cover.csv"]
        ),
        float_precision="round_trip",
    )
    require(len(points) == 25, "Same purpose-selected 25 source points")
    raster = retain(
        "data/raw/landcover/landcover_copernicus_2017.tif",
        "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    )
    with rasterio.open(raster) as dataset:
        result = describe_neighborhoods(points, dataset)
    for name in (
        "scripts/quality/review_cover_neighborhoods.py",
        "src/wildfire_risk_prediction/cover_neighborhood.py",
        "src/wildfire_risk_prediction/point_cover_context.py",
        "src/wildfire_risk_prediction/landscape.py",
        "src/wildfire_risk_prediction/target_admission.py",
    ):
        retain(name)
    summary = (
        result.groupby(["radius_m", "center_cover_group_2017"])
        .agg(
            source_points=("detection_id", "size"),
            points_with_forest_shrub_centers_nearby=(
                "forest_shrub_pixel_centers",
                lambda x: int(x.gt(0).sum()),
            ),
            minimum_forest_shrub_center_count_fraction=(
                "forest_shrub_center_count_fraction",
                "min",
            ),
            maximum_forest_shrub_center_count_fraction=(
                "forest_shrub_center_count_fraction",
                "max",
            ),
        )
        .reset_index()
    )
    out = (
        ROOT
        / "outputs/reports/dataset/cover_neighborhood_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (("point_neighborhoods.csv", result), ("center_group_summary.csv", summary)):
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            pd.read_csv(path, float_precision="round_trip"),
            check_dtype=False,
        )
        artifacts[name] = sha(path)
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, "Unchanged input")
    path = out / "input_manifest.json"
    path.write_text(json.dumps(pins, indent=2) + "\n")
    artifacts[path.name] = sha(path)
    groups = []
    for radius, g in result.groupby("radius_m"):
        noncore = ~g.center_cover_group_2017.isin(["forest", "shrub"])
        groups.append(
            {
                "radius_m": int(radius),
                "source_points": len(g),
                "noncore_center_points": int(noncore.sum()),
                "noncore_points_with_nearby_forest_shrub_centers": int(
                    (noncore & g.forest_shrub_pixel_centers.gt(0)).sum()
                ),
                "points_without_mapped_centers": int(g.mapped_pixel_centers.eq(0).sum()),
                "clipped_search_windows": int(g.conservative_search_window_clipped.sum()),
            }
        )
    report = {
        "version": "cover_neighborhood_v1",
        "client_date": "2026-10-23",
        "status": "scope_direction_recorded_neighborhoods_exploratory_only",
        "source_points": len(points),
        "neighborhood_rows": len(result),
        "primary_research_cover_groups": ["forest", "shrub"],
        "radius_summaries": groups,
        "reference_map_year": 2017,
        "radius_selected": None,
        "automatic_exclusion_performed": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
        "final_test_accessed": False,
        "validation_accessed": False,
        "network_requests": 0,
        "input_count": len(pins),
        "artifact_sha256": artifacts,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    require(json.loads(path.read_text()) == report, "Report readback")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "report_sha256": sha(path),
                "all_input_hashes_unchanged": True,
                "all_csv_content_roundtrips_passed": True,
                "scientific_acceptance_granted": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(report, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(path))


if __name__ == "__main__":
    main()
