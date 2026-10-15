"""Pin fixed 156-unit / 292-pair local work queue; no authentication or download."""

import importlib.util
import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.core_pilot import expected_pairs_for_day
from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.pilot_time_filter import required_pairs

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/observation_expansion_v1/20261014T233502Z_81275155"
SOURCE = ROOT / "outputs/reports/dataset/observation_core_transfer_v1/20261015T104255Z_9750c1c4"
PROTECTED = ROOT / (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
TRIAGE = ROOT / "outputs/reports/dataset/observation_pilot_time_triage_v1/20261015T112942Z_8cd17175"
TRIAGE_SHA = "dc01d0c302416a3cdc448558ec7729ecf7aaf5abb2d77a12ab8ba6b6917173f8"


def run():
    spec = importlib.util.spec_from_file_location(
        "queue_native", ROOT / "scripts/firms/run_observation_core_pair.py"
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    require(
        digest(SOURCE / "native_plan.json")
        == "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc",
        "Accepted native source plan",
    )
    original, _ = native.load_plan(SOURCE / "native_plan.json")
    reference_pairs = original["all_pairs_inventory_only"]
    require(
        len(reference_pairs) == 292 and len({p["sample_id"] for p in reference_pairs}) == 292,
        "Exact core pair inventory",
    )
    pins = dict(original["input_sha256"])

    def retain(path, expected=None):
        sha = digest(path)
        require(expected is None or expected == sha, "Queue input hash")
        pins[path.relative_to(ROOT).as_posix()] = sha

    retain(TRIAGE / "readback.json", TRIAGE_SHA)
    time_report = json.loads((TRIAGE / "readback.json").read_text(encoding="utf-8"))
    time_completion = json.loads((TRIAGE / "completion_readback.json").read_text(encoding="utf-8"))
    require(time_completion["report_sha256"] == TRIAGE_SHA, "Complete time witness receipt")
    retain(TRIAGE / "completion_readback.json")
    for name, expected in time_report["input_sha256"].items():
        retain(ROOT / name, expected)
    for name, expected in time_report["artifact_sha256"].items():
        retain(TRIAGE / name, expected)
    witnesses = pd.read_csv(TRIAGE / "pair_window_triage.csv")
    pairs = required_pairs(reference_pairs, witnesses)
    require(
        len(pairs) == time_report["required_geometry_pairs"] == 98,
        "Retained native-time geometry scope",
    )

    parent = json.loads((BASE / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((BASE / "completion_readback.json").read_text(encoding="utf-8"))
    require(
        completion["report_sha256"]
        == "8a29ea70339965497e4e5499ef718c684ecdbc9c833e3e2fa0c0db824a14e7c2",
        "Accepted fixed cohort receipt",
    )
    retain(BASE / "readback.json", completion["report_sha256"])
    retain(BASE / "completion_readback.json")
    retain(BASE / "calendar_core.csv", parent["artifact_sha256"]["calendar_core.csv"])
    retain(SOURCE / "native_plan.json")
    retain(SOURCE / "readback.json")
    retain(SOURCE / "completion_readback.json")
    core = pd.read_csv(BASE / "calendar_core.csv")
    require(
        len(core) == 156 and core.review_unit_id.is_unique and core.target.isna().all(),
        "Fixed unlabelled cohort",
    )
    require(
        core.obs_negative_label_permitted.eq(False).all()
        and core.obs_daily_observation_status.eq("unknown").all(),
        "Closed cohort",
    )
    # Only declared raw science files are inspected; never private connection folders.
    native_files = list((ROOT / "data/raw").rglob("*.nc"))
    found, missing = {}, 0
    for pair in pairs:
        for source in pair["sources"]:
            matches = sorted(
                [p for p in native_files if p.name == source["filename"]],
                key=lambda p: ("fa3cce2822c3825e" not in p.parts, p.as_posix()),
            )
            if matches:
                for path in matches:
                    check_file(path, source)
                    retain(path, source["sha256"])
                found[source["filename"]] = matches[0].relative_to(ROOT).as_posix()
            else:
                missing += source["bytes"]
    for name in (
        "scripts/quality/prepare_observation_pilot_queue.py",
        "scripts/firms/run_observation_pilot_queue.py",
        "scripts/firms/process_observation_pilot_pair.py",
        "src/wildfire_risk_prediction/core_pilot.py",
        "src/wildfire_risk_prediction/pilot_time_filter.py",
        "scripts/firms/audit_l2_observation_timing.py",
        "scripts/firms/combine_l2_area_estimates.py",
        "scripts/firms/estimate_l2_observed_area.py",
        "src/wildfire_risk_prediction/scan_support.py",
        "src/wildfire_risk_prediction/observation_window.py",
        "data/aoi/aoi.geojson",
        "data/aoi/grid_5km.geojson",
        "data/interim/grid_aoi_parts.geojson",
    ):
        retain(ROOT / name)
    protected = json.loads(PROTECTED.read_text(encoding="utf-8"))
    retain(PROTECTED)
    for name, sha in protected.items():
        retain(ROOT / name, sha)
    require(len(protected) == 22, "Frozen production source inventory")
    for name, sha in pins.items():
        require(digest(ROOT / name) == sha, "Queue input closure")
    units = core[
        [
            "review_unit_id",
            "grid_id",
            "target_day",
            "primary_province",
            "calendar_season",
            "signal_group",
            "cover_group",
        ]
    ].to_dict("records")
    day_pairs = {d: expected_pairs_for_day(pairs, d) for d in sorted(core.target_day.unique())}
    day_outside = {
        d: witnesses.loc[
            witnesses.target_day.eq(d) & witnesses.decision.eq("outside_by_full_scan_witness"),
            "sample_id",
        ].tolist()
        for d in day_pairs
    }
    for day in day_pairs:
        require(
            set(day_pairs[day]) | set(day_outside[day])
            == set(expected_pairs_for_day(reference_pairs, day)),
            "Full neighbour-day accounting",
        )
    free = shutil.disk_usage(ROOT).free
    require(free >= missing + 30_000_000_000, "Raw budget plus derived reserve and free disk")
    plan = {
        "version": "observation_pilot_queue_v2_time_witness",
        "status": "bounded_local_method_pilot_not_label_policy",
        "execution_scope": "fixed_calendar_core_156_units_native_time_filtered",
        "reference_pair_count": 292,
        "reference_source_plan": (SOURCE / "native_plan.json").relative_to(ROOT).as_posix(),
        "reference_source_plan_sha256": digest(SOURCE / "native_plan.json"),
        "required_geometry_pair_count": 98,
        "outside_by_time_witness_pair_count": 194,
        "time_witness_report": (TRIAGE / "readback.json").relative_to(ROOT).as_posix(),
        "time_witness_sha256": TRIAGE_SHA,
        "day_outside_pairs": day_outside,
        "pairs": pairs,
        "units": units,
        "day_expected_pairs": day_pairs,
        "existing_source_paths": found,
        "missing_raw_bytes_at_preparation": missing,
        "raw_inventory_bytes": sum(p["bytes"] for p in pairs),
        "raw_cache_limit_bytes": 20_000_000_000,
        "minimum_free_bytes": 20_000_000_000,
        "derived_disk_reserve_bytes": 10_000_000_000,
        "hard_runtime_seconds": 14400,
        "pair_workers": 1,
        "private_login_required_for_missing_sources": True,
        "raw_eviction_permitted": False,
        "cloud_jobs_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "input_sha256": pins,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/observation_pilot_queue_v2"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    for name, value in (
        ("queue_plan.json", plan),
        (
            "readback.json",
            {
                "status": "queue_prepared_not_executed",
                "plan_sha256": None,
                "input_count": len(pins),
                "pair_count": len(pairs),
                "unit_count": len(units),
                "found_file_count": len(found),
                "missing_raw_bytes": missing,
                "free_disk_bytes_at_preparation": free,
                "labels_created": False,
            },
        ),
    ):
        if name == "readback.json":
            value["plan_sha256"] = digest(out / "queue_plan.json")
        (out / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (out / "completion_readback.json").write_text(
        json.dumps({"status": "passed", "report_sha256": digest(out / "readback.json")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    run()
