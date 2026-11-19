"""One outcome-guided WF1538 follow-up pair, kept separate from the frozen first-pass review."""

import csv
import hashlib
import io
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from prepare_marmaris_native_pair import module, write

from wildfire_risk_prediction.cmr_identity import assess, producer_name
from wildfire_risk_prediction.core_transfer import digest, source_url
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONTEXT = BASE / "source_sample_catalog_context_v1/20261119T175521Z_e371683f/readback.json"
MONTH = ROOT / "outputs/gcp_delivery/2026-10-14/compact/products/month/2022-05/payload.zip"
TEMPLATE = BASE / "observation_core_transfer_v1/20261015T104255Z_9750c1c4/native_plan.json"
PINS = {
    CONTEXT: "ce513b9d644f49c8f9dca46fa6962816e8e92705412aad8bbc9f2f01d7364817",
    MONTH: "ccd14ce4be45de2b9caab6cce710c3a17b0a7afcc33c5a9e86fceacd0632904e",
    TEMPLATE: "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc",
}
SAMPLE = "N20:2022147.1030"
CATALOG_ID = "N20_815590_170090"


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned exploratory follow-up context")
    context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    require(
        all(digest(ROOT / n) == h for n, h in context["input_sha256"].items()), "Context closure"
    )
    hits = [r for r in context["contexts"] if r["catalogue_records"]]
    require(
        len(hits) == 2
        and all(r["archive_row"] == "WF1538" and r["catalogue_ids"] == [CATALOG_ID] for r in hits),
        "One catalogue candidate, not two independent detections",
    )
    catalogue = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    with catalogue.open(encoding="utf-8-sig", newline="") as stream:
        selected = [
            r
            for r in csv.DictReader(stream)
            if r["detection_timestamp_utc"][:4] == "2022" and r["detection_id"] == CATALOG_ID
        ]
    require(len(selected) == 1, "Exact fit-role catalogue row")
    candidate = selected[0]
    require(
        candidate["source_sensor"] == "N20" and candidate["grid_id"] == "E6933_5K_V1_C642_R876",
        "Sensor and candidate cell",
    )
    with zipfile.ZipFile(MONTH) as z:
        with zipfile.ZipFile(io.BytesIO(z.read("2022-05-27.zip"))) as daily:
            raw = daily.read("report.json")
    require(
        hashlib.sha256(raw).hexdigest()
        == "ff8df0ba2237d43ce54a3f4190dc2eca9a13ad3fe8be0ba93ce1f2a9991ae68a",
        "Accepted daily source report",
    )
    historical = next(
        r["audit"]["sources"] for r in json.loads(raw)["sources"] if r["sample_id"] == SAMPLE
    )
    stamp = datetime.fromisoformat(candidate["detection_timestamp_utc"])
    require(
        all(
            datetime.fromisoformat(s["cmr_interval"]["BeginningDateTime"])
            <= stamp
            < datetime.fromisoformat(s["cmr_interval"]["EndingDateTime"])
            for s in historical.values()
        ),
        "Catalogue minute lies in the historical pair interval",
    )
    refs = [
        {
            "source_id": SAMPLE + "|" + role,
            "source_day": "2022-05-27",
            "sample_id": SAMPLE,
            "role": role,
            "filename": Path(s["path"]).name,
            "bytes": s["bytes"],
            "sha256": s["sha256"],
        }
        for role, s in historical.items()
    ]
    require(
        len(refs) == 2 and {r["role"] for r in refs} == {"fire", "geolocation"}, "One exact pair"
    )
    names = {r["filename"] for r in refs}
    require(
        not any(p.name in names for p in (ROOT / "data/raw").rglob("*.nc")),
        "Existing native bytes require offline reuse",
    )
    runner = module("followup_runner", "scripts/firms/run_observation_core_pair.py")
    plan, _ = runner.load_plan(TEMPLATE)
    out = (
        BASE
        / "observation_core_transfer_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "responses").mkdir()
    cmr = module("followup_cmr", "scripts/firms/check_observation_core_catalogue.py")
    members = []
    for number, ref in enumerate(refs):
        _, items, _, _ = cmr.fetch_batch(out, number, [ref])
        check = assess(ref, items)
        require(
            check["metadata_checks_passed"] and len(check["metadata_data_urls"]) == 1,
            "Exact public source identity",
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
        members.append(member)
    amount = sum(s["bytes"] for s in members)
    require(
        amount == 186934166 and shutil.disk_usage(ROOT).free >= 20_000_000_000 + amount,
        "Size and disk reserve",
    )
    pair = {"sample_id": SAMPLE, "source_day": "2022-05-27", "bytes": amount, "sources": members}
    plan.update(
        {
            "all_pairs_inventory_only": [pair],
            "first_pair": SAMPLE,
            "first_pair_bytes": amount,
            "source_review_archive_row": "WF1538",
            "selection_parent_sha256": PINS[CONTEXT],
            "selection_reason": (
                "Outcome-guided follow-up of the single near-source catalogue candidate; "
                "not a replacement first pass"
            ),
            "selection_catalog_ids": [CATALOG_ID],
            "outcome_blind_pass_selection": False,
            "followup_not_used_for_recall_or_noise_rate": True,
            "source_clock_standard_resolved": False,
        }
    )
    for p in [*PINS, catalogue, Path(__file__), *sorted((out / "responses").glob("*.json"))]:
        plan["input_sha256"][p.relative_to(ROOT).as_posix()] = digest(p)
    target = out / "native_plan.json"
    write(target, plan)
    write(
        out / "readback.json",
        {
            "status": "WF1538_exploratory_followup_prepared_not_downloaded",
            "raw_bytes_to_download": amount,
            "raw_files_downloaded": 0,
            "frozen_ten_source_rows_retained": True,
            "first_pass_results_replaced": False,
            "clock_hypothesis_selected": False,
            "new_L_memberships": 0,
            "labels_created": False,
            "artifact_sha256": {target.name: digest(target)},
        },
    )
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    runner.load_plan(target)
    print(target.relative_to(ROOT).as_posix(), digest(target))
    print("PASS one exploratory follow-up prepared", amount, "bytes; private login still required")


if __name__ == "__main__":
    main()
