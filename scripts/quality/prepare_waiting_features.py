"""Offline full training feature readback before institutional replies; no label admission."""

import json
import socket
from datetime import UTC, datetime

import pandas as pd
from prepare_dataset import ROOT, candidate_report, index_references, new_directory, sha

from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month, landscape
from wildfire_risk_prediction.feature_readiness import inspect_day

PARENT = "outputs/reports/dataset/candidate_audit_v1/20261014T202202Z_ba43b54a/readback.json"
PARENT_SHA = "7e20556fcdf4aa90e32ce98605ebe57f9d81f4c839a0a6cb2a946a1a9df0fa12"
STATIC = "data/interim/landscape/v1/grid_static.csv"
GRID = "data/interim/grid_aoi_parts.geojson"


def run():
    print("FEATURE AUDIT START", flush=True)

    def deny(*args, **kwargs):
        raise RuntimeError("Offline waiting-point feature audit")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    started = datetime.now(UTC)
    join.require(sha(ROOT / PARENT) == PARENT_SHA, "Pinned candidate audit")
    parent = json.loads((ROOT / PARENT).read_text(encoding="utf-8"))
    refs, _ = index_references(parent["source_index"], parent["source_index_sha256"])
    print("FEATURE AUDIT INDEX", len(refs), flush=True)
    join.require(batch.candidate_inventory(refs)["candidate_calendar_complete"], "72 months")
    pins = {PARENT: PARENT_SHA, parent["source_index"]: parent["source_index_sha256"]}
    reports = [candidate_report(ref) for ref in refs]
    for ref, report in zip(refs, reports, strict=True):
        for name, expected in {ref["path"]: ref["sha256"], **report["inputs_sha256"]}.items():
            join.require(name not in pins or pins[name] == expected, "Consistent source hash")
            pins[name] = expected
    for name in (
        "scripts/quality/prepare_waiting_features.py",
        "src/wildfire_risk_prediction/feature_readiness.py",
    ):
        pins[name] = sha(ROOT / name)
    for ordinal, (name, expected) in enumerate(pins.items(), 1):
        join.require(sha(ROOT / name) == expected, "Retained source identity changed")
        if ordinal % 500 == 0:
            print("FEATURE SOURCE HASH", ordinal, "/", len(pins), flush=True)
    ids = sorted(
        f["properties"]["grid_id"]
        for f in json.loads((ROOT / GRID).read_text(encoding="utf-8"))["features"]
    )
    static = landscape.validate_cover(pd.read_csv(ROOT / STATIC, float_precision="round_trip"), ids)
    folder = new_directory("waiting_features_v1")
    daily, file_index = [], []
    try:
        for ref, report in zip(refs, reports, strict=True):
            month_folder = (ROOT / ref["path"]).parent
            month_manifest = month_folder / "month_manifest.json"
            join.require(sha(month_manifest) == ref["manifest_sha256"], "Month identity")
            manifest = json.loads(month_manifest.read_text(encoding="utf-8"))
            parts_path = month_folder / "parts/manifest.json"
            join.require(sha(parts_path) == manifest["parts_manifest_sha256"], "Parts identity")
            pins[month_manifest.relative_to(ROOT).as_posix()] = ref["manifest_sha256"]
            pins[parts_path.relative_to(ROOT).as_posix()] = manifest["parts_manifest_sha256"]
            parts_manifest = json.loads(parts_path.read_text(encoding="utf-8"))
            missing = dict.fromkeys(join.feature_names(), 0)
            for entry, (day, features, qa) in zip(
                parts_manifest["days"],
                feature_month.iter_month(
                    month_folder, expected_manifest_sha256=ref["manifest_sha256"], grid_ids=ids
                ),
                strict=True,
            ):
                result = inspect_day(features, qa, ids, day, static)
                join.require(
                    result["missing_by_feature"] == entry["missing_by_feature"],
                    "Stored daily missingness",
                )
                daily.append(result)
                for field, count in result["missing_by_feature"].items():
                    missing[field] += count
                for kind, artifact in entry["artifacts"].items():
                    file_index.append(
                        {
                            "day": day,
                            "kind": kind,
                            "path": (month_folder / "parts" / artifact["path"])
                            .relative_to(ROOT)
                            .as_posix(),
                            "sha256": artifact["sha256"],
                            "bytes": artifact["bytes"],
                        }
                    )
            join.require(missing == report["missing_by_feature"], "Stored monthly missingness")
            print("FEATURE READBACK", ref["month"], "days", len(daily), flush=True)
        join.require(len(daily) == 2191 and len(file_index) == 4382, "Full training calendar")
        for name, expected in pins.items():
            join.require(sha(ROOT / name) == expected, "Metadata/source changed during readback")
        family_counts = [sum(d["joint_missing_family_counts"][i] for d in daily) for i in range(32)]
        summary = {
            "status": "training_feature_preparation_readback_passed",
            "started_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(UTC).isoformat(),
            "months": 72,
            "days": len(daily),
            "grid_count": len(ids),
            "rows": sum(d["rows"] for d in daily),
            "feature_columns": join.feature_names(),
            "daily_files_content_hash_verified": len(file_index),
            "daily_file_bytes_read": sum(f["bytes"] for f in file_index),
            "complete_27_feature_rows": family_counts[0],
            "joint_missing_family_counts": family_counts,
            "missing_family_bit_order": daily[0]["missing_family_bit_order"],
            "missing_by_feature": {
                f: sum(d["missing_by_feature"][f] for d in daily) for f in join.feature_names()
            },
            "weather_profile_counts": {
                p: sum(d["weather_profile_counts"][p] for d in daily)
                for p in ("primary", "sensitivity90", "observed")
            },
            "publication_availability_verified": False,
            "historical_availability_interpretation": "retrospective_only_not_operational",
            "eligible_labeled_rows": None,
            "scientific_acceptance_granted": False,
            "fresh_final_five_part_review": False,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "labels_created": False,
            "final_merge_executed": False,
            "final_test_accessed": False,
            "validation_data_accessed": False,
            "new_imputation_applied": False,
            "network_requests": 0,
        }
        daily_rows = [
            {
                "day": d["day"],
                "rows": d["rows"],
                "complete_27_feature_rows": d["complete_27_feature_rows"],
                **d["weather_profile_counts"],
                **{
                    f"missing_mask_{i:02d}": n
                    for i, n in enumerate(d["joint_missing_family_counts"])
                },
            }
            for d in daily
        ]
        pd.DataFrame(daily_rows).to_csv(folder / "daily_quality.csv", index=False)
        pd.DataFrame(file_index).to_csv(folder / "verified_daily_files.csv", index=False)
        (folder / "input_manifest.json").write_text(
            json.dumps(pins, indent=2) + "\n", encoding="utf-8"
        )
        artifacts = {p.name: sha(p) for p in folder.iterdir() if p.is_file()}
        summary["artifact_sha256"] = artifacts
        report_path = folder / "readback.json"
        report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        for name, expected in artifacts.items():
            join.require(sha(folder / name) == expected, "Artifact readback")
        join.require(json.loads(report_path.read_text()) == summary, "Report readback")
        (folder / "completion_readback.json").write_text(
            json.dumps(
                {
                    "status": "feature_preparation_outputs_verified",
                    "report_sha256": sha(report_path),
                    "artifact_sha256": artifacts,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("FEATURE REPORT", folder.relative_to(ROOT).as_posix(), flush=True)
        return folder
    except BaseException as exc:
        (folder / "failure.json").write_text(
            json.dumps(
                {
                    "status": "incomplete_outputs_retained",
                    "error_type": type(exc).__name__,
                    "completed_days": len(daily),
                    "scientific_acceptance_granted": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    run()
