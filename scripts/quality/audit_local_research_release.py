"""Audit copied source parts and scientific state separately from packaging."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from verify_local_research_release import verify

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
KEYS = ["grid_id", "prediction_timestamp_utc"]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main(release):
    container = verify(release)
    package = release / "package"
    manifest = json.loads((package / "manifest.json").read_bytes())
    check(
        manifest["experimental_research_only"]
        and not manifest["labelled_training_dataset"]
        and not manifest["final_merge"],
        "Experimental separate-part release",
    )
    copied = 0
    for name, entry in manifest["files"].items():
        if "source_path" in entry:
            check(
                digest(ROOT / entry["source_path"]) == entry["sha256"],
                "Source copy equality: " + name,
            )
            copied += 1
    features = pd.read_csv(package / "data/features.csv")
    memberships = pd.read_csv(package / "data/inspection_memberships.csv")
    check(len(features) == len(memberships) == 44082, "44,082 existing keys")
    check(features.shape[1] == 29 and features.grid_id.nunique() == 822, "27 fields / 822 cells")
    pd.testing.assert_frame_equal(features[KEYS], memberships[KEYS])
    check(not features.duplicated(KEYS).any(), "Unique main keys")
    dates = pd.to_datetime(features.prediction_timestamp_utc, utc=True)
    check(dates.dt.year.between(2018, 2022).all(), "Only approved years")
    check(int(dates.dt.year.eq(2022).sum()) == 6573, "Explored 2022 count")
    check(int(features.iloc[:, 2:].notna().all(axis=1).sum()) == 41358, "Complete 27-field support")
    check(
        memberships.target.isna().all()
        and memberships.accepted_L_membership.isna().all()
        and memberships.daily_observation_status.eq("unknown").all()
        and memberships.negative_label_permitted.eq(False).all(),
        "Unknown scientific targets retained",
    )
    flags = [c for c in memberships if c.startswith("S_candidate_context_")]
    check(
        len(flags) == 9 and int(memberships[flags].any(axis=1).sum()) == 1670,
        "All proposal scenarios",
    )
    check(
        int(memberships[flags].nunique(axis=1).gt(1).sum()) == 412, "Scenario-dependent proposals"
    )
    dynamic = json.loads((package / "models/dynamic_features.json").read_bytes())
    models = sorted((package / "models").glob("*/ranker.json"))
    check(len(models) == 9 and len(dynamic) == 15, "Nine frozen dynamic models")
    for model in models:
        learner = json.loads(model.read_bytes())["learner"]
        check(
            learner["feature_names"] == dynamic
            and learner["learner_model_param"]["num_feature"] == "15"
            and learner["objective"]["name"] == "rank:pairwise"
            and learner["gradient_booster"]["model"]["gbtree_model_param"]["num_trees"] == "100",
            "Frozen model specification",
        )
        fit = pd.read_csv(model.parent / "fit_layout.csv")
        check(
            pd.to_datetime(fit.prediction_timestamp_utc, utc=True)
            .dt.year.between(2018, 2021)
            .all(),
            "Frozen fit years",
        )
        for cohort, count in (("four_province", 6573), ("separate_Mersin", 2383)):
            scores = pd.read_csv(model.parent / (cohort + "_scores.csv"))
            check(
                len(scores) == count
                and pd.to_datetime(scores.prediction_timestamp_utc, utc=True)
                .dt.year.eq(2022)
                .all(),
                "Existing assessment scores only",
            )
    payload = (package / "interface/review_data.js").read_text(encoding="utf-8").strip()
    data = json.loads(payload.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    check(
        len(data["records"]) == 8956 and len(data["scenarios"]) == 9,
        "Offline interface data support",
    )
    check(
        data["scientific_state"]
        == {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
        "Interface preserves scientific state",
    )
    for name in ("inceleme.html", "research-app.js", "research-core.js", "review_data.js"):
        check((package / "interface" / name).is_file(), "Local interface dependency")
    check((package / "AI_USE.md").is_file(), "Dataset card contribution link resolves")
    metrics = pd.read_csv(package / "results/primary_weather_metrics.csv")
    check(len(metrics) == 270, "Frozen comparison export")
    audit = json.loads((package / "evidence/frozen_score_support_audit_v1.json").read_bytes())
    check(
        audit["status"] == "independent_relational_pair_audit_passed"
        and audit["summary_rows"] == 54
        and audit["context_rows"] == 864
        and audit["source_day_variant_rows"] == 6456
        and audit["omission_rows"] == 5262,
        "Separate fixed-score audit complete",
    )
    out = (
        BASE
        / "local_research_release_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "local_experimental_release_integrity_and_scope_audit_passed",
        "release_path": release.relative_to(ROOT).as_posix(),
        "container": container,
        "source_byte_copies_verified": copied,
        "main_keys": len(features),
        "features": 27,
        "models": len(models),
        "assessment_memberships": len(data["records"]),
        "new_training_or_prediction_calls": 0,
        "true_Y_or_L_created": 0,
        "visual_browser_render_checked": False,
        "final_merge": False,
        "release_readback_sha256": digest(release / "readback.json"),
        "manifest_sha256": digest(package / "manifest.json"),
        "zip_sha256": digest(release / "research_release.zip"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    main(parser.parse_args().release.resolve())
