"""Prepare one historical Marmaris pair with current public metadata; never download raw data."""

import csv
import hashlib
import importlib.util
import io
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.cmr_identity import assess, producer_name
from wildfire_risk_prediction.core_transfer import check_file, digest, source_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
COMPACT = ROOT / "outputs/gcp_delivery/2026-10-14/compact/products/month/2022-06/payload.zip"
COMPACT_SHA = "247af45e21e8b1d94137730ab2567cdf120cddc8635393ac663a1329c2a243c4"
CONTEXT = BASE / "marmaris_published_marker_v1/20261119T124316Z_6993b935/readback.json"
CONTEXT_SHA = "6672e96bb52dbc65d385b9debd00675528f868086b6eb0df2992feb6a438301b"
TEMPLATE = BASE / "observation_core_transfer_v1/20261015T104255Z_9750c1c4/native_plan.json"
TEMPLATE_SHA = "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc"
SAMPLE = "N20:2022172.2318"


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write(path, value):
    require(not path.exists(), "No evidence overwrite")
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == value, "JSON readback")


def main():
    require(digest(COMPACT) == COMPACT_SHA and digest(CONTEXT) == CONTEXT_SHA, "Marmaris lineage")
    context = json.loads(CONTEXT.read_text())
    require(
        context["source_case_id"] == "marmaris_2022"
        and context["L_memberships_created"] == 0
        and context["catalog_context_by_radius_m"]["2000"]["first_same_window_utc"]
        == "2022-06-21T23:22:00+00:00",
        "Published-symbol context, not accepted source position",
    )
    context_csv = CONTEXT.parent / "local_catalog_context.csv"
    require(
        digest(context_csv) == context["artifact_sha256"][context_csv.name],
        "Pinned local catalog centers",
    )
    first_time = datetime(2022, 6, 21, 23, 22, tzinfo=UTC)
    with context_csv.open(encoding="utf-8", newline="") as stream:
        centers = [
            row
            for row in csv.DictReader(stream)
            if datetime.fromisoformat(row["detection_timestamp_utc"]) == first_time
            and float(row["distance_to_published_symbol_m"]) <= 2000
        ]
    require(
        len(centers) == 5
        and all(row["source_sensor"] == "N20" and row["target"] == "" for row in centers),
        "Five unlabelled centers in the first local pass",
    )
    runner = module("marmaris_native_runner", "scripts/firms/run_observation_core_pair.py")
    require(digest(TEMPLATE) == TEMPLATE_SHA, "Reviewed bounded runner template")
    plan, _ = runner.load_plan(TEMPLATE)
    with zipfile.ZipFile(COMPACT) as month:
        with zipfile.ZipFile(io.BytesIO(month.read("2022-06-21.zip"))) as daily:
            raw = daily.read("report.json")
    require(
        hashlib.sha256(raw).hexdigest()
        == "631c3df9686e07678e18c14f94954d719decf9fa8ee7081776c8dfb6536f39f0",
        "Accepted compact day report",
    )
    reports = json.loads(raw)
    entries = [r for r in reports["sources"] if r["sample_id"] == SAMPLE]
    require(len(entries) == 1, "One historical source audit")
    historical = entries[0]["audit"]["sources"]
    require(set(historical) == {"fire", "geolocation"}, "Exact native source roles")
    require(
        all(
            datetime.fromisoformat(record["cmr_interval"]["BeginningDateTime"])
            <= first_time
            < datetime.fromisoformat(record["cmr_interval"]["EndingDateTime"])
            for record in historical.values()
        ),
        "23:22 catalog centers lie inside the 23:18 native granule",
    )
    references = [
        {
            "source_id": SAMPLE + "|" + role,
            "source_day": "2022-06-21",
            "sample_id": SAMPLE,
            "role": role,
            "filename": Path(record["path"]).name,
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }
        for role, record in historical.items()
    ]
    require(len(references) == 2, "Exactly one fire/geolocation pair")
    cache_matches = {}
    for path in (ROOT / "data/raw").rglob("*.nc"):
        for ref in references:
            if path.name == ref["filename"]:
                check_file(path, ref)
                cache_matches[path.relative_to(ROOT).as_posix()] = ref["sha256"]
    require(not cache_matches, "Local pair exists; use existing bytes rather than request download")
    out = (
        BASE
        / "observation_core_transfer_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "responses").mkdir()
    catalog = module("marmaris_public_catalog", "scripts/firms/check_observation_core_catalogue.py")
    members = []
    for number, reference in enumerate(references):
        _, items, _, _ = catalog.fetch_batch(out, number, [reference])
        check = assess(reference, items)
        require(
            check["metadata_checks_passed"] and len(check["metadata_data_urls"]) == 1,
            "Current exact source identity",
        )
        item = next(i for i in items if producer_name(i) == reference["filename"])
        archive = item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"][0]
        source = {
            **reference,
            "product": check["product"],
            "url": check["metadata_data_urls"][0],
            "provider_checksum": archive.get("Checksum"),
            "metadata": item["umm"],
        }
        source_url(source)
        members.append(source)
    amount = sum(r["bytes"] for r in members)
    require(
        amount == 175759551 and shutil.disk_usage(ROOT).free > 20_000_000_000 + amount,
        "Pair size and reserve",
    )
    pair = {"sample_id": SAMPLE, "source_day": "2022-06-21", "bytes": amount, "sources": members}
    plan["all_pairs_inventory_only"] = [pair]
    plan["first_pair"], plan["first_pair_bytes"] = SAMPLE, amount
    plan["selection_parent_sha256"] = CONTEXT_SHA
    plan["selection_reason"] = (
        "First local Marmaris pass: five centers, native identity/quality review only; "
        "source multi-origin ambiguity remains open"
    )
    plan["selection_catalog_ids"] = sorted(row["detection_id"] for row in centers)
    for path in [
        COMPACT,
        CONTEXT,
        context_csv,
        TEMPLATE,
        Path(__file__),
        *sorted((out / "responses").glob("*.json")),
    ]:
        plan["input_sha256"][path.relative_to(ROOT).as_posix()] = digest(path)
    target = out / "native_plan.json"
    write(target, plan)
    report = {
        "status": "single_marmaris_pair_prepared_not_downloaded",
        "sample_id": SAMPLE,
        "raw_bytes_to_download": amount,
        "raw_files_downloaded": 0,
        "cache_match_count": len(cache_matches),
        "public_metadata_responses": 2,
        "cloud_jobs_started": 0,
        "labels_created": False,
        "artifact_sha256": {target.name: digest(target)},
    }
    write(out / "readback.json", report)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    checked, checked_pair = runner.load_plan(target)
    require(
        len(checked["all_pairs_inventory_only"]) == 1 and checked_pair == pair, "Normal runner load"
    )
    print(target.relative_to(ROOT))
    print("plan_sha256", digest(target))
    print("PASS one_pair_metadata_and_limits; raw download requires private interactive login")


if __name__ == "__main__":
    main()
