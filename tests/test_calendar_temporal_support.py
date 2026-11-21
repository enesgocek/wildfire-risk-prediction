import importlib.util
from pathlib import Path


def test_pair_support_excludes_missing_shared_graph_and_other_roles_without_mutation():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_calendar_temporal_split.py"
    spec = importlib.util.spec_from_file_location("calendar_temporal_support_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    keys = {
        (g, f"2022-{m:02d}-{d:02d}T00:00:00+00:00") for g in "AB" for m in (5, 6) for d in (1, 2, 3)
    }
    source = {k for k in keys if k[1][8:10] == "01"}
    phase = {k: "held" if k[0] == "A" else "fit" for k in keys}
    missing = {k for k in keys if k[1][8:10] == "03"}
    affected = {k for k in source if "-06-" in k[1]}
    result = module.potential_support(keys, phase, keys - missing, affected, source, "held")
    assert result == {
        "complete_dynamic_source_context_rows": 1,
        "complete_dynamic_other_rows_not_fire_negatives": 2,
        "potential_same_grid_year_month_pairs": 1,
        "strata_with_both_source_contexts": 1,
    }
    assert len(keys) == 12 and len(source) == 4
