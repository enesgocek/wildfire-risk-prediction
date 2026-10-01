import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Geod, Transformer
from shapely.geometry import Point, box
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]


def audit_recurrent_sources(cell_size_m):
    sources = [
        ("SNPP", "815579", "data/interim/firms_pilot_2018_2024.csv"),
        ("N20", "815590", "data/interim/firms_noaa20_pilot_2018_2024.csv"),
    ]
    frames = []
    provenance = []
    for sensor, request_id, filename in sources:
        path = ROOT / filename
        data = pd.read_csv(path, dtype="string")
        data["timestamp"] = pd.to_datetime(
            data["detection_timestamp_utc"], utc=True, errors="raise"
        )
        data = data.loc[data["timestamp"].dt.year.between(2018, 2023)].copy()
        data["source_sensor"] = sensor
        data["detection_id"] = sensor + "_" + request_id + "_" + data["source_record_number"]
        frames.append(data)
        provenance.append(
            {
                "sensor": sensor,
                "file": filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "training_records": len(data),
            }
        )
    data = pd.concat(frames, ignore_index=True)
    if data.empty or data["detection_id"].isna().any() or data["detection_id"].duplicated().any():
        raise ValueError("Boş eğitim verisi veya geçersiz tespit kimliği.")
    if not data["type"].isin(["0", "1", "2", "3"]).all():
        raise ValueError("Beklenmeyen type kodu.")
    if not data["confidence"].isin(["l", "n", "h"]).all():
        raise ValueError("Beklenmeyen güven kodu.")
    lon = pd.to_numeric(data["longitude"], errors="raise").to_numpy(dtype=float)
    lat = pd.to_numeric(data["latitude"], errors="raise").to_numpy(dtype=float)
    if not (
        np.isfinite(lon).all()
        and np.isfinite(lat).all()
        and (np.abs(lon) <= 180).all()
        and (np.abs(lat) < 90).all()
    ):
        raise ValueError("Geçersiz koordinat.")
    # Bölgesel, metre birimli inceleme ızgarası. Bu hücreler tesis veya olay değildir.
    audit_crs = "+proj=aeqd +lat_0=38 +lon_0=31 +datum=WGS84 +units=m +no_defs"
    transformer = Transformer.from_crs(4326, audit_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    column = np.floor(np.asarray(x) / cell_size_m).astype(np.int64)
    row = np.floor(np.asarray(y) / cell_size_m).astype(np.int64)
    data["audit_cell_id"] = [
        f"AEQD31_38_{cell_size_m}M_C{c}_R{r}" for c, r in zip(column, row, strict=True)
    ]
    data["lon"] = lon
    data["lat"] = lat
    data["day"] = data["timestamp"].dt.strftime("%Y-%m-%d")
    data["month"] = data["timestamp"].dt.strftime("%Y-%m")
    data["year"] = data["timestamp"].dt.year
    data["vegetation_candidate"] = data["type"].eq("0") & data["confidence"].isin(["n", "h"])
    data["static_detection"] = data["type"].eq("2")
    data["offshore_detection"] = data["type"].eq("3")
    data["night_detection"] = data["daynight"].eq("N")

    table = data.groupby("audit_cell_id").agg(
        detection_count=("detection_id", "size"),
        active_days=("day", "nunique"),
        active_months=("month", "nunique"),
        active_years=("year", "nunique"),
        first_detection_utc=("timestamp", "min"),
        last_detection_utc=("timestamp", "max"),
        representative_latitude=("lat", "median"),
        representative_longitude=("lon", "median"),
        vegetation_candidate_count=("vegetation_candidate", "sum"),
        static_detection_count=("static_detection", "sum"),
        offshore_detection_count=("offshore_detection", "sum"),
        night_detection_count=("night_detection", "sum"),
        sensor_count=("source_sensor", "nunique"),
    )
    geod = Geod(ellps="WGS84")
    centres = data["audit_cell_id"].map(table["representative_longitude"]).to_numpy()
    centre_lat = data["audit_cell_id"].map(table["representative_latitude"]).to_numpy()
    _, _, distance = geod.inv(centres, centre_lat, lon, lat)
    data["distance_from_representative_m"] = distance
    table["p90_distance_from_representative_m"] = data.groupby("audit_cell_id")[
        "distance_from_representative_m"
    ].quantile(0.9)
    table["night_fraction"] = table["night_detection_count"] / table["detection_count"]
    table["static_fraction"] = table["static_detection_count"] / table["detection_count"]
    table["candidate_and_static_same_cell"] = table["vegetation_candidate_count"].gt(0) & table[
        "static_detection_count"
    ].gt(0)
    candidate_days = (
        data.loc[data["vegetation_candidate"]].groupby("audit_cell_id")["day"].nunique()
    )
    table["candidate_active_days"] = candidate_days.reindex(table.index, fill_value=0)
    table["review_status"] = "unreviewed; no exclusion decision"
    table = table.sort_values(
        ["candidate_and_static_same_cell", "active_months", "active_days", "detection_count"],
        ascending=[False, False, False, False],
        kind="stable",
    )
    if int(table["detection_count"].sum()) != len(data):
        raise ValueError("Denetim hücrelerinde kayıt kaybı.")

    report_dir = ROOT / "outputs/reports"
    interim_dir = ROOT / "data/interim/source_audit"
    report_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)
    name = f"firms_source_audit_{cell_size_m}m"
    table.to_csv(report_dir / f"{name}.csv", encoding="utf-8-sig")
    data.to_csv(interim_dir / f"{name}_membership.csv", index=False)
    report = {
        "period": "2018–2023; training only",
        "sources": provenance,
        "training_detection_count": len(data),
        "audit_cell_count": len(table),
        "cells_with_candidates": int(table["vegetation_candidate_count"].gt(0).sum()),
        "cells_with_candidates_and_static": int(table["candidate_and_static_same_cell"].sum()),
        "audit_cell_size_projected_m": cell_size_m,
        "audit_crs": audit_crs,
        "representative": "coordinate-wise median; not exact facility location",
        "spread_distance": "WGS84 geodesic distance from representative",
        "ranking": "mixed candidate/static first, then active months, days, detections",
        "automatic_exclusion_applied": False,
        "limitations": [
            "Audit cells are not facilities or fire events; boundaries can split sources.",
            "Different sources or fires can occupy the same audit cell.",
            "Pilot-only records omit neighbouring sources outside the AOI.",
            "No-detection days do not establish observation coverage.",
            "Type processing provenance remains unresolved.",
            "Historical training recurrence is label-review evidence, not a prediction feature.",
        ],
    }
    (report_dir / f"{name}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ["sources", "limitations"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    columns = [
        "representative_latitude",
        "representative_longitude",
        "active_days",
        "active_months",
        "active_years",
        "vegetation_candidate_count",
        "static_detection_count",
        "night_fraction",
    ]
    candidates = table.loc[table["vegetation_candidate_count"].gt(0)]
    print("\nİnceleme sırasındaki ilk 15 aday hücre (sabit kaynak kararı değildir):")
    print(candidates[columns].head(15).to_string())
    print("\nDenetim tablosu:", report_dir / f"{name}.csv")
    print("Kayıt eşleştirmesi:", interim_dir / f"{name}_membership.csv")


