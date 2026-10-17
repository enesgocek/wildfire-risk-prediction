"""Check readiness without writing a dataset; current scientific protocol remains closed."""

import argparse
import json
from pathlib import Path

from wildfire_risk_prediction.dataset_execution import preflight_training_merge, public_file
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review")
    parser.add_argument("--approval")
    args = parser.parse_args()

    def record(name):
        if name is None:
            return None
        path = public_file(ROOT, name)
        require(path.stat().st_size <= 1_000_000, "Bounded review receipt")
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        result = preflight_training_merge(ROOT, record(args.review), record(args.approval))
    except PermissionError:
        print("BLOCKED: scientific protocol/final review/explicit approval incomplete; no merge")
        return 3
    print(result["status"] + "; no dataset written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
