"""Read two pre-event dates at two reported archive points for cover review."""

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

import rasterio
from audit_mersin_open_incidents import ARCHIVE, PINS, ROOT, read_incidents
from audit_stage_one_selection import verify
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_anamur_preevent_cover import UTM, fetch_images, plt
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.core_transfer import digest


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    verify(ARCHIVE, PINS[ARCHIVE])
    events, _ = read_incidents()
    ids = ("WF1578", "WF1579")
    project = Transformer.from_crs(4326, UTM, always_xy=True)
    circles = {
        key: Point(
            *project.transform(
                float(events.loc[key, "longitude"]), float(events.loc[key, "latitude"])
            )
        ).buffer(250)
        for key in ids
    }
    out = (
        ROOT
        / "outputs/reports/dataset/gulnar_reference_cover_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    print(out.relative_to(ROOT), flush=True)
    cutoff = datetime(2022, 9, 7, tzinfo=UTC)
    report = {
        "selection": "two_same_day_gulnar_silifke_archive_rows_identity_unresolved",
        "cutoff_utc": cutoff.isoformat(),
        "archive_sha256": PINS[ARCHIVE],
        "radius_m": 250,
        "coordinate_basis": "published_archive_point_start_unverified",
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    try:
        images, candidates = fetch_images(out, circles, cutoff)
        report.update(images=images, metadata_candidates=candidates)
    except Exception as error:
        report.update(status="source_access_incomplete", error_type=type(error).__name__)
        (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Source access incomplete", type(error).__name__, flush=True)
        return
    fig, axes = plt.subplots(2, 2, figsize=(10, 10), layout="constrained")
    for key, panels in zip(ids, axes, strict=True):
        for panel in panels:
            panel.set_axis_off()
        for panel, image in zip(panels, images[key], strict=False):
            panel.set_title(f"{key} | {image['acquired_utc'][:10]}")
            if image["state"] != "read":
                continue
            with rasterio.open(ROOT / image["crop_directory"] / "visual.tif") as source:
                panel.imshow(source.read().transpose(1, 2, 0), extent=plotting_extent(source))
                circle = transform(
                    Transformer.from_crs(UTM, source.crs, always_xy=True).transform, circles[key]
                )
                panel.plot(*circle.exterior.xy, color="#ffe000", linewidth=1.5)
                panel.scatter(circle.centroid.x, circle.centroid.y, marker="+", color="white")
    fig.suptitle(
        "Arşiv koordinatlarında olay öncesi örtü\nSarı çevre 250 m · Başlangıç konumu belirsiz"
    )
    image_path = out / "cover_review.png"
    fig.savefig(image_path, dpi=145)
    plt.close(fig)
    report["plot_sha256"] = digest(image_path)
    report["status"] = "dated_cover_crops_review_only"
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT), digest(path), flush=True)


if __name__ == "__main__":
    main()
