"""Offline 25-point habitat evidence register and focused researcher review sheet."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from wildfire_risk_prediction.habitat_evidence import assemble_review

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "native": (
        "native_candidate_cover_v1/20261023T143656Z_90c1c93b",
        "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b",
    ),
    "first": (
        "preevent_image_windows_v1/20261023T152456Z_e03ae61d",
        "a3d1378c3f13a2b1947b045aaa2f296426bdfb4246861160aa83adf3caa6a5f8",
    ),
    "context": (
        "linked_candidate_context_v1/20261022T210339Z_23e2e5a4",
        "58363f7e1640af945195ecf9d13144a5ec4951fb259a30816274c12956710de8",
    ),
    "dates": (
        "preevent_date_comparison_v1/20261023T154219Z_144befb7",
        "f50778b9bd1a344c35336273fb46d19258481dc50676a692682e8772bd8b468d",
    ),
    "cards": (
        "preevent_review_cards_v1/20261023T152812Z_f80d7979",
        "3b91679a93850141ea8c338cc6e275b36c46a4b230571155cc61c8c8d7437d24",
    ),
    "human": (
        "preevent_researcher_review_v1/20261023T153234Z_ecee9147",
        "36fac85b3d6fe2f288af7070b70cfed5b037f70bd5b0601646a2eeb38e184645",
    ),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    def offline(*args, **kwargs):
        raise RuntimeError("Offline review only")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = offline
    pins, folders, reports = {}, {}, {}

    def pin(path, expected=None):
        actual = sha(path)
        if expected is not None and actual != expected:
            raise ValueError("Changed source")
        pins[path.relative_to(ROOT).as_posix()] = actual

    for role, (relative, digest) in SOURCES.items():
        folder = BASE / relative
        pin(folder / "readback.json", digest)
        report = json.loads((folder / "readback.json").read_text())
        for name, expected in report.get("artifact_sha256", {}).items():
            pin(folder / name, expected)
        for name, expected in report.get("input_sha256", {}).items():
            pin(ROOT / name, expected)
        folders[role], reports[role] = folder, report
    pin(Path(__file__).resolve())
    pin(ROOT / "src/wildfire_risk_prediction/habitat_evidence.py")
    pin(ROOT / "configs/habitat_scope_direction_v1.json")
    native = pd.read_csv(folders["native"] / "native_point_context.csv")
    quality = pd.read_csv(folders["first"] / "quality.csv")
    witnesses = pd.read_csv(folders["context"] / "scenario_first_point_witnesses.csv")
    cases = pd.read_csv(folders["context"] / "case_cover_reference_context.csv")
    rows = assemble_review(native, quality, reports["human"]["records"], witnesses)
    if len(rows) != 25 or len(cases) != 21:
        raise ValueError("Expected limited review cohort")
    relations = witnesses[
        ["detection_id", "scenario", "cluster_id", "grid_id", "prediction_timestamp_utc"]
    ].drop_duplicates()
    relations = relations.merge(
        cases[
            [
                "grid_id",
                "prediction_timestamp_utc",
                "review_unit_id",
                "primary_province",
                "candidate_review_category",
                "daily_observation_status",
                "independent_event_identity_proven",
            ]
        ],
        on=["grid_id", "prediction_timestamp_utc"],
        validate="many_to_one",
        how="left",
        indicator=True,
    )
    if not relations._merge.eq("both").all():
        raise ValueError("Missing point-case relation")
    relations = relations.drop(columns="_merge")
    alternatives = pd.read_csv(folders["dates"] / "comparison.csv")
    rows["available_image_dates"] = [
        3 if i in set(alternatives.detection_id) else 1 for i in rows.detection_id
    ]
    out = (
        BASE
        / "habitat_evidence_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    rows.to_csv(out / "point_evidence.csv", index=False)
    relations.to_csv(out / "point_case_relations.csv", index=False)
    pd.testing.assert_frame_equal(rows, pd.read_csv(out / "point_evidence.csv"), check_dtype=False)
    pd.testing.assert_frame_equal(
        relations.reset_index(drop=True),
        pd.read_csv(out / "point_case_relations.csv"),
        check_dtype=False,
    )
    review = []
    lines = [
        "# 25 nokta — örtü inceleme kaydı",
        "",
        "Bu tablo nihai habitat/yangın kabulü değildir.",
        "",
        "| Nokta | 2017 merkez sınıfı | Yaklaşık alanda orman+çalı % | "
        "Araştırmacı ön notu | Görsel |",
        "|---|---|---:|---|---|",
    ]
    for r in rows.itertuples():
        card = folders["cards"] / f"{r.detection_id}.png"
        lines.append(
            f"| {r.detection_id} | {r.center_cover_group_2017} | "
            f"{100 * r.forest_shrub_fraction_of_entire_support:.2f} | "
            f"{r.researcher_preliminary_context or 'İncelenmedi'} | [Aç]({card.as_posix()}) |"
        )
        review.append(
            {
                "detection_id": r.detection_id,
                "card_sha256": sha(card),
                "natural_woody_cover": None,
                "managed_woody_crop_or_parcels": None,
                "built_or_industrial_context": None,
                "mixed_support": None,
                "image_interpretable": None,
                "reason": None,
                "researcher": None,
                "reviewed_utc": None,
                "habitat_admission": "undecided",
                "target": None,
            }
        )
    (out / "review_index.md").write_text("\n".join(lines), encoding="utf-8")
    dump(
        out / "new_review_template.json",
        {"purpose": "new_observations_not_replacement_of_prior_notes", "records": review},
    )
    shapes = {
        p["detection_id"]: p
        for p in json.loads((folders["native"] / "approximate_support_geometry.json").read_text())[
            "points"
        ]
    }
    focused = rows.loc[rows.center_cover_group_2017.isin(["forest", "shrub"])]
    if len(focused) != 4:
        raise ValueError("Expected four reference forest/shrub centers")
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    order = []
    for code, ax, r in zip(["D", "E", "F", "C"], axes.flat, focused.itertuples(), strict=True):
        folder = folders["first"] / r.detection_id
        receipt = json.loads((folder / "receipt.json").read_text())
        with rasterio.open(folder / "visual.tif") as src:
            image = np.dstack((np.moveaxis(src.read(), 0, -1), src.dataset_mask()))
            b = src.bounds
            conversion = Transformer.from_crs(6933, src.crs, always_xy=True)
            p = shapes[r.detection_id]
            cx, cy = conversion.transform(*p["native_center_6933"])
            x, y = conversion.transform(*zip(*p["approximate_corners_6933"], strict=True))
            ax.imshow(image, extent=[b.left - cx, b.right - cx, b.bottom - cy, b.top - cy])
        ax.plot(np.asarray(x) - cx, np.asarray(y) - cy, color="yellow", linewidth=1.5)
        ax.plot(0, 0, "+", color="red", markersize=10)
        ax.set_title(
            f"{code} — {r.detection_id}\n{receipt['acquired_utc'][:10]} | "
            f"Eski haritada %{100 * r.forest_shrub_fraction_of_entire_support:.1f} orman/çalı",
            fontsize=10,
        )
        ax.set_xlabel("Doğu-batı (m)")
        ax.set_ylabel("Kuzey-güney (m)")
        order.append({"code": code, "detection_id": r.detection_id})
    fig.suptitle("Doğal orman/çalılık mı, parsellerle karışık örtü mü?", fontsize=16)
    fig.text(
        0.5,
        0.015,
        "Sarı: yaklaşık tespit alanı • Kırmızı: kaynak merkez • Oranlar 2017 haritasından\n"
        "C ön notu korunur. D/E/F yeni araştırmacı incelemesi bekler. Yangın etiketi değildir.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(out / "forest_shrub_focus.png", dpi=160)
    plt.close(fig)
    dump(out / "focus_order.json", order)
    for path, digest in pins.items():
        if sha(ROOT / path) != digest:
            raise ValueError("Source changed during run")
    dump(out / "input_manifest.json", pins)
    report = {
        "version": "habitat_evidence_review_v1",
        "status": "preliminary_review_only",
        "point_count": len(rows),
        "case_count": relations.review_unit_id.nunique(),
        "scenario_relation_count": len(relations),
        "reference_routes": rows.reference_review_route.value_counts().to_dict(),
        "researcher_confirmed_preliminary_contexts": int(
            rows.researcher_confirmation_recorded.sum()
        ),
        "new_researcher_reviews": 0,
        "labels_created": False,
        "rows_excluded": 0,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "final_merge_performed": False,
        "validation_or_final_test_accessed": False,
        "network_used": False,
        "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
    }
    dump(out / "readback.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "artifact_sha256"}, indent=2))
    print("Output:", out.relative_to(ROOT))
    print("Readback SHA:", sha(out / "readback.json"))


if __name__ == "__main__":
    main()
