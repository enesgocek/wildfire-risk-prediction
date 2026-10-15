"""Build a sequential cache/time budget and exact source plan; offline, no download."""

import hashlib
import importlib.util
import json
import shutil
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.cmr_identity import assess, identity, producer_name
from wildfire_risk_prediction.core_transfer import source_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "outputs/reports/dataset/observation_core_catalogue_v1/20261014T235401Z_f3cdca96"
PARENT_SHA = "251bbc38b26344b23d959312f59d9d75d708437103b1056db2f860165d164b39"
EXPANSION = ROOT / "outputs/reports/dataset/observation_expansion_v1/20261014T233502Z_81275155"
PROTECTED = (
    ROOT / "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline core transfer preparation")


def run():
    pins = {}

    def retain(path, expected=None):
        require(
            path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Project input",
        )
        value = sha(path)
        require(expected is None or value == expected, "Transfer preparation input hash")
        pins[path.relative_to(ROOT).as_posix()] = value
        return path

    parent = json.loads(retain(PARENT / "readback.json", PARENT_SHA).read_text(encoding="utf-8"))
    require(
        parent["status_counts"] == {"exact_identity_metadata_match": 584},
        "Full exact metadata parent",
    )
    require(
        parent["negative_label_permitted"] is False
        and parent["daily_observation_status"] == "unknown",
        "Closed parent",
    )
    for name, expected in parent["artifact_sha256"].items():
        retain(PARENT / name, expected)
    for name in ("native_source_queue.csv", "plan_source_links.csv", "calendar_core.csv"):
        retain(
            EXPANSION / name,
            parent["input_sha256"][(EXPANSION / name).relative_to(ROOT).as_posix()],
        )
    queue = pd.read_csv(EXPANSION / "native_source_queue.csv")
    links = pd.read_csv(EXPANSION / "plan_source_links.csv")
    wanted = set(links.loc[links.selection_plan.eq("calendar_core"), "source_id"])
    sources = queue.loc[queue.source_id.isin(wanted)].sort_values(
        ["source_day", "sample_id", "role"]
    )
    require(len(sources) == 584 and sources.source_id.is_unique, "Exact core source scope")
    metadata = {}
    for path in sorted((PARENT / "responses").glob("*.json")):
        if "_receipt" not in path.name:
            for item in json.loads(path.read_text(encoding="utf-8"))["items"]:
                name = producer_name(item)
                require(name not in metadata, "Unique current native identity")
                metadata[name] = item
    pairs, schedule = [], []
    for sample, group in sources.groupby("sample_id", sort=False):
        require(len(group) == 2 and set(group.role) == {"fire", "geolocation"}, "Exact pair roles")
        members = []
        for reference in group.to_dict("records"):
            product, _, _ = identity(reference)
            item = metadata[reference["filename"]]
            checked = assess(reference, [item])
            require(
                checked["metadata_checks_passed"] and len(checked["metadata_data_urls"]) == 1,
                "Exact current source",
            )
            entry = item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"][0]
            source = {
                **{
                    k: reference[k]
                    for k in (
                        "source_id",
                        "source_day",
                        "sample_id",
                        "role",
                        "filename",
                        "bytes",
                        "sha256",
                    )
                },
                "url": checked["metadata_data_urls"][0],
                "product": product,
                "provider_checksum": entry.get("Checksum"),
                "metadata": item["umm"],
            }
            source_url(source)
            members.append(source)
        amount = sum(x["bytes"] for x in members)
        pairs.append(
            {
                "sample_id": sample,
                "source_day": group.source_day.iloc[0],
                "bytes": amount,
                "sources": members,
            }
        )
        schedule.append(
            {
                "order": len(pairs),
                "sample_id": sample,
                "source_day": group.source_day.iloc[0],
                "raw_bytes": amount,
            }
        )
    require(len(pairs) == 292, "Core pair plan")
    maximum = max(p["bytes"] for p in pairs)
    cache_limit, reserve, runtime = 2_000_000_000, 20_000_000_000, 900
    require(
        maximum < cache_limit and shutil.disk_usage(ROOT).free >= reserve + maximum,
        "Sequential disk budget",
    )
    protected = json.loads(retain(PROTECTED).read_text(encoding="utf-8"))
    for name, expected in protected.items():
        retain(ROOT / name, expected)
    for name in (
        "scripts/quality/prepare_observation_core_transfer.py",
        "scripts/firms/run_observation_core_pair.py",
        "scripts/firms/inspect_l2_observation_sample.py",
        "src/wildfire_risk_prediction/core_transfer.py",
        "src/wildfire_risk_prediction/cmr_identity.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "pyproject.toml",
        "uv.lock",
    ):
        retain(ROOT / name)
    # Exercise the new header reader on one old accepted local witness, outside the core.
    # This is explicitly not a successful download or a new pilot source acceptance.
    timing_path = retain(
        ROOT / "outputs/reports/observation_coverage/observation_timing_2019-01-14.json",
        "e2dd39df16edd27fbc54270ede9a5ab8f8aa5d517770168d501be3a9f1c4d361",
    )
    witness_id = "SNPP:2019014.0042"
    witness = json.loads(timing_path.read_text(encoding="utf-8"))["sources"][witness_id]
    witness_members, witness_directories = [], set()
    for role, source in witness["sources"].items():
        path = retain(ROOT / source["path"], source["sha256"])
        witness_directories.add(path.parent)
        witness_members.append(
            {
                "role": role,
                "filename": path.name,
                "metadata": {"TemporalExtent": {"RangeDateTime": source["cmr_interval"]}},
            }
        )
    require(len(witness_directories) == 1, "Co-located accepted local witness")
    spec = importlib.util.spec_from_file_location(
        "core_probe_headers", ROOT / "scripts/firms/run_observation_core_pair.py"
    )
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    witness_headers = probe.native_headers(
        {"sample_id": witness_id, "sources": witness_members}, witness_directories.pop()
    )
    require(
        witness_headers["orbit_id"] == "SNPP:" + str(witness["orbit_number"]),
        "Old native witness orbit",
    )
    plan = {
        "status": "bounded_one_pair_access_and_header_probe",
        "selection_parent_sha256": PARENT_SHA,
        "execution_scope": "first_chronological_pair_only",
        "all_pairs_inventory_only": pairs,
        "first_pair": pairs[0]["sample_id"],
        "first_pair_bytes": pairs[0]["bytes"],
        "cache_limit_bytes": cache_limit,
        "minimum_free_bytes": reserve,
        "hard_runtime_seconds": runtime,
        "pair_workers": 1,
        "partial_file_policy": "retain_and_stop_no_range_resume_or_overwrite",
        "redirect_policy": "one_exact_cmr_s3_object_in_separate_credential_free_session",
        "raw_eviction_permitted": False,
        "cloud_execution_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "input_sha256": pins,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/observation_core_transfer_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "native_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(schedule).to_csv(out / "pair_inventory.csv", index=False)
    require(
        json.loads((out / "native_plan.json").read_text(encoding="utf-8")) == plan,
        "Plan JSON readback",
    )
    require(
        pd.read_csv(out / "pair_inventory.csv").to_dict("records") == schedule,
        "Inventory CSV readback",
    )
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Plan input closure")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "bounded_probe_preparation_passed",
        "pair_inventory_count": len(pairs),
        "file_inventory_count": len(sources),
        "historical_total_raw_bytes": int(sources.bytes.sum()),
        "maximum_pair_bytes": maximum,
        "first_pair": plan["first_pair"],
        "first_pair_bytes": plan["first_pair_bytes"],
        "free_disk_bytes_at_check": shutil.disk_usage(ROOT).free,
        "cache_limit_bytes": cache_limit,
        "minimum_free_bytes": reserve,
        "hard_runtime_seconds": runtime,
        "redirect_policy": plan["redirect_policy"],
        "native_probe_started": False,
        "existing_local_witness_header_check": {"sample_id": witness_id, **witness_headers},
        "raw_files_downloaded": 0,
        "cloud_jobs_started": 0,
        "labels_created": False,
        "model_ready": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "protected_inputs_verified": len(protected),
        "input_sha256": pins,
        "artifact_sha256": {n: sha(out / n) for n in ("native_plan.json", "pair_inventory.csv")},
        "limits": [
            "One chronological pair is an access/header smoke test, not a representative study",
            "292-pair inventory does not authorize bulk execution",
            "No raw eviction or partial-file overwrite",
        ],
    }
    (out / "readback.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    require(
        json.loads((out / "readback.json").read_text(encoding="utf-8")) == report,
        "Preparation readback",
    )
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(out / "readback.json"),
                "inputs_verified": len(pins),
                "artifacts_verified": len(report["artifact_sha256"]),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Bounded probe plan:", out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
