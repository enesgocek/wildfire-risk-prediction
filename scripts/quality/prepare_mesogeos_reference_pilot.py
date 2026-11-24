"""Quantify an unexecuted supplementary-reference proposal using existing metadata."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pyproj import CRS
from shapely.geometry import shape

from wildfire_risk_prediction.mesogeos_reference import (
    dbf_header,
    shp_header,
    validate_proposal,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/mesogeos_reference_pilot_proposal_v1.json"
SOURCES = [
    (
        "mesogeos_public_access_v1/20261124T223728Z_ed9b08ea",
        "2f01e5f3eaf0e3299c797773ee78dc3bbcd4988616ef2afefad6b5beed5a23ee",
    ),
    (
        "mesogeos_public_children_v1/20261124T223810Z_ebd72c9c",
        "6f7fff1ab75601ee7c73388f5f82c4df069b902132ce42a0027d988811f856f2",
    ),
    (
        "mesogeos_vector_access_v1/20261124T223857Z_2b72c128",
        "bc1fc44624d0d7182a838051b9ac331289aa9845878416c2f90ced3d322c1104",
    ),
    (
        "mesogeos_reference_header_probe_v1/20261124T224319Z_d1ad6d77",
        "8da329d230d7fe4906479f17bc056dfe165d7a96fe5382a11d3e153a8580a57d",
    ),
    (
        "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98",
        "c20b988ba0ab1387f4e4121efeabe6a6939e30eac2bedbf7c6ba9cfbafffa45f",
    ),
    (
        "evaluation_review_package_v1/20261123T141815Z_be04a5fe",
        "4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e",
    ),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, note):
    if not value:
        raise ValueError(note)


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    config = json.loads(CONFIG.read_bytes())
    validate_proposal(config)
    pins = {CONFIG: digest(CONFIG)}
    receipts = {}
    for folder, expected in SOURCES:
        path = BASE / folder / "readback.json"
        require(digest(path) == expected, "Frozen receipt")
        receipts[folder.split("/")[0]] = json.loads(path.read_bytes())
        pins[path] = expected

    def artifact(folder, name):
        path = folder / name
        receipt = json.loads((folder / "readback.json").read_bytes())
        expected = receipt["artifact_sha256"][name]
        require(digest(path) == expected, "Frozen artifact: " + name)
        pins[path] = expected
        return path

    public = BASE / "mesogeos_public_access_v1/20261124T223728Z_ed9b08ea"
    vector = BASE / "mesogeos_vector_access_v1/20261124T223857Z_2b72c128"
    probe = BASE / "mesogeos_reference_header_probe_v1/20261124T224319Z_d1ad6d77"
    source_plan = BASE / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"
    review = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
    items = json.loads(artifact(vector, "items.json").read_bytes())
    require(
        {(r["name"], r["id"], r["numeric_fields"]["13"]) for r in items}
        == {(r["name"], r["id"], r["expected_bytes"]) for r in config["files"]},
        "Proposal matches the actual public listing",
    )
    for item in items:
        require(
            item["numeric_fields"]["13"] == item["numeric_fields"]["27"],
            "Two public size fields agree",
        )
    dbf = dbf_header(artifact(probe, "dbf_schema.bin").read_bytes())
    index = shp_header(artifact(probe, "shx_header.bin").read_bytes())
    require(
        dbf == receipts["mesogeos_reference_header_probe_v1"]["dbf"],
        "Metadata parser compatibility after proposal extension",
    )
    require(
        index == receipts["mesogeos_reference_header_probe_v1"]["shx"], "Index metadata unchanged"
    )
    require(
        (index["file_bytes_declared"] - 100) // 8 == dbf["record_count_declared"],
        "Header record-count agreement",
    )
    by_suffix = {Path(row["name"]).suffix: row for row in config["files"]}
    require(
        by_suffix[".dbf"]["expected_bytes"]
        == dbf["header_bytes"] + dbf["record_count_declared"] * dbf["record_bytes"] + 1,
        "Declared DBF size including EOF byte",
    )
    crs = CRS.from_wkt(artifact(probe, "projection.prj").read_text(encoding="utf-8"))
    require(
        crs.to_authority() == ("EPSG", "5643") and crs.is_projected,
        "Verified vector coordinate system",
    )
    code_tree = json.loads(artifact(public, "repository_tree.json").read_bytes())
    code_lookup = {row["path"]: row for row in code_tree}
    for record in receipts["mesogeos_vector_access_v1"]["code"]:
        path = artifact(vector, record["stored_name"])
        code_path = record["requested_url"].split(config["source_commit"] + "/")[1]
        raw = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()
        require(blob == code_lookup[code_path]["sha"], "Public code matches the pinned Git blob")
    notebook = json.loads(
        (
            vector / "ml_tracks__a.fire_danger__dataset-extraction__sample_positives.ipynb.txt"
        ).read_bytes()
    )
    cells = [
        "".join(row.get("source", [])) for row in notebook["cells"] if row["cell_type"] == "code"
    ]
    source_code = "\n".join(cells)
    require(
        "gdf['IGNITION_D'] = gdf['IGNITION_D'] - pd.Timedelta(days=1)" in source_code,
        "Published one-day backward shift identified",
    )
    require('gdf.crs = "EPSG:5643"' in source_code, "Published point CRS assignment identified")
    anchors = rows(artifact(source_plan, "source_anchor_inventory.csv"))
    calendar = rows(artifact(review, "record_memberships.csv"))
    require(len(anchors) == 81 and len(calendar) == 8956, "Existing planning population")
    require(
        all(r["prediction_timestamp_utc"][:4] == "2022" for r in anchors + calendar),
        "Only existing 2022 metadata",
    )
    require(
        all(
            not r["target"]
            and not r["accepted_L_membership"]
            and r["daily_observation_status"] == "unknown"
            and r["negative_label_permitted"] == "False"
            for r in calendar
        ),
        "Unknown target and observation state preserved",
    )
    date_support = []
    for end in ["2022-09-29", "2022-09-30"]:
        date_support.append(
            {
                "candidate_native_upper_date_not_verified_coverage": end,
                "Mersin_source_anchors_before_or_on": sum(
                    r["prediction_timestamp_utc"][:10] <= end for r in anchors
                ),
                "primary_eligible_Mersin_anchors_before_or_on": sum(
                    r["primary_eligible"] == "True" and r["prediction_timestamp_utc"][:10] <= end
                    for r in anchors
                ),
                "four_province_calendar_rows_before_or_on": sum(
                    r["cohort"] == "four_province" and r["prediction_timestamp_utc"][:10] <= end
                    for r in calendar
                ),
                "separate_Mersin_calendar_rows_before_or_on": sum(
                    r["cohort"] == "separate_Mersin" and r["prediction_timestamp_utc"][:10] <= end
                    for r in calendar
                ),
            }
        )
    aoi_path, manifest_path = ROOT / "data/aoi/aoi.geojson", ROOT / "data/aoi/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    require(digest(aoi_path) == manifest["aoi_sha256"], "Existing AOI identity")
    pins[aoi_path], pins[manifest_path] = digest(aoi_path), digest(manifest_path)
    bounds = shape(json.loads(aoi_path.read_bytes())["features"][0]["geometry"]).bounds
    declared = [-10.72, 30.07, 36.74, 47.7]
    require(
        declared[0] <= bounds[0] <= bounds[2] <= declared[2]
        and declared[1] <= bounds[1] <= bounds[3] <= declared[3],
        "AOI inside published rectangular extent; not event coverage evidence",
    )
    stage_one = sum(by_suffix[s]["expected_bytes"] for s in config["stage_one"])
    stage_two = sum(
        by_suffix[s]["expected_bytes"]
        for s in config["stage_two_if_stage_one_supports_relevant_rows"]
    )
    out = (
        BASE
        / "mesogeos_reference_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "execution_proposal.json").write_bytes(CONFIG.read_bytes())
    (out / "date_support.json").write_text(
        json.dumps(date_support, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    result = {
        "status": "bounded_reference_proposal_ready_scope_choice_pending",
        "analysis_date": "2026-11-25",
        "input_sha256": {p.relative_to(ROOT).as_posix(): value for p, value in pins.items()},
        "source_entries_declared_all_regions_not_independent_fires": dbf["record_count_declared"],
        "source_schema_fields": dbf["field_count"],
        "source_vector_CRS": "EPSG:5643",
        "published_date_shift_days": -1,
        "published_date_shift_applied_to_project": False,
        "stage_one_expected_bytes": stage_one,
        "stage_two_expected_bytes": stage_two,
        "total_expected_file_bytes": stage_one + stage_two,
        "AOI_bounds": list(bounds),
        "inside_published_rectangular_extent": True,
        "actual_event_coverage_verified": False,
        "actual_reference_records_opened": 0,
        "new_performance_metrics": 0,
        "new_model_or_labels": False,
        "years_2023_to_2025_opened": False,
        "final_merge": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        "producer_sha256": digest(Path(__file__)),
        "metadata_and_scope_module_sha256": digest(
            ROOT / "src/wildfire_risk_prediction/mesogeos_reference.py"
        ),
    }
    require(
        all(digest(path) == expected for path, expected in pins.items()),
        "Preparation inputs unchanged",
    )
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
