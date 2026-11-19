"""Prepare a reviewable one-case membership choice; both current options remain unassigned."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "marmaris_published_marker_v1/20261119T124316Z_6993b935/readback.json"
NATIVE = BASE / "marmaris_native_support_v1/20261119T130257Z_bf16c6bd/readback.json"
COVER = BASE / "marmaris_cover_review_v1/20261119T130607Z_f0819694/readback.json"
TEMPORAL = BASE / "marmaris_temporal_context_v1/20261119T131219Z_97f55f00/readback.json"
NOTES = ROOT / "configs/marmaris_cover_notes_v1.json"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
PINS = {
    SOURCE: "6672e96bb52dbc65d385b9debd00675528f868086b6eb0df2992feb6a438301b",
    NATIVE: "09baaccbd41d5e8a175b2bd988d46acf25c782fd5ac0b20ab21679bea6024ff4",
    COVER: "6bd38dabb3f24a6774a3a1a7586050eeae26f62c814aa8c7603d063340b38a61",
    TEMPORAL: "e8e0086ffb0caa73fcceb362e5a33bdb061978c4b33be566c99316f5d8264be0",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
}
CELL = "E6933_5K_V1_C541_R878"


def render(out, source, native, codes):
    project = Transformer.from_crs(6933, 32635, always_xy=True).transform
    lonlat = Transformer.from_crs(4326, 32635, always_xy=True).transform
    center = Point(lonlat(*source["estimates"]["all_seven"]["approximate_marker_lon_lat"]))
    polygons = [
        transform(project, Polygon(p["approximate_support_corners_6933"])) for p in native["points"]
    ]
    envelope = unary_union([*polygons, center]).buffer(500).bounds
    frame = gpd.read_file(GRID).to_crs(32635)
    cells = frame.loc[frame.intersects(unary_union(polygons))]
    fig, ax = plt.subplots(figsize=(9, 6))
    cells.plot(ax=ax, facecolor="#f2f5f4", edgecolor="#323c4b", linewidth=1.2)
    for point, polygon in zip(native["points"], polygons, strict=True):
        color = "#b528cf" if point["planned_primary_center"] else "#9aa5b1"
        ax.fill(*polygon.exterior.xy, color=color, alpha=0.25)
        ax.plot(*polygon.exterior.xy, color=color, linewidth=1)
        if point["detection_id"] in codes:
            x, y = polygon.centroid.coords[0]
            ax.text(x, y, codes[point["detection_id"]], ha="center", fontsize=10)
    for row in cells.itertuples():
        x, y = (
            row.geometry.intersection(unary_union(polygons).envelope)
            .representative_point()
            .coords[0]
        )
        ax.text(
            x,
            envelope[3] - 170,
            row.grid_id.removeprefix("E6933_5K_V1_"),
            ha="center",
            fontsize=11,
            weight="bold",
        )
    ax.scatter(center.x, center.y, marker="*", color="#b27a00", s=140)
    ax.text(center.x - 200, center.y + 100, "S", color="#986500", fontsize=11)
    ax.set(
        xlim=(envelope[0] - 200, envelope[2]),
        ylim=(envelope[1], envelope[3] + 400),
        xlabel="UTM 35N doğu (m)",
        ylabel="UTM 35N kuzey (m)",
    )
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.set_aspect("equal")
    ax.set_title("Marmaris • beş ana merkez ve 1 km ayarındaki 15 kayıtlık bağlam")
    fig.text(
        0.5,
        0.025,
        "Mor: planlanan beş merkez • Gri: bağlantı bağlamındaki diğer on kayıt\n"
        "S: yayımlanmış sembolün yaklaşık merkezi; kesin tutuşma yeri değil.\n"
        "Şema bir gerçek yangın sayımı, resmî piksel sınırı veya L ataması değildir.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(out / "source_and_first_cells.png", dpi=110, facecolor="white")
    plt.close(fig)


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned case reviews")
    source, native, cover, temporal = [
        json.loads(p.read_text()) for p in (SOURCE, NATIVE, COVER, TEMPORAL)
    ]
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    require(notes["parent_sha256"] == PINS[COVER], "Same researcher image set")
    figure = COVER.parent / "marmaris_cover_review.png"
    require(digest(figure) == notes["figure_sha256"], "Same viewed figure")
    require(notes["percentages_are_measured_area_fractions"] is False, "Visual estimates only")
    require(set(notes["notes"]) == set(cover["primary_index"]), "All five notes preserved")
    for code, note in notes["notes"].items():
        require(
            note["detection_id"] == cover["primary_index"][code]["detection_id"], "Code identity"
        )
    require(notes["notes"]["M2"]["preliminary_cover"] == "uncertain_wooded_cover", "M2 unresolved")
    require(
        all(
            not e["center_AOI_cells"] and e["visible_glyph_AOI_cells"] == [CELL]
            for e in source["estimates"].values()
        ),
        "Symbol overlap, never a snapped center",
    )
    appearances = {}
    for scenario in temporal["scenarios"]:
        for name, check in scenario["checks"].items():
            require(check["prefix_history_unchanged_by_later_data"], "No future history rewrite")
            require(
                not check["anchor_ids_with_preT_ancestry"], "Bounded catalog pre-T ancestry check"
            )
            require(check["matched_ancestry_starts_at_first_local_minute"], "Saved first minute")
            if name == "first_local":
                cells = set().union(
                    *(set(v["earliest_grid_ids"]) for v in check["matched_anchor_birth_candidates"])
                )
                for cell in cells:
                    appearances[cell] = appearances.get(cell, 0) + 1
    require(len(temporal["scenarios"]) == 9 and appearances[CELL] == 9, "Nine dependent scenarios")
    records = []
    for cell, count in sorted(appearances.items()):
        checked = [p for p in native["points"] if p["grid_id"] == cell]
        records.append(
            {
                "source_case_id": "marmaris_2022",
                "grid_id": cell,
                "prediction_timestamp_utc": "2022-06-21T00:00:00+00:00",
                "target_end_inclusive_utc": "2022-06-22T00:00:00+00:00",
                "first_cells_scenario_count_of_9": count,
                "both_symbol_fits_overlap_this_cell": cell == CELL,
                "symbol_center_inside_clipped_AOI": False,
                "native_checked_centers_in_1km_context": len(checked),
                "planned_primary_centers": sum(p["planned_primary_center"] for p in checked),
                "current_membership": "review_unassigned",
                "if_researcher_selects_option_A": "possible_noisy_L_proposal"
                if cell == CELL
                else "review_unassigned",
                "if_researcher_selects_option_B": "review_unassigned",
                "target": None,
            }
        )
    out = (
        BASE
        / "marmaris_L_direction_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(records).to_csv(out / "conditional_cell_options.csv", index=False)
    codes = {v["detection_id"]: k for k, v in notes["notes"].items()}
    render(out, source, native, codes)
    result = {
        "status": "concrete_membership_options_await_researcher_direction",
        "candidate_cell_if_option_A": CELL,
        "current_L_memberships_created": 0,
        "current_targets_assigned": 0,
        "global_mapping_rule_accepted": False,
        "source_coordinate_error_bound_known": False,
        "source_three_vs_four_starts_resolved": False,
        "positive_enrichment_verified": False,
        "class_conditional_selection_verified": False,
        "researcher_cover_notes": notes,
        "gate": specification(),
        "training_authorized": False,
        "final_merge_permitted": False,
        "input_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
            NOTES.relative_to(ROOT).as_posix(): digest(NOTES),
            figure.relative_to(ROOT).as_posix(): digest(figure),
        },
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    path = out / "readback.json"
    require(
        all(digest(ROOT / rel) == h for rel, h in result["input_sha256"].items()), "Input closure"
    )
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))


if __name__ == "__main__":
    main()
