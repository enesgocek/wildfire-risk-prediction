"""Summarize accepted training readbacks without inventing labels or joint missingness."""

from datetime import timedelta

from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month


def count(value, rows):
    join.require(type(value) is int and 0 <= value <= rows, "Bounded integer quality count")
    return value


def summarize(reports):
    """Aggregate marginal counts from all 72 accepted month summaries, not CSV rows."""
    expected = {entry["month"] for entry in batch.calendar_inventory()}
    months = [report["month"] for report in reports]
    join.require(len(months) == len(set(months)) == 72, "Unique complete training months")
    join.require(set(months) == expected, "Training calendar only")
    names = join.feature_names()
    monthly = []
    for report in sorted(reports, key=lambda r: r["month"]):
        days = feature_month.calendar_days(report["month"])
        rows = len(days) * batch.GRID_COUNT
        join.require(
            report["status"] == "complete_month_candidate_readback_passed"
            and report["version"] == feature_month.VERSION
            and report["split"] == "train"
            and report["days"] == days
            and type(report["rows"]) is int
            and report["rows"] == rows
            and report["candidate_features"] == names
            and report["inputs_unchanged"] is True
            and report["daily_observation_status"] == "unknown"
            and all(report[field] is False for field in feature_month.FALSE_FLAGS),
            "Accepted candidate scope and closed scientific gates",
        )
        join.require(set(report["missing_by_feature"]) == set(names), "Exact missingness schema")
        missing = {name: count(report["missing_by_feature"][name], rows) for name in names}
        support = report["vegetation_supported_cell_days"]
        join.require(set(support) == {"30", "60"}, "Two vegetation support windows")
        monthly.append(
            {
                "month": report["month"],
                "days": len(days),
                "rows": rows,
                "missing_by_feature": missing,
                "vegetation_supported_cell_days": {w: count(support[w], rows) for w in support},
            }
        )
    rows = sum(month["rows"] for month in monthly)
    features = []
    for name in names:
        missing = sum(month["missing_by_feature"][name] for month in monthly)
        worst = max(monthly, key=lambda m: m["missing_by_feature"][name] / m["rows"])
        features.append(
            {
                "feature": name,
                "missing_cell_days": missing,
                "nonmissing_cell_days": rows - missing,
                "denominator_cell_days": rows,
                "missing_fraction": missing / rows,
                "worst_month": worst["month"],
                "worst_month_missing_fraction": worst["missing_by_feature"][name] / worst["rows"],
            }
        )
    yearly = []
    for year in range(2018, 2024):
        selected = [m for m in monthly if m["month"].startswith(str(year))]
        yearly.append(
            {
                "year": year,
                "rows": sum(m["rows"] for m in selected),
                "missing_by_feature": {
                    name: sum(m["missing_by_feature"][name] for m in selected) for name in names
                },
            }
        )
    return {
        "months": 72,
        "days": sum(month["days"] for month in monthly),
        "rows": rows,
        "features": features,
        "monthly": monthly,
        "yearly": yearly,
        "complete_case_rows": None,
        "eligible_training_rows": None,
        "count_basis": "hash_bound_accepted_monthly_readback_marginal_counts",
        "limitation": "Marginal missingness does not identify overlap or eligible labeled rows.",
    }


def source_gap_review(days):
    """Conservative day-level review only; includes the previous window's closed endpoint."""
    join.require(days == sorted(set(days)), "Ordered unique deferred dates")
    targets = set()
    for value in days:
        day = join.training_day(value)
        targets.add(value)
        previous = day - timedelta(days=1)
        if previous.year >= 2018:
            targets.add(previous.date().isoformat())
    return {
        "unresolved_source_days": days,
        "target_window": "(T,T+24h]",
        "conservative_target_review_dates": sorted(targets),
        "calendar_cell_days_to_review": len(targets) * batch.GRID_COUNT,
        "automatic_exclusions_applied": False,
        "negative_labels_created": 0,
        "future_fire_history_lookback_policy": "unresolved; no lookback length invented",
        "reason": "Day-level gap includes a possible midnight endpoint in the previous target; "
        "this is a review bound, not proof that all listed observations or cells are missing.",
    }
