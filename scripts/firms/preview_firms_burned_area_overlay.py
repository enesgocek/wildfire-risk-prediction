import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[2]

df = pd.read_csv(
    ROOT / "data/interim/firms_combined_candidates_2018_2024.csv",
    dtype="string",
)
df["timestamp"] = pd.to_datetime(df["detection_timestamp_utc"], utc=True, errors="raise")
df = df.loc[df["timestamp"].dt.year.between(2018, 2023)].copy()

indices = df["grid_id"].str.extract(r"_C(-?\d+)_R(-?\d+)$")
df["column"] = pd.to_numeric(indices[0], errors="raise")
df["row"] = pd.to_numeric(indices[1], errors="raise")

samples = [
    (
        "2021 örneği",
        606,
        879,
        "2021-07-26",
        "2021-08-03",
        ["2021_07", "2021_08"],
    ),
    (
        "2019 örneği",
        520,
        906,
        "2019-08-16",
        "2019-08-24",
        ["2019_08"],
    ),
]

fig, axes = plt.subplots(1, 2, figsize=(14, 7), layout="constrained")
reports = []
temporal_tables = []
temporal_reports = []

for ax, (title, column, row, start, end, months) in zip(axes, samples, strict=True):
    selected = df.loc[
        df["column"].sub(column).abs().le(1)
        & df["row"].sub(row).abs().le(1)
        & df["timestamp"].ge(pd.Timestamp(start, tz="UTC"))
        & df["timestamp"].lt(pd.Timestamp(end, tz="UTC"))
    ].copy()

    if selected.empty:
        raise ValueError(f"{title}: aday tespit bulunamadı.")

    reference = None
    burned_union = None
    on_burned = np.zeros(len(selected), dtype=bool)
    on_unburned = np.zeros(len(selected), dtype=bool)
    in_bounds = np.zeros(len(selected), dtype=bool)

    for month in months:
        path = ROOT / "data/interim/burned_area/samples" / f"burned_area_sample_{month}.tif"

        with rasterio.open(path) as src:
            if src.descriptions != ("BurnDate", "Uncertainty", "QA", "FirstDay", "LastDay"):
                raise ValueError(f"{path.name}: beklenmeyen bantlar.")

            expected_crs = rasterio.crs.CRS.from_string(
                "+proj=sinu +R=6371007.181 +units=m +no_defs"
            )
            if src.crs != expected_crs:
                raise ValueError(f"{path.name}: MODIS küresel çalışma CRS bekleniyor.")

            grid = (src.crs, src.transform, src.height, src.width)
            if reference is None:
                reference = grid
                transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                x, y = transformer.transform(
                    pd.to_numeric(selected["longitude"], errors="raise").to_numpy(),
                    pd.to_numeric(selected["latitude"], errors="raise").to_numpy(),
                )
                burned_union = np.zeros((src.height, src.width), dtype=bool)
                extent = [
                    src.bounds.left / 1000,
                    src.bounds.right / 1000,
                    src.bounds.bottom / 1000,
                    src.bounds.top / 1000,
                ]
            elif grid != reference:
                raise ValueError("Aylık rasterların gridleri farklı.")

            burn = src.read(1)
            qa = src.read(3)
            uncertainty = src.read(2)
            available = (burn != src.nodata) & (qa != src.nodata)
            valid = available & ((qa & 2) != 0)

            burned = valid & (burn >= 1) & (burn <= 366)
            unburned = valid & (burn == 0)
            burned_union |= burned

            rows, cols = rasterio.transform.rowcol(src.transform, x, y)
            rows = np.asarray(rows)
            cols = np.asarray(cols)
            inside = (rows >= 0) & (rows < src.height) & (cols >= 0) & (cols < src.width)
            in_bounds |= inside

            positions = np.flatnonzero(inside)
            on_burned[positions] |= burned[rows[inside], cols[inside]]
            on_unburned[positions] |= unburned[rows[inside], cols[inside]]

            # Her kaynak ayı ayrı incelenir; tarihe en yakın ay seçilmez.
            matched_positions = positions[burned[rows[inside], cols[inside]]]
            if len(matched_positions):
                matched = selected.iloc[matched_positions].copy()
                pixel_rows = rows[matched_positions]
                pixel_cols = cols[matched_positions]
                matched["modis_row"] = pixel_rows
                matched["modis_column"] = pixel_cols
                burn_days = burn[pixel_rows, pixel_cols].astype("int64")
                year = int(month.split("_")[0])
                matched["modis_burn_date_utc"] = pd.Timestamp(
                    f"{year}-01-01", tz="UTC"
                ) + pd.to_timedelta(burn_days - 1, unit="D")
                u = uncertainty[pixel_rows, pixel_cols].astype("float64")
                u[u == src.nodata] = np.nan
                matched["modis_uncertainty_days"] = u
                matched["qa_shortened_mapping_period"] = (qa[pixel_rows, pixel_cols] & 4) != 0

                pixels = matched.groupby(["modis_row", "modis_column"], as_index=False).agg(
                    window_first_detection_utc=("timestamp", "min"),
                    window_last_detection_utc=("timestamp", "max"),
                    candidate_count=("detection_id", "size"),
                    modis_burn_date_utc=("modis_burn_date_utc", "first"),
                    modis_uncertainty_days=("modis_uncertainty_days", "first"),
                    qa_shortened_mapping_period=("qa_shortened_mapping_period", "first"),
                )
                pixels["first_detection_minus_burn_day"] = (
                    pixels["window_first_detection_utc"].dt.floor("D")
                    - pixels["modis_burn_date_utc"]
                ).dt.days
                pixels["sample"] = title
                pixels["source_month"] = month
                pixels["window_start_utc"] = start
                pixels["window_end_exclusive_utc"] = end
                temporal_tables.append(pixels)

                differences = pixels["first_detection_minus_burn_day"]
                temporal_reports.append(
                    {
                        "sample": title,
                        "source_month": month,
                        "matched_pixel_count": len(pixels),
                        "matched_detection_count": len(matched),
                        "first_detection_minus_burn_day_min": int(differences.min()),
                        "first_detection_minus_burn_day_median": float(differences.median()),
                        "first_detection_minus_burn_day_max": int(differences.max()),
                        "modis_uncertainty_days_median": (
                            float(pixels["modis_uncertainty_days"].median())
                            if pixels["modis_uncertainty_days"].notna().any()
                            else None
                        ),
                        "missing_uncertainty_pixel_count": int(
                            pixels["modis_uncertainty_days"].isna().sum()
                        ),
                        "first_detection_scope": "selected window and pixel; not event ignition",
                        "interpretation": "descriptive date differences; no acceptance threshold",
                    }
                )

    # Geçerli sıfır yalnızca seçili ayın MODIS sınıflandırmasıdır.
    unburned_only = ~on_burned & on_unburned
    unknown = in_bounds & ~on_burned & ~on_unburned
    outside = ~in_bounds

    ax.imshow(
        np.ma.masked_where(~burned_union, burned_union),
        extent=extent,
        origin="upper",
        cmap=ListedColormap(["#fbbf24"]),
        vmin=0,
        vmax=1,
        interpolation="nearest",
        alpha=0.65,
    )

    for sensor, marker, color in [
        ("SNPP", "o", "#2563eb"),
        ("N20", "^", "#dc2626"),
    ]:
        mask = selected["source_sensor"].eq(sensor).to_numpy()
        ax.scatter(
            np.asarray(x)[mask] / 1000,
            np.asarray(y)[mask] / 1000,
            marker=marker,
            color=color,
            s=9,
            alpha=0.55,
            label=sensor,
        )

    ax.set_title(f"{title}\nYanmış piksele düşen: {int(on_burned.sum())} / {len(selected)}")
    ax.set_xlabel("MODIS doğu koordinatı (km)")
    ax.set_ylabel("MODIS kuzey koordinatı (km)")
    ax.set_aspect("equal")
    ax.legend()
    ax.grid(alpha=0.15)

    reports.append(
        {
            "sample": title,
            "candidate_count": len(selected),
            "on_burned_pixel": int(on_burned.sum()),
            "on_valid_unburned_pixel_only": int(unburned_only.sum()),
            "unknown_or_insufficient_data": int(unknown.sum()),
            "outside_raster": int(outside.sum()),
            "months": months,
            "method": "point centre in native MODIS pixel; spatial only",
            "event_verification_completed": False,
        }
    )

