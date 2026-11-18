"""Render the Salur graph-change witness for a research-method decision."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import pandas as pd
from audit_salur_event_context import MARKER, PINS, ROOT
from audit_stage_one_selection import verify
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

SOURCE = ROOT / "outputs/reports/dataset/salur_event_context_v1/20261118T230221Z_cab0c9e1"
SOURCE_SHA = "89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846"


def main():
    report = json.loads(verify(SOURCE / "readback.json", SOURCE_SHA).read_bytes())
    marker = json.loads(verify(MARKER, PINS[MARKER]).read_bytes())
    members = pd.read_csv(
        verify(SOURCE / "component_members.csv", report["artifact_sha256"]["component_members.csv"])
    )
    frame = members.loc[members.scenario.eq("d2000m_t72h")].copy()
    frame["time"] = pd.to_datetime(frame.timestamp, utc=True, format="ISO8601")
    witness = report["future_edge_witness"]
    earlier = frame.loc[frame.detection_id.eq(witness["historical_detection_id"])].iloc[0]
    bridge = frame.loc[frame.detection_id.isin(witness["first_edge_detection_ids"])].iloc[0]
    first = frame.loc[frame.time.eq(pd.Timestamp(report["first_local_detection_utc"]))]
    lon, lat = marker["estimates"]["sentinel_2b_pre_event"]["marker_lon_lat"]
    project = Transformer.from_crs(4326, 32636, always_xy=True)
    mx, my = project.transform(lon, lat)
    grid_path = ROOT / "data/interim/grid_aoi_parts.geojson"
    grid_sha = marker["input_sha256"][grid_path.relative_to(ROOT).as_posix()]
    grid = gpd.read_file(verify(grid_path, grid_sha)).to_crs(32636)
    first_cells = set(
        json.loads(report["scenarios"][-1]["at_target_end"][0]["earliest_grid_ids_json"])
    )
    chosen = grid.loc[grid.grid_id.isin(first_cells | {earlier.grid_id})].copy()
    chosen["geometry"] = chosen.geometry.translate(xoff=-mx, yoff=-my).scale(
        xfact=0.001, yfact=0.001, origin=(0, 0)
    )
    fig, (ax, timeline) = plt.subplots(1, 2, figsize=(14, 6), layout="constrained")
    chosen.loc[chosen.grid_id.isin(first_cells)].plot(
        ax=ax, facecolor="#dbeafe", edgecolor="#2563eb", linewidth=1
    )
    chosen.loc[chosen.grid_id.eq(earlier.grid_id)].plot(
        ax=ax, facecolor="#fee2e2", edgecolor="#b91c1c", linewidth=1
    )
    x, y = project.transform(first.longitude.to_numpy(), first.latitude.to_numpy())
    ax.scatter((x - mx) / 1000, (y - my) / 1000, s=12, c="#2563eb", label="10.12 bağlı tespitler")
    ax.scatter(0, 0, marker="*", s=180, c="#111827", zorder=5, label="Yayımlanan başlangıç işareti")
    for row, color, text, symbol in (
        (earlier, "#b91c1c", "28 Temmuz 10.11", "o"),
        (bridge, "#d97706", "30 Temmuz 11.14", "D"),
    ):
        px, py = project.transform(row.longitude, row.latitude)
        ax.scatter((px - mx) / 1000, (py - my) / 1000, c=color, marker=symbol, s=65, zorder=6)
        ax.annotate(
            text,
            ((px - mx) / 1000, (py - my) / 1000),
            xytext=(-7, -20 if symbol == "o" else 12),
            textcoords="offset points",
            ha="right",
            fontsize=9,
            color=color,
        )
    ax.set_title("2 km / 72 saat ayarında bağlantı", fontsize=12)
    ax.set_xlabel("Başlangıç işaretine göre doğu uzaklığı (km)")
    ax.set_ylabel("Kuzey uzaklığı (km)")
    ax.legend(loc="upper right", fontsize=8)
    ax.margins(0.17)
    ax.text(
        0.02,
        0.02,
        "Uzak ilk kayıt ↔ işaret: 25,8 km\nBağlantı kenarı: 1.933 m / 49 saat 03 dk",
        transform=ax.transAxes,
        fontsize=9,
        va="bottom",
    )
    events = [
        ("Bildirilen başlangıç", report["reported_onset_utc"], "#111827"),
        ("Uzak ilk kayıt", witness["historical_detection_utc"], "#b91c1c"),
        ("İlk yerel tespit", report["first_local_detection_utc"], "#2563eb"),
        ("Hedef pencere sonu", report["target_end_utc"], "#6b7280"),
        ("Birleştiren sonraki kayıt", witness["first_edge_utc"], "#d97706"),
    ]
    for i, (_label, stamp, color) in enumerate(events):
        t = pd.Timestamp(stamp).to_pydatetime()
        timeline.scatter(t, i, c=color, s=65)
        timeline.annotate(
            pd.Timestamp(stamp).strftime("%d.%m %H.%M"),
            (t, i),
            xytext=(6, -17),
            textcoords="offset points",
            fontsize=9,
        )
    timeline.axvline(pd.Timestamp(report["target_end_utc"]).to_pydatetime(), ls="--", c="#9ca3af")
    timeline.set_yticks(range(len(events)), [e[0] for e in events])
    timeline.invert_yaxis()
    timeline.set_ylim(4.7, -0.5)
    timeline.xaxis.set_major_locator(mdates.DayLocator())
    timeline.xaxis.set_major_formatter(mdates.DateFormatter("%d Tem"))
    timeline.set_title("Sonraki bağlantı geçmiş başlangıcı değiştiriyor", fontsize=12)
    timeline.set_xlabel("2021 • bütün saatler UTC")
    timeline.margins(x=0.18)
    timeline.grid(axis="x", alpha=0.2)
    fig.suptitle("Salur vaka incelemesi • olay kimliği için yöntem kararı", fontsize=15)
    fig.supxlabel(
        "Harita ve grafik küme ilişkisini gösterir. Fiziksel yangın kimliği, "
        "kesin tutuşma konumu veya eğitim etiketi doğrulanmış değildir.",
        fontsize=9,
    )
    run = (
        ROOT
        / "outputs/reports/dataset/salur_event_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    run.mkdir(parents=True, exist_ok=False)
    plot = run / "salur_graph_change.png"
    fig.savefig(plot, dpi=160)
    plt.close(fig)
    receipt = {
        "source_readback_sha256": SOURCE_SHA,
        "marker_readback_sha256": PINS[MARKER],
        "grid_sha256": grid_sha,
        "image_sha256": hashlib.sha256(plot.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "research_method_review_only",
        "researcher_decision": None,
    }
    out = run / "readback.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(plot.relative_to(ROOT))
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
