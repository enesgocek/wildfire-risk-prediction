"""Separate metadata/count readback for the unexecuted source-review proposal."""

import argparse
import csv
import hashlib
import json
import struct
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pyproj import CRS

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparation", required=True, type=Path)
    path = parser.parse_args().preparation.resolve()
    path.relative_to(BASE / "mesogeos_reference_preparation_v1")
    readback = json.loads((path / "readback.json").read_bytes())
    require(
        sha(ROOT / "scripts/quality/prepare_mesogeos_reference_pilot.py")
        == readback["producer_sha256"]
        and sha(ROOT / "src/wildfire_risk_prediction/mesogeos_reference.py")
        == readback["metadata_and_scope_module_sha256"],
        "Preparation producer and scope code identity",
    )
    for name, expected in readback["input_sha256"].items():
        require(sha(ROOT / name) == expected, "Frozen preparation input")
    for name, expected in readback["artifact_sha256"].items():
        require(sha(path / name) == expected, "Preparation artifact")
    config = json.loads((path / "execution_proposal.json").read_bytes())
    require(config["execute_authorized"] is False, "Not an execution decision")
    require(config["permitted_years"] == list(range(2018, 2023)), "No later research years")
    require(
        all(
            config[key] is False
            for key in [
                "target_assignment",
                "accepted_L_assignment",
                "source_absence_is_negative",
                "new_model_training",
                "new_model_predictions",
                "final_merge",
                "cloud_execution",
            ]
        ),
        "Reference acquisition plan does not grant labels or training",
    )
    probe_folder = BASE / "mesogeos_reference_header_probe_v1/20261124T224319Z_d1ad6d77"
    header = (probe_folder / "dbf_schema.bin").read_bytes()
    count = int.from_bytes(header[4:8], "little")
    header_length = int.from_bytes(header[8:10], "little")
    row_width = int.from_bytes(header[10:12], "little")
    fields = [
        header[i : i + 11].split(b"\x00", 1)[0].decode("ascii")
        for i in range(32, header_length - 1, 32)
    ]
    require(count == 23225 and len(fields) == 34, "Independent DBF schema readback")
    require(
        {"YEAR", "IGNITION_D", "ACQ_DATE", "ACQ_TIME", "geometry_h"} <= set(fields),
        "Required review fields are declared, not assumed complete",
    )
    index = (probe_folder / "shx_header.bin").read_bytes()
    index_size = struct.unpack(">I", index[24:28])[0] * 2
    require((index_size - 100) // 8 == count, "Independent index-count agreement")
    require(
        CRS.from_wkt((probe_folder / "projection.prj").read_text()).to_authority()
        == ("EPSG", "5643"),
        "Independent CRS readback",
    )
    sizes = {Path(r["name"]).suffix: r["expected_bytes"] for r in config["files"]}
    require(sizes[".dbf"] == header_length + count * row_width + 1, "DBF byte extent")
    require(
        sum(sizes.values()) == readback["total_expected_file_bytes"] == 159822559,
        "Total proposed transfer bytes",
    )
    require(sum(sizes[x] for x in config["stage_one"]) == 52513359, "First-phase bytes")
    with (
        BASE
        / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"
        / "source_anchor_inventory.csv"
    ).open(encoding="utf-8-sig", newline="") as handle:
        anchors = list(csv.DictReader(handle))
    with (
        BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe/record_memberships.csv"
    ).open(encoding="utf-8-sig", newline="") as handle:
        calendar = list(csv.DictReader(handle))
    support = json.loads((path / "date_support.json").read_bytes())
    for row in support:
        end = row["candidate_native_upper_date_not_verified_coverage"]
        relevant = [r for r in anchors if r["prediction_timestamp_utc"][:10] <= end]
        eligible = [r for r in relevant if r["primary_eligible"] == "True"]
        require(
            len(relevant) == row["Mersin_source_anchors_before_or_on"]
            and len(eligible) == row["primary_eligible_Mersin_anchors_before_or_on"],
            "Source-date planning count",
        )
        for cohort, field in [
            ("four_province", "four_province_calendar_rows_before_or_on"),
            ("separate_Mersin", "separate_Mersin_calendar_rows_before_or_on"),
        ]:
            require(
                sum(
                    r["cohort"] == cohort and r["prediction_timestamp_utc"][:10] <= end
                    for r in calendar
                )
                == row[field],
                "Calendar-date planning count",
            )
    require(
        [r["primary_eligible_Mersin_anchors_before_or_on"] for r in support] == [51, 52],
        "Date-axis ambiguity is preserved",
    )
    require(
        readback["actual_reference_records_opened"] == 0
        and not readback["actual_event_coverage_verified"],
        "No event acceptance from metadata",
    )
    require(
        readback["published_date_shift_days"] == -1
        and not readback["published_date_shift_applied_to_project"],
        "No silent date shift",
    )
    out = (
        BASE
        / "mesogeos_reference_preparation_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "metadata_and_scope_proposal_readback_passed_no_reference_acceptance",
        "analysis_date": "2026-11-25",
        "preparation_receipt_sha256": sha(path / "readback.json"),
        "checked_input_files": len(readback["input_sha256"]),
        "schema_fields": 34,
        "declared_source_entries_not_fire_count": count,
        "date_support_values_checked": 8,
        "records_opened_from_new_event_source": 0,
        "actual_event_coverage_verified": False,
        "reference_pilot_executed": False,
        "new_training_or_target_labels": False,
        "final_merge": False,
        "auditor_sha256": sha(Path(__file__)),
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