fig.suptitle(
    "Sarı: seçili aylarda MODIS yanmış pikselleri\n"
    "Noktalar: eğitim dönemindeki VIIRS aday tespitleri"
)

figure_path = ROOT / "outputs/figures/firms_burned_area_overlay.png"
report_path = ROOT / "outputs/reports/firms_burned_area_overlay.json"
figure_path.parent.mkdir(parents=True, exist_ok=True)
report_path.parent.mkdir(parents=True, exist_ok=True)

fig.savefig(figure_path, dpi=180)
plt.close(fig)
report_path.write_text(
    json.dumps(reports, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(reports, ensure_ascii=False, indent=2))
if not temporal_tables:
    raise ValueError("Tarih karşılaştırması için eşleşen yanmış piksel yok.")
temporal_csv = ROOT / "outputs/reports/firms_burned_area_temporal_pixels.csv"
temporal_json = ROOT / "outputs/reports/firms_burned_area_temporal_check.json"
pd.concat(temporal_tables, ignore_index=True).to_csv(
    temporal_csv, index=False, encoding="utf-8-sig"
)
temporal_json.write_text(
    json.dumps(temporal_reports, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("\nPiksel bazında tarih karşılaştırması:")
print(json.dumps(temporal_reports, ensure_ascii=False, indent=2))
print("Tarih tablosu:", temporal_csv)
print("Tarih raporu:", temporal_json)
print("Görsel:", figure_path)
print("Rapor:", report_path)
