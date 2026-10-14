"""Offline nine-case graph witnesses; retains source ambiguity and closed label gates."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import pandas as pd

from wildfire_risk_prediction.event_case_trace import trace_cases
from wildfire_risk_prediction.feature_join import require

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REVIEW = "outputs/reports/dataset/event_decisions_v1/20261014T171606Z_3062f053"
MEMBERS = "outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2/event_members.csv"
PROXIMITY = "data/interim/source_audit/firms_candidates_static_proximity.csv"
REGISTRY = "configs/gcp_source_blocks_2026-10-13.json"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline priority event trace")


def run():
    pins = {}

    def retained(name, expected=None):
        p = ROOT / name
        require(p.is_file() and not p.is_symlink(), "Regular trace source")
        digest = sha(p)
        require(expected is None or digest == expected, "Pinned trace input changed")
        pins[name] = digest
        return p

    old = json.loads(
        retained(
            REVIEW + "/readback.json",
            "d0210a017a57a3a5d327237e280ecfb4aae9dbc00e892b888759613c9a791a55",
        ).read_text()
    )
    require(not old["labels_created"] and not old["model_ready"], "Diagnostic-only source")
    sources = {name: retained(REVIEW + "/" + name, h) for name, h in old["artifact_sha256"].items()}
    cases = pd.read_csv(sources["case_decision_queue.csv"])
    selected = cases.loc[cases.review_order_group.eq("A_target_window_differs")].copy()
    require(
        len(selected) == 9 and selected.review_family_id.nunique() == 3, "Fixed priority packet"
    )
    members = pd.read_csv(
        retained(MEMBERS, "bb24d25379acde97d65edd7bcff93e07b2b0ec61f84adb811ecfcf06e958c391")
    )
    members = members.loc[members.cluster_id.isin(selected.cluster_id)].copy()
    proximity = pd.read_csv(
        retained(PROXIMITY, "98585c8bc4a8711af605089a73779f7150cf33d413c3e692afb197b0677b8f94")
    )
    require(
        pd.to_datetime(proximity.detection_timestamp_utc, utc=True)
        .dt.year.between(2018, 2023)
        .all(),
        "Training-only retrospective context",
    )
    proximity = proximity.loc[proximity.detection_id.isin(members.detection_id)].copy()
    registry = json.loads(
        retained(
            REGISTRY, "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95"
        ).read_text()
    )
    require(
        not registry["negative_label_permitted"]
        and registry["daily_observation_status"] == "unknown",
        "Source exception gates",
    )
    for name in (
        "outputs/reports/firms_static_proximity_summary.json",
        "src/wildfire_risk_prediction/event_case_trace.py",
        "scripts/quality/trace_priority_event_cases.py",
        PROTECTED,
    ):
        retained(name)
    retained(
        "src/wildfire_risk_prediction/event_review.py",
        "b2b6531d1660ab03b668a81b59f92bf3a81330c707de38bfb50b67f46fa30302",
    )
    for name, digest in json.loads((ROOT / PROTECTED).read_text()).items():
        retained(name, digest)
    summary, paths, comparisons, points = trace_cases(
        selected, members, proximity, registry["deferred_days"]
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/priority_trace_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("case_trace_summary.csv", summary),
        ("first_to_anchor_paths.csv", paths),
        ("pairwise_membership_comparison.csv", comparisons),
        ("detection_source_context.csv", points),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        reread = pd.read_csv(path, float_precision="round_trip")
        expected = (
            frame.reset_index(drop=True)
            .astype(object)
            .where(frame.reset_index(drop=True).notna(), None)
        )
        actual = reread.astype(object).where(reread.notna(), None)
        pd.testing.assert_frame_equal(expected, actual, check_exact=True)
        artifacts[name] = sha(path)
    fig, axes = plt.subplots(3, 1, figsize=(11, 9))
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.07, top=0.86, hspace=0.8)
    for ax, (family, rows) in zip(
        axes, selected.groupby("review_family_id", sort=True), strict=True
    ):
        rows = rows.assign(
            radius=rows.scenario.str.extract(r"d(\d+)m", expand=False).astype(int)
        ).sort_values("radius")
        for n, row in enumerate(rows.itertuples()):
            subset = members.loc[members.cluster_id.eq(row.cluster_id)]
            times = pd.to_datetime(subset.detection_timestamp_utc, utc=True)
            ax.scatter(times, [n] * len(times), marker="|", color="#266786", s=70)
            ax.scatter(pd.Timestamp(row.first_detection_utc), n, color="#d55e00", s=36, zorder=3)
        ax.set_yticks(range(len(rows)), rows.scenario)
        ax.invert_yaxis()
        ax.set_title(family + "; detections are not independent fires", fontsize=10)
        short = pd.to_datetime(rows.last_detection_utc, utc=True).max() - pd.to_datetime(
            rows.first_detection_utc, utc=True
        ).min() < pd.Timedelta(72, unit="h")
        ax.xaxis.set_major_locator(
            mdates.HourLocator(interval=12, tz=UTC)
            if short
            else mdates.DayLocator(interval=10, tz=UTC)
        )
        ax.set_xlabel("UTC; " + str(pd.Timestamp(rows.iloc[0].first_detection_utc).year))
        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%d %b\n%H:%M UTC" if short else "%d %b %Y", tz=UTC)
        )
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        "Selected graph cases: first detections (orange) and retained members (blue)\n"
        "Retrospective review only; no event or label accepted",
        fontsize=12,
        y=0.98,
    )
    fig.savefig(out / "case_timelines.png", dpi=150)
    plt.close(fig)
    artifacts["case_timelines.png"] = sha(out / "case_timelines.png")
    result = {
        "status": "priority_case_trace_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "case_variants": len(summary),
        "review_families": selected.review_family_id.nunique(),
        "unique_detections": len(points),
        "graph_connected_cases": len(summary),
        "path_nodes": len(paths),
        "case_comparisons": len(comparisons),
        "unique_detections_with_prior_type2_within_1000m": int(
            points.static_prior_records_1000m.gt(0).sum()
        ),
        "cases_with_deferred_source_in_context_envelope": int(
            summary.deferred_days_in_context_calendar_envelope_json.ne("[]").sum()
        ),
        "cases_with_context_beyond_training": int(summary.context_extends_outside_training.sum()),
        "labels_created": False,
        "event_identities_accepted": 0,
        "source_type_semantics_verified": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Undirected graph witness is not causal fire-spread evidence",
            "Nearby Type=2 and recurrence do not establish industrial origin or justify exclusion",
            "Calendar context envelope is not exact target-window observation coverage",
            "Purpose-selected cases; no population error or independent fire count",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Trace input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Trace report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Trace artifact closure")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(path),
                "input_files_verified": len(pins),
                "artifacts_verified": len(artifacts),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Priority trace result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
