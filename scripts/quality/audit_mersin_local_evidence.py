"""Check existing Mersin case contexts and dated local crops against archive rows."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import geopandas as gpd
import pandas as pd
import rasterio
from audit_mersin_observation_context import incident_windows
from audit_mersin_open_incidents import ARCHIVE, GRID, PINS, PROVINCES, ROOT, read_incidents
from audit_stage_one_selection import verify
from shapely.geometry import box

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "mersin_joint_reference_v1/20261118T140734Z_19b35a6d": (
        "20c458af72b4a77e69d9e4713acfe91bbeaaaac2322165fa6e2a4fe248bcf5bc"
    ),
    "public_case_distribution_v1/20261108T130911Z_460265b4": (
        "13e3a6d3def4836ce32907e46ca1ba0723c5b75f41992b9558934dc27527a20d"
    ),
    "public_event_cover_v1/20261107T233443Z_6e504fcb": (
        "aa0ad0e753d04be890837c7f5e46f7d2ac03ba1ecf9c6e183016946f30bfe38e"
    ),
    "anamur_preevent_cover_v1/20261108T032025Z_2e88ca22": (
        "ef0333fce0b9339f6559d7f4516f9f49b2f03b73c59f52a9da2b24b88b5f1c0e"
    ),
}


def main():
    reports, inputs = {}, {}
    for folder, expected in SOURCES.items():
        path = BASE / folder / "readback.json"
        verify(path, expected)
        reports[folder.split("/")[0]] = json.loads(path.read_bytes())
        inputs[path.relative_to(ROOT).as_posix()] = expected
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
        inputs[path.relative_to(ROOT).as_posix()] = PINS[path]
    units = pd.DataFrame(reports["mersin_joint_reference_v1"]["reference_units"]).set_index(
        "archive_row"
    )
    events, _ = read_incidents()
    selected = events.loc[units.index]
    windows = incident_windows()
    cutoff = (
        pd.to_datetime(windows.prediction_timestamp_utc, utc=True)
        .groupby(windows.archive_row)
        .min()
    )
    points = gpd.GeoSeries(
        gpd.points_from_xy(selected.longitude.astype(float), selected.latitude.astype(float)),
        index=units.index,
        crs=4326,
    ).to_crs(6933)
    case_contexts = []
    for case in reports["public_case_distribution_v1"]["cases"]:
        if case["province"] == "Mersin":
            ids = selected.index[selected.date.map(str).eq(case["reported_local_day"])]
            case_contexts.append(
                {
                    "reference_key": case["reference_key"],
                    "reported_local_day": case["reported_local_day"],
                    "same_day_archive_rows": [
                        {
                            "archive_row": i,
                            "forestry_district": selected.loc[i, "district"],
                            "center_context": units.loc[i, "center_context"],
                            "stable_day_and_250m": bool(units.loc[i, "stable_day_and_250m"]),
                        }
                        for i in ids
                    ],
                    "event_identity_match_confirmed": False,
                }
            )
    crops = []
    cover_folder = BASE / next(p for p in SOURCES if p.startswith("public_event_cover_v1/"))
    aydincik_ids = {
        p["id"]
        for p in reports["public_event_cover_v1"]["first_points"]
        if p["case"] == "aydincik_pembecik"
    }
    for window in reports["public_event_cover_v1"]["successful_windows"]:
        if window["point_id"] in aydincik_ids:
            crops.append(
                (
                    cover_folder / window["folder"] / "SCL.tif",
                    window["assets"]["SCL"]["sha256"],
                    window["acquired_utc"],
                )
            )
    for windows_list in reports["anamur_preevent_cover_v1"]["images"].values():
        for window in windows_list:
            crops.append(
                (
                    ROOT / window["crop_directory"] / "SCL.tif",
                    window["assets"]["SCL"]["sha256"],
                    window["acquired_utc"],
                )
            )
    require(
        len(crops) == 14 and len({p for p, _, _ in crops}) == 14,
        "Fixed eight Aydincik and six Anamur local crops",
    )
    image_contexts = []
    for path, expected, acquired in crops:
        verify(path, expected)
        inputs[path.relative_to(ROOT).as_posix()] = expected
        with rasterio.open(path) as raster:
            footprint = gpd.GeoSeries([box(*raster.bounds)], crs=raster.crs).to_crs(6933).iloc[0]
        acquired_time = pd.Timestamp(acquired)
        target_times = cutoff.reindex(units.index)
        ages_ns = target_times.map(
            lambda cutoff, acquired_ns=acquired_time.value: cutoff.value - acquired_ns
        )
        temporal = ages_ns.gt(0) & ages_ns.le(60 * 86400 * 1_000_000_000)
        geometric = points.covered_by(footprint)
        ids = units.index[temporal & geometric]
        image_contexts.append(
            {
                "crop": path.relative_to(ROOT).as_posix(),
                "acquired_utc": acquired,
                "rows_in_prior_60_days": list(units.index[temporal]),
                "rows_with_center_and_prior_date": list(ids),
                "rows_with_250m_and_prior_date": list(
                    ids[points.loc[ids].buffer(250).covered_by(footprint)]
                ),
                "stable_forest_center_rows": list(
                    ids[
                        units.loc[ids, "stable_day_and_250m"]
                        & units.loc[ids, "center_context"].eq("forest_shrub")
                    ]
                ),
            }
        )
    result = {
        "scope": "three_existing_public_cases_and_14_local_scl_crops_only",
        "case_contexts": case_contexts,
        "local_image_contexts": image_contexts,
        "inputs_sha256": inputs,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    out = (
        BASE / "mersin_local_evidence_v1" / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Local evidence readback")
    print(json.dumps(result, indent=2))
    print(path.relative_to(ROOT), digest(path))


if __name__ == "__main__":
    main()
