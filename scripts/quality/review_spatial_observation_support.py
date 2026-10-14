"""Offline geometry study of eight retained training swaths, never daily labels."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_support import overlap_bounds, spatial_support

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("outputs/reports/observation_coverage")
STEM = "l2_area_union_2019-01-14_SNPP_N20_8samples"
ANCHOR = "d4598b888465069898543ec844b83b17fd24f65e36f9a5ff46eedcd5f6dea1cc"
GROUPS = ("reconstructed_domain", "nominal_nonfire_land", "cloud")
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline geometry review")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT), "Project-local geometry source")
        require(path.is_file() and not path.is_symlink(), "Regular geometry source")
        digest = sha(path)
        require(expected is None or digest == expected, "Pinned geometry source changed")
        pins[path.relative_to(ROOT).as_posix()] = digest
        return path

    def report(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    def closed(value):
        require(value["daily_observation_status"] == "unknown", "Closed observation state")
        require(value["negative_label_permitted"] is False, "Closed negative permission")

    combined = report(SOURCE / f"{STEM}.json", ANCHOR)
    closed(combined)
    require(combined["day_utc"] == "2019-01-14", "Fixed training-only geometry day")
    require(combined["grid_count"] == 2899, "Fixed grid inventory")
    require(
        len(set(combined["sample_keys"])) == len(combined["sample_keys"]) == 8,
        "Eight distinct listed swaths",
    )
    retained("scripts/firms/combine_l2_area_estimates.py", combined["script_sha256"])
    protected = report(PROTECTED)
    for name, digest in protected.items():
        retained(name, digest)
    retained(Path(__file__).relative_to(ROOT))
    retained("src/wildfire_risk_prediction/observation_support.py")
    parts_path = retained(
        "data/interim/grid_aoi_parts.geojson",
        next(iter(combined["sources"].values()))["aoi_parts_sha256"],
    )
    parts = gpd.read_file(parts_path).to_crs(6933).sort_values("grid_id")
    ids = parts.grid_id.tolist()
    require(len(ids) == 2899 and len(set(ids)) == 2899, "AOI keys")
    regions = parts.geometry.to_numpy()
    require(shapely.is_valid(regions).all(), "Valid AOI")
    areas = shapely.area(regions)
    require((areas > 0).all() and np.isfinite(areas).all(), "Finite AOI areas")
    tolerance = np.maximum(0.05, areas * 1e-8)  # Geometry arithmetic tolerance, not admission.

    def layers(path, table):
        require(table.index.is_unique and set(table.index) == set(ids), "Exact area keys")
        table = table.loc[ids]
        require(
            table.daily_observation_status.eq("unknown").all()
            and table.negative_label_permitted.eq(False).all(),
            "Closed area rows",
        )
        require(np.allclose(table.aoi_area_m2, areas, rtol=1e-8, atol=0.05), "Same AOI")
        result = {}
        for group in GROUPS:
            frame = gpd.read_file(path, layer=group)
            require(frame.crs.to_epsg() == 6933, "EPSG:6933 geometry")
            require(frame.grid_id.is_unique and set(frame.grid_id) == set(ids), "Geometry keys")
            g = frame.set_index("grid_id").loc[ids].geometry.to_numpy()
            require(
                not shapely.is_missing(g).any() and shapely.is_valid(g).all(),
                "Valid explicit geometry",
            )
            require(
                (shapely.area(shapely.difference(g, regions)) <= tolerance).all(),
                "Geometry within AOI",
            )
            require(
                np.allclose(
                    shapely.area(g), table[f"{group}_area_estimate_m2"], rtol=1e-10, atol=0.01
                ),
                "Area/geometry readback",
            )
            result[group] = g
        for group in GROUPS[1:]:
            require(
                (
                    shapely.area(shapely.difference(result[group], result[GROUPS[0]])) <= tolerance
                ).all(),
                "Class is a reconstructed-domain subset",
            )
        return result

    union_path = retained(SOURCE / f"{STEM}.gpkg", combined["geometry_sha256"])
    union_csv = retained(SOURCE / f"{STEM}.csv", combined["area_csv_sha256"])
    saved = layers(union_path, pd.read_csv(union_csv).set_index("grid_id"))
    all_layers, swath_rows, time_rows, sensors, within_overlaps = [], [], [], [], []
    for key in combined["sample_keys"]:
        sensor, pair = key.split(":")
        require(sensor in {"SNPP", "N20"} and pair.startswith("2019014."), "Same-day swath")
        stem = f"l2_sample_{'N20_' if sensor == 'N20' else ''}{pair}"
        pin = combined["sources"][key]
        value = report(SOURCE / f"{stem}_area_estimate.json", pin["area_report_sha256"])
        closed(value)
        require(
            value["sensor"] == sensor
            and value["pair_key"] == pair
            and value["method"] == combined["method"],
            "Swath report identity",
        )
        require(
            value["sources"] == {k: v for k, v in pin.items() if k != "area_report_sha256"},
            "Swath lineage agreement",
        )
        retained("scripts/firms/estimate_l2_observed_area.py", pin["script_sha256"])
        prior = report(SOURCE / f"{stem}_audit.json", pin["previous_audit_sha256"])
        retained("scripts/firms/inspect_l2_observation_sample.py", prior["script_sha256"])
        gpkg = retained(SOURCE / f"{stem}_area_estimate.gpkg", pin["geometry_sha256"])
        csv = retained(SOURCE / f"{stem}_area_estimate.csv", pin["area_csv_sha256"])
        scans = pd.read_csv(retained(SOURCE / f"{stem}_scan_times.csv", pin["scan_times_sha256"]))
        require(scans.scan_index.is_unique and len(scans) == value["scan_count"], "Scan inventory")
        starts, ends = (
            pd.to_datetime(scans.start_utc, utc=True),
            pd.to_datetime(scans.end_utc, utc=True),
        )
        require(
            (starts < ends).all()
            and (starts > pd.Timestamp("2019-01-14", tz="UTC")).all()
            and (ends <= pd.Timestamp("2019-01-15", tz="UTC")).all(),
            "Inside target day",
        )
        g = layers(gpkg, pd.read_csv(csv).set_index("grid_id"))
        all_layers.append(g)
        sensors.append(sensor)
        within_geometry = shapely.intersection(g[GROUPS[1]], g[GROUPS[2]])
        within_overlaps.append(within_geometry)
        within_overlap = shapely.area(within_geometry)
        swath_rows.append(
            pd.DataFrame(
                {
                    "grid_id": ids,
                    "swath_key": key,
                    "land_m2": shapely.area(g[GROUPS[1]]),
                    "cloud_m2": shapely.area(g[GROUPS[2]]),
                    "within_granule_land_cloud_overlap_m2": within_overlap,
                }
            )
        )
        time_rows.append(
            {
                "swath_key": key,
                "start_utc": starts.min().isoformat(),
                "end_utc": ends.max().isoformat(),
                "land_km2": shapely.area(g[GROUPS[1]]).sum() / 1e6,
                "cloud_km2": shapely.area(g[GROUPS[2]]).sum() / 1e6,
                "within_granule_land_cloud_overlap_km2": within_overlap.sum() / 1e6,
            }
        )
        print("Verified geometry:", key, flush=True)

    for group in GROUPS:
        fresh = shapely.union_all(np.stack([g[group] for g in all_layers]), axis=0)
        require(
            (shapely.area(shapely.symmetric_difference(fresh, saved[group])) <= tolerance).all(),
            "Fresh/saved spatial union agreement",
        )
    domain, land, cloud = (saved[g] for g in GROUPS)
    domain_area, land_area, cloud_area = (shapely.area(g) for g in (domain, land, cloud))
    # Tiny geometric arithmetic discrepancies are bounded above, not evidence of larger domains.
    low, high = overlap_bounds(
        domain_area, np.minimum(land_area, domain_area), np.minimum(cloud_area, domain_area)
    )
    actual = shapely.area(shapely.intersection(land, cloud))
    require(
        ((actual >= low - tolerance) & (actual <= high + tolerance)).all(),
        "Measured overlap within area-only bounds",
    )
    _, repeated, max_area = spatial_support([g[GROUPS[1]] for g in all_layers])
    within_union = shapely.union_all(np.stack(within_overlaps), axis=0)
    only_cross_granule = shapely.area(
        shapely.difference(shapely.intersection(land, cloud), within_union)
    )
    require(
        np.allclose(actual, shapely.area(within_union) + only_cross_granule, rtol=1e-8, atol=0.05),
        "Within/cross-granule overlap partition",
    )
    by_sensor = {
        s: spatial_support(
            [g[GROUPS[1]] for g, sensor in zip(all_layers, sensors, strict=True) if sensor == s]
        )[0]
        for s in set(sensors)
    }
    both = shapely.area(shapely.intersection(by_sensor["SNPP"], by_sensor["N20"]))
    result = pd.DataFrame(
        {
            "grid_id": ids,
            "aoi_area_m2": areas,
            "domain_union_m2": domain_area,
            "land_union_m2": land_area,
            "cloud_union_m2": cloud_area,
            "land_cloud_overlap_m2": actual,
            "within_granule_overlap_union_m2": shapely.area(within_union),
            "land_cloud_overlap_only_across_granules_m2": only_cross_granule,
            "overlap_lower_bound_m2": low,
            "overlap_upper_bound_m2": high,
            "land_never_cloud_in_listed_swaths_m2": shapely.area(shapely.difference(land, cloud)),
            "land_in_at_least_two_granules_m2": shapely.area(repeated),
            "land_in_both_sensor_unions_m2": both,
            "max_single_granule_land_m2": max_area,
            "land_union_aoi_fraction": land_area / areas,
            "max_single_granule_land_aoi_fraction": max_area / areas,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
        }
    )
    swaths = pd.concat(swath_rows, ignore_index=True)
    thresholds = []
    for cut in (0.8, 0.9, 0.95):
        union_high = land_area / areas >= cut
        single_high = max_area / areas >= cut
        thresholds.append(
            {
                "illustrative_fraction": cut,
                "daily_union_grids": int(union_high.sum()),
                "single_granule_grids": int(single_high.sum()),
                "union_high_single_low_grids": int((union_high & ~single_high).sum()),
                "accepted_negative_grids": 0,
            }
        )
    # Selected geometry witnesses are explanatory, not a random accuracy sample.
    witness = result.assign(union_gain=(land_area - max_area) / areas).nlargest(3, "union_gain")
    out = (
        ROOT
        / "outputs/reports/dataset/spatial_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("grid_support.csv", result),
        ("swath_support.csv", swaths),
        ("swath_times.csv", pd.DataFrame(time_rows)),
        ("illustrative_screens.csv", pd.DataFrame(thresholds)),
        ("geometry_witnesses.csv", witness),
    ):
        path = out / name
        frame.to_csv(path, index=False)
        reread = pd.read_csv(path, float_precision="round_trip")
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), reread, check_dtype=False)
        artifacts[name] = sha(path)
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(bottom=0.26, top=0.84, left=0.08, right=0.98)
    x = np.arange(len(witness))
    for shift, col, label in (
        (-0.25, "land_union_aoi_fraction", "Daily listed-swath union"),
        (0, "max_single_granule_land_aoi_fraction", "Best single granule"),
        (0.25, "land_in_at_least_two_granules_m2", "At least two granules"),
    ):
        values = witness[col].to_numpy()
        if col.endswith("m2"):
            values = values / witness.aoi_area_m2.to_numpy()
        ax.bar(x + shift, values, 0.25, label=label)
    ax.set(
        xticks=x,
        xticklabels=[s.replace("E6933_5K_V1_", "") for s in witness.grid_id],
        ylim=(0, 1.05),
        ylabel="Fraction of AOI-clipped grid area",
        title="2019-01-14: largest union gains\n2,899 grids / 8 approximate swaths",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)
    fig.text(
        0.5,
        0.025,
        "Purpose-selected examples; granules are not independent passes. No labels.",
        fontsize=8,
        ha="center",
    )
    path = out / "geometry_witnesses.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    artifacts[path.name] = sha(path)
    summary = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed_diagnostic_only",
        "day_utc": combined["day_utc"],
        "method": combined["method"],
        "grid_count": len(ids),
        "listed_granules": len(all_layers),
        "aoi_km2": float(areas.sum() / 1e6),
        "land_union_km2": float(land_area.sum() / 1e6),
        "cloud_union_km2": float(cloud_area.sum() / 1e6),
        "land_cloud_overlap_km2": float(actual.sum() / 1e6),
        "within_granule_overlap_km2_sum": float(
            swaths.within_granule_land_cloud_overlap_m2.sum() / 1e6
        ),
        "within_granule_overlap_union_km2": float(shapely.area(within_union).sum() / 1e6),
        "land_cloud_overlap_only_across_granules_km2": float(only_cross_granule.sum() / 1e6),
        "land_in_at_least_two_granules_km2": float(shapely.area(repeated).sum() / 1e6),
        "land_in_both_sensor_unions_km2": float(both.sum() / 1e6),
        "illustrative_screens": thresholds,
        "protected_inputs_verified": len(protected),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limitations": [
            "One purpose-selected training day, no population error rate",
            "Approximate interiors, not official footprints or independent fire truth",
            "Within-granule overlap may include different scans/geometry approximation",
            "Spatial repeated support is not independent passes or continuous observation",
            "Raw product bytes not re-audited; retained report/geometry lineage checked",
            "No new pixel-level time geometry, habitat denominator or eligibility rule",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == summary, "Summary readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact closure")
    completion = {
        "status": "passed",
        "report_sha256": sha(path),
        "inputs_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    path = out / "completion_readback.json"
    path.write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    print("Spatial support review:", out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
