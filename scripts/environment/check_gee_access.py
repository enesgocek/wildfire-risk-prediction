"""Noninteractive Earth Engine check; never authenticate or export images automatically."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import ee
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    project = os.getenv("GEE_PROJECT_ID", "").strip()
    report = {"checked_at_utc": datetime.now(UTC).isoformat(), "api_verified": False}
    if not project:
        report.update(
            status="not_configured",
            reason="Set GEE_PROJECT_ID in .env; complete Earth Engine registration and login.",
        )
        code = 2
    else:
        try:
            ee.Initialize(project=project)
            value = ee.Number(1).getInfo()
            if value != 1:
                raise RuntimeError("Unexpected API response.")
            report.update(status="api_verified", api_verified=True)
            # API success does not establish the account's noncommercial eligibility status.
            report["noncommercial_status"] = "must_be_confirmed_in_google_console"
            code = 0
        except Exception as error:
            report.update(
                status="access_failed",
                error_type=type(error).__name__,
                reason="Check login, project registration, API enablement and permissions.",
            )
            code = 1
    output = ROOT / "outputs" / "reports"
    output.mkdir(parents=True, exist_ok=True)
    (output / "gee_access.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
