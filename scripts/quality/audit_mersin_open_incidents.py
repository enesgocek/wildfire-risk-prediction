"""Audit a public operational archive for training-period reference use only."""

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/public_start_geometry_v1"
ARCHIVE = BASE / "sources/mersin_zenodo_21455927.zip"
PROVINCES = ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
COUNTS = (
    ROOT / "outputs/reports/dataset/ogm_province_year_v1/20261108T125959Z_992396ed/summary.json"
)
CORINE_DIR = ROOT / "outputs/reports/dataset/corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
CORINE_RECEIPT = CORINE_DIR / "readback.json"
CORINE_RASTER = CORINE_DIR / "source/DATA/U2018_CLC2018_V2020_20u1.tif"
PINS = {
    ARCHIVE: "21bb776f1c4a4d96b25c15e72da2730eb0a4ca6472451c9f7f7a3dfb4246ae8a",
    PROVINCES: "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    COUNTS: "e8ad9a0d4c0a3b70ccc135295d96bcbce2021bc5be06ff3db62ddb61d6391ac0",
    CORINE_RECEIPT: "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f",
    CORINE_RASTER: "69057d527b4338b89f58cf15693effcf18017611ff48144e5c491d083cf1b004",
}
YEARS = {str(year) for year in range(2018, 2024)}
MEMBER_DIR = "SCI-26-1321_GitHub_Zenodo/data/"
COMMON_FIELDS = ["event_id", "date", "year", "district", "burned_area_ha"]
LINK_FIELDS = COMMON_FIELDS[1:]
RADII_M = (250, 1000)
FOREST_SHRUB = {311, 312, 313, 322, 323, 324}
START, END = date(2018, 1, 1), date(2024, 1, 1)


def incident_table(archive, member, extra_fields):
    columns = [*COMMON_FIELDS, *extra_fields]
    with TextIOWrapper(archive.open(MEMBER_DIR + member), encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        require(set(columns) <= set(reader.fieldnames or ()), "Missing required incident fields")
        rows = [{key: row[key] for key in columns} for row in reader if row["year"] in YEARS]
    data = pd.DataFrame(rows, columns=columns)
    require(data.event_id.is_unique and data.event_id.ne("").all(), "Unique public event ID")
    data["date"] = data.date.map(date.fromisoformat)
    require(
        all(d.year == int(y) for d, y in zip(data.date, data.year, strict=True)),
        "Event date/year mismatch",
    )
    return data.set_index("event_id")


def read_incidents():
    with ZipFile(ARCHIVE) as archive:
        locations = incident_table(
            archive,
            "incident_geography_anonymized.csv",
            ["latitude", "longitude", "coordinate_qc_pass"],
        )
        hours = incident_table(archive, "model_input_anonymized.csv", ["ignition_hour"])
    require(
        set(locations.coordinate_qc_pass) == {"True", "False"}, "Unexpected coordinate QC value"
    )
    shared_ids = locations.index.intersection(hours.index)
    aligned = locations.loc[shared_ids, LINK_FIELDS].eq(hours.loc[shared_ids, LINK_FIELDS])
    # The same public ID does not identify the same incident across both files.
    geography_unique = locations[~locations.duplicated(LINK_FIELDS, keep=False)]
    clock_unique = hours[~hours.duplicated(LINK_FIELDS, keep=False)]
    matched = geography_unique.reset_index().merge(
        clock_unique[[*LINK_FIELDS, "ignition_hour"]], on=LINK_FIELDS, validate="one_to_one"
    )
    return locations.join(matched.set_index("event_id").ignition_hour), {
        "clock_table_rows": len(hours),
        "public_ids_present_in_both_tables": len(shared_ids),
        "shared_ids_with_all_link_fields_equal": int(aligned.all(axis=1).sum()),
        "nonunique_signatures_in_geography_rows": len(locations) - len(geography_unique),
        "nonunique_signatures_in_clock_rows": len(hours) - len(clock_unique),
        "unique_signatures_linked_for_review": len(matched),
        "unlinked_geography_rows_with_unique_signatures": len(geography_unique) - len(matched),
    }


def clock_diagnostics(events):
    minutes = events.ignition_hour.dropna().map(lambda x: Decimal(x) * 60)
    rounded = minutes.map(round)
    require(
        rounded.between(0, 1439).all()
        and all(abs(a - b) < Decimal("0.00001") for a, b in zip(minutes, rounded, strict=True)),
        "Published clock values are outside a minute grid",
    )
    dates = events.loc[rounded.index, "date"]
    # Two diagnostic interpretations. The publication does not establish the time basis.
    return pd.DataFrame(
        {
            "if_source_utc": [
                d - timedelta(days=(m == 0)) for d, m in zip(dates, rounded, strict=True)
            ],
            "if_source_turkiye": [
                d - timedelta(days=(m <= 180)) for d, m in zip(dates, rounded, strict=True)
            ],
        },
        index=rounded.index,
    )


def spatial_diagnostics(events):
    provinces = gpd.read_file(PROVINCES)
    (province,) = provinces.loc[provinces.GAUL1_CODE.astype(str).eq("3160"), "geometry"]
    passing = events[events.coordinate_qc_pass.eq("True")]
    locations = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(passing.longitude, passing.latitude),
        index=passing.index,
        crs=4326,
    )
    in_province = locations[locations.geometry.covered_by(province)]
    grid = gpd.read_file(GRID).to_crs("EPSG:6933")[["grid_id", "geometry"]]
    require(grid.grid_id.is_unique, "Unique grid key")
    projected = in_province.to_crs(grid.crs)
    joins = projected.sjoin(grid, predicate="covered_by")
    hits = joins.groupby(level=0).grid_id.agg(list)
    single = hits[hits.str.len().eq(1)].str[0]
    footprints = {}
    for radius in RADII_M:
        buffers = projected.set_geometry(projected.buffer(radius))
        joined = buffers.sjoin(grid, predicate="intersects")
        candidate_ids = joined.groupby(level=0).grid_id.agg(list)
        # Use containment as well as intersecting cells. An AOI edge may cut a buffer.
        one = candidate_ids[candidate_ids.str.len().eq(1)].str[0]
        cell_geometries = grid.set_index("grid_id").geometry.loc[one].set_axis(one.index)
        footprints[radius] = int(buffers.loc[one.index].geometry.covered_by(cell_geometries).sum())
    return single, {
        "publisher_qc_pass": len(passing),
        "publisher_qc_pass_and_in_mersin_boundary": len(in_province),
        "in_mersin_and_single_cell_center": len(single),
        "in_mersin_and_no_cell_center": len(in_province) - len(hits),
        "in_mersin_and_multiple_cell_centers": len(hits) - len(single),
        "hypothetical_buffer_wholly_in_one_cell": footprints,
    }


