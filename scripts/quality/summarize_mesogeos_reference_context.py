"""Describe audited reference context, including outside-center examples, without labels."""

import csv
import hashlib
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyogrio
from shapely import affinity, wkt
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
FIRST = BASE / "mesogeos_reference_pilot_run_v1/20261124T231948Z_e9a7e57e"
GEO = BASE / "mesogeos_reference_geometry_review_v1/20261124T232735Z_136d2a12"
AUDIT = BASE / "mesogeos_reference_pilot_audit_v1/20261124T233152Z_7d080df8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    audit = json.loads((AUDIT / "readback.json").read_bytes())
    if sha(GEO / "readback.json") != audit["geometry_receipt_sha256"]:
        raise ValueError("Audited source geometry receipt")
    receipt = json.loads((GEO / "readback.json").read_bytes())
    points = {
        int(r["source_record_index"]): r for r in csv_rows(FIRST / "point_context_review.csv")
    }
    polygons = csv_rows(GEO / "perimeter_context_review.csv")
    outside = sorted(
        [r for r in polygons if float(r["native_point_to_final_perimeter_distance_m"]) > 0],
        key=lambda r: (
            float(r["native_point_to_final_perimeter_distance_m"]),
            int(r["source_record_index"]),
        ),
    )
    inside = sorted(
        [r for r in polygons if r["native_point_covered_by_final_perimeter"] == "True"],
        key=lambda r: int(r["source_record_index"]),
    )
    cases = [inside[0], outside[len(outside) // 2], outside[-1]]
    selected = [int(r["source_record_index"]) for r in cases]
    raw = ROOT / receipt["source_directory"]
    shapes = pyogrio.read_dataframe(
        raw / "med_burned_areas_updated.shp",
        columns=[],
        fids=selected,
        fid_as_index=True,
        use_arrow=False,
    )
    out = (
        BASE
        / "mesogeos_reference_context_summary_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.5), layout="constrained")
    examples = []
    for ax, record, title in zip(
        axes,
        cases,
        ["Merkez alan içinde", "Dışarıdaki örneklerin ortası", "En uzak dış merkez"],
        strict=True,
    ):
        index = int(record["source_record_index"])
        point = wkt.loads(points[index]["geometry_h"])
        shifted = affinity.translate(shapes.loc[index].geometry, -point.x, -point.y)
        clipped = shifted.intersection(Point(0, 0).buffer(1400))
        pieces = list(clipped.geoms) if hasattr(clipped, "geoms") else [clipped]
        for piece in pieces:
            if piece.geom_type != "Polygon":
                continue
            ax.fill(*piece.exterior.xy, color="#bad3e6", alpha=0.8)
            ax.plot(*piece.exterior.xy, color="#235878", linewidth=1)
            for ring in piece.interiors:
                ax.fill(*ring.xy, color="white")
        ax.add_patch(
            plt.Circle((0, 0), 1000, fill=False, linestyle="--", color="#777777", linewidth=1)
        )
        ax.scatter([0], [0], color="black", s=28, zorder=5)
        distance = float(record["native_point_to_final_perimeter_distance_m"])
        ax.set_title(
            f"{title}\nHam tarih {points[index]['IGNITION_D'][:10]} · {distance:.1f} m",
            fontsize=10,
        )
        ax.set(
            xlim=(-1350, 1350),
            ylim=(-1350, 1350),
            xlabel="Merkeze göre kaynak projeksiyonu m",
            ylabel="Kaynak projeksiyonu m",
        )
        ax.set_aspect("equal")
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.15)
        examples.append(
            {
                "source_record_index": index,
                "source_id": points[index]["id"],
                "native_date": points[index]["IGNITION_D"],
                "native_distance_m": distance,
                "selection": title,
            }
        )
    fig.suptitle(
        "MODIS tespit merkezi ve kaynaktaki nihai yanmış alan\n"
        "Mavi alan kaynak çokgeni · Siyah nokta tespit merkezi · Kesikli çember 1 km",
        fontsize=12,
    )
    fig.savefig(out / "point_perimeter_context.png", dpi=160)
    plt.close(fig)
    values = [float(r["native_point_to_final_perimeter_distance_m"]) for r in polygons]
    result = {
        "status": "audited_supplementary_context_summary_not_true_fire_validation",
        "analysis_date": "2026-11-25",
        "audit_receipt_sha256": sha(AUDIT / "readback.json"),
        "geometry_receipt_sha256": sha(GEO / "readback.json"),
        "rows": len(polygons),
        "centers_inside_final_polygon": len(inside),
        "centers_outside_final_polygon": len(outside),
        "native_distance_m_min_median_max": [min(values), statistics.median(values), max(values)],
        "illustrative_cases": examples,
        "selection_is_representative_sample": False,
        "native_lookup_counts": audit["native_lookup_counts"],
        "new_S_or_Y_or_L": False,
        "final_merge": False,
        "artifact_sha256": {p.name: sha(p) for p in out.iterdir()},
        "producer_sha256": sha(Path(__file__)),
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
