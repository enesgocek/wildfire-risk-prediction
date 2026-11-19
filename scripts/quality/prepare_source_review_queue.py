"""Prepare seven one-pair plans using public CMR metadata; no raw download or login."""

import json
import shutil
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from prepare_marmaris_native_pair import module, write

from wildfire_risk_prediction.cmr_identity import assess, identity, producer_name
from wildfire_risk_prediction.core_transfer import digest, source_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
META = BASE / "source_queue_metadata_v1/20261119T140541Z_58ea114d/readback.json"
META_SHA = "5980e221bd3d74eff6ad6b17fd17fb11c48fe5e9aa6373eb1aaa30c2f88da04d"
TEMPLATE = BASE / "observation_core_transfer_v1/20261015T104255Z_9750c1c4/native_plan.json"
TEMPLATE_SHA = "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc"


def main():
    require(digest(META) == META_SHA and digest(TEMPLATE) == TEMPLATE_SHA, "Pinned preparation")
    meta = json.loads(META.read_text(encoding="utf-8"))
    require(
        meta["all_ten_source_rows_retained"] is True
        and meta["untransportable_source_rows"] == ["WF1342", "WF1556"]
        and all(digest(ROOT / n) == h for n, h in meta["input_sha256"].items()),
        "Frozen evidence and unchanged sample",
    )
    queue_runner = module("source_queue_runner", "scripts/firms/run_source_review_queue.py")
    runner = queue_runner.runner_module()
    template, _ = runner.load_plan(TEMPLATE)
    out = (
        BASE
        / "source_review_queue_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "responses").mkdir()
    references = []
    for unit in meta["units"]:
        sample = unit["sample_id"]
        day = unit["selected_scan"]["start_utc"][:10]
        for role, source in unit["historical_source_audit"]["sources"].items():
            references.append(
                {
                    "source_id": sample + "|" + role,
                    "source_day": day,
                    "sample_id": sample,
                    "role": role,
                    "filename": Path(source["path"]).name,
                    "bytes": source["bytes"],
                    "sha256": source["sha256"],
                }
            )
    require(len(references) == 14, "Fourteen fixed historical source files")
    # Refuse redundant requests when an identical file is already in the local raw cache.
    names = {r["filename"] for r in references}
    require(
        not any(p.name in names for p in (ROOT / "data/raw/observation_core_v1").rglob("*.nc")),
        "Existing native bytes require offline reuse planning",
    )
    groups = defaultdict(list)
    for reference in references:
        groups[identity(reference)[0]].append(reference)
    catalogue = module("source_public_catalog", "scripts/firms/check_observation_core_catalogue.py")
    members, requests = {}, 0
    for number, product in enumerate(sorted(groups)):
        refs = groups[product]
        require(len(refs) <= 16, "Bounded single-product metadata batch")
        _, items, _, calls = catalogue.fetch_batch(out, number, refs)
        requests += calls
        for ref in refs:
            check = assess(ref, items)
            require(
                check["metadata_checks_passed"] and len(check["metadata_data_urls"]) == 1,
                "Exact current catalogue identity",
            )
            item = next(i for i in items if producer_name(i) == ref["filename"])
            archive = item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"][0]
            member = {
                **ref,
                "product": check["product"],
                "url": check["metadata_data_urls"][0],
                "provider_checksum": archive.get("Checksum"),
                "metadata": item["umm"],
            }
            source_url(member)
            members[ref["source_id"]] = member
    inputs = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in [
            META,
            TEMPLATE,
            Path(__file__),
            ROOT / "scripts/quality/prepare_source_queue_metadata.py",
            ROOT / "scripts/firms/run_source_review_queue.py",
            ROOT / "scripts/firms/run_observation_core_pair.py",
            ROOT / "scripts/firms/check_observation_core_catalogue.py",
            ROOT / "src/wildfire_risk_prediction/cmr_identity.py",
            *sorted((out / "responses").glob("*.json")),
        ]
    }
    units = []
    for number, unit in enumerate(meta["units"]):
        sample = unit["sample_id"]
        sources = [members[sample + "|" + r] for r in ("fire", "geolocation")]
        pair = {
            "sample_id": sample,
            "source_day": sources[0]["source_day"],
            "bytes": sum(s["bytes"] for s in sources),
            "sources": sources,
        }
        plan = json.loads(json.dumps(template))
        plan.update(
            {
                "all_pairs_inventory_only": [pair],
                "first_pair": sample,
                "first_pair_bytes": pair["bytes"],
                "source_review_archive_row": unit["archive_row"],
                "selection_parent_sha256": META_SHA,
                "selection_reason": "First grid pass after both source clock hypotheses; "
                "frozen source-row review, no fire or quality selection",
            }
        )
        plan["input_sha256"].update(inputs)
        folder = BASE / "observation_core_transfer_v1" / (out.name + f"_{number:02d}")
        folder.mkdir(parents=True, exist_ok=False)
        path = folder / "native_plan.json"
        write(path, plan)
        write(
            folder / "readback.json",
            {
                "status": "source_review_single_pair_prepared_not_downloaded",
                "archive_row": unit["archive_row"],
                "raw_files_downloaded": 0,
                "artifact_sha256": {path.name: digest(path)},
            },
        )
        write(
            folder / "completion_readback.json", {"report_sha256": digest(folder / "readback.json")}
        )
        runner.load_plan(path)
        units.append(
            {
                "archive_row": unit["archive_row"],
                "sample_id": sample,
                "source_day": pair["source_day"],
                "bytes": pair["bytes"],
                "plan": path.relative_to(ROOT).as_posix(),
                "plan_sha256": digest(path),
            }
        )
    total = sum(u["bytes"] for u in units)
    require(shutil.disk_usage(ROOT).free >= 20_000_000_000 + total, "Disk reserve")
    queue = {
        "scope": "seven_frozen_source_rows_download_headers_only",
        "source_sample_sha256": queue_runner.SAMPLE_SHA,
        "units": units,
        "total_raw_bytes": total,
        "workers": 1,
        "download_runtime_seconds": 3600,
        "per_pair_runtime_seconds": 900,
        "runtime_starts_after_private_login": True,
        "stop_on_first_failure": True,
        "automatic_restart": False,
        "raw_eviction_permitted": False,
        "cloud_execution_permitted": False,
        "labels_created": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_training_permitted": False,
        "spatial_or_daily_acceptance_permitted": False,
        "input_sha256": inputs,
    }
    target = out / "queue_plan.json"
    write(target, queue)
    write(
        out / "readback.json",
        {
            "status": "seven_pair_queue_prepared_not_downloaded",
            "source_metadata_sha256": META_SHA,
            "public_metadata_requests": requests,
            "public_metadata_batches": len(groups),
            "raw_bytes": total,
            "raw_files_downloaded": 0,
            "labels_created": False,
            "artifact_sha256": {target.name: digest(target)},
        },
    )
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    queue_runner.load_plan(target, runner)
    print(target.relative_to(ROOT).as_posix(), digest(target))
    print("PASS seven_pair_preparation_only", total, "bytes")


if __name__ == "__main__":
    main()
