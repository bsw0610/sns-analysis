#!/usr/bin/env python3
"""Check the classifier output for sample_data/sample_posts.csv.

The sample exists so that a fresh clone can run the classifier without the
private dataset. This checker verifies that the run produced a well-formed
result and that the outcome still matches the recorded baseline, including
the posts the classifier is known to get wrong.

Agreement is deliberately not asserted to be perfect. The sample reproduces
documented weaknesses of the rule-based classifier, and pinning the exact
failure set means a change in behaviour fails loudly instead of passing
unnoticed.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# The checker lives in sample_data/ but reads the classifier's own definitions
# so that the schema and label set can never drift apart from it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from classify_sns_rule_based import ACTIVE_CATEGORIES, OUTPUT_COLUMNS  # noqa: E402

NEUTRAL = "中立"
VALID_CATEGORIES = {*ACTIVE_CATEGORIES, NEUTRAL}

EXPECTED_ROWS = 30
EXPECTED_AGREEMENT = 21

# Posts the classifier does not label as intended, with the documented cause.
# Section references are to docs/baseline_evaluation.md.
EXPECTED_DISAGREEMENTS = {
    "S09": ("欲望・執着", "情報共有"),   # 6.3 目撃情報 fires on word presence
    "S10": ("欲望・執着", NEUTRAL),      # 6.4 indirect desire has no rule
    "S12": ("不満・怒り", NEUTRAL),      # 6.4 scores 1.70, below the 1.8 threshold
    "S14": ("不満・怒り", NEUTRAL),      # 6.4 no rule fires
    "S19": ("焦り・競争", NEUTRAL),      # 6.2 並びます is not in the 並んで/並ぶ forms
    "S21": ("交換・取引", NEUTRAL),      # 6.1 \b交換\b does not fire on 交換して
    "S23": ("交換・取引", NEUTRAL),      # 6.1 same word-boundary defect
    "S26": ("情報共有", NEUTRAL),        # 6.3 information sharing scores 0.000 F1
    "S28": ("情報共有", NEUTRAL),        # 6.3 same
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_sample_output.py <classified.csv>")
    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"{path} was not produced")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != EXPECTED_ROWS:
        fail(f"expected {EXPECTED_ROWS} rows, found {len(rows)}")

    missing = [column for column in OUTPUT_COLUMNS if column not in rows[0]]
    if missing:
        fail(f"output is missing columns: {missing}")

    invalid = {
        row["post_id"]: row["sentiment_category"]
        for row in rows
        if row["sentiment_category"] not in VALID_CATEGORIES
    }
    if invalid:
        fail(f"rows predicted a category outside the seven labels: {invalid}")

    disagreements = {
        row["post_id"]: (row["intended_category"], row["sentiment_category"])
        for row in rows
        if row["sentiment_category"] != row["intended_category"]
    }
    agreement = len(rows) - len(disagreements)

    if disagreements != EXPECTED_DISAGREEMENTS:
        added = {k: v for k, v in disagreements.items() if k not in EXPECTED_DISAGREEMENTS}
        removed = {k: v for k, v in EXPECTED_DISAGREEMENTS.items() if k not in disagreements}
        changed = {
            k: (EXPECTED_DISAGREEMENTS[k], v)
            for k, v in disagreements.items()
            if k in EXPECTED_DISAGREEMENTS and EXPECTED_DISAGREEMENTS[k] != v
        }
        fail(
            "the recorded outcome changed.\n"
            f"  newly wrong : {added or '{}'}\n"
            f"  newly right : {removed or '{}'}\n"
            f"  different   : {changed or '{}'}\n"
            "  If this was intended, update EXPECTED_DISAGREEMENTS and\n"
            "  EXPECTED_AGREEMENT in this file."
        )

    if agreement != EXPECTED_AGREEMENT:
        fail(f"expected agreement {EXPECTED_AGREEMENT}/{EXPECTED_ROWS}, got {agreement}")

    print(f"OK: {len(rows)} rows classified, {agreement}/{len(rows)} match the intended label")
    print(f"OK: {len(disagreements)} known disagreements reproduced exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
