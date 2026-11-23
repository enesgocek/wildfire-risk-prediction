"""Check offline payload/source equivalence and static DOM references; no browser claim."""

import argparse
import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
QA = BASE / "weather_score_support_review_v1/20261123T142800Z_8725a867"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.scripts, self.csp = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "script":
            self.scripts.append(a.get("src"))
        if tag == "meta" and a.get("http-equiv") == "Content-Security-Policy":
            self.csp.append(a.get("content", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", type=Path, required=True)
    folder = parser.parse_args().prototype.resolve()
    require(
        folder.parent == (BASE / "historical_research_prototype_v1").resolve(),
        "Workspace local prototype",
    )
    report = json.loads((folder / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in report["input_sha256"].items()}
    pins[folder / "readback.json"] = digest(folder / "readback.json")
    pins.update({folder / p: sha for p, sha in report["artifact_sha256"].items()})
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "Current audited payload and source identities",
    )
    require(
        report["decision"]["decision_source"]
        == "explicit_researcher_A_conditional_research_prototype"
        and report["new_model_or_prediction_calls"] == report["new_Y_or_accepted_L"] == 0,
        "Explicit historical inspection scope only",
    )
    raw = (folder / "review_data.js").read_text(encoding="utf-8")
    prefix = "globalThis.RESEARCH_DATA="
    require(raw.startswith(prefix) and raw.endswith(";\n"), "JSON-only data assignment")
    payload = json.loads(raw[len(prefix) : -2])
    require(
        payload["scientific_state"]
        == {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
        "Scientific unknowns unchanged",
    )
    records = payload["records"]
    require(len(records) == 8956 and len(payload["scenarios"]) == 9, "Full two-calendar payload")
    ids = [(r["cohort"], r["grid"], r["time"]) for r in records]
    require(
        len(set(ids)) == 8956
        and len({r[1:] for r in ids}) == 8711
        and all(r[2].startswith("2022-") for r in ids),
        "Overlap and year accounting",
    )
    memberships = pd.read_csv(REVIEW / "record_memberships.csv")
    origins = pd.read_csv(REVIEW / "record_provenance.csv")
    quality = pd.read_csv(QA / "record_quality_context.csv", float_precision="round_trip")
    x = pd.read_csv(REVIEW / "features.csv", float_precision="round_trip")
    features = x.set_index(KEYS)
    flags = pd.read_csv(REVIEW / "score_review.csv").pivot(
        index=["cohort"] + KEYS, columns="scenario", values="existing_source_context_not_true_Y"
    )
    require(
        [d["name"] for d in payload["dictionary"]] == list(features.columns),
        "Exact feature dictionary",
    )
    cohort_counters = {c: 0 for c in memberships.cohort.unique()}
    original_scores = {
        c: {
            s: pd.read_csv(RUN / s / (c + "_scores.csv"), float_precision="round_trip")
            for s in payload["scenarios"]
        }
        for c in cohort_counters
    }
    require(
        ids == list(memberships[["cohort"] + KEYS].itertuples(index=False, name=None)),
        "Exact record ordering",
    )
    for i, r in enumerate(records):
        key, cohort = (r["grid"], r["time"]), r["cohort"]
        j = cohort_counters[cohort]
        cohort_counters[cohort] += 1
        q, origin, membership = quality.iloc[i], origins.iloc[i], memberships.iloc[i]
        expected_x = features.loc[key].to_numpy(dtype=float)
        np.testing.assert_array_equal(
            np.array([np.nan if v is None else v for v in r["x"]]), expected_x
        )
        require(
            r["eligible"] is bool(q.primary_full_area_and_dynamic_15_complete)
            and r["province"] == membership.province_area_intersections,
            "Original coverage and area context",
        )
        require(
            r["quality"]
            == [
                q.weather_min_valid_area_fraction,
                bool(q.vegetation_30d_missing),
                bool(q.vegetation_60d_missing),
            ],
            "Exact QA fields",
        )
        require(
            payload["paths"][r["origin"][0]] == origin.original_features_csv
            and payload["paths"][r["origin"][1]] == origin.original_metadata_csv
            and r["origin"][2] == origin.original_zero_based_calendar_row,
            "Exact source-row links",
        )
        for scenario_index, scenario in enumerate(payload["scenarios"]):
            saved = original_scores[cohort][scenario].iloc[j]
            expected = saved[
                [
                    "new_primary_weather_source_score_not_probability",
                    "previous_broad_xgboost_source_score_not_probability",
                    "previous_broad_frozen_linear_source_score_not_probability",
                ]
            ].to_numpy(dtype=float)
            np.testing.assert_array_equal(
                np.array([np.nan if v is None else v for v in r["scores"][scenario_index]]),
                expected,
            )
            require(
                bool(r["flags"] & (1 << scenario_index))
                == bool(flags.loc[(cohort, *key), scenario]),
                "Unchanged source-context bit",
            )
    require(
        sum(r["eligible"] for r in records if r["cohort"] == "four_province") == 4841
        and sum(r["eligible"] for r in records if r["cohort"] == "separate_Mersin") == 1929,
        "Exact primary quality support",
    )
    doc = Document()
    doc.feed((folder / "inceleme.html").read_text(encoding="utf-8"))
    require(
        len(doc.ids) == len(set(doc.ids))
        and doc.scripts == ["review_data.js", "research-core.js", "research-app.js"],
        "Unique DOM IDs and local classic scripts",
    )
    app = (folder / "research-app.js").read_text(encoding="utf-8")
    references = set(re.findall(r"\$\('([^']+)'\)", app))
    require(
        references <= set(doc.ids) and len(doc.csp) == 1 and "connect-src 'none'" in doc.csp[0],
        "Static DOM references and offline connection policy",
    )
    require(
        not re.search(r"\b(fetch|XMLHttpRequest|WebSocket|sendBeacon)\s*\(", app),
        "No network operation in app source",
    )
    require(all(digest(p) == sha for p, sha in pins.items()), "Unchanged inputs after audit")
    out = (
        BASE
        / "historical_research_prototype_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "offline_prototype_payload_scores_features_QA_and_source_links_verified",
        "prototype": folder.relative_to(ROOT).as_posix(),
        "memberships_verified": len(records),
        "score_values_verified": len(records) * 9 * 3,
        "feature_values_verified": len(records) * 27,
        "browser_render_or_manual_usability_verified": False,
        "new_model_or_prediction_calls": 0,
        "fire_risk_validated": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
