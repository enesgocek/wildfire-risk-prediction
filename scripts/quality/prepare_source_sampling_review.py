"""Freeze ten source-row keys before clock, coordinates, size, cover or satellite review."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.source_review_sampling import sample_source_keys
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
ARCHIVE = BASE / "public_start_geometry_v1/sources/mersin_zenodo_21455927.zip"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
PROVINCES = ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
POLICY = ROOT / "configs/source_sampling_review_v1.json"
DIRECTORY = "SCI-26-1321_GitHub_Zenodo/data/"
GEO = DIRECTORY + "incident_geography_anonymized.csv"
CLOCK = DIRECTORY + "model_input_anonymized.csv"
LINK_FIELDS = ("date", "year", "district", "burned_area_ha")
FIT = {str(y) for y in range(2018, 2023)}
PINS = {
    ARCHIVE: "21bb776f1c4a4d96b25c15e72da2730eb0a4ca6472451c9f7f7a3dfb4246ae8a",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
    PROVINCES: "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb",
}


def filtered_rows(archive, member):
    with TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="") as stream:
        return [row for row in csv.DictReader(stream) if row["year"] in FIT]


def source_windows(row, hour):
    if hour is None:
        return []
    minutes = Decimal(hour) * 60
    minute = round(minutes)
    require(0 <= minute <= 1439 and abs(minutes - minute) < Decimal("0.00001"), "Clock minute")
    local = datetime.combine(date.fromisoformat(row["date"]), time()) + timedelta(minutes=minute)
    windows = []
    for name, zone in (("if_source_UTC", UTC), ("if_source_Turkiye", ZoneInfo("Europe/Istanbul"))):
        stamp = local.replace(tzinfo=zone).astimezone(UTC)
        start = (stamp - timedelta(microseconds=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=1)
        windows.append(
            {
                "basis": name,
                "reported_time_utc": stamp.isoformat(),
                "diagnostic_window_start_utc": start.isoformat(),
                "diagnostic_window_end_utc": end.isoformat(),
                "inside_current_fit_role": start.year >= 2018
                and end < datetime(2023, 1, 1, tzinfo=UTC),
                "is_admitted_first_satellite_detection_time": False,
            }
        )
    return windows


def main():
    pins = {**PINS, POLICY: digest(POLICY)}
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned source archive and geometry")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    require(policy["selection_columns"] == ["archive_row", "year"], "Restricted selection inputs")
    require(
        all(policy[k] is False for k in policy if k.startswith("filter_on_")),
        "No outcome eligibility cuts",
    )
    require(policy["replace_unprocessable_rows"] is False, "No source-row replacement")
    # First pass reads only the source year/identifier into the sampler.
    with ZipFile(ARCHIVE) as archive:
        with TextIOWrapper(archive.open(GEO), encoding="utf-8-sig", newline="") as stream:
            keys = [
                {"archive_row": row["event_id"], "year": row["year"]}
                for row in csv.DictReader(stream)
                if row["year"] in FIT
            ]
    frame = pd.DataFrame(keys).sort_values(["year", "archive_row"]).reset_index(drop=True)
    require(len(frame) == 424, "Published fit-role source-frame size")
    selected = sample_source_keys(frame, per_year=policy["rows_per_year"], seed=policy["seed"])
    out = (
        BASE
        / "source_sampling_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    frame.to_csv(out / "source_frame_keys.csv", index=False, mode="x")
    selected.to_csv(out / "frozen_selected_keys.csv", index=False, mode="x")
    selection_sha = digest(out / "frozen_selected_keys.csv")
    # Only after the key file has been frozen are the selected rows' context fields read.
    with ZipFile(ARCHIVE) as archive:
        geography, clocks = filtered_rows(archive, GEO), filtered_rows(archive, CLOCK)
        member_sha = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in (GEO, CLOCK)}

    def signature(row):
        return tuple(row[k] for k in LINK_FIELDS)

    geo_count = Counter(signature(row) for row in geography)
    hours = defaultdict(list)
    for row in clocks:
        hours[signature(row)].append(row)
    source = {row["event_id"]: row for row in geography}
    grid = gpd.read_file(GRID).to_crs(6933)
    province = gpd.read_file(PROVINCES)
    boundary = province.loc[province.GAUL1_CODE.astype(str).eq("3160"), "geometry"].iloc[0]
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    intake = []
    for pick in selected.itertuples():
        row = source[pick.archive_row]
        linked = hours[signature(row)]
        unique_link = geo_count[signature(row)] == len(linked) == 1
        windows = source_windows(row, linked[0]["ignition_hour"] if unique_link else None)
        lon, lat = float(row["longitude"]), float(row["latitude"])
        point = Point(lon, lat)
        reasonable = bool(row["coordinate_qc_pass"] == "True" and boundary.covers(point))
        cells = (
            sorted(
                grid.loc[
                    grid.geometry.covers(Point(*project.transform(lon, lat))), "grid_id"
                ].tolist()
            )
            if reasonable
            else []
        )
        intake.append(
            {
                "archive_row": pick.archive_row,
                "year": int(pick.year),
                "reported_date": row["date"],
                "reported_district": row["district"],
                "longitude": lon,
                "latitude": lat,
                "published_coordinate_QC": row["coordinate_qc_pass"],
                "point_in_Mersin": bool(boundary.covers(point)),
                "candidate_grid_ids": cells,
                "temporary_clock_signature_link_unique": unique_link,
                "clock_event_id_not_assumed_equal_to_geography_id": True,
                "clock_hypotheses": windows,
                "reported_final_area_ha_context_only": row["burned_area_ha"],
                "inclusion_probability_within_source_year": (
                    pick.inclusion_probability_within_source_year
                ),
                "source_coordinate_origin_role_verified": False,
                "physical_event_identity_verified": False,
                "review_state": "source_context_prepared_not_L",
                "target": None,
            }
        )
    require(
        digest(out / "frozen_selected_keys.csv") == selection_sha,
        "Selection unchanged after context reads",
    )
    assert_targets_unassigned(pd.read_csv(out / "frozen_selected_keys.csv"))
    result = {
        "status": "outcome_independent_source_rows_frozen_context_prepared_not_L",
        "source_frame_rows": len(frame),
        "selected_rows": len(selected),
        "source_year_counts": {str(k): int(v) for k, v in frame.groupby("year").size().items()},
        "selection_columns_used": ["archive_row", "year"],
        "policy": policy,
        "selection_frozen_before_context_lookup": True,
        "selection_sha256": selection_sha,
        "source_archive_member_sha256": member_sha,
        "intake": intake,
        "satellite_or_observation_results_read": False,
        "cover_classes_read": False,
        "recorded_fires_population_coverage_verified": False,
        "class_conditional_selection_verified": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "src/wildfire_risk_prediction/source_review_sampling.py",
            ]
        },
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print("PASS ten source-row keys frozen without satellite/observation/cover selection")


if __name__ == "__main__":
    main()
