"""Bind measured cover, dated imagery and researcher notes by detection identity."""

import json
import logging
from collections import Counter, defaultdict
from datetime import UTC, datetime
from os.path import relpath
from pathlib import Path
from uuid import uuid4

import rasterio
import requests
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_public_event_cover import QA_FLAGS, catalogue, plt, require, sha
from shapely.geometry import Point, box
from shapely.ops import transform

from wildfire_risk_prediction.imagery_review import support_quality
from wildfire_risk_prediction.preevent_imagery import utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
INPUTS = (
    (
        "candidate_center_footprint_v1/20261107T235952Z_cbc4f2b3",
        "159771b79506df43bdedf5f4004ecf3d6003384600c84fe4ba055fd8bfd21394",
    ),
    (
        "habitat_evidence_matrix_v1/20261103T215030Z_1106f3eb",
        "da877cc44c0626995dde7577892b2dbfbbc9f3a2efea5f226aa268569298366e",
    ),
    (
        "pu_researcher_cover_notes_v1/20261107T220751Z_2b5bf4b1",
        "b9f5e68587bb278719f3e9e787bdd66ead3b7c2d4798d106ee758358d0b96898",
    ),
    (
        "public_event_cover_v1/20261107T233443Z_6e504fcb",
        "aa0ad0e753d04be890837c7f5e46f7d2ac03ba1ecf9c6e183016946f30bfe38e",
    ),
    (
        "urla_coastal_detection_v1/20261107T234917Z_ca86f9d4",
        "e9d5cfc4052503463923e7d10dacb296a09f5f674d1c331a558d7dec24f739ea",
    ),
)
WOODY = {311, 312, 313, 322, 323, 324}
EXTRA_POINT = "SNPP_815579_135300"


def projected_circle(point, crs):
    project = Transformer.from_crs(4326, crs, always_xy=True)
    return Point(*project.transform(point["longitude"], point["latitude"])).buffer(250)


def image_record(window, paths, quality):
    return {
        "acquired_utc": window["acquired_utc"],
        "item_id": window["item_id"],
        "visual": paths["visual"].relative_to(ROOT).as_posix(),
        "scl": paths["SCL"].relative_to(ROOT).as_posix(),
        "quality": quality,
        "zero_all_selected_quality_flags": all(quality[k] == 0 for k in QA_FLAGS),
        "geometry": "250_m_circle_at_this_detection",
    }


def local_images(points, windows, retain):
    result = defaultdict(dict)
    for case, folder, window in windows:
        paths = {
            band: retain(folder / window["folder"] / f"{band}.tif", meta["sha256"])
            for band, meta in window["assets"].items()
        }
        with rasterio.open(paths["SCL"]) as scl, rasterio.open(paths["visual"]) as visual:
            require(scl.crs == visual.crs, "Aligned source projections")
            available = box(*scl.bounds).intersection(box(*visual.bounds))
            data, valid = scl.read(1), scl.dataset_mask() > 0
            for key, point in points.items():
                if point["case"] != case:
                    continue
                circle = projected_circle(point, scl.crs)
                if available.covers(circle):
                    quality = support_quality(data, valid, scl.transform, circle)
                    date = window["acquired_utc"][:10]
                    record = image_record(window, paths, quality)
                    existing = result[key].setdefault(date, record)
                    require(
                        existing["item_id"] == record["item_id"] and existing["quality"] == quality,
                        "Overlapping source windows disagree",
                    )
    return result


def read_missing(point, out, expected_ids, retain):
    cutoff = utc_time(point["day"] + "T00:00:00Z")
    circle = projected_circle(point, 32636)
    support = transform(Transformer.from_crs(32636, 4326, always_xy=True).transform, circle)
    with requests.Session() as session:
        session.trust_env = False
        _, selected = catalogue(session, support, cutoff)
    require({item["id"] for item, _ in selected} == expected_ids, "Same dated scenes required")
    reader = PublicWindows()
    try:
        result = {}
        for index, (item, meta) in enumerate(selected, 1):
            folder = out / f"aydincik_extra_date{index}"
            folder.mkdir()
            assets, quality = reader.read(item, circle, folder)
            paths = {
                band: retain(folder / f"{band}.tif", asset["sha256"])
                for band, asset in assets.items()
            }
            record = image_record(meta, paths, quality)
            record["new_crop_assets"] = assets
            result[meta["acquired_utc"][:10]] = record
        return result
    finally:
        reader.close()


