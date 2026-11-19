"""Prepare one exact cached-audit pair for the first outcome-independent source review."""

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from prepare_marmaris_native_pair import module, write

from wildfire_risk_prediction.cmr_identity import assess, producer_name
from wildfire_risk_prediction.core_transfer import check_file, digest, source_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "source_sample_first_pass_v1/20261119T133541Z_a7fafe0c/readback.json"
PARENT_SHA = "36d209d4c5c6b6c9b656c5c57f49b22a2f9736c65f9b150494f24c136c51faa3"
TEMPLATE = BASE / "observation_core_transfer_v1/20261015T104255Z_9750c1c4/native_plan.json"
TEMPLATE_SHA = "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-cache", type=Path)
    args = parser.parse_args()
    cache_source = args.metadata_cache.resolve() if args.metadata_cache else None
    if cache_source is not None:
        require(
            cache_source.is_relative_to(BASE / "observation_core_transfer_v1"),
            "Project-local public metadata cache",
        )
    require(
        digest(PARENT) == PARENT_SHA and digest(TEMPLATE) == TEMPLATE_SHA, "Pinned source choice"
    )
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    require(
        parent["archive_row"] == "WF1206"
        and parent["sample_id"] == "SNPP:2018175.2306"
        and parent["fire_quality_or_land_counts_used_for_choice"] is False,
        "Previously frozen first review unit and pass",
    )
    sample_id = parent["sample_id"]
    sources = parent["historical_source_audit"]["sources"]
    require(set(sources) == {"fire", "geolocation"}, "Exactly two historical native sources")
    inspector = module("sample_source_identity", "scripts/firms/inspect_l2_observation_sample.py")
    refs = []
    for role, source in sources.items():
        filename = Path(source["path"]).name
        sensor, parsed_role, _, stamp = inspector.product_identity(filename)
        require(
            sensor == "SNPP" and parsed_role == role and 2018 <= stamp.year <= 2022,
            "Fit-role identity",
        )
        refs.append(
            {
                "source_id": sample_id + "|" + role,
                "source_day": stamp.date().isoformat(),
                "sample_id": sample_id,
                "role": role,
                "filename": filename,
                "bytes": source["bytes"],
                "sha256": source["sha256"],
            }
        )
    found = {}
    for path in (ROOT / "data/raw").rglob("*.nc"):
        for ref in refs:
            if path.name == ref["filename"]:
                check_file(path, ref)
                found[path.relative_to(ROOT).as_posix()] = ref["sha256"]
    runner = module("source_sample_runner", "scripts/firms/run_observation_core_pair.py")
    plan, _ = runner.load_plan(TEMPLATE)
    out = (
        BASE
        / "observation_core_transfer_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "responses").mkdir()
    catalog = module("source_sample_catalog", "scripts/firms/check_observation_core_catalogue.py")
    members = []
    network_requests = 0
    for number, ref in enumerate(refs):
        if cache_source is not None:
            for suffix in (".json", "_receipt.json"):
                name = f"{number:03d}" + suffix
                shutil.copyfile(cache_source / "responses" / name, out / "responses" / name)
        _, items, _, calls = catalog.fetch_batch(out, number, [ref])
        network_requests += calls
        checked = assess(ref, items)
        require(
            checked["metadata_checks_passed"] and len(checked["metadata_data_urls"]) == 1,
            "Exact current public source identity",
        )
        item = next(item for item in items if producer_name(item) == ref["filename"])
        archive = item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"][0]
        member = {
            **ref,
            "product": checked["product"],
            "url": checked["metadata_data_urls"][0],
            "provider_checksum": archive.get("Checksum"),
            "metadata": item["umm"],
        }
        source_url(member)
        members.append(member)
    amount = sum(member["bytes"] for member in members)
    require(
        amount == 175717496 and shutil.disk_usage(ROOT).free > 20_000_000_000 + amount,
        "Pair size and local disk reserve",
    )
    pair = {
        "sample_id": sample_id,
        "source_day": refs[0]["source_day"],
        "bytes": amount,
        "sources": members,
    }
    plan["all_pairs_inventory_only"] = [pair]
    plan["first_pair"], plan["first_pair_bytes"] = sample_id, amount
    plan["selection_parent_sha256"] = PARENT_SHA
    plan["selection_reason"] = (
        "First metadata-transportable frozen Mersin source row WF1206; "
        "earliest saved cell scan after both clock hypotheses, not selected on fire or QA"
    )
    for path in [PARENT, TEMPLATE, Path(__file__), *sorted((out / "responses").glob("*.json"))]:
        plan["input_sha256"][path.relative_to(ROOT).as_posix()] = digest(path)
    write(out / "native_plan.json", plan)
    result = {
        "status": "one_source_sample_pair_prepared_not_downloaded",
        "archive_row": "WF1206",
        "sample_id": sample_id,
        "raw_bytes_to_download": amount,
        "raw_files_downloaded": 0,
        "existing_cache_matches": found,
        "public_metadata_responses": 2,
        "metadata_network_requests": network_requests,
        "public_metadata_cache_reused": cache_source is not None,
        "point_inside_native_scan_verified": False,
        "source_clock_standard_verified": False,
        "source_coordinate_start_role_verified": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "cloud_jobs_started": 0,
        "artifact_sha256": {"native_plan.json": digest(out / "native_plan.json")},
    }
    write(out / "readback.json", result)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    checked_plan, checked_pair = runner.load_plan(out / "native_plan.json")
    require(
        checked_pair == pair and len(checked_plan["all_pairs_inventory_only"]) == 1,
        "Normal bounded runner entry point",
    )
    print((out / "native_plan.json").relative_to(ROOT).as_posix())
    print("plan_sha256", digest(out / "native_plan.json"))
    print("PASS source-sampled one-pair plan; raw download requires private interactive login")


if __name__ == "__main__":
    main()
