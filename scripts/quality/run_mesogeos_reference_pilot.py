"""Run the accepted, bounded public-reference context review without fire labels."""

import argparse
import codecs
import csv
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.mesogeos_reference import validate_proposal
from wildfire_risk_prediction.mesogeos_review import read_open_year_rows, review_points

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROPOSAL = ROOT / "configs/mesogeos_reference_pilot_proposal_v1.json"
DECISION = ROOT / "configs/mesogeos_reference_pilot_execution_v1.json"
PREP = BASE / "mesogeos_reference_preparation_v1/20261124T224948Z_e1def508"
AUDIT = BASE / "mesogeos_reference_preparation_audit_v1/20261124T225146Z_5ae84eea"
HEADER = BASE / "mesogeos_reference_header_probe_v1/20261124T224319Z_d1ad6d77"


class StopReview(Exception):
    pass


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def require(value, message):
    if not value:
        raise StopReview(message)


def save(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def table(path, rows):
    if not rows:
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def work(out):
    import pyogrio
    from pyproj import CRS
    from shapely import wkt
    from shapely.geometry import mapping, shape

    started = time.monotonic()
    proposal, decision = json.loads(PROPOSAL.read_bytes()), json.loads(DECISION.read_bytes())
    validate_proposal(proposal)
    require(
        decision["selected_direction"] == "A_run_bounded_supplementary_reference_review"
        and decision["reference_acquisition_and_context_review"] is True,
        "accepted_reference_scope",
    )
    require(
        all(
            decision[key] is False
            for key in [
                "new_model_training",
                "new_model_predictions",
                "target_or_accepted_L_assignment",
                "negative_label_assignment",
                "years_2023_to_2025_scientific_values",
                "risk_categories",
                "cloud_execution",
                "external_contact",
                "final_merge",
            ]
        ),
        "restricted_reference_scope",
    )
    require(
        decision["maximum_runtime_seconds"] == proposal["max_elapsed_seconds"] == 900
        and decision["maximum_total_file_bytes"] == proposal["max_total_file_bytes"] == 170000000,
        "unchanged_bounds",
    )
    aoi_path = ROOT / "data/aoi/aoi.geojson"
    pins = {
        PROPOSAL: decision["proposal_sha256"],
        PREP / "readback.json": decision["preparation_sha256"],
        AUDIT / "readback.json": decision["preparation_audit_sha256"],
        DECISION: digest(DECISION),
        aoi_path: "d727a6c1e320650a47fd18c7077af847a82d4c99cdc87e49a3c32cb144ea7c22",
        ROOT / "src/wildfire_risk_prediction/mesogeos_review.py": digest(
            ROOT / "src/wildfire_risk_prediction/mesogeos_review.py"
        ),
    }
    require(all(digest(path) == expected for path, expected in pins.items()), "frozen_inputs")
    raw = ROOT / "data/raw/external/mesogeos_reference_pilot_v1" / out.name
    raw.mkdir(parents=True, exist_ok=False)
    save(out / "execution_decision.json", decision)
    ledger, consumed, phase_one, phase_two = [], 0, None, None
    suffixes = {Path(row["name"]).suffix: row for row in proposal["files"]}

    def download(suffix):
        nonlocal consumed
        item = suffixes[suffix]
        expected = item["expected_bytes"]
        require(time.monotonic() - started < 900, "time_limit")
        require(consumed + expected <= 170000000, "byte_limit")
        print("Public reference file:", suffix, flush=True)
        part, final = raw / (item["name"] + ".part"), raw / item["name"]
        require(not part.exists() and not final.exists(), "one_attempt_per_file")
        entry = {
            "name": item["name"],
            "expected_bytes": expected,
            "bytes_read": 0,
            "status": "started",
        }
        ledger.append(entry)
        request = urllib.request.Request(
            "https://drive.google.com/uc?export=download&id=" + item["id"],
            headers={
                "User-Agent": "wildfire-public-reference-review/1",
                "Range": f"bytes=0-{expected - 1}",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            mime = response.headers.get_content_type()
            entry["http_status"], entry["content_type"] = response.status, mime
            require(
                mime not in {"text/html", "application/json", "application/xml", "text/xml"},
                "public_access_requires_manual_step",
            )
            require(response.status in {200, 206}, "unexpected_public_response")
            if response.status == 206:
                require(
                    response.headers.get("Content-Range") == f"bytes 0-{expected - 1}/{expected}",
                    "file_range_identity_changed",
                )
            length = response.headers.get("Content-Length")
            require(length is None or int(length) == expected, "file_size_changed")
            with part.open("xb") as handle:
                while True:
                    require(time.monotonic() - started < 900, "time_limit")
                    chunk = response.read(min(1024 * 1024, expected - entry["bytes_read"] + 1))
                    if not chunk:
                        break
                    entry["bytes_read"] += len(chunk)
                    consumed += len(chunk)
                    require(
                        entry["bytes_read"] <= expected and consumed <= 170000000,
                        "file_exceeded_bound",
                    )
                    handle.write(chunk)
            require(entry["bytes_read"] == expected, "incomplete_file")
        part.rename(final)
        entry.update({"status": "complete", "sha256": digest(final)})
        save(out / "transfer_checkpoint.json", {"ledger": ledger, "bytes_read": consumed})
        return final

    status, stop_code = "reference_pilot_not_completed", None
    try:
        for suffix in proposal["stage_one"]:
            download(suffix)
        encoding = (raw / suffixes[".cpg"]["name"]).read_text(encoding="ascii").strip()
        codecs.lookup(encoding)
        require(
            digest(raw / suffixes[".prj"]["name"]) == digest(HEADER / "projection.prj"),
            "coordinate_definition_changed",
        )
        require(
            CRS.from_wkt((raw / suffixes[".prj"]["name"]).read_text()).to_authority()
            == ("EPSG", "5643"),
            "native_CRS",
        )
        dbf = raw / suffixes[".dbf"]["name"]
        with dbf.open("rb") as handle:
            require(
                hashlib.sha256(handle.read(1121)).hexdigest() == digest(HEADER / "dbf_schema.bin"),
                "source_schema_changed",
            )
        permitted, counts, schema = read_open_year_rows(dbf, encoding)
        aoi = shape(
            json.loads((ROOT / "data/aoi/aoi.geojson").read_bytes())["features"][0]["geometry"]
        )
        reviewed, point_issues = review_points(permitted, aoi)
        table(out / "point_context_review.csv", reviewed)
        table(out / "native_point_parse_issues.csv", point_issues)
        phase_one = {
            "status": "open_year_point_context_review_complete",
            "encoding": encoding,
            "dbf_schema": schema,
            "year_guards": counts,
            "AOI_review_rows": len(reviewed),
            "AOI_raw_year_counts": dict(Counter(r["YEAR"] for r in reviewed)),
            "point_parse_issue_count_all_permitted_rows": len(point_issues),
            "nonunique_source_ids_in_AOI": sum(
                v - 1 for k, v in Counter(r["id"] for r in reviewed).items() if k and v > 1
            ),
            "point_date_consistent_rows": sum(
                r["native_ignition_date_equals_acquisition_date"] for r in reviewed
            ),
            "clock_candidates_present": sum(
                r["acquisition_utc_candidate_if_FIRMS_fields_preserved"] is not None
                for r in reviewed
            ),
            "clock_semantics_accepted": False,
            "new_labels": False,
        }
        save(out / "phase_one_summary.json", phase_one)
        print("Phase one AOI context rows:", len(reviewed), flush=True)
        require(bool(reviewed), "no_relevant_rows_after_phase_one")
        for suffix in proposal["stage_two_if_stage_one_supports_relevant_rows"]:
            download(suffix)
        with (raw / suffixes[".shx"]["name"]).open("rb") as handle:
            require(
                hashlib.sha256(handle.read(100)).hexdigest() == digest(HEADER / "shx_header.bin"),
                "source_index_changed",
            )
        selected_indices = [r["source_record_index"] for r in reviewed]
        perimeters = pyogrio.read_dataframe(
            raw / suffixes[".shp"]["name"],
            columns=[],
            fids=selected_indices,
            fid_as_index=True,
            use_arrow=False,
        )
        require(
            set(map(int, perimeters.index)) == set(selected_indices),
            "selected_open_year_feature_ids",
        )
        require(perimeters.crs == CRS.from_epsg(5643), "native_geometry_CRS")
        require(list(perimeters.columns) == ["geometry"], "geometry_only_no_other_year_attributes")
        geo = perimeters.to_crs(4326)
        geometry_rows, features = [], []
        for row in reviewed:
            index = row["source_record_index"]
            polygon = perimeters.loc[index].geometry
            valid = polygon is not None and not polygon.is_empty and polygon.is_valid
            point = wkt.loads(row["geometry_h"]) if row["native_point_lon"] is not None else None
            geometry_rows.append(
                {
                    "source_record_index": index,
                    "geometry_type": polygon.geom_type if polygon is not None else None,
                    "geometry_valid": bool(valid),
                    "native_point_covered_by_final_perimeter": bool(polygon.covers(point))
                    if valid and point is not None
                    else None,
                    "native_point_to_final_perimeter_distance_m": float(polygon.distance(point))
                    if valid and point is not None
                    else None,
                    "perimeter_intersects_AOI": bool(geo.loc[index].geometry.intersects(aoi))
                    if valid
                    else None,
                    "target": None,
                    "accepted_L_membership": None,
                    "negative_label_permitted": False,
                }
            )
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "source_record_index": index,
                        "source_role": "supplementary_satellite_perimeter_context",
                    },
                    "geometry": mapping(geo.loc[index].geometry) if polygon is not None else None,
                }
            )
        table(out / "perimeter_context_review.csv", geometry_rows)
        save(
            out / "selected_perimeters.geojson", {"type": "FeatureCollection", "features": features}
        )
        phase_two = {
            "status": "selected_open_year_perimeter_context_complete",
            "selected_geometry_rows": len(geometry_rows),
            "valid_geometry_rows": sum(r["geometry_valid"] for r in geometry_rows),
            "first_point_covered_by_perimeter_rows": sum(
                r["native_point_covered_by_final_perimeter"] is True for r in geometry_rows
            ),
            "not_independent_fire_truth": True,
        }
        save(out / "phase_two_summary.json", phase_two)
        status = "supplementary_reference_pilot_complete_pending_separate_audit"
    except Exception as exc:
        stop_code = str(exc) if isinstance(exc, StopReview) else type(exc).__name__
        status = (
            "phase_one_complete_phase_two_stopped_outputs_retained"
            if phase_one
            else "reference_pilot_stopped_outputs_retained"
        )
        print("Reference review stopped:", stop_code, flush=True)
    require(
        all(digest(path) == expected for path, expected in pins.items()), "earlier_inputs_preserved"
    )
    result = {
        "status": status,
        "analysis_date": "2026-11-25",
        "decision": decision,
        "stop_code": stop_code,
        "elapsed_worker_seconds": time.monotonic() - started,
        "source_directory": raw.relative_to(ROOT).as_posix(),
        "file_bytes_read": consumed,
        "transfer_ledger": ledger,
        "phase_one": phase_one,
        "phase_two": phase_two,
        "new_training_or_predictions": False,
        "new_target_or_L": False,
        "negative_labels_assigned": False,
        "years_2023_to_2025_scientific_values_decoded": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "raw_file_sha256": {p.name: digest(p) for p in raw.iterdir() if p.is_file()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        "producer_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(status, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        out = args.worker.resolve()
        out.relative_to(BASE / "mesogeos_reference_pilot_run_v1")
        work(out)
        return
    out = (
        BASE
        / "mesogeos_reference_pilot_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    with (out / "child.log").open("w", encoding="utf-8") as log:
        try:
            child = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", str(out)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                timeout=900,
                check=False,
            )
            outcome = {
                "status": "child_completed_outputs_retained"
                if child.returncode == 0
                else "child_failed_outputs_retained",
                "returncode": child.returncode,
            }
        except subprocess.TimeoutExpired:
            outcome = {"status": "child_timeout_outputs_retained", "timeout_seconds": 900}
    save(out / "launcher_receipt.json", outcome)
    print(outcome["status"], flush=True)


if __name__ == "__main__":
    main()