def draw_aydincik(out, rows, points):
    fig, axes = plt.subplots(3, 2, figsize=(10, 13), layout="constrained")
    for panels, row in zip(axes, rows, strict=True):
        for ax, record in zip(panels, row["images"], strict=True):
            with rasterio.open(ROOT / record["visual"]) as src:
                circle = projected_circle(points[row["id"]], src.crs)
                x, y = circle.centroid.coords[0]
                ax.imshow(src.read().transpose(1, 2, 0), extent=plotting_extent(src))
                ax.plot(*circle.exterior.xy, color="#ffdf24", linewidth=1.5)
                ax.scatter(x, y, marker="+", color="white")
                ax.set(xlim=(x - 330, x + 330), ylim=(y - 330, y + 330))
            ax.set_title(f"{row['id'][-6:]} | {record['acquired_utc'][:10]}")
            ax.set_axis_off()
    fig.suptitle("Aydıncık | Üç yönelime duyarlı tespit\nSarı: 250 m görüntü inceleme çevresi")
    fig.savefig(out / "aydincik_review.png", dpi=140)
    plt.close(fig)


def write_review(out, rows):
    group_labels = {
        "method_pilot": "Pilot",
        "aydincik_pembecik": "Aydıncık",
        "urla_karaburun": "Urla",
    }
    lines = [
        "# İlk tespitlerde örtü inceleme tablosu",
        "",
        "Tarihler UTC. Oran CORINE 2018 kod grubunun 180 olası yönelimdeki aralığıdır.",
        "Pilot bağlantıları okuma kaydına, açık olay bağlantıları 250 m çevreyi kapsayan "
        "RGB kesitine gider.",
        "Görsel ön not ve kaynak uyuşmazlığı inceleme içindir.",
        "",
        "| Grup / Nokta | Tarih | CORINE merkez | Alan aralığı | Olay öncesi görüntüler "
        "| İnsan ön notu | İnceleme işaretleri |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in rows:
        lo, hi = row["nominal"]["woody_fraction"]
        images = []
        for image in row["images"]:
            target = ROOT / (image.get("visual") or image["receipt_path"])
            link = Path(relpath(target, out)).as_posix()
            images.append(f"[{image['acquired_utc'][:10]}]({link})")
        name = row["code"] or row["id"][-6:]
        group = group_labels[row["cohort"]]
        flags = ", ".join(row["review_flags"]) or "—"
        note = "Var" if row["researcher_notes"] else "—"
        lines.append(
            f"| {group} / {name} | {row['day']} | {row['center_clc']} | "
            f"%{lo * 100:.1f}–{hi * 100:.1f} | {', '.join(images) or '—'} | {note} | {flags} |"
        )
    (out / "inceleme_tablosu.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    pins = {}

    def retain(path, expected=None):
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained source")
        actual = sha(path)
        require(expected is None or actual == expected, "Changed input")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    reports = []
    for folder, expected in INPUTS:
        path = retain(BASE / folder / "readback.json", expected)
        reports.append((path.parent, json.loads(path.read_text(encoding="utf-8"))))
    (_, rotation), (_, pilot), (_, note_report), (public_dir, public), (coast_dir, coast) = reports
    points = {row["id"]: row for row in public["first_points"]}
    pilot_rows = {row["detection_id"]: row for row in pilot["rows"]}
    notes = {row["detection_id"]: row for row in note_report["rows"]}
    require(len(points) == 46 and len(pilot_rows) == 25 and len(notes) == 3, "Review denominators")
    windows = [(points[w["point_id"]]["case"], public_dir, w) for w in public["successful_windows"]]
    windows.extend(
        (points[coast["point_id"]]["case"], coast_dir, w) for w in coast["sentinel_windows"]
    )
    by_point = local_images(points, windows, retain)
    require(not by_point[EXTRA_POINT], "Unexpected local coverage for extra point")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "candidate_cover_readiness_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    expected_ids = {w["item_id"] for case, _, w in windows if case == "aydincik_pembecik"}
    failure = None
    try:
        by_point[EXTRA_POINT] = read_missing(points[EXTRA_POINT], out, expected_ids, retain)
    except Exception as exc:
        failure = type(exc).__name__
    rows = []
    for source in rotation["points"]:
        key = source["id"]
        prior = pilot_rows.get(key)
        note = notes.get(key)
        history = list(prior["human_note_history"]) if prior else []
        if note:
            history.append(
                {"source": "pu_researcher_cover_notes", "record": note["researcher_note"]}
            )
        images = prior["image_evidence"] if prior else list(by_point.get(key, {}).values())
        if prior:
            for image in images:
                retain(ROOT / image["receipt_path"])
            require(
                prior["local_context_2018"]["center_code"] == source["center_clc"], "Pilot identity"
            )
        cutoff = utc_time(source["day"] + "T00:00:00Z")
        require(
            all(utc_time(img["acquired_utc"]) < cutoff for img in images), "Pre-event acquisition"
        )
        lo, hi = source["nominal"]["woody_fraction"]
        flags = []
        if lo < 0.5 <= hi:
            flags.append("yönelime duyarlı")
        elif (source["center_clc"] in WOODY) != (lo >= 0.5):
            flags.append("merkez–alan farkı")
        if source["nominal"]["water_fraction"][0] > 0:
            flags.append("su kesişimi")
        if (
            note
            and note["researcher_note"].get("map_comparison")
            == "different_context_between_image_and_older_map"
        ):
            flags.append("eski harita–görsel farkı")
        if not images:
            flags.append("tam çevre görüntüsü yok")
        rows.append(
            {
                **source,
                "images": sorted(images, key=lambda image: image["acquired_utc"]),
                "researcher_notes": history,
                "review_flags": flags,
                "cell_context": prior["prediction_cell_context_2017"] if prior else None,
                "habitat_admission": "undecided",
                "target": None,
            }
        )
    require(len(rows) == len({row["id"] for row in rows}) == 71, "Complete distinct rows")
    require(sum(bool(row["researcher_notes"]) for row in rows) == 13, "Retained researcher notes")
    borderline = [
        r
        for r in rows
        if r["cohort"] == "aydincik_pembecik" and "yönelime duyarlı" in r["review_flags"]
    ]
    require(len(borderline) == 3, "Three borderline points")
    if all(len(row["images"]) == 2 for row in borderline):
        draw_aydincik(out, borderline, points)
    write_review(out, rows)
    for name in (
        Path(__file__),
        Path(__file__).with_name("review_public_event_cover.py"),
        ROOT / "src/wildfire_risk_prediction/imagery_review.py",
        ROOT / "src/wildfire_risk_prediction/public_sentinel_windows.py",
    ):
        retain(name.resolve())
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "Inputs changed")
    report = {
        "source_sha256": pins,
        "rows": rows,
        "public_points_with_image": dict(
            Counter(r["cohort"] for r in rows if r["cohort"] != "method_pilot" and r["images"])
        ),
        "review_flags": dict(Counter(f for row in rows for f in row["review_flags"])),
        "additional_crop_failure": failure,
        "artifact_sha256": {path.name: sha(path) for path in out.iterdir() if path.is_file()},
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    receipt = out / "readback.json"
    receipt.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    require(json.loads(receipt.read_text(encoding="utf-8")) == report, "Readback identity")
    print(
        receipt.relative_to(ROOT).as_posix(),
        sha(receipt),
        report["public_points_with_image"],
        failure,
    )


if __name__ == "__main__":
    main()
