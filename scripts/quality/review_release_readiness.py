"""Fresh local part checks and a limited 400-row inspection preview, never final assembly."""

import argparse
import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import observation_table as obs
from wildfire_risk_prediction.background_readiness import (
    inspection_preview,
    release_state,
    review_background,
)
from wildfire_risk_prediction.dataset_contract import feature_dictionary
from wildfire_risk_prediction.feature_month import calendar_days
from wildfire_risk_prediction.final_merge_gate import require_final_merge_approval

ROOT = Path(__file__).resolve().parents[2]
PILOT = "outputs/reports/dataset/label_protocol_v1/20261014T193224Z_54fdbb95"
WINDOW = "outputs/reports/dataset/window_pilot_v1/20261014T191547Z_b008fcf9"
TRACE = "outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1"
OBS = "outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline release preflight")


def run(audit_name, audit_sha):
    started = datetime.now(UTC)
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        join.require(path.resolve().is_relative_to(ROOT), "Project-local preflight path")
        join.require(path.is_file() and not path.is_symlink(), "Regular preflight source")
        digest = sha(path)
        join.require(expected is None or digest == expected, "Pinned preflight source changed")
        pins[name] = digest
        return path

    def report(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    def packet(folder, expected):
        value = report(folder + "/readback.json", expected)
        for n, h in value["artifact_sha256"].items():
            retained(folder + "/" + n, h)
        return value

    feature = report(audit_name, audit_sha)
    join.require(
        audit_name.startswith("outputs/reports/dataset/candidate_audit_v1/"),
        "Fresh candidate audit path",
    )
    join.require(
        pd.Timestamp(feature["checked_at_utc"]) >= started - pd.Timedelta(2, unit="h"),
        "Recent candidate structural audit",
    )
    retained(feature["source_index"], feature["source_index_sha256"])
    pilot_report = packet(PILOT, "534d67c44cad55a267aaf57330b4396a9cbb6aa65baa8bfdd71b9037b7bb0cab")
    window = packet(WINDOW, "f79fcb11ede0b7d0c24cf3a976146eae6df871791e9abddf179b4fa96a9e195f")
    packet(TRACE, "f613115b0d67caea55353b102e2c420d1879666dfc8f94ea52416b0e9954fa11")
    join.require(
        not pilot_report["labels_created"] and not window["labels_created"],
        "Retained diagnostic packets",
    )
    sample = pd.read_csv(ROOT / PILOT / "pilot_protocol_review.csv", float_precision="round_trip")
    scans = pd.read_csv(ROOT / WINDOW / "window_scan_rows.csv", float_precision="round_trip")
    background, screens = review_background(sample, scans)
    join.require(len(sample) == 400 and len(background) == 181, "Fixed background selection")
    master = report(
        OBS + "/accepted_readback.json",
        "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    )
    join.require(
        master["status"] == "selected_observation_months_materialized"
        and master["scope_is_full_training"] is True,
        "Full observation source",
    )

    previews, part_rows = [], []
    grid_ids = None
    for ref in feature["reports"]:
        month = ref["month"]
        join.require(
            month in [f"{y}-{m:02d}" for y in range(2018, 2024) for m in range(1, 13)],
            "Training feature month only",
        )
        value = report(ref["path"], ref["sha256"])
        for name, expected in value["inputs_sha256"].items():
            if name in pins:
                join.require(pins[name] == expected, "Consistent shared source identity")
            else:
                retained(name, expected)
        folder = Path(ref["path"]).parent.as_posix()
        manifest = report(folder + "/month_manifest.json", ref["manifest_sha256"])
        parts = report(folder + "/parts/manifest.json", manifest["parts_manifest_sha256"])
        if grid_ids is None:
            name = "data/interim/grid_aoi_parts.geojson"
            grid = report(name, value["inputs_sha256"][name])
            grid_ids = {f["properties"]["grid_id"] for f in grid["features"]}
            join.require(len(grid_ids) == 2899, "Frozen project grid")
        selected = sample.loc[sample.prediction_timestamp_utc.str.startswith(month)]
        for entry in parts["days"]:
            day = entry["day"]
            part_row = {"month": month, "day": day, "rows": entry["rows"]}
            for kind in ("features", "provenance"):
                artifact = entry["artifacts"][kind]
                join.require(artifact["path"] == f"{month}/{day}_{kind}.csv", "Daily part path")
                name = folder + "/parts/" + artifact["path"]
                path = retained(name, artifact["sha256"])
                join.require(path.stat().st_size == artifact["bytes"], "Part byte size")
                part_row[kind + "_path"] = name
                part_row[kind + "_sha256"] = artifact["sha256"]
            part_rows.append(part_row)
            rows = selected.loc[selected.prediction_timestamp_utc.str.startswith(day)]
            if rows.empty:
                continue
            item = entry["artifacts"]["features"]
            join.require(item["path"] == f"{month}/{day}_features.csv", "Daily preview path")
            frame = pd.read_csv(
                retained(folder + "/parts/" + item["path"], item["sha256"]),
                float_precision="round_trip",
            )
            join.require(
                frame.columns.tolist() == join.KEYS + join.feature_names()
                and set(frame.grid_id) == grid_ids
                and frame.grid_id.is_unique,
                "Preview feature schema and grid",
            )
            join.require(
                join.utc_times(frame.prediction_timestamp_utc)
                .eq(pd.Timestamp(day, tz="UTC"))
                .all(),
                "Preview source day",
            )
            previews.append(frame.loc[frame.grid_id.isin(rows.grid_id)])
    preview = inspection_preview(sample, pd.concat(previews, ignore_index=True))
    join.require(
        len(preview) == 400 and preview.target.isna().all(), "Unlabelled inspection preview"
    )
    part_index = pd.DataFrame(part_rows).sort_values("day").reset_index(drop=True)
    join.require(
        len(part_index) == 2191 and part_index.day.is_unique and part_index.rows.sum() == 6351709,
        "Complete candidate part index",
    )

    totals = {"months_reread": 0, "rows_reread": 0, "missing_product_rows": 0}
    seen = set()
    for item in sorted(master["reports"], key=lambda r: r["month"]):
        month = item["month"]
        join.require(
            month not in seen and 2018 <= int(month[:4]) <= 2023, "Unique training observation"
        )
        seen.add(month)
        name = OBS + "/" + month
        join.require(report(name + "/readback.json") == item, "Observation report identity")
        frame = pd.read_csv(
            retained(name + "/observations.csv.gz", item["table_sha256"]),
            float_precision="round_trip",
        )
        stats = obs.summarize(frame)
        join.require(all(stats[k] == item[k] for k in stats), "Observation source statistics")
        times = join.utc_times(frame.prediction_timestamp_utc)
        join.require(
            set(frame.grid_id) == grid_ids
            and not frame.duplicated(join.KEYS).any()
            and set(times.dt.strftime("%Y-%m-%d")) == set(calendar_days(month))
            and times.eq(times.dt.floor("D")).all()
            and frame.groupby("prediction_timestamp_utc").size().eq(2899).all(),
            "Full observation keys/calendar",
        )
        totals["months_reread"] += 1
        totals["rows_reread"] += len(frame)
        totals["missing_product_rows"] += stats["rows_missing_product"]
        print("Observation preflight", month, totals["months_reread"], "/ 72", flush=True)
    observation_audit = {
        "status": "structural_readback_passed",
        **totals,
        "negative_label_permitted": False,
        "source_report": OBS,
    }
    evidence = {
        "features": {"path": audit_name, "sha256": audit_sha},
        "observation": OBS,
        "background": PILOT,
        "event_trace": TRACE,
    }
    state = release_state(feature, observation_audit, evidence)
    try:
        require_final_merge_approval(state, None)
    except PermissionError:
        pass
    else:
        raise ValueError("Unaccepted parts must not admit final assembly")
    retained(PROTECTED)
    protected = report(PROTECTED)
    for name, h in protected.items():
        retained(name, h)
    for name in (
        "scripts/quality/review_release_readiness.py",
        "src/wildfire_risk_prediction/background_readiness.py",
        "src/wildfire_risk_prediction/observation_review.py",
        "src/wildfire_risk_prediction/observation_window.py",
        "src/wildfire_risk_prediction/observation_table.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/final_merge_gate.py",
        "configs/final_merge_review_v1.json",
        "configs/inspection_release_v1.json",
        "src/wildfire_risk_prediction/dataset_contract.py",
    ):
        retained(name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/release_readiness_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("background_evidence.csv", background),
        ("hypothetical_screens.csv", screens),
        ("candidate_inspection_preview_400.csv", preview),
        ("full_candidate_parts_index.csv", part_index),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        strings = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda x: isinstance(x, str)).all()
        }
        actual = pd.read_csv(path, dtype=strings, float_precision="round_trip")
        pd.testing.assert_frame_equal(
            frame.astype(object).where(frame.notna(), None),
            actual.astype(object).where(actual.notna(), None),
            check_exact=True,
        )
        artifacts[name] = sha(path)
    for name, value in (
        ("parts_preflight.json", state),
        ("observation_fresh_audit.json", observation_audit),
        ("feature_dictionary.json", feature_dictionary()),
    ):
        path = out / name
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        join.require(json.loads(path.read_text()) == value, "Preflight JSON readback")
        artifacts[name] = sha(path)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.25, top=0.82, wspace=0.32)
    for count, color in ((1, "#777777"), (2, "#28759c")):
        subset = background.loc[background.background_land_sensor_count.eq(count)]
        axes[0].scatter(
            subset.obs_nominal_nonfire_land_fraction_estimate,
            subset.background_land_scan_longest_gap_hours,
            color=color,
            alpha=0.55,
            s=28,
            label=f"{count} sensör",
        )
    axes[0].axvline(0.9, color="#cc6b25", linestyle="--", linewidth=1)
    axes[0].axhline(12, color="#cc6b25", linestyle="--", linewidth=1)
    axes[0].set(
        xlabel="Nominal kara alan payı",
        ylabel="En uzun tarama zarfı boşluğu (saat)",
        title="181 amaçlı örnek; ham, ağırlıksız görünüm",
        xlim=(-0.03, 1.04),
        ylim=(9, 25),
    )
    axes[0].legend(loc="upper left", fontsize=8)
    names = ["Alan ≥0,80", "Alan ≥0,90", "Alan ≥0,90\n2 granül", "Alan ≥0,90\n2 sensör, ≤12 saat"]
    positions = list(range(4))
    axes[1].bar(positions, screens.raw_selected_units, color="#28759c", label="Koşulu sağlayan")
    axes[1].bar(
        positions,
        screens.selected_with_nominal_land_cloud_overlap,
        color="#cc6b25",
        label="Bunlarda kara/bulut çakışması",
    )
    for i, row in enumerate(screens.itertuples()):
        axes[1].text(i, row.raw_selected_units + 3, str(row.raw_selected_units), ha="center")
    axes[1].set_xticks(positions, names, fontsize=8)
    axes[1].set(ylabel="Örnek hücre-gün", title="Kabul edilmemiş kesimler", ylim=(0, 200))
    axes[1].legend(loc="upper right", fontsize=7)
    fig.suptitle("Gözlem tanıları: bu koşullar negatif etiket kabulü değildir", fontsize=12)
    fig.text(
        0.5,
        0.06,
        "Alan birleşimi ve tarama zarfı farklı ölçülerdir; sürekli bulutsuz gözlem değildir.\n"
        "Granüller bağımsız geçiş sayısı değildir. Eşik seçilmedi; hedefler boş kaldı.",
        ha="center",
        fontsize=9,
    )
    figure_path = out / "background_screens.png"
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)
    artifacts[figure_path.name] = sha(figure_path)
    guide = (
        "# Denetlenmiş eğitim adayı inceleme sürümü\n\n"
        "2018–2023: 72 ay, 2.191 gün, 2.899 hücre, 6.351.709 hücre-gün, 27 özellik.\n"
        "İnceleme teslimidir; 0/1 etiketli veya model eğitimine hazır sürüm değildir.\n\n"
        "- `candidate_inspection_preview_400.csv`: 400 örnek, 27 özellik ve boş target.\n"
        "- `full_candidate_parts_index.csv`: günlük feature/provenance dosyaları ve hash.\n"
        "  Yollar proje köküne göredir; veriler yeniden kopyalanmadı veya filtrelenmedi.\n"
        "- `feature_dictionary.json`: özellik anlamı, birim, kaynak zamanı ve eksik değer kuralı.\n"
        "- `background_evidence.csv`: 181 amaçlı arka plan adayının ayrı gözlem incelemesi.\n"
        "- `hypothetical_screens.csv`: kabul edilmemiş örnek kesimler; negatif etiket değildir.\n"
        "- `background_screens.png`: alan/zaman/sensör tanıları ve örnek kesimler.\n"
        "- `parts_preflight.json`: beş parçanın teknik/bilimsel kabul ayrımı.\n\n"
        "Eksik değerler korunur. 10 harita-su hücresi özgün tam takvimde tutulmuştur;\n"
        "kapsam filtresi ve önizleme bayrağı sonraki kullanımda uygulanmalıdır.\n"
        "400 örnek eşit olasılıklı değildir; genelleme için örnekleme ağırlıkları gereklidir.\n"
        "Hedef günü gözlem bilgisi model girdisi değildir. İlk tespit tutuşma zamanı değildir.\n"
        "2024/2025 bu teslimde yoktur; nihai birleştirme ve model eğitimi yapılmadı.\n\n"
        "İnsan incelemesi: sütun/birimleri, NaN yerlerini ve üç ayrı kalite bayrağını inceleyin.\n"
        "Boş target alanını sıfırla doldurmayın; bu görünüm yangın doğrulaması değildir.\n"
        "Sonraki kabul: olay/ilk hücre, kaynak semantiği, habitat, gözlem ve dönem sınırı.\n"
    )
    guide_path = out / "README.md"
    guide_path.write_text(guide, encoding="utf-8")
    join.require(guide_path.read_text(encoding="utf-8") == guide, "Inspection guide readback")
    artifacts[guide_path.name] = sha(guide_path)
    result = {
        "status": "readiness_evidence_readback_passed_release_blocked",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "background_units": len(background),
        "preview_rows": len(preview),
        "full_candidate_daily_parts": len(part_index),
        "fresh_feature_rows": feature["verified_candidate_rows"],
        "fresh_observation_audit": observation_audit,
        "protected_inputs_verified": len(protected),
        "background_land_cloud_overlap_units": int(
            background.background_nominal_land_cloud_union_overlap.sum()
        ),
        "background_max_envelope_gap_hours": float(
            background.background_land_scan_longest_gap_hours.max()
        ),
        "background_min_envelope_gap_hours": float(
            background.background_land_scan_longest_gap_hours.min()
        ),
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
    }
    join.require(all(sha(ROOT / n) == h for n, h in pins.items()), "Preflight input closure")
    report_path = out / "readback.json"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    join.require(json.loads(report_path.read_text()) == result, "Readiness report readback")
    join.require(all(sha(out / n) == h for n, h in artifacts.items()), "Preflight artifact closure")
    completion = {
        "status": "passed",
        "report_sha256": sha(report_path),
        "inputs_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    (out / "completion_readback.json").write_text(
        json.dumps(completion, indent=2) + "\n", encoding="utf-8"
    )
    print("Readiness result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-audit", required=True)
    parser.add_argument("--expected-feature-audit-sha256", required=True)
    args = parser.parse_args()
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run(args.feature_audit, args.expected_feature_audit_sha256)
