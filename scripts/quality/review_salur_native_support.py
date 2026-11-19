"""Inspect one downloaded Salur fire center and approximate support, entirely offline."""

import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import pandas as pd
import rasterio
from exactextract import exact_extract
from prepare_salur_native_pair import BASE, ROOT, module
from pyproj import Geod, Transformer, network
from rasterio.windows import Window
from review_salur_local_cover import CGLS, CORINE, DELIVERY, PINS, VISUAL, class_areas
from shapely.geometry import Point, Polygon
from shapely.ops import transform

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.native_cover_context import (
    center_patch_polygon,
    overlap_reference_map,
    rounded_coordinate_matches,
)
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PLAN = BASE / "observation_core_transfer_v1/20261119T113530Z_92bbba6c/native_plan.json"
PLAN_SHA = "060a2456898a709a07b1a3e95b3abd05bf6921fa91bb11477a0439c6f4d4c4c8"
PROBE = BASE / "observation_core_native_v1/20261119T113907Z_b104e81d/native_probe.json"
PROBE_SHA = "2fb726fb9467091ddcffcbf49590bc26d6e9b97fd025a36a9de4541c357608b8"
POINTS = BASE / "salur_event_context_v1/20261118T230221Z_cab0c9e1/local_detections.csv"
POINTS_SHA = "2b28fed54408fd32495d3f925efa33c25f0145c0793284bb8afe6ebe87379199"
GUIDE = BASE / "salur_native_support_v1/sources/VIIRS_C2_AF-375m_User_Guide_1.2.pdf"
GUIDE_SHA = "fb957afb6e465cb312fb8229a2b6e424c489344bb09e76a7baee80a248d1ccb7"


