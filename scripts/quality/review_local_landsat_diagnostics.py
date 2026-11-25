"""Offline boundary-weight sensitivity and figure; no method or feature admission."""

import json
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import matplotlib
import numpy as np

from wildfire_risk_prediction.core_transfer import digest

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "local_landsat_compatibility_v1/20261125T092425Z_afc36fb5"
AUDIT = BASE / "local_landsat_compatibility_audit_v1/20261125T092809Z_3454247d"


def main():
    pins = {
        RUN / "readback.json": "2ff8413250d1d56cb8ac87eb66cdd29663362c798f55e6cab60b34865e9242d5",
        AUDIT / "readback.json": "371d61701eee785a21d9d809fac3f5a173f060023bc230b83770fe9690cf3460",
    }
    for path, expected in pins.items():
        if digest(path) != expected:
            raise ValueError("Upstream receipt changed")
    upstream = json.loads((RUN / "readback.json").read_bytes())
    for name, expected in upstream["artifact_sha256"].items():
        if digest(RUN / name) != expected:
            raise ValueError("Retained upstream artifact changed")
    scenes = json.loads((RUN / "public_scene_inventory.json").read_bytes())
    summaries = json.loads((RUN / "diagnostic_summaries.json").read_bytes())
    with np.load(RUN / "candidate_AOI_weights.npz", allow_pickle=False) as file:
        exact = file["area_m2"]
    # These are exploratory approximations, not an implementation claim about EE.
    weights = {
        "exact_planar_intersections": exact,
        "nearest_255_sensitivity_only": np.rint(exact / 900 * 255) / 255 * 900,
        "floor_255_sensitivity_only": np.floor(exact / 900 * 255) / 255 * 900,
    }
    arrays = {}
    for scene in scenes:
        with np.load(RUN / (scene["id"] + "_diagnostic.npz"), allow_pickle=False) as file:
            arrays[scene["id"]] = (file["ndvi"], file["ndmi"])
    rows = []
    for row in summaries:
        cutoff = datetime(row["year"], 7, 1, tzinfo=UTC)
        selected = [
            s
            for s in scenes
            if s["year"] == row["year"]
            and cutoff - timedelta(days=row["window_days"])
            <= datetime.fromisoformat(s["datetime"])
            < cutoff
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            medians = [
                np.nanmedian(np.stack([arrays[s["id"]][i] for s in selected]), axis=0)
                for i in range(2)
            ]
        valid = np.isfinite(medians[0]) & np.isfinite(medians[1])
        for name, area in weights.items():
            support = float(area[valid].sum())
            result = {
                "year": row["year"],
                "window_days": row["window_days"],
                "weight_hypothesis": name,
                "support_m2": support,
            }
            for i, field in enumerate(("ndvi", "ndmi")):
                value = float((medians[i][valid] * area[valid]).sum() / support)
                result[field] = value
                result[field + "_minus_exact"] = value - row["local_" + field]
                if row["year"] == 2022:
                    result[field + "_minus_old"] = value - row["old_" + field]
                if (
                    name == "exact_planar_intersections"
                    and abs(result[field + "_minus_exact"]) > 1e-12
                ):
                    raise ValueError("Baseline summary mismatch")
            rows.append(result)
    out = (
        BASE
        / "local_landsat_diagnostic_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "weight_sensitivity.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5))
    old_rows = [r for r in summaries if r["year"] == 2022]
    for axis, field in zip(axes, ("ndvi", "ndmi"), strict=True):
        values = [r[field + "_local_minus_old"] for r in old_rows]
        axis.bar(["30 gün", "60 gün"], values, width=0.45, color="#426e91")
        axis.axhline(0, color="#444444", linewidth=0.8)
        axis.set_ylim(-0.0002, 0.00013)
        axis.ticklabel_format(axis="y", style="sci", scilimits=(-4, -4))
        axis.set_title(field.upper() + ": yerel eksi eski özet")
        axis.set_ylabel("İndeks farkı (birimsiz)")
        axis.grid(axis="y", alpha=0.2)
        for i, value in enumerate(values):
            axis.annotate(
                f"{value:+.6f}",
                (i, value),
                xytext=(0, 8 if value >= 0 else -17),
                textcoords="offset points",
                ha="center",
            )
    fig.suptitle("Tek hücrelik yöntem provası · 1 Temmuz 2022", fontsize=15)
    fig.text(
        0.5,
        0.035,
        "C517/R913 · Küçük farklar yöntem eşdeğerliği veya yangın başarımı kabulü değildir.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.92))
    fig.savefig(out / "2022_local_reference_differences.png", dpi=160)
    plt.close(fig)
    result = {
        "status": "offline_sensitivity_complete_not_EE_emulation_or_feature_acceptance",
        "upstream_receipt_sha256": {str(p.relative_to(ROOT)): v for p, v in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "hypothesis_count": len(weights),
        "summary_count": len(rows),
        "maximum_absolute_index_change_from_exact": max(
            abs(r[f + "_minus_exact"]) for r in rows for f in ("ndvi", "ndmi")
        ),
        "EE_grid_or_rasterization_reproduced": False,
        "selected_best_matching_method": False,
        "new_network_training_prediction_labels_or_merge": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(result))


if __name__ == "__main__":
    main()
