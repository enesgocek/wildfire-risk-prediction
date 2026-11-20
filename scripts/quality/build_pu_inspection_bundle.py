"""Create an offline research inspection view, never an accepted labelled/model dataset."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd
from prepare_full_u_feature_review import GRID, PREVIEW, PREVIEW_SHA, PROVINCES, province_support
from prepare_source_pu_feature_review import review_key

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.dataset_contract import feature_dictionary
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
TEMPLATE = Path(__file__).with_name("pu_inspection_template.html")


def checked_report(path, expected, pins):
    path = path.resolve()
    join.require(
        path.is_relative_to(BASE.resolve()) and digest(path) == expected, "Pinned local report"
    )
    pins[path] = expected
    value = json.loads(path.read_bytes())
    for name, fingerprint in value["artifact_sha256"].items():
        item = (path.parent / name).resolve()
        join.require(
            item.is_relative_to(path.parent) and digest(item) == fingerprint, "Snapshot artifact"
        )
        pins[item] = fingerprint
    return value


def make_review_tables(u, sources, u_features, source_features, mapping, support):
    for frame in (u, sources, u_features, source_features):
        join.require(not frame.duplicated(join.KEYS).any(), "Unique review keys")
        for grid, stamp in frame[join.KEYS].itertuples(index=False, name=None):
            review_key(grid, stamp)
    join.require(
        u.target.isna().all()
        and sources.target.isna().all()
        and u.daily_observation_status.eq("unknown").all()
        and sources.daily_observation_status.eq("unknown").all(),
        "Unassigned Y only",
    )
    key_sets = [set(map(tuple, frame[join.KEYS].to_numpy())) for frame in (u, sources)]
    join.require(not key_sets[0].intersection(key_sets[1]), "No silent source/U overlap removal")
    for meta, values in ((u, u_features), (sources, source_features)):
        join.require(
            values.columns.tolist() == join.KEYS + join.feature_names()
            and set(map(tuple, meta[join.KEYS].to_numpy()))
            == set(map(tuple, values[join.KEYS].to_numpy())),
            "Every review key has exact feature X",
        )
    labels = support.groupby("grid_id").province.agg(lambda x: "|".join(sorted(x)))
    groups = []
    for name, meta, features in (
        ("U_belirsiz", u, u_features),
        ("kaynak_merkezi_adayi", sources, source_features),
    ):
        frame = features.copy()
        frame.insert(2, "inceleme_grubu", name)
        frame.insert(3, "il_alan_kesisimi", frame.grid_id.map(labels))
        frame["target"] = np.nan
        frame["daily_observation_status"] = "unknown"
        frame["eksik_ozellik_sayisi"] = frame[join.feature_names()].isna().sum(axis=1)
        join.require(frame.il_alan_kesisimi.notna().all(), "Every review cell has province context")
        if name == "U_belirsiz":
            for field in ("population_index", "sampling_probability", "sampling_weight"):
                frame[field] = (
                    meta.set_index(join.KEYS)
                    .loc[frame.set_index(join.KEYS).index, field]
                    .to_numpy()
                )
        else:
            counts = {}
            for row in mapping:
                join.require(row["target"] is None, "Source mapping remains unassigned")
                key = (row["grid_id"], row["prediction_timestamp_utc"])
                counts[key] = counts.get(key, 0) + 1
            join.require(set(counts) == key_sets[1], "All source identities represented")
            frame["kaynak_kayit_sayisi"] = [
                counts[k] for k in frame[join.KEYS].itertuples(index=False, name=None)
            ]
        groups.append(frame)
    result = pd.concat(groups, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    join.require(
        len(result) == len(u) + len(sources) and result.target.isna().all(),
        "Limited inspection union, never final labeled merge",
    )
    return result


def json_rows(frame):
    """JSON null for absent observations, never zero or NaN tokens."""
    return json.loads(frame.to_json(orient="records", force_ascii=False, double_precision=15))


def render_page(frame, qa, dictionary, template):
    join.require(
        not qa.duplicated(join.KEYS).any()
        and set(map(tuple, qa[join.KEYS].to_numpy()))
        == set(map(tuple, frame[join.KEYS].to_numpy())),
        "Exact separate provenance key set",
    )
    payload = {
        "rows": json_rows(frame),
        "provenance": json_rows(qa),
        "dictionary": dictionary,
        "target_status": "Y_unknown",
        "risk_predictions_present": False,
    }
    # Preserve round-trip float precision in CSV; web values are display-only.
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    encoded = encoded.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    encoded = encoded.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    join.require(template.count("__PAYLOAD_JSON__") == 1, "One safe embedded payload")
    return template.replace("__PAYLOAD_JSON__", encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--u-report", required=True)
    parser.add_argument("--u-report-sha256", required=True)
    args = parser.parse_args()
    pins = {TEMPLATE: digest(TEMPLATE)}
    u_path = (ROOT / args.u_report).resolve()
    full_u = checked_report(u_path, args.u_report_sha256, pins)
    checked_report(PREVIEW, PREVIEW_SHA, pins)
    join.require(
        full_u["U_keys"] == 2048
        and full_u["sampling_unchanged"]
        and full_u["new_L_or_Y_labels"] == 0
        and not full_u["model_trained"],
        "Frozen U review only",
    )
    for filename in (GRID, PROVINCES):
        expected = full_u["input_sha256"][filename.relative_to(ROOT).as_posix()]
        join.require(digest(filename) == expected, "Original geometry pins")
        pins[filename] = expected
    dictionary_code = ROOT / "src/wildfire_risk_prediction/dataset_contract.py"
    pins[dictionary_code] = digest(dictionary_code)
    u = parse_csv((u_path.parent / "inspection.csv").read_bytes())
    prior = parse_csv((PREVIEW.parent / "inspection.csv").read_bytes())
    sources = prior.loc[prior.review_population.eq("source_center_hypothesis")].copy()
    u_features = parse_csv((u_path.parent / "features.csv").read_bytes())
    source_features = sources[join.KEYS + join.feature_names()].copy()
    mapping = json.loads((PREVIEW.parent / "source_case_mapping.json").read_bytes())
    join.require(
        len(sources) == 374 and len(mapping) == 380 and len(u) == 2048, "Declared review cohorts"
    )
    grid = gpd.read_file(GRID).to_crs(6933)
    cells = set(u.grid_id) | set(sources.grid_id)
    support = province_support(
        grid.loc[grid.grid_id.isin(cells)], gpd.read_file(PROVINCES).to_crs(6933)
    )
    frame = make_review_tables(u, sources, u_features, source_features, mapping, support)
    source_qa = parse_csv((PREVIEW.parent / "provenance.csv").read_bytes()).set_index(join.KEYS)
    source_qa = source_qa.loc[sources.set_index(join.KEYS).index].reset_index()
    qa = pd.concat(
        [parse_csv((u_path.parent / "provenance.csv").read_bytes()), source_qa], ignore_index=True
    )
    qa = qa.sort_values(join.KEYS).reset_index(drop=True)
    dictionary = feature_dictionary()
    out = (
        BASE
        / "PU_inspection_bundle_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    frame.to_csv(out / "inceleme.csv", index=False)
    qa.to_csv(out / "kaynak_izleri.csv", index=False)
    support.to_csv(out / "il_alan_kesisimleri.csv", index=False)
    (out / "ozellik_sozlugu.json").write_text(
        json.dumps(dictionary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "kaynak_kayit_eslemeleri.json").write_text(
        json.dumps(mapping, indent=2) + "\n", encoding="utf-8"
    )
    page = render_page(frame, qa, dictionary, TEMPLATE.read_text(encoding="utf-8"))
    (out / "inceleme.html").write_text(page, encoding="utf-8")
    readme = (
        "VERI INCELEME PAKETI — ETIKETLI EGITIM VERI SETI DEGIL\n\n"
        "inceleme.html dosyasini tarayicida acin; internet veya giris gerekmez.\n"
        "2.048 degismeyen U anahtari ve 374 kaynak merkezi hipotezi, 2018–2022.\n"
        "Kaynak hipotezleri 380 Mersin kaydindan; dort ilde U var, "
        "dort ilde dogrulanmis pozitif yok.\n"
        "Gercek Y hedeflerinin tamami bos; U negatif, kaynak adaylari kesin yangin degildir.\n"
        "Bu arastirma orneklemi, tum gunlerin 2.889 hucrelik tam paneli degildir.\n"
        "Il alanlari sinir hucrelerinde ortusebilir. Ornekleme agirligi sinif agirligi degildir.\n"
        "27 ozellik doldurulmadi; bos deger sifir degildir. Model veya risk rengi uretilmedi.\n"
        "CSV sayilari tam geri okuma icindir; HTML sayilari gosterim icin yuvarlanabilir.\n"
        "ERA5-Land geriye donuk; tarihsel yayin erisimi bilinmiyor. "
        "Operasyonel tahmin iddiasi yok.\n"
        "Kaynak saat/konum/olay anlami ve PU degerlendirme dayanaklari acik.\n"
        "Bu sinirli inceleme baglantisi nihai etiketli birlestirme veya kabul degildir.\n"
        "Son birlestirmeden once guncel parca denetimi ve arastirmaci onayi gerekir.\n"
    )
    (out / "README.txt").write_text(readme, encoding="utf-8")
    pd.testing.assert_frame_equal(
        frame, parse_csv((out / "inceleme.csv").read_bytes()), check_dtype=False, check_exact=True
    )
    pd.testing.assert_frame_equal(
        qa, parse_csv((out / "kaynak_izleri.csv").read_bytes()), check_dtype=False, check_exact=True
    )
    names = [
        "inceleme.csv",
        "kaynak_izleri.csv",
        "il_alan_kesisimleri.csv",
        "ozellik_sozlugu.json",
        "kaynak_kayit_eslemeleri.json",
        "inceleme.html",
        "README.txt",
    ]
    artifacts = {name: digest(out / name) for name in names}
    (out / "manifest.json").write_text(
        json.dumps({"artifact_sha256": artifacts}, indent=2) + "\n", encoding="utf-8"
    )
    archive = out / "inceleme_paketi.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as z:
        for name in names + ["manifest.json"]:
            z.write(out / name, name)
    with ZipFile(archive) as z:
        join.require(
            z.testzip() is None and set(z.namelist()) == set(names + ["manifest.json"]),
            "Exact review ZIP",
        )
    artifacts.update(
        {name: digest(out / name) for name in ("manifest.json", "inceleme_paketi.zip")}
    )
    report = {
        "status": "offline_unlabeled_PU_review_bundle_complete_not_final_dataset",
        "review_keys": len(frame),
        "U_keys": 2048,
        "source_keys": 374,
        "source_records": 380,
        "complete_27_feature_rows": int(frame.eksik_ozellik_sayisi.eq(0).sum()),
        "incomplete_rows_preserved": int(frame.eksik_ozellik_sayisi.gt(0).sum()),
        "model_predictions_or_fire_colors_present": False,
        "source_population_is_four_province_positive_reference": False,
        "new_L_or_Y_labels": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Input snapshots unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("PASS inspectable_research_sample_only; no accepted labels/model/final merge", flush=True)
    print("readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