def render(out, result):
    polygon = Polygon(result["approximate_support_corners_6933"])
    with rasterio.open(VISUAL) as ds:
        project = Transformer.from_crs(6933, ds.crs, always_xy=True).transform
        support = transform(project, polygon)
        point = Point(result["catalog_center_6933"])
        center = transform(project, point)
        circle = transform(project, point.buffer(250))
        rgb = ds.read().transpose(1, 2, 0)
        fig, axes = plt.subplots(1, 2, figsize=(12, 7))
        for ax, half in zip(axes, (1100, 500), strict=True):
            ax.imshow(
                rgb, extent=(ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
            )
            ax.plot(*support.exterior.xy, color="#ff44ff", lw=2, label="Yaklaşık piksel alanı")
            ax.plot(*circle.exterior.xy, color="cyan", ls="--", lw=1.2, label="Önceki 250 m çevre")
            ax.scatter(center.x, center.y, marker="+", s=140, c="cyan")
            ax.set_xlim(center.x - half, center.x + half)
            ax.set_ylim(center.y - half, center.y + half)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.plot(
                [center.x - half * 0.8, center.x - half * 0.8 + 200],
                [center.y - half * 0.8] * 2,
                c="white",
                lw=3,
            )
            ax.text(center.x - half * 0.8, center.y - half * 0.8 + 30, "200 m", c="white")
        axes[0].set_title("Salur ilk yerel tespiti: geniş bağlam")
        axes[1].set_title("Mor sınır içindeki örtü: yakın görünüm")
        axes[0].legend(loc="upper left", fontsize=9)
        fig.suptitle("20 Temmuz 2021 Sentinel-2B RGB • olay öncesi", fontsize=14)
        fig.text(
            0.5,
            0.1,
            "Mor sınır komşu piksel merkezlerinden yaklaşık hesaplandı; "
            "resmî piksel köşeleri değil.\n"
            "Alan 0,314 km²; yaklaşık %37,6'sı önceki 250 m çemberinin dışında.\n"
            "Pikselin hangi bölümünün yandığı bilinmiyor. "
            "Kalite biti veya orman haritası arazi onayı değildir.",
            ha="center",
            fontsize=10,
        )
        fig.subplots_adjust(top=0.88, bottom=0.23, wspace=0.08)
        path = out / "salur_native_support.png"
        fig.savefig(path, dpi=150, facecolor="white")
        plt.close(fig)
    return path


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline native support review")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    require(digest(PLAN) == PLAN_SHA and digest(PROBE) == PROBE_SHA, "Pinned pair admission")
    require(
        digest(GUIDE) == GUIDE_SHA and digest(VISUAL) == PINS[VISUAL], "Guide and pre-event RGB"
    )
    probe = json.loads(PROBE.read_text())
    done = json.loads((PROBE.parent / "completion_readback.json").read_text())
    require(done["report_sha256"] == PROBE_SHA and probe["plan_sha256"] == PLAN_SHA, "Completion")
    runner = module("salur_pair_runner", "scripts/firms/run_observation_core_pair.py")
    plan, pair = runner.load_plan(PLAN)
    require(pair["sample_id"] == "N20:2021209.1012", "Selected case granule only")
    cache = ROOT / probe["cache_directory"]
    require(
        cache.resolve().is_relative_to(ROOT / "data/raw/observation_core_v1"), "Contained raw cache"
    )
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    for source in pair["sources"]:
        check_file(paths[source["role"]], source)
    for path in (CGLS, CORINE, DELIVERY / "readback.json"):
        require(digest(path) == PINS[path], "Pinned cover input")
    require(digest(POINTS) == POINTS_SHA, "Pinned local catalog")
    points = pd.read_csv(POINTS)
    point = points.loc[points.detection_id.eq("N20_815590_134793")]
    require(len(point) == 1 and point.target.isna().all(), "Single unlabeled local point")
    point = point.iloc[0]
    inspector = module("salur_native_inspector", "scripts/firms/inspect_l2_observation_sample.py")
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = inspector.layer(stack, paths["fire"], "fire_mask")
        qa = inspector.layer(stack, paths["fire"], "algorithm_QA")
        lat = inspector.layer(stack, paths["geolocation"], "geolocation_data/latitude")
        lon = inspector.layer(stack, paths["geolocation"], "geolocation_data/longitude")
        inspector.validate_pair(paths["fire"], paths["geolocation"], mask.tags(), lat.tags())
        sparse = inspector.read_sparse(stack, paths["fire"], int(mask.tags()["FirePix"]))
        matches = rounded_coordinate_matches(
            point.latitude, point.longitude, sparse["FP_latitude"], sparse["FP_longitude"]
        )
        require(len(matches) == 1, "Unique five-decimal catalog/native match")
        index = int(matches[0])
        thermal = {
            name: float(inspector.layer(stack, paths["fire"], name).read(1).ravel()[index])
            for name in ("FP_T4", "FP_T5", "FP_Rad13", "FP_MeanRad13", "FP_power")
        }
        r, c = int(sparse["FP_line"][index]), int(sparse["FP_sample"][index])
        require(1 <= r < mask.height - 1 and 1 <= c < mask.width - 1, "Complete native patch")
        require(r % 32 not in (0, 31), "Same-scan patch required")
        window = Window(c - 1, r - 1, 3, 3)
        lng, lt = lon.read(1, window=window), lat.read(1, window=window)
        values, flags = mask.read(1, window=window), qa.read(1, window=window)
        require(
            lng.shape == lt.shape == values.shape == flags.shape == (3, 3), "Native patch shape"
        )
        require(
            int(values[1, 1]) == int(sparse["FP_confidence"][index]) == 9
            and point.confidence == "h",
            "High confidence mask agrees with catalog",
        )
        require(
            abs(lng[1, 1] - sparse["FP_longitude"][index]) <= 1e-5
            and abs(lt[1, 1] - sparse["FP_latitude"][index]) <= 1e-5,
            "Sparse/native orientation",
        )
        polygon = center_patch_polygon(lng, lt, r)
        bad, geo_bad, residual = inspector.input_quality_flags(flags[1, 1])
        scan = r // 32
        scan_fields = {
            name: inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + name)
            .read(1)
            .ravel()
            for name in ("scan_start_time", "scan_end_time", "scan_quality", "sensor_mode")
        }
        require(
            all(len(v) == mask.height // 32 for v in scan_fields.values()), "Scan metadata lengths"
        )
        leap = int(lat.tags()["TAI93_leapseconds"])
        require(0 <= leap <= 100, "Recorded time conversion")
        times = {
            name: (
                pd.Timestamp("1993-01-01T00:00:00Z")
                + pd.to_timedelta(float(scan_fields[name][scan]) - leap, unit="s")
            ).isoformat()
            for name in ("scan_start_time", "scan_end_time")
        }
        distance = Geod(ellps="WGS84").inv(
            point.longitude, point.latitude, float(lng[1, 1]), float(lt[1, 1])
        )[2]
    delivery = json.loads((DELIVERY / "readback.json").read_text())
    with rasterio.open(CGLS) as old, rasterio.open(CORINE) as corine:
        cgls = overlap_reference_map(polygon, old)
        projected = transform(
            Transformer.from_crs(6933, corine.crs, always_xy=True).transform, polygon
        )
        areas = class_areas(corine, projected)
        require(all(str(v) in delivery["legend"] for v in areas), "Mapped cover classes")
        classes = [
            {**delivery["legend"][str(v)], "raster_value": v, "fraction": a / projected.area}
            for v, a in sorted(areas.items())
        ]
        actual = exact_extract(
            corine,
            gpd.GeoDataFrame({"geometry": [projected]}, crs=corine.crs),
            ["unique", "frac"],
        )[0]["properties"]
        independent = dict(zip(map(int, actual["unique"]), map(float, actual["frac"]), strict=True))
        require(set(independent) == set(areas), "Independent classes")
        error = max(abs(independent[v] - a / projected.area) for v, a in areas.items())
        require(error < 1e-6, "Independent support area fractions")
    center = Point(
        Transformer.from_crs(4326, 6933, always_xy=True).transform(point.longitude, point.latitude)
    )
    result = {
        "scope": "single_Salur_native_center_support_diagnostic_only",
        "detection_id": point.detection_id,
        "sample_id": pair["sample_id"],
        "input_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                PLAN,
                PROBE,
                POINTS,
                CGLS,
                CORINE,
                DELIVERY / "readback.json",
                GUIDE,
                VISUAL,
                *paths.values(),
            ]
        },
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "src/wildfire_risk_prediction/native_cover_context.py",
                ROOT / "scripts/firms/inspect_l2_observation_sample.py",
            ]
        },
        "native_row_column": [r, c],
        "scan_index": scan,
        "scan_utc": times,
        "geolocation_scan_quality": int(scan_fields["scan_quality"][scan]),
        "sensor_mode": int(scan_fields["sensor_mode"][scan]),
        "catalog_native_center_distance_m": distance,
        "fire_mask_3x3": values.tolist(),
        "algorithm_QA_center": int(flags[1, 1]),
        "algorithm_QA_set_bits": [i for i in range(32) if int(flags[1, 1]) & (1 << i)],
        "m13_non_nominal": bool(int(flags[1, 1]) & (1 << 6)),
        "m13_non_nominal_cause_verified": False,
        "quality_flag_alone_used_to_reject_fire": False,
        "quality_semantics_source": "Collection 2 user guide v1.2, printed p.5 Table 2",
        "sparse_thermal_fields": thermal,
        "input_non_nominal": bool(bad),
        "geo_non_nominal": bool(geo_bad),
        "residual_bowtie": bool(residual),
        "approximate_support_corners_6933": list(map(list, polygon.exterior.coords)),
        "approximate_support_area_m2": polygon.area,
        "catalog_center_6933": list(center.coords[0]),
        "support_fraction_inside_prior_250m_review_circle": polygon.intersection(
            center.buffer(250)
        ).area
        / polygon.area,
        "official_pixel_footprint": False,
        "true_subpixel_fire_location_known": False,
        "cgls_2017": cgls,
        "corine_2018_classes": classes,
        "independent_fraction_error": error,
        "habitat_admission": "undecided",
        "gate": specification(),
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "heldout_data_read": False,
        "network_used": False,
    }
    out = (
        BASE
        / "salur_native_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    figure = render(out, result)
    result["artifact_sha256"] = {figure.name: digest(figure)}
    for source in pair["sources"]:
        check_file(paths[source["role"]], source)
    require(
        result["gate"]["daily_observation_status"] == "unknown"
        and not any(
            result["gate"][k]
            for k in ("positive_label_permitted", "negative_label_permitted", "model_ready")
        ),
        "Closed admission",
    )
    for relative, expected in result["input_sha256"].items():
        require(digest(ROOT / relative) == expected, "Input closure")
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text(encoding="utf-8")) == result, "JSON readback")
    print(out.relative_to(ROOT), digest(report))
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "native_row_column",
                    "scan_utc",
                    "approximate_support_area_m2",
                    "support_fraction_inside_prior_250m_review_circle",
                    "corine_2018_classes",
                    "input_non_nominal",
                    "geo_non_nominal",
                    "residual_bowtie",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