def audit_static_proximity(cell_size_m):
    report_dir = ROOT / "outputs/reports"
    name = f"firms_source_audit_{cell_size_m}m"
    membership_path = ROOT / f"data/interim/source_audit/{name}_membership.csv"
    audit_report = json.loads((report_dir / f"{name}.json").read_text(encoding="utf-8"))
    for source in audit_report["sources"]:
        actual = hashlib.sha256((ROOT / source["file"]).read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError("Kaynak değişmiş; önce --source-audit işlemini yeniden çalıştır.")
    data = pd.read_csv(membership_path, dtype="string")
    timestamps = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    if not timestamps.dt.year.between(2018, 2023).all():
        raise ValueError("Kaynak denetiminde eğitim dönemi dışında kayıt bulundu.")
    if data["detection_id"].isna().any() or data["detection_id"].duplicated().any():
        raise ValueError("Eksik veya tekrarlanan tespit kimliği.")
    candidate_mask = data["type"].eq("0") & data["confidence"].isin(["n", "h"])
    candidates = data.loc[candidate_mask].copy().reset_index(drop=True)
    static = data.loc[data["type"].eq("2")].copy().reset_index(drop=True)
    if candidates.empty or static.empty:
        raise ValueError("Aday veya sabit kaynak kayıtları boş.")
    sx = pd.to_numeric(static["longitude"], errors="raise").to_numpy(dtype=float)
    sy = pd.to_numeric(static["latitude"], errors="raise").to_numpy(dtype=float)
    cx = pd.to_numeric(candidates["longitude"], errors="raise").to_numpy(dtype=float)
    cy = pd.to_numeric(candidates["latitude"], errors="raise").to_numpy(dtype=float)
    for coords in [sx, sy, cx, cy]:
        if not np.isfinite(coords).all():
            raise ValueError("Geçersiz koordinat.")
    if not (
        (np.abs(sy) < 90).all()
        and (np.abs(cy) < 90).all()
        and (np.abs(sx) <= 180).all()
        and (np.abs(cx) <= 180).all()
    ):
        raise ValueError("Koordinatlar geçerli aralık dışında.")
    static_time = pd.to_datetime(static["timestamp"], utc=True, errors="raise")
    static_ns = np.array([value.value for value in static_time], dtype=np.int64)
    candidate_time = pd.to_datetime(candidates["timestamp"], utc=True, errors="raise")
    candidate_ns = np.array([value.value for value in candidate_time], dtype=np.int64)
    days = static_time.dt.strftime("%Y-%m-%d").to_numpy()
    years = static_time.dt.year.to_numpy()
    sensors = static["source_sensor"].to_numpy()
    ids = static["detection_id"].to_numpy()
    tree = STRtree([Point(x, y) for x, y in zip(sx, sy, strict=True)])
    geod = Geod(ellps="WGS84")
    radii = [100, 250, 500, 1000]
    maximum = max(radii)
    results = []
    print("Adayların sabit kaynak kayıtlarına uzaklığı hesaplanıyor...", flush=True)
    for i, (x, y) in enumerate(zip(cx, cy, strict=True)):
        # Kutuyla hızlı arama; kabul edilen uzaklık WGS84 ile hesaplanır.
        dy = maximum / 100000
        dx = dy / np.cos(np.deg2rad(y))
        neighbours = tree.query(box(x - dx, y - dy, x + dx, y + dy))
        if len(neighbours):
            _, _, distance = geod.inv(
                np.full(len(neighbours), x),
                np.full(len(neighbours), y),
                sx[neighbours],
                sy[neighbours],
            )
            distance = np.asarray(distance)
            within = distance <= maximum
            neighbours, distance = neighbours[within], distance[within]
        else:
            distance = np.array([], dtype=float)
        entry = {
            "nearest_static_distance_m_within_1000m": np.nan,
            "nearest_static_detection_id": "",
        }
        if len(neighbours):
            nearest = int(np.argmin(distance))
            entry["nearest_static_distance_m_within_1000m"] = float(distance[nearest])
            entry["nearest_static_detection_id"] = ids[neighbours[nearest]]
        for radius in radii:
            nearby = neighbours[distance <= radius]
            entry[f"static_records_{radius}m"] = len(nearby)
            entry[f"static_active_days_{radius}m"] = len(np.unique(days[nearby]))
            entry[f"static_active_years_{radius}m"] = len(np.unique(years[nearby]))
            entry[f"static_sensor_count_{radius}m"] = len(np.unique(sensors[nearby]))
            prior = nearby[static_ns[nearby] < candidate_ns[i]]
            simultaneous = nearby[static_ns[nearby] == candidate_ns[i]]
            later = nearby[static_ns[nearby] > candidate_ns[i]]
            entry[f"static_prior_records_{radius}m"] = len(prior)
            entry[f"static_simultaneous_records_{radius}m"] = len(simultaneous)
            entry[f"static_later_records_{radius}m"] = len(later)
            entry[f"static_prior_active_days_{radius}m"] = len(np.unique(days[prior]))
            entry[f"static_prior_active_years_{radius}m"] = len(np.unique(years[prior]))
            entry[f"static_prior_sensor_count_{radius}m"] = len(np.unique(sensors[prior]))
            entry[f"days_since_last_prior_static_{radius}m"] = (
                float((candidate_ns[i] - static_ns[prior].max()) / 86400e9)
                if len(prior)
                else np.nan
            )
            entry[f"days_until_first_later_static_{radius}m"] = (
                float((static_ns[later].min() - candidate_ns[i]) / 86400e9)
                if len(later)
                else np.nan
            )
            if len(prior) + len(simultaneous) + len(later) != len(nearby):
                raise ValueError("Zaman gruplarında kayıt kaybı.")
        results.append(entry)
        if (i + 1) % 5000 == 0:
            print(f"İşlenen aday: {i + 1} / {len(candidates)}", flush=True)
    metrics = pd.DataFrame(results)
    result = pd.concat([candidates, metrics], axis=1)
    if len(result) != len(candidates) or result["detection_id"].nunique() != len(candidates):
        raise ValueError("Mesafe denetiminde kayıt kaybı.")
    summary = []
    previous = 0
    for radius in radii:
        near = result[f"static_records_{radius}m"].gt(0)
        count = int(near.sum())
        prior = result[f"static_prior_records_{radius}m"].gt(0)
        simultaneous = result[f"static_simultaneous_records_{radius}m"].gt(0)
        later = result[f"static_later_records_{radius}m"].gt(0)
        same_without_prior = simultaneous & ~prior
        later_only = later & ~prior & ~simultaneous
        if int(prior.sum() + same_without_prior.sum() + later_only.sum()) != count:
            raise ValueError("Zamansal aday kategorileri toplamla uyuşmuyor.")
        if count < previous:
            raise ValueError("Artan mesafelerde aday sayısı azaldı.")
        previous = count
        summary.append(
            {
                "radius_m": radius,
                "candidates_with_static_nearby": count,
                "candidate_percentage": round(100 * count / len(result), 3),
                "candidates_with_prior_static": int(prior.sum()),
                "candidates_with_simultaneous_but_no_prior_static": int(same_without_prior.sum()),
                "candidates_with_later_static_only": int(later_only.sum()),
                "distinct_audit_cells_with_nearby_static": result.loc[
                    near, "audit_cell_id"
                ].nunique(),
            }
        )
    output = ROOT / "data/interim/source_audit/firms_candidates_static_proximity.csv"
    result.to_csv(output, index=False)
    summary_table = pd.DataFrame(summary)
    summary_table.to_csv(report_dir / "firms_static_proximity_summary.csv", index=False)
    report = {
        "period": "2018–2023; training only",
        "candidate_count": len(candidates),
        "static_record_count": len(static),
        "membership_sha256": hashlib.sha256(membership_path.read_bytes()).hexdigest(),
        "sources": audit_report["sources"],
        "radii_m": radii,
        "distance_method": "WGS84 geodesic point-centre distance",
        "static_records_are_not_distinct_facilities": True,
        "temporal_rule": "strictly before / exact timestamp / strictly after candidate detection",
        "audit_version": "2-temporal-context",
        "automatic_exclusion_applied": False,
        "summary": summary,
        "limitations": [
            "No nearby type=2 record does not establish a vegetation fire.",
            "Nearby type=2 records do not establish an industrial origin.",
            "Only pilot records are available; sources outside AOI are omitted.",
            "Recurrence uses the full training period for retrospective label review.",
            "This retrospective information must not become a prediction feature.",
            "Nearest distance is searched only within 1000m; blank means no match in that range.",
            "The first static detection is not a facility construction date.",
            "Earlier static detections do not prove unchanged land use at candidate time.",
            "Later-only static evidence cannot justify excluding an earlier fire candidate.",
            "Type processing provenance remains unresolved.",
        ],
    }
    (report_dir / "firms_static_proximity_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nYakınlık karşılaştırması (eleme kararı değildir):")
    print(summary_table.to_string(index=False))
    print("\nAday bazında mesafe tablosu:", output)
    print("Özet:", report_dir / "firms_static_proximity_summary.json")


def prepare_historical_review():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    report_dir = ROOT / "outputs/reports"
    proximity_path = ROOT / "data/interim/source_audit/firms_candidates_static_proximity.csv"
    report = json.loads(
        (report_dir / "firms_static_proximity_summary.json").read_text(encoding="utf-8")
    )
    if report.get("audit_version") != "2-temporal-context":
        raise ValueError("Önce zamansal --static-proximity denetimini çalıştır.")
    for source in report["sources"]:
        if hashlib.sha256((ROOT / source["file"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Kaynak değişmiş; kaynak denetimlerini yenile.")
    # Membership yolu rapordaki inceleme hücresi boyutundan bağımsız bulunur.
    memberships = list(
        (ROOT / "data/interim/source_audit").glob("firms_source_audit_*m_membership.csv")
    )
    matches = [
        path
        for path in memberships
        if hashlib.sha256(path.read_bytes()).hexdigest() == report["membership_sha256"]
    ]
    if len(matches) != 1:
        raise ValueError("Mesafe raporuyla eşleşen tek bir kayıt tablosu bulunamadı.")
    data = pd.read_csv(matches[0], dtype="string")
    candidates = pd.read_csv(proximity_path, dtype="string")
    for frame in [data, candidates]:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        if not frame["timestamp"].dt.year.between(2018, 2023).all():
            raise ValueError("Tarihsel incelemeye eğitim dışı kayıt girdi.")
        if frame["detection_id"].isna().any() or frame["detection_id"].duplicated().any():
            raise ValueError("Geçersiz tespit kimliği.")
    expected = set(
        data.loc[data["type"].eq("0") & data["confidence"].isin(["n", "h"]), "detection_id"]
    )
    if set(candidates["detection_id"]) != expected:
        raise ValueError("Mesafe tablosu aday kimlikleriyle eşleşmiyor.")
    for column in [
        "static_prior_records_100m",
        "static_simultaneous_records_100m",
        "static_later_records_100m",
    ]:
        candidates[column] = pd.to_numeric(candidates[column], errors="raise")
    groups = [
        (
            "later_only",
            candidates["static_prior_records_100m"].eq(0)
            & candidates["static_simultaneous_records_100m"].eq(0)
            & candidates["static_later_records_100m"].gt(0),
        ),
        ("prior_static", candidates["static_prior_records_100m"].gt(0)),
    ]
    geod = Geod(ellps="WGS84")
    cases = []
    for category, mask in groups:
        subset = candidates.loc[mask].copy()
        counts = subset["audit_cell_id"].value_counts()
        chosen = 0
        for audit_cell_id in counts.index:
            anchor = (
                subset.loc[subset["audit_cell_id"].eq(audit_cell_id)]
                .sort_values(["timestamp", "detection_id"])
                .iloc[0]
            )
            lon, lat = float(anchor["longitude"]), float(anchor["latitude"])
            # İnceleme çeşitliliği için aynı çevreyi tekrar seçme; filtre eşiği değildir.
            if any(
                geod.inv(lon, lat, case["longitude"], case["latitude"])[2] < 5000 for case in cases
            ):
                continue
            cases.append(
                {
                    "case_id": f"H{len(cases) + 1:02d}",
                    "category": category,
                    "audit_cell_id": audit_cell_id,
                    "anchor_detection_id": anchor["detection_id"],
                    "candidate_timestamp_utc": anchor["timestamp"],
                    "latitude": lat,
                    "longitude": lon,
                    "category_candidate_count_in_cell": int(counts[audit_cell_id]),
                    "review_status": "unreviewed; not an exclusion decision",
                }
            )
            chosen += 1
            if chosen == 3:
                break
    if not cases:
        raise ValueError("İnceleme örneği bulunamadı.")
    x = pd.to_numeric(data["longitude"], errors="raise").to_numpy(dtype=float)
    y = pd.to_numeric(data["latitude"], errors="raise").to_numpy(dtype=float)
    data["month"] = data["timestamp"].dt.strftime("%Y-%m")
    data["review_type"] = "other"
    data.loc[data["type"].eq("2"), "review_type"] = "static_type2"
    data.loc[data["type"].eq("0") & data["confidence"].isin(["n", "h"]), "review_type"] = (
        "vegetation_candidate"
    )
    monthly_dates = pd.date_range("2018-01-01", "2023-12-01", freq="MS", tz="UTC")
    monthly_index = monthly_dates.strftime("%Y-%m")
    fig, axes = plt.subplots(
        len(cases), 1, figsize=(14, 3 * len(cases)), layout="constrained", squeeze=False
    )
    tables = []
    for i, case in enumerate(cases):
        _, _, distance = geod.inv(
            np.full(len(data), case["longitude"]),
            np.full(len(data), case["latitude"]),
            x,
            y,
        )
        distance = np.asarray(distance)
        # Grafik 100m: kategoriyle aynı çevre. CSV ayrıca 500m bağlamını içerir.
        for radius in [100, 500]:
            near = data.loc[distance <= radius]
            monthly = pd.crosstab(near["month"], near["review_type"]).reindex(
                index=monthly_index,
                columns=["vegetation_candidate", "static_type2", "other"],
                fill_value=0,
            )
            monthly.index.name = "month"
            saved = monthly.reset_index()
            saved.insert(0, "radius_m", radius)
            saved.insert(0, "case_id", case["case_id"])
            tables.append(saved)
            if radius == 100:
                ax = axes[i, 0]
                bottom = np.zeros(len(monthly))
                for label, colour in [
                    ("vegetation_candidate", "tab:red"),
                    ("static_type2", "tab:blue"),
                    ("other", "gray"),
                ]:
                    values = monthly[label].to_numpy(dtype=float)
                    ax.bar(
                        monthly_dates, values, bottom=bottom, width=22, label=label, color=colour
                    )
                    bottom += values
                ax.axvline(
                    case["candidate_timestamp_utc"],
                    color="black",
                    linestyle="--",
                    label="Seçilen aday tarihi",
                )
                ax.set_title(
                    f"{case['case_id']} | {case['category']} | "
                    f"{case['latitude']:.5f}, {case['longitude']:.5f} | 100m çevre"
                )
                ax.set_ylabel("Aylık tespit sayısı")
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
                ax.legend(fontsize=8, loc="upper left")
                static = near.loc[near["type"].eq("2")]
                earlier = static.loc[static["timestamp"].lt(case["candidate_timestamp_utc"])]
                later = static.loc[static["timestamp"].gt(case["candidate_timestamp_utc"])]
                case["last_prior_static_utc_100m"] = earlier["timestamp"].max()
                case["first_later_static_utc_100m"] = later["timestamp"].min()
    fig.suptitle(
        "Tarihsel inceleme örnekleri — olay doğrulaması yapılmadı\n"
        "Sıfır tespit, gözlem yokluğu veya yangın yokluğu arasında ayrım yapmaz."
    )
    figure_dir = ROOT / "outputs/figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    figure = figure_dir / "firms_historical_review_timelines.png"
    fig.savefig(figure, dpi=160)
    plt.close(fig)
    table = pd.DataFrame(cases)
    output = report_dir / "firms_historical_review_cases.csv"
    table.to_csv(output, index=False)
    pd.concat(tables, ignore_index=True).to_csv(
        report_dir / "firms_historical_review_monthly.csv", index=False
    )
    manifest = {
        "period": "2018–2023; training only",
        "case_count": len(cases),
        "selection": (
            "Up to three cells per temporal category; descending candidate count; "
            "earliest eligible detection as anchor; 5km spacing"
        ),
        "classification_radius_m": 100,
        "monthly_context_radii_m": [100, 500],
        "proximity_sha256": hashlib.sha256(proximity_path.read_bytes()).hexdigest(),
        "membership_sha256": report["membership_sha256"],
        "automatic_exclusion_applied": False,
        "limitations": [
            "Targeted examples, not a representative accuracy sample.",
            "Later-only refers to the anchor detection, not the entire location history.",
            "First/last static detections do not prove facility construction or removal dates.",
            "Historical imagery and source processing provenance still need review.",
        ],
    }
    (report_dir / "firms_historical_review_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        table[
            [
                "case_id",
                "category",
                "candidate_timestamp_utc",
                "latitude",
                "longitude",
                "last_prior_static_utc_100m",
                "first_later_static_utc_100m",
            ]
        ].to_string(index=False)
    )
    print("\nİnceleme tablosu:", output)
    print("Zaman çizelgesi:", figure)


parser = argparse.ArgumentParser(description="FIRMS tür profili ve kaynak denetimi")
parser.add_argument(
    "--source-audit", action="store_true", help="İki sensörü eğitim döneminde incele"
)
parser.add_argument("--cell-size-m", type=int, choices=[250, 500, 1000], default=500)
parser.add_argument(
    "--static-proximity", action="store_true", help="Adayların sabit kayıtlara mesafesini denetle"
)
parser.add_argument(
    "--historical-review",
    action="store_true",
    help="Tarihsel inceleme örneklerini ve zaman çizelgelerini hazırla",
)
args = parser.parse_args()
if sum([args.source_audit, args.static_proximity, args.historical_review]) > 1:
    parser.error("Denetim seçeneklerini ayrı çalıştır.")
if args.historical_review:
    prepare_historical_review()
    raise SystemExit(0)
if args.static_proximity:
    audit_static_proximity(args.cell_size_m)
    raise SystemExit(0)
if args.source_audit:
    audit_recurrent_sources(args.cell_size_m)
    raise SystemExit(0)


source_path = ROOT / "data/interim/firms_pilot_2018_2024.csv"
output_dir = ROOT / "outputs/reports"

df = pd.read_csv(source_path, dtype="string")

timestamps = pd.to_datetime(
    df["detection_timestamp_utc"],
    utc=True,
    errors="raise",
)

df["year"] = timestamps.dt.year

year_type = pd.crosstab(df["year"], df["type"]).reindex(
    index=range(2018, 2025),
    columns=["0", "2", "3"],
    fill_value=0,
)

type_confidence = pd.crosstab(
    df["type"],
    df["confidence"],
).reindex(
    index=["0", "2", "3"],
    columns=["l", "n", "h"],
    fill_value=0,
)

# Tekrarlanan sabit kaynak incelemesi yalnızca eğitim döneminde
train = df.loc[df["year"] <= 2023]
static_train = train.loc[train["type"] == "2"]

static_grid_counts = (
    static_train.groupby("grid_id").size().sort_values(ascending=False).rename("detection_count")
)

output_dir.mkdir(parents=True, exist_ok=True)

year_type.to_csv(
    output_dir / "firms_pilot_year_type.csv",
    encoding="utf-8-sig",
)

type_confidence.to_csv(
    output_dir / "firms_pilot_type_confidence.csv",
    encoding="utf-8-sig",
)

static_grid_counts.to_csv(
    output_dir / "firms_train_static_grid_counts.csv",
    encoding="utf-8-sig",
)

print("Yıllara göre tespit türleri:")
print(year_type.to_string())

print("\nTespit türüne göre güven düzeyleri:")
print(type_confidence.to_string())

print("\nEğitim döneminde en fazla type=2 tespiti bulunan 10 hücre:")
print(static_grid_counts.head(10).to_string())

print("\nİnceleme tabloları kaydedildi:", output_dir)
