#!/usr/bin/env python3
"""Extract a blind 200-post gold-standard labelling sheet.

Sampling frame : data/output/sentiment_classified_2511-2604.csv (109,037 posts)
Excluded       : every 投稿ID_文字列 already present in
                 data/output/random_sample_100_202511_202604.csv
Method         : simple random sample without replacement, random.Random(SEED).sample()
Seed           : 20260728  (fixed, recorded in the sidecar JSON)

The output deliberately carries NO model output: sentiment_category,
sentiment_score, sentiment_secondary, sentiment_polarity, sentiment_confidence,
matched_keywords, category_scores and legacy_* are all withheld so that manual
labelling stays uncontaminated.

The six label columns are emitted empty for the human to fill with 0/1.
They are multi-label: a post may be 0, 1 or several categories.
An all-zero row means 中立 (there is deliberately no 中立 column).
"""

from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

csv.field_size_limit(10**9)

SOURCE = Path("data/output/sentiment_classified_2511-2604.csv")
EXCLUDE = Path("data/output/random_sample_100_202511_202604.csv")
OUTPUT = Path("data/output/gold_standard_200.csv")
SIDECAR = Path("data/output/gold_standard_200_provenance.json")

SEED = 20260728
N_SAMPLE = 200

ID_COLUMN = "投稿ID_文字列"
LABEL_COLUMNS = [
    "喜び満足",
    "欲望執着",
    "不満怒り",
    "焦り競争",
    "情報共有",
    "交換取引",
]
OUTPUT_COLUMNS = ["post_id", "投稿日", "clean_text"] + LABEL_COLUMNS

WHITESPACE_RE = re.compile(r"\s+")

# Every model-produced column in the source, kept here so the exclusion is
# explicit and auditable rather than implicit in the column selection.
WITHHELD_COLUMNS = [
    "sentiment_category",
    "sentiment_secondary",
    "sentiment_polarity",
    "sentiment_score",
    "sentiment_confidence",
    "matched_keywords",
    "category_scores",
    "classification_version",
    "legacy_sentiment_category",
    "legacy_matched_keywords",
    "classification_changed_from_v1",
]


def clean_text(raw: str) -> str:
    """Collapse newlines/tabs/runs of spaces so the post fits one sheet cell.

    Nothing else is altered: URLs, mentions, emoji, digits and punctuation are
    all preserved, because removing them would change what the labeller reads.
    """
    return WHITESPACE_RE.sub(" ", raw or "").strip()


def post_date(timestamp: str) -> str:
    return (timestamp or "").strip()[:10]


def main() -> None:
    excluded_ids = set()
    with EXCLUDE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            post_id = (row.get(ID_COLUMN) or "").strip()
            if post_id:
                excluded_ids.add(post_id)

    frame: list[dict[str, str]] = []
    excluded_hits = 0
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_seen = len(frame) + excluded_hits
            if (row.get(ID_COLUMN) or "").strip() in excluded_ids:
                excluded_hits += 1
                continue
            frame.append(row)
    total_rows = len(frame) + excluded_hits

    rng = random.Random(SEED)
    picked = rng.sample(frame, N_SAMPLE)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in picked:
            record = {
                "post_id": (row.get(ID_COLUMN) or "").strip(),
                "投稿日": post_date(row.get("投稿時間", "")),
                "clean_text": clean_text(row.get("内容", "")),
            }
            for column in LABEL_COLUMNS:
                record[column] = ""
            writer.writerow(record)

    provenance = {
        "output": str(OUTPUT),
        "seed": SEED,
        "rng": "python random.Random(seed).sample(frame, 200)",
        "python_sampling_note": (
            "frame is built in source-file row order, so the draw is fully "
            "reproducible by re-running this script unchanged"
        ),
        "source": str(SOURCE),
        "source_rows": total_rows,
        "exclusion_file": str(EXCLUDE),
        "excluded_ids": len(excluded_ids),
        "rows_excluded_from_frame": excluded_hits,
        "eligible_frame": len(frame),
        "sample_size": N_SAMPLE,
        "label_columns": LABEL_COLUMNS,
        "label_scheme": (
            "multi-label 0/1; all-zero row means 中立 (no 中立 column by design)"
        ),
        "withheld_model_columns": WITHHELD_COLUMNS,
        "clean_text_definition": (
            "内容 with whitespace runs collapsed to a single space; no other "
            "modification (URLs, mentions, emoji, digits, punctuation preserved)"
        ),
    }
    SIDECAR.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
