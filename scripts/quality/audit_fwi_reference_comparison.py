"""Separate readback of the frozen FWI comparison, common pairs, scores and native samples."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "fwi_reference_comparison_run_v1/20261123T101431Z_805e6449"
SCORES = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"


def main():
    receipt = RUN / "readback.json"
    require(
        digest(receipt) == "5e5a7bd7a920b15d1288c7969b9841c62ac9948af5e74255c901ff6eb5a4d40c",
        "Frozen comparison receipt",
    )
    r = json.loads(receipt.read_bytes())
    require(
        all(digest(ROOT / p) == h for p, h in r["input_sha256"].items()), "Unchanged run inputs"
    )
    require(all(digest(RUN / p) == h for p, h in r["artifact_sha256"].items()), "Unchanged outputs")
    require(
        digest(ROOT / "scripts/quality/run_fwi_reference_comparison.py") == r["producer_sha256"],
        "Original producer identity",
    )
    frame = pd.read_csv(RUN / "common_calendar_review.csv", float_precision="round_trip")
    mapping = pd.read_csv(RUN / "native_node_mapping.csv", float_precision="round_trip")
    require(
        len(frame) == 203
        and frame.target.isna().all()
        and frame.accepted_L_membership.isna().all()
        and frame.daily_observation_status.eq("unknown").all(),
        "All unlabelled rows retained",
    )
    to_geographic = Transformer.from_crs(6933, 4326, always_xy=True, allow_ballpark=False)
    file = ROOT / "data/raw/external/cems_fwi_pilot_v1/ff72cf1a14e9faea5681118fe8888717.nc"
    with rasterio.open(file) as ds:
        xx, yy = np.meshgrid(np.arange(25, 37.0001, 0.25), np.arange(40, 34.9999, -0.25))

        def xyz(lon, lat):
            x, y = np.radians(lon), np.radians(lat)
            return np.stack([np.cos(y) * np.cos(x), np.cos(y) * np.sin(x), np.sin(y)], axis=-1)

        native = xyz(xx.ravel(), yy.ravel())
        independently_selected = {}
        for row in mapping.itertuples():
            match = re.fullmatch(r"E6933_5K_V1_C(\d+)_R(\d+)", row.grid_id)
            require(match is not None, "Known original grid identity")
            c, q = map(int, match.groups())
            lon, lat = to_geographic.transform(c * 5000 + 2500, q * 5000 + 2500)
            require(
                abs(row.projected_center_x_m - (c * 5000 + 2500)) < 0.01
                and abs(row.projected_center_y_m - (q * 5000 + 2500)) < 0.01,
                "Independent ID-based center within original 1 cm numerical tolerance",
            )
            index = int(np.argmin(np.square(native - xyz(lon, lat)).sum(axis=1)))
            y, x = np.unravel_index(index, xx.shape)
            require(
                (y, x) == (row.native_row, row.native_column),
                "Independent Cartesian/chord nearest node",
            )
            independently_selected[row.grid_id] = (y, x)
        arrays = {}
        for stamp in frame.prediction_timestamp_utc.unique():
            t = datetime.fromisoformat(stamp)
            require(
                t.year == 2022 and t.month == 6 and 2 <= t.day <= 30,
                "Approved assessment dates only",
            )
            band = t.day - 1
            arrays[stamp] = ds.read(band, masked=True)
        for row in frame.itertuples():
            y, x = independently_selected[row.grid_id]
            value = arrays[row.prediction_timestamp_utc][y, x]
            require(
                not np.ma.is_masked(value)
                and float(value) == row.FWI_retrospective_reference_not_probability,
                "Independent native sample and calendar-band equality",
            )
    score_columns = {"previous_day_FWI": "FWI_retrospective_reference_not_probability"}
    for scenario in [
        s["scenario"]
        for s in json.loads((SCORES / "readback.json").read_bytes())["scenario_summaries"]
    ]:
        original = pd.read_csv(SCORES / (scenario + "_source_calendar_scores.csv"))
        original = (
            original.loc[
                original.prediction_timestamp_utc.str[:10].between("2022-06-02", "2022-06-30")
            ]
            .sort_values(["grid_id", "prediction_timestamp_utc"])
            .reset_index(drop=True)
        )
        require(
            original[["grid_id", "prediction_timestamp_utc"]].equals(
                frame[["grid_id", "prediction_timestamp_utc"]]
            ),
            "Exact frozen-score key alignment",
        )
        column = scenario + "_frozen_source_score"
        np.testing.assert_allclose(
            frame[column],
            original.fixed_linear_source_score_not_fire_probability,
            rtol=0,
            atol=1e-12,
        )
        score_columns[scenario] = column
    supported = frame[list(score_columns.values())].notna().all(axis=1)
    require(
        np.array_equal(supported, frame.common_reference_and_all_nine_scores_finite),
        "Independent common support",
    )
    timestamps = pd.to_datetime(frame.prediction_timestamp_utc, utc=True)
    pairs = []
    for _grid_id, group in frame.loc[supported].groupby("grid_id"):
        source = group.index[group.original_source_record_key_present]
        other = group.index[~group.original_source_record_key_present]
        pairs.extend(
            (i, j) for i in source for j in other if timestamps[i].month == timestamps[j].month
        )
    saved_pairs = pd.read_csv(RUN / "common_pairs.csv")
    require(
        set(pairs)
        == set(zip(saved_pairs.source_row, saved_pairs.other_row_not_true_negative, strict=True))
        and len(pairs) == len(saved_pairs) == 196,
        "Exact independent pairs",
    )
    for row in saved_pairs.itertuples():
        require(
            row.source_grid == frame.grid_id.iloc[row.source_row]
            and row.source_timestamp == frame.prediction_timestamp_utc.iloc[row.source_row]
            and row.other_timestamp
            == frame.prediction_timestamp_utc.iloc[row.other_row_not_true_negative],
            "Pair CSV timestamps and identities",
        )
    checks = []
    for metric in r["metrics"]:
        name, label = metric["variant"], metric["slice"]
        used = []
        for i, j in pairs:
            gap = (timestamps[i] - timestamps[j]).days
            keep = (
                label == "all_same_grid_month"
                or label == "other_before_source"
                and gap > 0
                or label == "other_after_source"
                and gap < 0
                or label == "gap_1_to_3_days"
                and 1 <= abs(gap) <= 3
                or label == "gap_4_to_30_days"
                and 4 <= abs(gap) <= 30
            )
            if keep:
                used.append((i, j))
        values = frame[score_columns[name]]
        wins = sum(values[i] > values[j] for i, j in used)
        ties = sum(values[i] == values[j] for i, j in used)
        value = (wins + ties / 2) / len(used) if used else None
        require(
            metric["pairs"] == len(used)
            and metric["wins"] == wins
            and metric["ties"] == ties
            and metric["auxiliary_pair_AUC"] == value,
            "Independent summary scalar result",
        )
        checks.append(
            {"variant": name, "slice": label, "pairs": len(used), "auxiliary_pair_AUC": value}
        )
    per_cell = pd.read_csv(RUN / "per_cell_reference_metrics.csv", float_precision="round_trip")
    for row in per_cell.itertuples():
        used = [(i, j) for i, j in pairs if frame.grid_id[i] == row.grid_id]
        values = frame[score_columns[row.variant]]
        value = sum(
            1 if values[i] > values[j] else 0.5 if values[i] == values[j] else 0 for i, j in used
        ) / len(used)
        require(
            row.pairs == len(used) and abs(row.auxiliary_pair_AUC - value) < 1e-15,
            "Independent cell summary",
        )
    out = (
        BASE
        / "fwi_reference_comparison_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(checks).to_csv(out / "independent_metric_checks.csv", index=False)
    summary = pd.DataFrame(checks).query("slice == 'all_same_grid_month'")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.3, 1]})
    axes[0].barh(summary.variant, summary.auxiliary_pair_AUC, color=["#667788"] + ["#285778"] * 9)
    axes[0].axvline(0.5, color="black", linewidth=0.7, linestyle="--")
    axes[0].set(
        xlim=(0, 1),
        xlabel="Auxiliary matched-day AUC (not fire AP)",
        title="Same 196 pairs / 7 source calendar keys",
    )
    cuts = pd.DataFrame(checks).query("variant == 'previous_day_FWI'")
    axes[1].barh(cuts.slice, cuts.auxiliary_pair_AUC, color="#667788")
    axes[1].axvline(0.5, color="black", linewidth=0.7, linestyle="--")
    axes[1].set(
        xlim=(0, 1), xlabel="Previous nominal day FWI", title="Exploratory June 2022, Mersin"
    )
    fig.suptitle(
        "Retrospective reference only; no verified fire labels or operational availability"
    )
    fig.tight_layout()
    fig.savefig(out / "FWI_reference_comparison.png", dpi=160)
    plt.close(fig)
    result = {
        "status": "independent_FWI_reference_sample_pair_and_metric_readback_complete",
        "input_receipt_sha256": digest(receipt),
        "native_samples_rechecked": len(frame),
        "nearest_nodes_rechecked": len(mapping),
        "existing_score_rows_rechecked": 9 * len(frame),
        "common_pairs_rechecked": len(pairs),
        "summary_metrics_recomputed": len(checks),
        "per_cell_metrics_recomputed": len(per_cell),
        "new_models_fitted": 0,
        "real_fire_or_operational_validation": False,
        "closed_years_or_final_merge": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
