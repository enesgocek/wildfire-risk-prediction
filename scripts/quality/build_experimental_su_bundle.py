"""Package existing snapshots and unchanged proposals for offline research inspection."""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import geopandas as gpd
import pandas as pd
from prepare_full_u_feature_review import province_support

from wildfire_risk_prediction import experimental_review as review
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.dataset_contract import feature_dictionary
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
X = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
P = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
CONFIG = ROOT / "configs/experimental_su_inspection_v2.json"
TEMPLATE = Path(__file__).with_name("experimental_review_template.html")
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
PROVINCES = ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"


def main():
    decision = json.loads(CONFIG.read_bytes())
    require(
        decision["decision_source"]
        == "explicit_researcher_A_preserve_main_target_prepare_inspectable_experimental_SU_package"
        and decision["keys"] == 44082
        and decision["scenarios"] == 9,
        "Explicit A bounded inspection direction",
    )
    require(
        all(
            decision[k] is False
            for k in (
                "new_training_authorized",
                "new_data_acquisition_authorized",
                "scientific_values_2023_2024_2025_read_authorized",
                "source_proposal_is_true_Y",
                "unassigned_calendar_is_true_negative",
                "main_method_scientifically_accepted",
                "negative_label_permitted",
                "final_labelled_merge_authorized",
            )
        ),
        "No scientific or final merge promotion",
    )
    pins = {
        CONFIG: digest(CONFIG),
        TEMPLATE: digest(TEMPLATE),
        Path(review.__file__): digest(Path(review.__file__)),
        X / "readback.json": "b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040",
        Path(province_support.__code__.co_filename): digest(
            Path(province_support.__code__.co_filename)
        ),
        Path(feature_dictionary.__code__.co_filename): digest(
            Path(feature_dictionary.__code__.co_filename)
        ),
        PARTS: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
        PROVINCES: "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb",
    }
    # Proposal identity is pinned below from the already recorded source calendar input chain.
    xr = json.loads((X / "readback.json").read_bytes())
    require(pins[X / "readback.json"] == digest(X / "readback.json"), "Existing accepted X receipt")
    require(
        (P / "readback.json").relative_to(ROOT).as_posix() in xr["input_sha256"],
        "Proposal receipt belongs to the existing X chain",
    )
    pins[P / "readback.json"] = xr["input_sha256"][
        (P / "readback.json").relative_to(ROOT).as_posix()
    ]
    pr = json.loads((P / "readback.json").read_bytes())
    for folder, receipt in ((X, xr), (P, pr)):
        pins.update({folder / name: h for name, h in receipt["artifact_sha256"].items()})
    require(
        all(digest(p) == h for p, h in pins.items()), "Unchanged existing snapshots and proposals"
    )
    snapshot = X / xr["snapshot_directory"]
    features, roles = [
        pd.read_csv(snapshot / name, float_precision="round_trip")
        for name in ("features.csv", "review_roles.csv")
    ]
    lineage = pd.read_csv(P / "all_first_cells_with_proposal_flags.csv")
    scenarios = sorted(lineage.scenario.unique())
    require(
        len(scenarios) == 9 and len(features) == 44082,
        "Full nine-scenario 44082-key inspection scope",
    )
    meta = review.memberships(features, roles, lineage, scenarios)
    grid = gpd.read_file(PARTS).to_crs(6933)
    grid = grid.loc[grid.grid_id.isin(meta.grid_id)].copy()
    support = province_support(grid, gpd.read_file(PROVINCES).to_crs(6933))
    names = support.groupby("grid_id").province.agg(lambda x: "|".join(sorted(x)))
    meta["province_area_intersections"] = meta.grid_id.map(names)
    require(meta.province_area_intersections.notna().all(), "No unmatched review province")
    dictionary = feature_dictionary()
    out = (
        BASE
        / "experimental_SU_inspection_v2"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    for source, target in (
        (snapshot / "features.csv", "features.csv"),
        (snapshot / "provenance.csv", "provenance.csv"),
        (snapshot / "review_roles.csv", "original_review_roles.csv"),
        (P / "all_first_cells_with_proposal_flags.csv", "original_candidate_lineage.csv"),
    ):
        shutil.copyfile(source, out / target)
        require(digest(out / target) == digest(source), "Bit-identical existing source file")
    meta.to_csv(out / "inspection_memberships.csv", index=False)
    support.to_csv(out / "province_support.csv", index=False)
    (out / "feature_dictionary.json").write_text(
        json.dumps(dictionary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    values = json.loads(features.to_json(orient="values", double_precision=15))
    display = [
        [
            r.grid_id,
            r.prediction_timestamp_utc,
            r.province_area_intersections,
            r.review_temporal_role,
            r.missing_feature_count,
            r.scenario_proposal_bitmask_for_display_only,
            *v[2:],
        ]
        for r, v in zip(meta.itertuples(), values, strict=True)
    ]
    payload = {
        "rows": display,
        "scenarios": scenarios,
        "dictionary": dictionary,
        "cells": int(meta.grid_id.nunique()),
        "incomplete": int(meta.missing_feature_count.gt(0).sum()),
        "provinces": sorted(support.province.unique()),
    }
    encoded = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    (out / "review_data.js").write_text("window.REVIEW=" + encoded + ";\n", encoding="utf-8")
    shutil.copyfile(TEMPLATE, out / "inceleme.html")
    readme = """DENEYSEL S/U İNCELEME PAKETİ — 23 Kasım 2026

inceleme.html dosyasını tarayıcıda açın; review_data.js aynı klasörde kalmalı.
44.082 kaynak koşullu hücre-gün, 2018–2022, 27 özellik; bu tam nüfus paneli değil.
Dokuz senaryo ayrı korunuyor. Varsayılan görünüm en az bir ayarda öneri varlığını gösterir;
bu bir üretim senaryosu veya bilimsel kabul seçimi değildir.
S: mevcut aday üyelik önerisi. U: bu ayarda atamasız takvim. Gerçek Y=1/Y=0 değildir.
Gerçek hedef ve kabul edilmiş L boş; günlük gözlem unknown. Eksik değerler korunur.
Önceki rastgele U örnekleminden yalnız 19 anahtar bu takvimdedir; eski U tasarımı ve
ağırlıkları bu havuza aktarılmadı. Yeni örnekleme ağırlığı türetilmedi.
2018–2021/2022 rolleri eski pilot rolleridir; yeni eğitim izni vermez.
2023–2025 yok. FWI veya model skorları bu pakete eklenmedi.
features.csv/provenance.csv özgün baytlarıyla korundu. inspection_memberships.csv
yalnız inceleme metadatasıdır. original_candidate_lineage.csv kapsam dışı tutulmuş
belirsiz ilk hücreleri de korur; bütün satırları ana inceleme önerisi değildir.
Web sayıları görüntüleme için yuvarlanır; tam hassasiyet features.csv dosyasındadır.
Nihai etiketli birleştirme, model eğitimi veya doğrulanmış risk ürünü kabulü yok.
"""
    (out / "README.txt").write_text(readme, encoding="utf-8")
    counts = {
        scenario: int(meta["S_candidate_context_" + scenario].sum()) for scenario in scenarios
    }
    require(all(digest(p) == h for p, h in pins.items()), "All original inputs unchanged")
    artifacts = {p.name: digest(p) for p in out.iterdir()}
    result = {
        "status": "experimental_SU_inspection_package_ready_not_true_label_or_final_merge",
        "decision": decision,
        "keys": len(meta),
        "grid_cells": int(meta.grid_id.nunique()),
        "feature_count": 27,
        "complete_features": int(meta.missing_feature_count.eq(0).sum()),
        "incomplete_features": int(meta.missing_feature_count.gt(0).sum()),
        "proposal_union_keys": int(meta.known_proposal_key_in_union.sum()),
        "original_U_keys_present_without_weight_transfer": int(
            meta.original_U_sample_key_present.sum()
        ),
        "scenario_proposal_key_counts": counts,
        "scenario_dependent_keys": int(
            meta.scenario_proposal_bitmask_for_display_only.between(1, 510).sum()
        ),
        "role_counts": meta.review_temporal_role.value_counts().to_dict(),
        "province_filter_counts_may_overlap": {
            p: int(
                meta.province_area_intersections.str.split("|").map(lambda xs, p=p: p in xs).sum()
            )
            for p in payload["provinces"]
        },
        "new_true_Y_or_accepted_L": 0,
        "new_model_training": 0,
        "final_labelled_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    archive = out / "deneysel_SU_inceleme.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=6) as z:
        for file in out.iterdir():
            if file != archive:
                z.write(file, arcname=file.name)
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("archive_sha256", digest(archive), "bytes", archive.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
