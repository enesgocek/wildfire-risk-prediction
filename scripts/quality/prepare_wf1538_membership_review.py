"""Bind human cover notes to concrete WF1538 membership options, without choosing either."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import pandas as pd
from prepare_marmaris_native_pair import write
from shapely.geometry import Point, Polygon

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows, specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
NATIVE = BASE / "wf1538_native_support_v1/20261119T181411Z_926a75aa/readback.json"
COVER = BASE / "wf1538_cover_review_v1/20261119T181659Z_55e092be/readback.json"
TEMPORAL = BASE / "wf1538_temporal_context_v1/20261119T181852Z_4b9b09f1/readback.json"
PRIOR = BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json"
NOTES = ROOT / "configs/wf1538_cover_notes_v1.json"
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
PINS = {
    NATIVE: "412c2a3209ea52b67c79f0460eefa31a3ade7c67fbad25ef8c3b5e22b198003a",
    COVER: "55ac06f4bb6e749a6dffae96c4d92c402b11449937481feba1647a26669146c1",
    TEMPORAL: "0998fc93977f1f35d01e69d8a28fddbf6ca26420d30573aac1ab56d38ec35e11",
    PRIOR: "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
}
CELL = "E6933_5K_V1_C642_R876"


def validate_notes(notes):
    require(
        notes["parent_sha256"] == PINS[COVER] and set(notes["notes"]) == {"A", "B"},
        "Same two-area human review",
    )
    b = notes["notes"]["B"]
    require(b["detection_id"] == "N20_815590_170090", "Same candidate support")
    require(
        notes["percentages_are_measured_area_fractions"] is False
        and b["landform_percentage_is_bare_ground_fraction"] is False
        and b["percentages_form_disjoint_landcover_classes"] is False
        and b["inferred_remainder_percent_created"] is False
        and b["road_percent_explicitly_reported"] is None,
        "Visual estimates; landform is not a disjoint vegetation class",
    )
    require(
        notes["L_memberships_created"] == 0
        and notes["positive_label_permitted"] is False
        and notes["negative_label_permitted"] is False
        and notes["daily_observation_status"] == "unknown"
        and notes["habitat_threshold_accepted"] is False
        and notes["same_physical_fire_verified"] is False
        and notes["training_authorized"] is False
        and notes["final_merge_permitted"] is False,
        "Cover note does not open membership or label gates",
    )


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned raw, cover, ancestry and grid")
    native, cover, temporal, prior = [
        json.loads(p.read_text(encoding="utf-8")) for p in (NATIVE, COVER, TEMPORAL, PRIOR)
    ]
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    validate_notes(notes)
    figure = COVER.parent / "wf1538_cover_review.png"
    require(digest(figure) == notes["figure_sha256"], "Human note bound to actual figure")
    require(cover["state"] == "researcher_review_pending", "Preserve original pre-note evidence")
    require(
        all(digest(ROOT / n) == h for n, h in prior["input_sha256"].items()),
        "Prior L and U unchanged",
    )
    source = Point(native["source_point_6933"])
    center = Point(native["native_center_6933"])
    support = Polygon(native["approximate_support_corners_6933"])
    grid = gpd.read_file(GRID).to_crs(6933)
    source_cells = sorted(grid.loc[grid.geometry.covers(source), "grid_id"])
    center_cells = sorted(grid.loc[grid.geometry.covers(center), "grid_id"])
    support_cells = sorted(grid.loc[grid.geometry.intersects(support), "grid_id"])
    require(source_cells == center_cells == support_cells == [CELL], "Observed one-cell geometry")
    require(not support.covers(source), "Source remains outside approximate fire support")
    window = detection_windows(pd.Series([native["start_utc"]])).iloc[0]
    require(
        window.prediction_timestamp_utc == pd.Timestamp("2022-05-27T00:00:00Z"),
        "Native target-day mapping",
    )
    require(
        all(
            h["diagnostic_window_start_utc"] == "2022-05-27T00:00:00+00:00"
            for h in native["source_row"]["clock_hypotheses"]
        ),
        "Both source clock hypotheses give the same diagnostic day",
    )
    for scenario in temporal["scenarios"]:
        for check in scenario["checks"].values():
            require(
                check["prefix_history_preserved"] and not check["has_preT_catalogue_ancestry"],
                "Bounded catalogue history",
            )
            require(
                all(b["earliest_grid_ids"] == [CELL] for b in check["anchor_births"]),
                "Same first cell in bounded scenarios",
            )
    out = (
        BASE
        / "wf1538_membership_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    record = {
        "source_archive_row": "WF1538",
        "catalogue_id": native["detection_id"],
        "grid_id": CELL,
        "prediction_timestamp_utc": window.prediction_timestamp_utc.isoformat(),
        "target_end_inclusive_utc": window.target_end_inclusive_utc.isoformat(),
        "current_membership": "review_unassigned",
        "target": None,
        "option_A_recommended": "retain_measured_review_case_without_L_assignment",
        "option_B": "prepare_possible_noisy_L_proposal_with_unverified_source_link",
    }
    pd.DataFrame([record]).to_csv(out / "conditional_cell_options.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    vicinity = source.buffer(650).union(support)
    grid.loc[grid.geometry.intersects(vicinity)].plot(
        ax=ax, facecolor="#f4f6f5", edgecolor="#505b65"
    )
    ax.fill(*support.exterior.xy, color="#d437be", alpha=0.25, label="Yaklaşık yangın pikseli")
    ax.plot(*support.exterior.xy, color="#d437be")
    ax.scatter(source.x, source.y, c="#b18200", marker="*", s=150, label="Kaynak A")
    ax.scatter(center.x, center.y, c="#168399", marker="+", s=110, label="Uydu merkezi B")
    ax.plot([source.x, center.x], [source.y, center.y], c="#606875", ls="--")
    ax.set_xlim(vicinity.bounds[0], vicinity.bounds[2])
    ax.set_ylim(vicinity.bounds[1], vicinity.bounds[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(
        "WF1538 • aynı 5 km hücre, farklı nokta/piksel\nC642/R876 • T: 27 Mayıs 2022 00:00 UTC"
    )
    ax.legend(loc="lower left", fontsize=9)
    fig.text(
        0.5,
        0.02,
        "Kaynak noktasının yaklaşık piksel sınırına uzaklığı: 126 m.\n"
        "Konum hata sınırı bilinmiyor; aynı hücre aynı yangın demek değil.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out / "source_pixel_and_cell.png", dpi=110)
    plt.close(fig)
    result = {
        "status": "human_cover_note_recorded_membership_direction_pending",
        "researcher_cover_notes": notes,
        "source_cells": source_cells,
        "native_center_cells": center_cells,
        "approximate_fire_support_cells": support_cells,
        "source_inside_fire_support": False,
        "source_to_support_projected_m": source.distance(support),
        "conditional_options": record,
        "recommended_option": "A_retain_review_unassigned",
        "recommendation_reason": (
            "Source coordinate role and location error are unverified; "
            "same coarse cell is not an independent same-fire link"
        ),
        "source_clock_standard_resolved": False,
        "same_physical_fire_verified": False,
        "natural_woodland_vs_plantation_vs_agriculture_resolved": False,
        "previous_possible_L_review_rows_unchanged": 2,
        "U_sha256_unchanged": prior["U_sample_sha256_unchanged"],
        "new_L_memberships": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
            NOTES.relative_to(ROOT).as_posix(): digest(NOTES),
            figure.relative_to(ROOT).as_posix(): digest(figure),
        },
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    write(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
