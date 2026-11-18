"""Propagate two clock readings and projected location margins through reference keys."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from io import TextIOWrapper
from uuid import uuid4
from zipfile import ZipFile

import geopandas as gpd
from audit_mersin_observation_context import incident_windows
from audit_mersin_open_incidents import (
    ARCHIVE,
    GRID,
    MEMBER_DIR,
    PINS,
    PROVINCES,
    ROOT,
    read_incidents,
)
from audit_stage_one_selection import verify

from wildfire_risk_prediction.feature_join import require


def main():
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
    windows = incident_windows()
    require(
        len(windows) == 958 and windows.groupby("archive_row").size().eq(2).all(),
        "Fixed 479-row two-clock scope",
    )
    events, _ = read_incidents()
    units = windows.loc[windows.basis.eq("if_source_utc")].set_index("archive_row").copy()
    units["year"] = events.loc[units.index, "year"]
    units["same_target_day"] = (
        windows.groupby("archive_row").prediction_timestamp_utc.nunique().eq(1)
    )
    grid = gpd.read_file(GRID).to_crs(6933).set_index("grid_id")
    points = gpd.GeoSeries(
        gpd.points_from_xy(
            events.loc[units.index, "longitude"], events.loc[units.index, "latitude"]
        ),
        index=units.index,
        crs=4326,
    ).to_crs(6933)
    cell_shapes = gpd.GeoSeries(
        grid.loc[units.grid_id, "geometry"].to_numpy(), index=units.index, crs=6933
    )
    require(points.covered_by(cell_shapes).all(), "Reference centers in assigned cells")
    boundary_distances = points.distance(cell_shapes.boundary)
    for radius in (250, 1000):
        units[f"margin_{radius}m_inside_cell"] = points.buffer(radius).covered_by(cell_shapes)
        require(
            units[f"margin_{radius}m_inside_cell"].eq(boundary_distances.ge(radius)).all(),
            "Buffer containment agrees with independent boundary distance",
        )
        units[f"stable_day_and_{radius}m"] = (
            units.same_target_day & units[f"margin_{radius}m_inside_cell"]
        )
    require(
        (~units.margin_1000m_inside_cell | units.margin_250m_inside_cell).all(),
        "Nested spatial margins",
    )
    columns = [
        "same_target_day",
        "margin_250m_inside_cell",
        "margin_1000m_inside_cell",
        "stable_day_and_250m",
        "stable_day_and_1000m",
    ]
    summary = []
    for (year, small), group in units.groupby(["year", "small"]):
        summary.append(
            {
                "year": year,
                "final_area_class": "under_1_ha" if small else "at_least_1_ha",
                "records": len(group),
                **{c: int(group[c].sum()) for c in columns},
            }
        )
    documents, schemas = {}, {}
    with ZipFile(ARCHIVE) as archive:
        for name in (
            "README.md",
            "RELEASE_NOTES_v1.0.0.md",
            "DATA_LICENSE.md",
            "data/DATA_DICTIONARY.md",
        ):
            data = archive.read("SCI-26-1321_GitHub_Zenodo/" + name)
            documents[name] = hashlib.sha256(data).hexdigest()
        for name in ("incident_geography_anonymized.csv", "model_input_anonymized.csv"):
            with TextIOWrapper(
                archive.open(MEMBER_DIR + name), encoding="utf-8-sig", newline=""
            ) as f:
                schemas[name] = csv.DictReader(f).fieldnames
    result = {
        "records": len(units),
        "summary": summary,
        "totals": {c: int(units[c].sum()) for c in columns},
        "independent_boundary_distance_checks": len(units) * 2,
        "closest_boundary_distance_to_threshold_m": float(
            min((boundary_distances - radius).abs().min() for radius in (250, 1000))
        ),
        "reference_units": units.reset_index()[
            ["archive_row", "grid_id", "year", "small", *columns]
        ].to_dict("records"),
        "archive_sha256": PINS[ARCHIVE],
        "grid_sha256": PINS[GRID],
        "province_sha256": PINS[PROVINCES],
        "source_document_sha256": documents,
        "published_table_columns": schemas,
        "margin_interpretation": "projected_diagnostic_sensitivity_not_measured_location_error",
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/mersin_reference_stability_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Reference stability readback")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k in ("records", "summary", "totals")}, indent=2
        )
    )
    print(path.relative_to(ROOT), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
