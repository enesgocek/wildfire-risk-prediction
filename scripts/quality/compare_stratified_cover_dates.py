"""Compare retained pilot windows with one different date per selected detection."""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import rasterio
import requests
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_public_event_cover import QA_FLAGS, catalogue, plt, require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.preevent_imagery import prediction_time, utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

PILOT = BASE / "stratified_cover_pilot_v1/20261108T002035Z_de57b547"
PLAN = PILOT / "plan.json"
PLAN_SHA = "706a7c2ad0676f4bdb24df970e23880e81f7c94f082bde2d799a4a32ab0e55aa"
FIRST = PILOT / "recovery_20261108T002332Z_0e2a5d07/readback.json"
FIRST_SHA = "76492ab0bcc075cc1184de0cc75373510d519f635d23017ffebeead91ba083ec"
COVER_QUESTIONS = ("H01", "H03", "H15")


def flagged_fraction(quality):
    return sum(quality[key] for key in QA_FLAGS)


def check_assets(folder, record, pins):
    for band, meta in record["assets"].items():
        path = folder / f"{band}.tif"
        require(sha(path) == meta["sha256"], "Crop byte identity")
        pins[path.relative_to(ROOT).as_posix()] = meta["sha256"]


def read_other(point, first, folder, session, reader):
    cutoff = prediction_time(point["detected_utc"])
    zone = 32635 if point["longitude"] < 30 else 32636
    project = Transformer.from_crs(4326, zone, always_xy=True)
    circle = Point(*project.transform(point["longitude"], point["latitude"])).buffer(250)
    support = transform(Transformer.from_crs(zone, 4326, always_xy=True).transform, circle)
    try:
        count, choices = catalogue(session, support, cutoff)
        other = next(
            (
                (item, meta)
                for item, meta in choices
                if meta["acquired_utc"][:10] != first["acquired_utc"][:10]
            ),
            None,
        )
        if other is None:
            return {"state": "no_second_date", "metadata_candidates": count}
        item, meta = other
        acquired = utc_time(meta["acquired_utc"])
        require(cutoff - timedelta(days=30) <= acquired < cutoff, "Pre-event window")
        target = transform(
            Transformer.from_crs(4326, item["properties"]["proj:epsg"], always_xy=True).transform,
            support,
        )
        folder.mkdir()
        assets, quality = reader.read(item, target, folder)
        return {
            "state": "read",
            "acquired_utc": meta["acquired_utc"],
            "item_id": item["id"],
            "scene_cloud_percent": meta["scene_cloud_percent"],
            "metadata_candidates": count,
            "assets": assets,
            "quality": quality,
            "selected_flag_fraction": flagged_fraction(quality),
            "crop_directory": folder.relative_to(ROOT).as_posix(),
        }
    except Exception as exc:
        return {"state": "failed", "error_type": type(exc).__name__}


def draw(path, rows):
    fig, axes = plt.subplots(len(rows), 2, figsize=(9, 4.25 * len(rows)), layout="constrained")
    for panels, row in zip(axes, rows, strict=True):
        for ax, data in zip(panels, (row["first"], row["second"]), strict=True):
            ax.set_axis_off()
            if data["state"] != "read":
                ax.set_title(f"{row['slot']} | İkinci kesit yok")
                continue
            with rasterio.open(ROOT / data["crop_directory"] / "visual.tif") as ds:
                ax.imshow(ds.read().transpose(1, 2, 0), extent=plotting_extent(ds))
                project = Transformer.from_crs(4326, ds.crs, always_xy=True)
                x, y = project.transform(row["longitude"], row["latitude"])
                ax.plot(*Point(x, y).buffer(250).exterior.xy, color="#ffdd32", linewidth=1.5)
                ax.scatter(x, y, color="white", marker="+")
                ax.set(xlim=(x - 370, x + 370), ylim=(y - 370, y + 370))
            date = data["acquired_utc"][:10]
            flags = 100 * data["selected_flag_fraction"]
            ax.set_title(f"{row['slot']} | {date} | SCL işaretli %{flags:.1f}")
    fig.suptitle("Aynı tespit çevresi | İlk ve alternatif olay öncesi görüntü")
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    require(sha(PLAN) == PLAN_SHA and sha(FIRST) == FIRST_SHA, "Frozen pilot inputs")
    plan, first = read_json(PLAN), read_json(FIRST)
    require(first["plan_sha256"] == PLAN_SHA, "Frozen plan identity")
    points = {r["slot"]: r for r in plan["selected"]}
    records = {r["slot"]: r for r in first["records"]}
    require(
        len(points) == len(records) == 24 and points.keys() == records.keys(), "Pilot identities"
    )
    quality_slots = sorted(
        slot for slot, r in records.items() if flagged_fraction(r["quality"]) > 0.5
    )
    require(quality_slots == ["H02", "H08", "H16", "H19"], "Frozen quality follow-up")
    slots = quality_slots + list(COVER_QUESTIONS)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = PILOT / f"alternate_dates_{stamp}"
    out.mkdir(exist_ok=False)
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    pins = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in (
            PLAN,
            FIRST,
            ROOT / "scripts/quality/review_public_event_cover.py",
            ROOT / "src/wildfire_risk_prediction/public_sentinel_windows.py",
            ROOT / "src/wildfire_risk_prediction/imagery_review.py",
            Path(__file__).resolve(),
        )
    }
    rows = []
    reader = PublicWindows()
    try:
        with requests.Session() as session:
            session.trust_env = False
            for slot in slots:
                point, original = points[slot], records[slot]
                require(
                    point["id"] == original["id"] and original["state"] == "read", "Point match"
                )
                check_assets(ROOT / original["crop_directory"], original, pins)
                second = read_other(point, original, out / slot, session, reader)
                if second["state"] == "read":
                    check_assets(out / slot, second, pins)
                rows.append(
                    {
                        **point,
                        "reason": "local_quality" if slot in quality_slots else "cover_ambiguity",
                        "first": {
                            **original,
                            "selected_flag_fraction": flagged_fraction(original["quality"]),
                        },
                        "second": second,
                        "target": None,
                        "habitat_admission": "undecided",
                    }
                )
                print(slot, second["state"], flush=True)
    finally:
        reader.close()
    require(all(sha(ROOT / p) == value for p, value in pins.items()), "Unchanged inputs")
    artifacts = {}
    for name, group in (
        ("quality_comparison.png", rows[: len(quality_slots)]),
        ("cover_comparison.png", rows[len(quality_slots) :]),
    ):
        draw(out / name, group)
        artifacts[name] = sha(out / name)
    report = {
        "source_sha256": pins,
        "rows": rows,
        "artifact_sha256": artifacts,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    receipt = out / "readback.json"
    write_json(receipt, report)
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))


if __name__ == "__main__":
    main()