def catalog_witnesses():
    prefixes = tuple(f"{year}-" for year in sorted(YEARS))
    with CATALOG.open(encoding="utf-8-sig", newline="") as handle:
        rows = [
            (row["grid_id"], row["detection_timestamp_utc"])
            for row in csv.DictReader(handle)
            if row["detection_timestamp_utc"].startswith(prefixes)
        ]
    detections = pd.DataFrame(rows, columns=["grid", "timestamp"])
    stamps = pd.to_datetime(detections.timestamp, format="ISO8601", utc=True, errors="raise")
    windows = detection_windows(stamps.map(pd.Timestamp.isoformat))
    eligible = ~windows.training_window_boundary_review
    return set(
        zip(
            detections.loc[eligible, "grid"],
            windows.loc[eligible, "prediction_timestamp_utc"].dt.date,
            strict=True,
        )
    )


def witness_diagnostics(events, single, clocks):
    review = clocks.join(single.rename("grid"), how="inner").join(events.burned_area_ha)
    valid = review.if_source_utc.between(
        START, END - timedelta(days=2)
    ) & review.if_source_turkiye.between(START, END - timedelta(days=2))
    known = review[valid].copy()
    witnesses = catalog_witnesses()
    for column in clocks:
        known[f"{column}_catalog_context"] = [
            (g, d) in witnesses for g, d in zip(known.grid, known[column], strict=True)
        ]
    masks = [
        known[column]
        for column in ["if_source_utc_catalog_context", "if_source_turkiye_catalog_context"]
    ]
    both = masks[0] & masks[1]
    # This area is the agency's recorded final area. It is used only to describe this archive.
    small = known.burned_area_ha.map(Decimal).lt(1)
    return {
        "single_cell_center_and_clock": len(review),
        "both_possible_windows_in_training": len(known),
        "same_window_under_both_clock_readings": int(
            known.if_source_utc.eq(known.if_source_turkiye).sum()
        ),
        "catalog_context_if_source_utc": int(masks[0].sum()),
        "catalog_context_if_source_turkiye": int(masks[1].sum()),
        "catalog_context_under_both_clock_readings": int(both.sum()),
        "by_final_area_ha": {
            "under_one": {
                "records": int(small.sum()),
                "with_context_in_both": int((small & both).sum()),
            },
            "at_least_one": {
                "records": int((~small).sum()),
                "with_context_in_both": int((~small & both).sum()),
            },
        },
    }


