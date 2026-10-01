import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]

parser = argparse.ArgumentParser(description="Eğitim tespitleri için örnek inceleme")
parser.add_argument("--time-bin", choices=["D", "6h"], default="D")
parser.add_argument("--grouping", action="store_true", help="Olay adayı gruplarını karşılaştır")
args = parser.parse_args()
time_label = "günlük" if args.time_bin == "D" else "6 saatlik"


df = pd.read_csv(
    ROOT / "data/interim/firms_combined_candidates_2018_2024.csv",
    dtype="string",
)
df["timestamp"] = pd.to_datetime(df["detection_timestamp_utc"], utc=True, errors="raise")

# İnceleme yalnızca eğitim döneminde yapılır.
df = df.loc[df["timestamp"].dt.year.between(2018, 2023)].copy()

indices = df["grid_id"].str.extract(r"_C(-?\d+)_R(-?\d+)$")
df["column"] = pd.to_numeric(indices[0], errors="raise")
df["row"] = pd.to_numeric(indices[1], errors="raise")

samples = [
    ("2021 örneği", 606, 879, "2021-07-26", "2021-08-03"),
    ("2019 örneği", 520, 906, "2019-08-16", "2019-08-24"),
]


def preview_grouping():
    folder = ROOT / "data/interim/event_grouping"
    report_dir = ROOT / "outputs/reports"
    figure_dir = ROOT / "outputs/figures"
    report_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(
        (report_dir / "event_grouping_sensitivity.json").read_text(encoding="utf-8")
    )
    source_hash = hashlib.sha256(
        (ROOT / "data/interim/firms_combined_candidates_2018_2024.csv").read_bytes()
    ).hexdigest()
    if source_hash != manifest["source_sha256"]:
        raise ValueError("Kaynak değişmiş; önce gruplama sonuçlarını yeniden üret.")

    scenarios = ["d500m_t24h", "d1000m_t48h", "d2000m_t72h"]
    joined = {}
    for scenario in scenarios:
        assignments = pd.read_csv(folder / f"{scenario}_assignments.csv", dtype="string")
        if assignments["cluster_id"].isna().any():
            raise ValueError(f"{scenario}: eksik grup kimliği.")
        if set(assignments["detection_id"]) != set(df["detection_id"]):
            raise ValueError(f"{scenario}: eğitim tespitleriyle eşleşmiyor.")
        joined[scenario] = df.merge(
            assignments[["detection_id", "cluster_id"]],
            on="detection_id",
            validate="one_to_one",
        )

    fig, axes = plt.subplots(2, 3, figsize=(17, 10), layout="constrained")
    review = []
    for row_i, (title, column, row, start, end) in enumerate(samples):
        start = pd.Timestamp(start, tz="UTC")
        end = pd.Timestamp(end, tz="UTC")
        for col_i, scenario in enumerate(scenarios):
            data = joined[scenario]
            selected = data.loc[
                data["column"].sub(column).abs().le(1)
                & data["row"].sub(row).abs().le(1)
                & data["timestamp"].ge(start)
                & data["timestamp"].lt(end)
            ].copy()
            if selected.empty:
                raise ValueError(f"{title}: örnek boş.")
            points = gpd.GeoDataFrame(
                selected,
                geometry=gpd.points_from_xy(
                    pd.to_numeric(selected["longitude"]),
                    pd.to_numeric(selected["latitude"]),
                ),
                crs=4326,
            )
            points = points.to_crs(points.estimate_utm_crs())
            counts = selected["cluster_id"].value_counts()
            # Her panelin ilk 10 grubu kendi yerel numarasıyla gösterilir.
            # Diğer gruplar gri; farklı panellerin renkleri eşleşme iddiası taşımaz.
            top = counts.head(10).index.tolist()
            ax = axes[row_i, col_i]
            other = ~points["cluster_id"].isin(top)
            ax.scatter(
                points.loc[other].geometry.x / 1000,
                points.loc[other].geometry.y / 1000,
                c="lightgray",
                s=12,
                label="Diğer gruplar" if other.any() else None,
            )
            for number, cluster_id in enumerate(top, start=1):
                colour = plt.get_cmap("tab10")(number - 1)
                for sensor, symbol in [("SNPP", "o"), ("N20", "^")]:
                    mask = points["cluster_id"].eq(cluster_id) & points["source_sensor"].eq(sensor)
                    ax.scatter(
                        points.loc[mask].geometry.x / 1000,
                        points.loc[mask].geometry.y / 1000,
                        color=colour,
                        marker=symbol,
                        s=13,
                        alpha=0.7,
                    )
                group_points = points.loc[points["cluster_id"].eq(cluster_id)]
                ax.text(
                    group_points.geometry.x.mean() / 1000,
                    group_points.geometry.y.mean() / 1000,
                    str(number),
                    bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
                )
                full = data.loc[data["cluster_id"].eq(cluster_id)]
                review.append(
                    {
                        "sample": title,
                        "scenario": scenario,
                        "panel_group_number": number,
                        "cluster_id": cluster_id,
                        "detections_in_window": int(counts[cluster_id]),
                        "full_cluster_detections": len(full),
                        "detections_outside_window": len(full) - int(counts[cluster_id]),
                        "full_first_detection_utc": full["timestamp"].min(),
                        "full_last_detection_utc": full["timestamp"].max(),
                        "full_grid_count": full["grid_id"].nunique(),
                    }
                )
            ax.set_title(f"{title} | {scenario}\n{len(selected)} tespit / {len(counts)} grup")
            ax.set_xlabel("UTM doğu (km)")
            ax.set_ylabel("UTM kuzey (km)")
            ax.set_aspect("equal")
            print(f"{title} | {scenario}: {len(selected)} tespit / {len(counts)} grup")
    fig.suptitle(
        "Eğitim örnekleri — keşif amaçlı grup karşılaştırması\n"
        "Renk ve numara panel içinde geçerli; daire SNPP, üçgen N20. "
        "Gri: ilk 10 dışındaki gruplar."
    )
    output = figure_dir / "firms_grouping_comparison.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    pd.DataFrame(review).to_csv(report_dir / "firms_grouping_sample_review.csv", index=False)
    print("Karşılaştırma görseli:", output)

    # En uzun grubu kırpmadan göster: sınırlı örnek penceresi zinciri gizlemesin.
    scenario = scenarios[-1]
    data = joined[scenario]
    durations = data.groupby("cluster_id")["timestamp"].agg(["min", "max"])
    cluster_id = (durations["max"] - durations["min"]).idxmax()
    selected = data.loc[data["cluster_id"].eq(cluster_id)].copy()
    points = gpd.GeoDataFrame(
        selected,
        geometry=gpd.points_from_xy(
            pd.to_numeric(selected["longitude"]), pd.to_numeric(selected["latitude"])
        ),
        crs=4326,
    )
    points = points.to_crs(points.estimate_utm_crs())
    first, last = selected["timestamp"].min(), selected["timestamp"].max()
    elapsed = (points["timestamp"] - first).dt.total_seconds() / 86400
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), layout="constrained")
    for sensor, symbol in [("SNPP", "o"), ("N20", "^")]:
        mask = points["source_sensor"].eq(sensor)
        scatter = axes[0].scatter(
            points.loc[mask].geometry.x / 1000,
            points.loc[mask].geometry.y / 1000,
            c=elapsed.loc[mask],
            cmap="viridis",
            vmin=0,
            vmax=max((last - first).total_seconds() / 86400, 1),
            marker=symbol,
            s=30,
            label=sensor,
        )
    fig.colorbar(scatter, ax=axes[0], label="İlk tespitten geçen gün")
    axes[0].set_aspect("equal")
    axes[0].set_xlabel("UTM doğu (km)")
    axes[0].set_ylabel("UTM kuzey (km)")
    axes[0].legend()
    selected["day"] = selected["timestamp"].dt.floor("D")
    daily = (
        pd.crosstab(selected["day"], selected["source_sensor"])
        .reindex(
            pd.date_range(first.floor("D"), last.floor("D"), freq="D"),
            fill_value=0,
        )
        .reindex(columns=["SNPP", "N20"], fill_value=0)
    )
    axes[1].bar(daily.index, daily["SNPP"], label="SNPP")
    axes[1].bar(daily.index, daily["N20"], bottom=daily["SNPP"], label="N20")
    axes[1].xaxis.set_major_locator(mdates.AutoDateLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].set_ylabel("Bu gruptaki tespit sayısı")
    axes[1].set_xlabel("Gün (UTC); sıfır tespit, gözlem kapsamını kanıtlamaz")
    axes[1].legend()
    fig.suptitle(
        f"En uzun aday grup: {cluster_id}\n"
        f"{len(selected)} tespit | {(last - first).total_seconds() / 86400:.1f} gün | "
        "Tek yangın olduğu doğrulanmadı"
    )
    output = figure_dir / "firms_grouping_long_cluster.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    selected.drop(columns="day").to_csv(
        report_dir / "firms_grouping_long_cluster_detections.csv",
        index=False,
    )
    print("Uzun grup görseli:", output)


