"""Report training-period detection counts; zeros are not confirmed outages."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / "data/raw/firms/815579/fire_archive_SV-C2_815579.csv"

raw = pd.read_csv(source, usecols=["acq_date"], dtype="string")
if raw.empty or raw["acq_date"].isna().any():
    raise ValueError("Missing detection dates or empty archive.")
dates = pd.to_datetime(raw["acq_date"], format="%Y-%m-%d", errors="raise", utc=True)

days = pd.date_range("2018-01-01", "2023-12-31", tz="UTC")
counts = dates.value_counts().reindex(days, fill_value=0).astype(int)
report = pd.DataFrame(
    {
        "date_utc": days.strftime("%Y-%m-%d"),
        "turkey_detection_count": counts.to_numpy(),
    }
)
report["zero_detection_day"] = report["turkey_detection_count"].eq(0)

output = ROOT / "outputs/reports/firms_train_daily_counts.csv"
output.parent.mkdir(parents=True, exist_ok=True)
report.to_csv(output, index=False, encoding="utf-8-sig")

zero = report["zero_detection_day"]
groups = zero.ne(zero.shift()).cumsum()
print("Zero-detection intervals (not confirmed outages):")
for _, part in report.loc[zero].groupby(groups[zero]):
    start = part["date_utc"].iloc[0]
    end = part["date_utc"].iloc[-1]
    print(f"{start} -> {end} | {len(part)} days")

print(f"\nTotal zero-detection days: {int(zero.sum())}")
print(f"Report saved: {output}")
