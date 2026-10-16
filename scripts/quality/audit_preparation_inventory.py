"""Inventory bound metadata and current file presence; never approve labels or final assembly."""

import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import feature_names, require, utc_times
from wildfire_risk_prediction.final_merge_gate import require_final_merge_approval
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/subgroup_report_v1/20261016T134755Z_0c95a351")
RELEASE = Path("outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de")
CANDIDATE = Path(
    "outputs/reports/dataset/candidate_audit_v1/20261014T202202Z_ba43b54a/readback.json"
)


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline preparation inventory")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def local(name):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained regular inventory file",
        )
        return path

    def retained(name, expected=None):
        path = local(name)
        actual = digest(path)
        require(expected is None or expected == actual, "Inventory evidence changed")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(
        PARENT / "readback.json", "df7fb636008606108342dc0fafe8fe164bbc96f1b940ae915ad59008a19893f7"
    )
    require(
        read(PARENT / "completion_readback.json")["report_sha256"]
        == pins[(PARENT / "readback.json").as_posix()],
        "Parent report closure",
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name, sha in read(PARENT / "input_manifest.json").items():
        retained(name, sha)

    release = read(
        RELEASE / "readback.json",
        "f494acb939d84024d5399139ea4e0fc6e45327c45114dfca2e441a6218d612ef",
    )
    require(
        read(RELEASE / "completion_readback.json")["report_sha256"]
        == pins[(RELEASE / "readback.json").as_posix()],
        "Inspection report closure",
    )
    for name, sha in release["artifact_sha256"].items():
        retained(RELEASE / name, sha)
    candidate = read(CANDIDATE, "7e20556fcdf4aa90e32ce98605ebe57f9d81f4c839a0a6cb2a946a1a9df0fa12")
    retained(candidate["source_index"], candidate["source_index_sha256"])
    index = pd.read_csv(ROOT / RELEASE / "full_candidate_parts_index.csv")
    days = pd.date_range("2018-01-01", "2023-12-31", freq="D").strftime("%Y-%m-%d").tolist()
    months = [f"{year}-{month:02d}" for year in range(2018, 2024) for month in range(1, 13)]
    require(
        index.day.is_unique
        and sorted(index.day) == days
        and index.month.eq(index.day.str[:7]).all()
        and index.rows.eq(2899).all()
        and int(index.rows.sum()) == 6351709
        and candidate["verified_candidate_months"] == 72
        and candidate["candidate_calendar_complete"] is True,
        "Complete unchanged candidate calendar metadata",
    )
    require(
        sorted(ref["month"] for ref in candidate["reports"]) == months,
        "Exactly 72 month references",
    )
    missing = dict.fromkeys(feature_names(), 0)
    expected_parts = {}
    for ref in candidate["reports"]:
        report = read(ref["path"], ref["sha256"])
        folder = Path(ref["path"]).parent
        manifest = read(folder / "month_manifest.json", ref["manifest_sha256"])
        parts = read(folder / "parts/manifest.json", manifest["parts_manifest_sha256"])
        require(report["month"] == manifest["month"] == ref["month"], "Consistent month identity")
        require(
            ref["rows"] == report["rows"] == manifest["rows"] == len(parts["days"]) * 2899,
            "Monthly metadata row conservation",
        )
        require(
            report["labels_created"] is False and report["model_ready"] is False, "Candidate only"
        )
        for entry in parts["days"]:
            day = entry["day"]
            require(
                day in days and day.startswith(ref["month"] + "-") and entry["rows"] == 2899,
                "Training daily part metadata",
            )
            require(set(entry["missing_by_feature"]) == set(missing), "Same 27 feature schema")
            for feature, count in entry["missing_by_feature"].items():
                require(type(count) is int and 0 <= count <= 2899, "Bound missing count")
                missing[feature] += count
            for kind in ("features", "provenance"):
                artifact = entry["artifacts"][kind]
                require(
                    artifact["path"] == f"{ref['month']}/{day}_{kind}.csv"
                    and (day, kind) not in expected_parts,
                    "Unique canonical daily part",
                )
                expected_parts[(day, kind)] = (
                    (folder / "parts" / artifact["path"]).as_posix(),
                    artifact["sha256"],
                    artifact["bytes"],
                )
    require(len(expected_parts) == 4382, "Both daily tables for 2191 days")
    checked_bytes = 0
    for row in index.to_dict("records"):
        for kind in ("features", "provenance"):
            name, sha, size = expected_parts[(row["day"], kind)]
            require(
                row[kind + "_path"] == name and row[kind + "_sha256"] == sha,
                "Index and part manifest agree",
            )
            require(local(name).stat().st_size == size, "Current daily file presence/size")
            checked_bytes += size

    quality = read(
        "outputs/reports/dataset/quality_profile_v1/20261014T144247Z_851417d0/readback.json",
        "ecd617369a1a24237059361b53c95edb8fe58a49d8bb95ea61e8f20a8c649911",
    )
    require(
        {item["feature"]: item["missing_cell_days"] for item in quality["features"]} == missing,
        "Bound daily missing counts reconcile with published profile",
    )
    water = read(
        "outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd/readback.json",
        "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae",
    )
    reference = read(
        "outputs/reports/dataset/reference_intake_v1/20261015T195625Z_e277865f/readback.json",
        "1f6fef07264e955725793e0bc8da4ba817741d0a13b4478981580f9c7fb8c0e1",
    )
    preflight = read(
        RELEASE / "parts_preflight.json", release["artifact_sha256"]["parts_preflight.json"]
    )
    policy = read("configs/final_merge_review_v1.json")
    require(
        water["cells_total"] == 2899
        and water["cells_excluded_map_water"] == 10
        and water["cells_retained_for_further_eligibility_review"] == 2889,
        "Recorded map-water decision, not final habitat acceptance",
    )
    require(
        reference["institutional_incident_rows"] == reference["matching_ready_context_records"] == 0
        and reference["context_records_held_for_review"] == 12,
        "Existing reference snapshot, not mailbox access",
    )
    require(
        preflight["scientific_protocol_status"] == "not_accepted"
        and policy["final_merge_authorized"] is False,
        "No final acceptance",
    )
    try:
        require_final_merge_approval(preflight, {})
    except PermissionError:
        gate_rejected = True
    else:
        gate_rejected = False
    require(gate_rejected, "Inspection evidence is not a final review/approval")
    label_gate = specification()
    require(
        label_gate["negative_label_permitted"] is False and label_gate["model_ready"] is False,
        "Current closed label gate",
    )
    preview = pd.read_csv(ROOT / RELEASE / "candidate_inspection_preview_400.csv")
    require(
        len(preview) == 400
        and preview.target.isna().all()
        and set(feature_names()) <= set(preview),
        "Same unlabelled inspection preview",
    )
    require(
        utc_times(preview.prediction_timestamp_utc).dt.year.between(2018, 2023).all(),
        "Preview training only",
    )
    retained(Path(__file__).relative_to(ROOT))

    facts = {
        "inventory_kind": "preparation_evidence_not_final_review",
        "candidate_months": 72,
        "candidate_days": 2191,
        "candidate_grid_cells": 2899,
        "candidate_cell_days": 6351709,
        "candidate_features": 27,
        "previous_full_data_audit_utc": candidate["checked_at_utc"],
        "current_daily_file_presence_size_checks": 4382,
        "current_daily_file_bytes_statted_not_read": checked_bytes,
        "daily_feature_provenance_contents_rehashed_now": False,
        "missing_counts_basis": "bound_daily_manifests_not_fresh_feature_values",
        "complete_case_rows": None,
        "final_eligible_rows": None,
        "map_water_excluded_cells": 10,
        "further_habitat_review_cells": 2889,
        "observation_rows_previously_audited": release["fresh_observation_audit"]["rows_reread"],
        "observation_csvs_reread_now": False,
        "missing_source_days": preflight["parts"]["observation"]["missing_source_days"],
        "missing_product_rows_previously_audited": release["fresh_observation_audit"][
            "missing_product_rows"
        ],
        "preview_rows_read_now": 400,
        "preview_assigned_targets": 0,
        "reference_snapshot_context_records": reference["public_context_records"],
        "reference_snapshot_matching_ready_records": reference["matching_ready_context_records"],
        "private_mailbox_checked": False,
        "new_correspondence_verified": False,
        "inspection_preflight_rejected_by_final_gate": gate_rejected,
        "user_final_approval_receipt_supplied": False,
        "model_ready": False,
        "labelled_training_dataset_ready": False,
        "final_merge_performed": False,
        "network_requests": 0,
        "cloud_jobs_started": 0,
        "validation_or_final_data_accessed": False,
    }
    work = [
        {
            "item": item["gate"],
            "stage": "scientific_protocol",
            "status": "open",
            "required_evidence": item["required"],
            "depends_on": "source_and_case_evidence",
            "independent_preparation_possible": True,
        }
        for item in candidate["release_blockers"]
    ]
    work.extend(
        [
            {
                "item": "independent_reference_validation",
                "stage": "scientific_protocol",
                "status": "no_matching_ready_reference_rows_in_snapshot",
                "required_evidence": (
                    "Usable incident/coverage evidence and source review; "
                    "institutional reply is one route"
                ),
                "depends_on": "usable_reference_evidence",
                "independent_preparation_possible": True,
            },
            {
                "item": "binary_target_parts",
                "stage": "training_dataset",
                "status": "not_admitted_not_produced",
                "required_evidence": (
                    "Accepted source/event/first-cell/habitat/negative/boundary protocol"
                ),
                "depends_on": "scientific_protocol",
                "independent_preparation_possible": False,
            },
            {
                "item": "fresh_final_part_review",
                "stage": "training_dataset",
                "status": "not_performed_for_labelled_dataset",
                "required_evidence": (
                    "Current five-part hashes/keys/schema/missingness/time/split "
                    "and scientific checks"
                ),
                "depends_on": "binary_target_parts",
                "independent_preparation_possible": False,
            },
            {
                "item": "explicit_user_final_merge_approval",
                "stage": "training_dataset",
                "status": "not_requested_no_final_review",
                "required_evidence": "Explicit user approval bound to fresh final review SHA-256",
                "depends_on": "fresh_final_part_review",
                "independent_preparation_possible": False,
            },
            {
                "item": "final_merger_implementation_and_execution",
                "stage": "training_dataset",
                "status": "future_implementation_execution_requires_approval",
                "required_evidence": (
                    "Current file verification plus existing final_merge_gate before execution"
                ),
                "depends_on": "explicit_user_final_merge_approval",
                "independent_preparation_possible": True,
            },
            {
                "item": "real_training_and_calibration_entrypoint",
                "stage": "model_development",
                "status": "technical_preparations_only_no_real_trainer",
                "required_evidence": (
                    "Accepted dataset, frozen fit/calibration roles "
                    "and selected experiment policies"
                ),
                "depends_on": "accepted_labelled_dataset",
                "independent_preparation_possible": True,
            },
            {
                "item": "validation_2024_assembly",
                "stage": "model_development",
                "status": "not_accepted_in_reviewed_evidence",
                "required_evidence": (
                    "2024 vegetation/observation/target preparation under frozen policy"
                ),
                "depends_on": "frozen_scientific_protocol",
                "independent_preparation_possible": True,
            },
            {
                "item": "final_2025_evaluation",
                "stage": "final_evaluation",
                "status": "sealed",
                "required_evidence": (
                    "Frozen model/data/threshold/calibration versions "
                    "before single final evaluation"
                ),
                "depends_on": "frozen_model_and_protocol",
                "independent_preparation_possible": False,
            },
            {
                "item": "operational_forecast_product",
                "stage": "later_product",
                "status": "not_implemented_retrospective_weather_only",
                "required_evidence": (
                    "Issue-time-valid forecast inputs and separately validated service"
                ),
                "depends_on": "validated_research_model_and_operational_data",
                "independent_preparation_possible": True,
            },
        ]
    )
    out = (
        ROOT
        / "outputs/reports/dataset/preparation_inventory_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save("preparation_facts.json", facts)
    pd.DataFrame(work).to_csv(out / "open_work.csv", index=False)
    pd.DataFrame(
        [
            {
                "feature": name,
                "missing_cell_days": count,
                "denominator_cell_days": 6351709,
                "missing_fraction": count / 6351709,
                "basis": "bound_daily_manifest_counts",
            }
            for name, count in missing.items()
        ]
    ).to_csv(out / "feature_missingness_inventory.csv", index=False)
    save("label_gate_snapshot.json", label_gate)
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()),
        "Final inventory metadata closure",
    )
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "inventory_metadata_and_presence_verified_not_dataset_acceptance",
            "input_file_count": len(pins),
            "daily_files_presence_size_checked": 4382,
            "large_daily_file_contents_rehashed": False,
            "open_work_items": len(work),
            "global_completion_percentage": None,
            "final_merge_performed": False,
            "model_ready": False,
            "network_requests": 0,
            "cloud_jobs_started": 0,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save(
        "completion_readback.json",
        {"status": "passed_inventory_only", "report_sha256": digest(out / "readback.json")},
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
