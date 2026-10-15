"""Offline subgroup selection audit on the unchanged 156-unit observation pilot."""

import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.protocol_selection import CUTS, SCREENS, describe_selection

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c")
PARENT_SHA = "c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2"


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline protocol selection audit")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained regular selection input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Selection source unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    parent = json.loads(retained(PARENT / "readback.json", PARENT_SHA).read_text())
    closing = json.loads(retained(PARENT / "completion_readback.json").read_text())
    require(
        closing["report_sha256"] == PARENT_SHA and parent["labels_created"] is False,
        "Closed unlabelled upstream report",
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/protocol_selection.py",
    ):
        retained(name)
    units = pd.read_csv(ROOT / PARENT / "unit_protocol_evidence.csv")
    require(len(units) == 156 and units.target_day.nunique() == 12, "Unchanged fixed pilot")
    rows, counts, paired = describe_selection(units)
    # The same marginal split previously published must agree exactly for every cut.
    old = pd.read_csv(ROOT / PARENT / "descriptive_protocol_comparison.csv")
    for record in old.to_dict("records"):
        sub = counts.loc[
            counts.dimension.eq("signal_group")
            & counts.stratum.eq(record["signal_group"])
            & counts.area_fraction_cut.eq(record["area_fraction_cut"])
        ].set_index("screen")
        for screen, old_column in (
            ("daily_land", "daily_land_passing"),
            ("repeat_12h", "repeat_12h_passing"),
            ("all_four_bins", "all_four_bins_passing"),
        ):
            require(
                sub.loc[screen, "passing_units"] == record[old_column]
                and sub.loc[screen, "denominator_units"] == record["denominator"],
                "Published marginal screen counts conserved",
            )
    out = (
        ROOT
        / "outputs/reports/dataset/protocol_selection_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    rows.to_csv(out / "unit_descriptive_screens.csv", index=False)
    counts.to_csv(out / "stratum_screen_counts.csv", index=False)
    paired.to_csv(out / "paired_screen_counts.csv", index=False)
    group = counts.loc[counts.area_fraction_cut.eq(0.95) & counts.dimension.eq("province_signal")]
    background = group.loc[group.stratum.str.endswith("|no_selected_thermal_center")].copy()
    background["province"] = background.stratum.str.split("|", regex=False).str[0]
    chart = background.pivot(index="province", columns="screen", values="passing_units")
    denominators = background.groupby("province").denominator_units.first().reindex(chart.index)
    fig, ax = plt.subplots(figsize=(10, 5.6), layout="constrained")
    x = np.arange(len(chart))
    labels = ["Günlük nominal kara", "12 saat ayrımlı tekrar", "Dört zaman dilimi ortak alanı"]
    for offset, (screen, label, color) in enumerate(
        zip(SCREENS, labels, ("#3B6C8E", "#519C9A", "#A66B42"), strict=True)
    ):
        bars = ax.bar(x + (offset - 1) * 0.24, chart[screen], 0.24, label=label, color=color)
        ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_xticks(x, [f"{p}\nAmaçlı örnek n={n}" for p, n in denominators.items()])
    ax.set_ylabel("Betimsel alan kesimini geçen hücre gün sayısı")
    ax.set_ylim(0, max(denominators) + 5)
    ax.set_title(
        "Termal merkez tanığı olmayan 96 amaçlı birimde il karşılaştırması\n"
        "%95 alan kesimi yalnız açıklayıcıdır ve etiket kuralı değildir",
        fontsize=12,
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(out / "province_selection.png", dpi=180)
    plt.close(fig)
    require(all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final input closure")
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "purpose_selected_subgroup_diagnostics_not_policy_acceptance",
        "parent_sha256": PARENT_SHA,
        "unit_count": len(units),
        "distinct_grids": units.grid_id.nunique(),
        "target_days": units.target_day.nunique(),
        "training_years": sorted(pd.to_datetime(units.target_day).dt.year.unique().tolist()),
        "explanatory_area_cuts": CUTS,
        "screen_unit_rows": len(rows),
        "stratum_screen_rows": len(counts),
        "paired_screen_rows": len(paired),
        "published_counts_reconciled": True,
        "thermal_absent_province_95_counts": background[
            ["province", "screen", "denominator_units", "passing_units"]
        ].to_dict("records"),
        "input_file_count": len(pins),
        "upstream_raw_inputs_rehashed": False,
        "raw_arrays_read": 0,
        "network_bytes": 0,
        "cloud_jobs_started": 0,
        "population_error_rate_estimated": False,
        "independent_reference_used": False,
        "label_protocol_selected": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
    }
    (out / "readback.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed_descriptive_audit_not_label_acceptance",
                "report_sha256": digest(out / "readback.json"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