def published_case_checks(events, cells, clocks):
    """Screen dates from the official Gülnar and Anamur notices without inferring identity."""
    gulnar_day = events.date.eq(date(2022, 9, 7))
    names = ["GÜLNAR", "SİLİFKE"]
    gulnar = events[gulnar_day & events.district.isin(names)].set_index("district", drop=False)
    require(set(gulnar.index) == set(names) and len(gulnar) == 2, "Expected Gülnar case rows")
    one, two = (gulnar.loc[name] for name in names)
    _, _, distance = GEOD.inv(
        float(one.longitude), float(one.latitude), float(two.longitude), float(two.latitude)
    )
    anamur = events[events.date.eq(date(2023, 7, 11)) & events.district.eq("ANAMUR")]
    (ref,) = anamur.index
    return {
        "gulnar_and_silifke_2022_09_07": {
            "recorded_clock_minutes_after_midnight": [
                round(Decimal(row.ignition_hour) * 60) for row in (one, two)
            ],
            "recorded_point_separation_m": round(distance, 2),
        },
        "anamur_2023_07_11": {
            "recorded_clock_minutes_after_midnight": round(
                Decimal(anamur.loc[ref, "ignition_hour"]) * 60
            ),
            "recorded_burned_area_ha": anamur.loc[ref, "burned_area_ha"],
            "recorded_point_cell": cells.loc[ref],
            "window_dates_if_source_utc_or_turkiye": [d.isoformat() for d in clocks.loc[ref]],
        },
    }


def cover_context(events, cells):
    """Sample the 2018 map at reported points. Event-date cover remains unknown."""
    legend = json.loads(CORINE_RECEIPT.read_bytes())["legend"]
    subset = events.loc[cells.index]
    with rasterio.open(CORINE_RASTER) as raster:
        project = Transformer.from_crs(4326, raster.crs, always_xy=True)
        x, y = project.transform(subset.longitude.astype(float), subset.latitude.astype(float))
        classes = [
            None if np.ma.is_masked(value) else legend[str(int(value))]["clc_code"]
            for (value,) in raster.sample(zip(x, y, strict=True), masked=True)
        ]
    counts = Counter(classes)
    return {
        "in_mersin_and_single_cell_center": len(classes),
        "forest_or_shrub_at_center": sum(counts[k] for k in FOREST_SHRUB),
        "agricultural_class_at_center": sum(n for k, n in counts.items() if k and 200 <= k < 300),
        "unmapped_center": counts[None],
    }


def main():
    for path, expected in PINS.items():
        with path.open("rb") as f:
            require(
                hashlib.file_digest(f, "sha256").hexdigest() == expected,
                "Unexpected input revision",
            )
    incidents, linkage = read_incidents()
    clocks = clock_diagnostics(incidents)
    single, spatial = spatial_diagnostics(incidents)
    yearly = Counter(incidents.year)
    official = [
        row
        for row in json.loads(COUNTS.read_bytes())["province_year_rows"]
        if row["province_code"] == "TR622"
    ]
    receipt = {
        "purpose": "administrative_reference_diagnostic_only",
        "source": "10.5281/zenodo.21455927",
        "records_with_geography_row": len(incidents),
        "table_linkage": linkage,
        "clock_basis_documented": False,
        "recorded_coordinate_uncertainty_documented": False,
        "by_year": [
            {**row, "archive_geography_rows": yearly[str(row["year"])]} for row in official
        ],
        "space": spatial,
        "clock_and_catalog": witness_diagnostics(incidents, single, clocks),
        "published_case_checks": published_case_checks(incidents, single, clocks),
        "corine_2018_point_context": cover_context(incidents, single),
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "inputs": {path.relative_to(ROOT).as_posix(): digest for path, digest in PINS.items()},
    }
    run = BASE / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    run.mkdir(parents=True, exist_ok=False)
    result = run / "readback.json"
    result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(result.relative_to(ROOT).as_posix(), hashlib.sha256(result.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
