"""Audit retained range/accounting, temporal membership and diagnostic summaries offline."""

import json
import re
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "local_landsat_compatibility_v1/20261125T092425Z_afc36fb5"


def save(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main():
    report = json.loads((RUN / "readback.json").read_bytes())
    launcher = json.loads((RUN / "launcher_receipt.json").read_bytes())
    require(
        launcher["returncode"] == 0
        and launcher["closed_child_log_sha256"] == digest(RUN / "child.log"),
        "Completed child/log closure",
    )
    for name, expected in report["input_sha256"].items():
        require(digest(ROOT / name) == expected, "Unchanged pilot inputs")
    for name, expected in report["artifact_sha256"].items():
        require(digest(RUN / name) == expected, "Retained pilot artifacts")
    continuation_path = ROOT / "configs/local_landsat_compatibility_continuation_v1.json"
    continuation = json.loads(continuation_path.read_bytes())
    previous = ROOT / continuation["previous_directory"]
    require(
        digest(previous / "network_checkpoint.json") == continuation["previous_network_sha256"],
        "Interrupted transfer accounting",
    )
    require(
        digest(previous / "public_scene_inventory.json") == continuation["previous_catalog_sha256"],
        "Retained complete scene lists",
    )
    net = json.loads((RUN / "network_checkpoint.json").read_bytes())
    require(
        net["body_bytes"]
        == report["body_bytes_including_prior_probe"]
        == continuation["prior_body_bytes"] + sum(r["bytes"] for r in net["ledger"]),
        "Cumulative bodies including prior attempts",
    )
    require(
        net["request_attempts"]
        == report["requests_including_prior_probes"]
        == continuation["prior_requests"] + len(net["ledger"]),
        "Cumulative request attempts",
    )
    require(
        net["body_bytes"] <= 134217728
        and net["request_attempts"] <= 512
        and report["global_elapsed_seconds"] <= 900,
        "Original unchanged budgets",
    )
    for path in RUN.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        require(
            not re.search(r"(?:[?&](?:sig|se|st|sp|sv)=)|(?:\"token\"\s*:)", text, flags=re.I),
            "No credential content in JSON",
        )
    require(
        not re.search(
            r"[?&](?:sig|se|st|sp|sv)=",
            (RUN / "child.log").read_text(encoding="utf-8", errors="replace"),
        ),
        "No signed query in log",
    )
    scenes = json.loads((RUN / "public_scene_inventory.json").read_bytes())
    require(
        scenes == json.loads((previous / "public_scene_inventory.json").read_bytes())
        and len(scenes) == 7,
        "Same seven complete scene metadata records",
    )
    with np.load(RUN / "candidate_AOI_weights.npz", allow_pickle=False) as weights_file:
        weights = weights_file["area_m2"]
    require(
        np.isfinite(weights).all() and (weights >= 0).all() and (weights <= 900 + 1e-6).all(),
        "Planar cell intersection weights",
    )
    grid = json.loads((RUN / "candidate_target_grid.json").read_bytes())
    require(abs(weights.sum() - grid["AOI_area_m2"]) < 1e-5, "Pixel/AOI area partition")
    arrays, quality = {}, []
    old_path = ROOT / "data/raw/vegetation/full_grid_v1/2022-07-01_b64/60days_batch_001.json"
    old = json.loads(old_path.read_bytes())
    old_times = dict(zip(old["scene_ids"], old["scene_acquisition_utc"], strict=True))
    for scene in scenes:
        stamp = datetime.fromisoformat(scene["datetime"])
        target = datetime(scene["year"], 7, 1, tzinfo=UTC)
        require(
            scene["year"] in (2022, 2024) and target - timedelta(days=60) <= stamp < target,
            "Only approved strictly past windows",
        )
        with np.load(RUN / (scene["id"] + "_diagnostic.npz"), allow_pickle=False) as file:
            a, b = file["ndvi"], file["ndmi"]
        require(
            a.shape == b.shape == weights.shape and np.array_equal(np.isnan(a), np.isnan(b)),
            "Common index QA masks",
        )
        require(
            (np.abs(a[np.isfinite(a)]) <= 1).all() and (np.abs(b[np.isfinite(b)]) <= 1).all(),
            "Scaled index bounds",
        )
        arrays[scene["id"]] = (a, b)
        row = {
            "id": scene["id"],
            "year": scene["year"],
            "finite_candidate_grid_pixels": int(np.isfinite(a).sum()),
            "finite_inside_AOI_pixels": int((np.isfinite(a) & (weights > 0)).sum()),
        }
        if scene["year"] == 2022:
            components = scene["id"].split("_")
            canonical = "_".join([components[0], components[2], components[3]])
            require(canonical in old_times, "Provider acquisition ID present in old batch union")
            row["old_time"] = old_times[canonical]
            row["provider_time_minus_old_seconds"] = (
                stamp - datetime.fromisoformat(old_times[canonical])
            ).total_seconds()
        quality.append(row)
    summaries = json.loads((RUN / "diagnostic_summaries.json").read_bytes())
    for row in summaries:
        target = datetime(row["year"], 7, 1, tzinfo=UTC)
        chosen = [
            s
            for s in scenes
            if s["year"] == row["year"]
            and datetime.fromisoformat(s["datetime"]) >= target - timedelta(days=row["window_days"])
        ]
        require(len(chosen) == row["scenes"], "Complete 30/60 day subset counts")
        medians = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            for i in range(2):
                medians.append(np.nanmedian(np.stack([arrays[s["id"]][i] for s in chosen]), axis=0))
        mask = np.isfinite(medians[0]) & np.isfinite(medians[1])
        support = float(sum(weights[mask].tolist()))
        require(abs(support - row["local_support_m2"]) < 1e-6, "Support scalar readback")
        for i, name in enumerate(("ndvi", "ndmi")):
            value = sum((medians[i][mask] * weights[mask]).tolist()) / support
            require(
                abs(value - row["local_" + name]) < 1e-12, "Index area weighted scalar readback"
            )
        require(
            row["feature_admitted"] is False
            and row["grid_and_area_rule_equivalence_accepted"] is False,
            "No feature admission",
        )
    out = (
        BASE
        / "local_landsat_compatibility_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    save(out / "scene_quality_and_clock_review.json", quality)
    result = {
        "status": "offline_accounting_temporal_and_summary_checks_passed_not_method_equivalence",
        "analysis_date": "2026-11-25",
        "review_receipt_sha256": digest(RUN / "readback.json"),
        "continuation_config_sha256": digest(continuation_path),
        "retained_old_scene_metadata_sha256": digest(old_path),
        "scene_count": len(scenes),
        "summary_count": len(summaries),
        "body_bytes": net["body_bytes"],
        "request_attempts": net["request_attempts"],
        "zero_valid_pixel_scenes": sum(q["finite_candidate_grid_pixels"] == 0 for q in quality),
        "feature_or_model_admission": False,
        "full_2024_production": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "auditor_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(result))


if __name__ == "__main__":
    main()