if args.grouping:
    preview_grouping()
    raise SystemExit(0)


fig, axes = plt.subplots(2, 2, figsize=(14, 10), layout="constrained")

for i, (title, column, row, start, end) in enumerate(samples):
    start = pd.Timestamp(start, tz="UTC")
    end = pd.Timestamp(end, tz="UTC")

    # Merkez hücre ve çevresindeki 8 hücre: yalnızca inceleme penceresi.
    selected = df.loc[
        df["column"].sub(column).abs().le(1)
        & df["row"].sub(row).abs().le(1)
        & df["timestamp"].ge(start)
        & df["timestamp"].lt(end)
    ].copy()

    if selected.empty:
        raise ValueError(f"{title}: inceleme penceresinde kayıt yok.")

    points = gpd.GeoDataFrame(
        selected,
        geometry=gpd.points_from_xy(
            pd.to_numeric(selected["longitude"], errors="raise"),
            pd.to_numeric(selected["latitude"], errors="raise"),
        ),
        crs=4326,
    )
    points = points.to_crs(points.estimate_utm_crs())

    elapsed = (points["timestamp"] - start).dt.total_seconds() / 86400

    for sensor, marker in [("SNPP", "o"), ("N20", "^")]:
        mask = points["source_sensor"].eq(sensor)
        scatter = axes[i, 0].scatter(
            points.loc[mask].geometry.x / 1000,
            points.loc[mask].geometry.y / 1000,
            c=elapsed.loc[mask],
            cmap="viridis",
            vmin=0,
            vmax=(end - start).days,
            marker=marker,
            s=14,
            alpha=0.65,
            label=sensor,
        )

    fig.colorbar(scatter, ax=axes[i, 0], label="Pencere başlangıcından geçen gün")
    axes[i, 0].set_title(f"{title} — {len(selected)} aday tespit")
    axes[i, 0].set_xlabel("UTM doğu koordinatı (km)")
    axes[i, 0].set_ylabel("UTM kuzey koordinatı (km)")
    axes[i, 0].set_aspect("equal")
    axes[i, 0].legend()

    selected["day"] = selected["timestamp"].dt.floor(args.time_bin)
    daily = pd.crosstab(selected["day"], selected["source_sensor"])
    daily = daily.reindex(
        pd.date_range(start=start, end=end, freq=args.time_bin, inclusive="left"),
        fill_value=0,
    ).reindex(columns=["SNPP", "N20"], fill_value=0)

    for sensor in daily.columns:
        axes[i, 1].plot(daily.index, daily[sensor], marker="o", label=sensor)

    axes[i, 1].set_title(f"{title} — {time_label} aday tespitler")
    axes[i, 1].set_ylabel("Tespit sayısı")
    axes[i, 1].set_xlabel("Zaman (UTC)")
    if args.time_bin == "6h":
        axes[i, 1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    axes[i, 1].tick_params(axis="x", rotation=45)
    axes[i, 1].grid(alpha=0.2)
    axes[i, 1].legend()

filename = "firms_event_samples.png" if args.time_bin == "D" else "firms_event_samples_6h.png"
output = ROOT / "outputs/figures" / filename
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output, dpi=180)
plt.close(fig)
print("Görsel kaydedildi:", output)
