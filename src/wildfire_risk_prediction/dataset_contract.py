"""Machine-readable candidate dictionary and current closed release criteria; no fitting."""

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as parts
from wildfire_risk_prediction import target_admission as targets

VERSION = "dataset_preparation_contract_v1"


def feature_dictionary():
    descriptions = {
        "temperature_mean_c": ("weather", "degC", "Önceki 24 saatin sıcaklık ortalaması"),
        "temperature_min_c": ("weather", "degC", "Önceki 24 saatin en düşük sıcaklığı"),
        "temperature_max_c": ("weather", "degC", "Önceki 24 saatin en yüksek sıcaklığı"),
        "dewpoint_mean_c": ("weather", "degC", "Önceki 24 saatin çiy noktası ortalaması"),
        "wind_speed_mean_ms": ("weather", "m/s", "Önceki 24 saatin rüzgâr hızı ortalaması"),
        "wind_speed_max_ms": ("weather", "m/s", "Önceki 24 saatin en yüksek rüzgâr hızı"),
        "soil_water_layer_1_mean": (
            "weather",
            "volume_fraction",
            "Önceki 24 saatte 0–7 cm toprak suyu hacim payı",
        ),
        "forest_fraction": ("landcover", "area_fraction", "2017 orman sınıfı alan payı"),
        "shrub_fraction": ("landcover", "area_fraction", "2017 çalılık sınıfı alan payı"),
        "herbaceous_fraction": ("landcover", "area_fraction", "2017 otsu örtü sınıfı alan payı"),
        "agriculture_fraction": ("landcover", "area_fraction", "2017 tarım sınıfı alan payı"),
        "urban_fraction": ("landcover", "area_fraction", "2017 yerleşim sınıfı alan payı"),
        "water_fraction": ("landcover", "area_fraction", "2017 su sınıflarının alan payı"),
        "natural_vegetation_fraction": (
            "landcover",
            "area_fraction",
            "Orman, çalılık ve otsu sınıf paylarının toplamı",
        ),
        "elevation_mean_m": ("terrain", "m", "Destekli arazi alanında ortalama yükseklik"),
        "elevation_std_m": ("terrain", "m", "Destekli arazi alanında yükseklik standart sapması"),
        "slope_mean_deg": ("terrain", "degree", "Destekli arazi alanında ortalama eğim"),
        "northness_mean": ("terrain", "dimensionless", "Düz olmayan yamaçlarda yönün kosinüsü"),
        "eastness_mean": ("terrain", "dimensionless", "Düz olmayan yamaçlarda yönün sinüsü"),
    }
    for hours in (24, 72, 168, 336):
        descriptions[f"rain_{hours}h_nonnegative_mm"] = (
            "weather",
            "mm",
            f"T'den önceki {hours} saatlik kayıtlı yağış aralığı; QC dönüşümlü",
        )
    for window in join.WINDOWS:
        for field in join.VEGETATION_FEATURES:
            index = "NDVI" if field.startswith("ndvi") else "NDMI"
            descriptions[f"vegetation_{window}d_{field}"] = (
                "vegetation",
                "dimensionless",
                f"Geçmiş {window} günlük {index} piksel medyanlarının destekli alan ortalaması",
            )
    join.require(set(descriptions) == set(join.feature_names()), "Dictionary/schema drift")
    return [
        {
            "name": name,
            "family": descriptions[name][0],
            "unit": descriptions[name][1],
            "meaning_tr": descriptions[name][2],
            "role": "candidate_model_input",
            "dtype": "float64_nullable",
            "missing_policy": "preserve_NaN_no_imputation",
            "historical_available_at_verified": False,
        }
        for name in join.feature_names()
    ]


def release_blockers():
    """Caller-provided booleans cannot approve scientific decisions in this version."""
    state = targets.specification()
    gates = [
        ("source_type_semantics_verified", "Kaynak Type ve üretim sürümü kanıtı"),
        ("event_definition_accepted", "Tekrar tespit ve zincir olay kuralı"),
        ("first_cell_policy_accepted", "İlk anda birden çok hücre kuralı"),
        ("habitat_policy_accepted", "Habitat kapsamı ve dışlama gerekçesi"),
        ("observation_negative_policy_accepted", "Gözlem yeterliliği ve negatif etiket kanıtı"),
    ]
    blockers = [
        {"gate": field, "status": "awaiting_scientific_acceptance", "required": meaning}
        for field, meaning in gates
        if state[field] is False
    ]
    blockers.append(
        {
            "gate": "period_boundary_policy",
            "status": "awaiting_scientific_acceptance",
            "required": "Dahil sağ uç, ortak olay ve dönem kenarı dışlama/embargo kararı",
        }
    )
    return blockers


def specification():
    return {
        "version": VERSION,
        "purpose": "retrospective_candidate_dataset_preparation_only",
        "keys": join.KEYS,
        "prediction_hour_utc": "00:00",
        "target_window": "(T,T+24h]",
        "splits": {"train": [2018, 2023], "validation": [2024, 2024], "final_test": [2025, 2025]},
        "features": feature_dictionary(),
        "provenance_columns": parts.provenance_columns(),
        "label_table_blueprint": {
            "keys": join.KEYS,
            "target": "nullable Int8; current protocol permits only unassigned values",
            "event_id": "accepted event identity; not exploratory cluster/canonical grid",
            "observation_status": "label audit only; not an input available at prediction T",
            "exclusion_reason": "explicit source/habitat/observation/boundary decision",
            "policy_version_and_evidence": "required before binary targets are admitted",
            "implemented_binary_label_builder": False,
            "unassigned_target_join_preview": "candidate_target_join_preview_v1",
        },
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "release_blockers": release_blockers(),
        "final_test_preparation": "sealed_until_separate_freeze_and_final_evaluation_protocol",
        "sources": [
            "docs/PROJECT.md",
            "docs/WEATHER_POLICY.md",
            "docs/DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md",
            "https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY",
        ],
    }
