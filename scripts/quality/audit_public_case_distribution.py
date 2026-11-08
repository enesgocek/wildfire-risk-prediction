"""Map selected public fire references to OGM's province-year comparison frame."""

import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
INPUTS = {
    "public_start_evidence_v1/20261108T025127Z_ce9218f2/readback.json": (
        "26c5fb18cfb2f444004d6d06c2aed00e298dfb26b7359643cf6aeb756bd5f6f4"
    ),
    "july_2023_start_context_v1/20261108T031417Z_6fa7cc62/readback.json": (
        "8532ad7435abca375bf546d3ebb916ac84264d931c80ce932b51d63019d64d45"
    ),
    "izmir_july_event_context_v1/20261108T034852Z_fa5863e0/readback.json": (
        "2cddafd97bace89d7f6b763951d7fd3c2952af413ff73ae1efe2b98b9fa6d3b6"
    ),
    "public_reference_cases_v1/20261107T231732Z_424d1731/readback.json": (
        "b1aac4c4bec040d0446dc64a99f3312a3ba9c86e90a1c478a3c4b0782984596c"
    ),
    "ogm_province_year_v1/20261108T125959Z_992396ed/summary.json": (
        "e8ad9a0d4c0a3b70ccc135295d96bcbce2021bc5be06ff3db62ddb61d6391ac0"
    ),
}
PROVINCES = ("Antalya", "Muğla", "İzmir", "Mersin")
LOCAL = ZoneInfo("Europe/Istanbul")
MGM = "https://www.mgm.gov.tr/FILES/genel/kitaplar/antalya-izmir.pdf"
MINISTRY = (
    "https://www.tarimorman.gov.tr/Haber/4674/Mendereste-Yanginin-Ciktigi-An-Ihalarca-Goruntulendi"
)
DHA = (
    "https://www.dha.com.tr/gundem/bakan-pakdemirli-menderes-yangini-"
    "yuzde-90-insan-hatasi-kaynakli-1784542"
)
AA_ANTALYA = "https://www.aa.com.tr/tr/turkiye/antalyadaki-orman-yangini-kismen-kontrol-altina-alindi/1210712"


def load_inputs():
    inputs = {}
    for path, expected in INPUTS.items():
        content = (BASE / path).read_bytes()
        require(hashlib.sha256(content).hexdigest() == expected, f"Input identity: {path}")
        inputs[path.split("/", 1)[0]] = json.loads(content)
    return inputs


def case_row(key, province, local_day, source):
    date.fromisoformat(local_day)
    return {
        "reference_key": key,
        "province": province,
        "reported_local_day": local_day,
        "context_source": source,
        "matching_ready": False,
    }


def local_day_from_utc(stamp):
    parsed = datetime.fromisoformat(stamp)
    require(parsed.utcoffset() == UTC.utcoffset(parsed), "Expected UTC source time")
    return parsed.astimezone(LOCAL).date().isoformat()


def existing_cases(inputs):
    source = "public_start_evidence_v1"
    cases = []
    for row in inputs[source]["cases"]:
        intake, fields = row["intake_result"], row["intake_fields"]
        require(
            intake["row_status"] == "needs_source_review"
            and intake["can_review_matching"] is False
            and intake["target"] is None,
            "Selected intake records remain under review",
        )
        require(
            fields["reported_date"] == local_day_from_utc(row["reported_time_utc"]),
            "Source local date",
        )
        cases.append(
            case_row(
                fields["reference_id"], fields["reported_province"], fields["reported_date"], source
            )
        )

    source = "july_2023_start_context_v1"
    for key, province in (
        ("milas_maya_yolu", "Muğla"),
        ("milas_kemikler", "Muğla"),
        ("anamur_belensazak_approximate", "Mersin"),
    ):
        row = inputs[source]["cases"][key]
        require(row["original_ignition_verified"] is False and row["target"] is None, key)
        cases.append(case_row(key, province, local_day_from_utc(row["reported_start_utc"]), source))

    source = "izmir_july_event_context_v1"
    for key, row in inputs[source]["cases"].items():
        require(row["original_ignition_verified"] is False and row["target"] is None, key)
        cases.append(case_row(f"{key}_2023", "İzmir", row["day"], source))

    source = "public_reference_cases_v1"
    for key, province in (("urla_karaburun", "İzmir"), ("aydincik_pembecik", "Mersin")):
        row = inputs[source]["cases"][key]
        require(row["target"] is None, key)
        cases.append(case_row(key, province, row["day"], source))
    require(len(cases) == 20, "Selected earlier references")
    return cases


def new_context_cases():
    # These are reported wall-clock readings. No verified time bounds were published.
    return [
        {
            **case_row("antalya_20180722", "Antalya", "2018-07-22", "MGM case study"),
            "reported_clock": "12:50",
            "clock_evidence": "approximate_as_published",
            "source_urls": [MGM, AA_ANTALYA],
        },
        {
            **case_row("buca_20180713", "İzmir", "2018-07-13", "MGM case study"),
            "reported_clock": "15:10",
            "clock_evidence": "approximate_as_published",
            "source_urls": [MGM, "https://www.yenisafak.com/gundem/izmirde-orman-yangini-3383826"],
        },
        {
            **case_row("menderes_cile_20200802", "İzmir", "2020-08-02", "Ministry and DHA"),
            "reported_clock": "13:24",
            "clock_evidence": "minister_reported_minute_telemetry_unavailable",
            "source_urls": [MINISTRY, DHA],
        },
    ]


def summarize(cases, ogm_rows):
    require(len({row["reference_key"] for row in cases}) == len(cases), "Unique review keys")
    counts = Counter(
        (row["province"], date.fromisoformat(row["reported_local_day"]).year) for row in cases
    )
    keys = {(row["province"], row["year"]) for row in ogm_rows}
    expected = {(province, year) for province in PROVINCES for year in range(2018, 2024)}
    require(
        len(ogm_rows) == len(keys) and keys == expected, "Complete training province-year frame"
    )
    require(counts.keys() <= keys, "Selected references outside training frame")
    return [
        {
            "province": row["province"],
            "year": row["year"],
            "selected_context_records": counts[row["province"], row["year"]],
            "published_ogm_province_count": row["province_fire_count"],
        }
        for row in ogm_rows
    ]


def main():
    inputs = load_inputs()
    earlier = existing_cases(inputs)
    cases = earlier + new_context_cases()
    ogm_rows = inputs["ogm_province_year_v1"]["province_year_rows"]
    earlier_summary = summarize(earlier, ogm_rows)
    summary = summarize(cases, ogm_rows)
    report = {
        "scope": "selected_public_context_records_by_local_year",
        "input_sha256": INPUTS,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "strata_with_context_before": sum(
            row["selected_context_records"] > 0 for row in earlier_summary
        ),
        "strata_with_context_after": sum(row["selected_context_records"] > 0 for row in summary),
        "province_year": summary,
        "cases": cases,
        "target_admission": specification(),
    }
    run_id = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    run = BASE / "public_case_distribution_v1" / run_id
    run.mkdir(parents=True)
    path = run / "readback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Output roundtrip")
    print(path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
