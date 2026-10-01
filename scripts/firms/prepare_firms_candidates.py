import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

parser = argparse.ArgumentParser(description="FIRMS aday tespit seçimi")
parser.add_argument(
    "--source",
    default="data/interim/firms_pilot_2018_2024.csv",
)
parser.add_argument(
    "--audit",
    default="data/interim/firms_pilot_candidate_audit.csv",
)
parser.add_argument(
    "--output",
    default="data/interim/firms_fire_candidates_2018_2024.csv",
)
parser.add_argument(
    "--report",
    default="outputs/reports/firms_candidates.json",
)
args = parser.parse_args()

source_path = ROOT / args.source
audit_path = ROOT / args.audit
candidate_path = ROOT / args.output
report_path = ROOT / args.report

df = pd.read_csv(source_path, dtype="string")

# Beklenmeyen kodları sessizce dışlama
if not df["type"].isin(["0", "1", "2", "3"]).all():
    raise ValueError("Eksik veya beklenmeyen type kodu var.")

if not df["confidence"].isin(["l", "n", "h"]).all():
    raise ValueError("Eksik veya beklenmeyen confidence kodu var.")

timestamps = pd.to_datetime(
    df["detection_timestamp_utc"],
    utc=True,
    errors="raise",
)

is_vegetation = df["type"].eq("0")
is_primary_confidence = df["confidence"].isin(["n", "h"])

df["candidate_for_event_grouping"] = is_vegetation & is_primary_confidence

df["candidate_selection_reason"] = df["type"].map(
    {
        "0": "vegetation_low_confidence",
        "1": "volcano",
        "2": "other_static_land_source",
        "3": "offshore_detection",
    }
)

df.loc[
    df["candidate_for_event_grouping"],
    "candidate_selection_reason",
] = "vegetation_nominal_or_high"

candidates = df.loc[df["candidate_for_event_grouping"]].copy()

if candidates.empty:
    raise ValueError("Olay gruplaması için aday tespit bulunamadı.")

candidate_years = timestamps.loc[candidates.index].dt.year

report = {
    "pilot_detection_count": len(df),
    "event_grouping_candidate_count": len(candidates),
    "low_confidence_vegetation_count": int((is_vegetation & df["confidence"].eq("l")).sum()),
    "selection_reason_counts": {
        str(key): int(value)
        for key, value in df["candidate_selection_reason"].value_counts().items()
    },
    "candidate_counts_by_year": {
        str(year): int((candidate_years == year).sum()) for year in range(2018, 2025)
    },
    "candidate_grid_count": int(candidates["grid_id"].nunique()),
    "selection_rule": "type=0 and confidence in {n,h}",
    "status": "exploratory candidates; not confirmed events or training labels",
}

audit_path.parent.mkdir(parents=True, exist_ok=True)

# Bütün pilot kayıtları ve seçim gerekçeleri korunur
df.to_csv(audit_path, index=False, encoding="utf-8-sig")
candidates.to_csv(candidate_path, index=False, encoding="utf-8-sig")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Seçim denetim tablosu:", audit_path)
print("Olay gruplaması adayları:", candidate_path)
