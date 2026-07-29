#!/usr/bin/env python3
"""Sample posts with negotiation wording that were not classified as trade.

Sampling frame:
  data/output/sentiment_classified_2511-2604.csv

Eligibility:
  - ``sentiment_category`` is not ``交換・取引``
  - ``内容`` contains one or more of the narrowly defined negotiation
    expressions below, including inflectional variants of the examples in the
    request.

Sampling:
  - simple random sample without replacement
  - fixed seed for reproducibility
"""

from __future__ import annotations

import csv
import random
import re
from collections import Counter
from pathlib import Path


SOURCE = Path("data/output/sentiment_classified_2511-2604.csv")
OUTPUT = Path(
    "data/output/random_sample_50_negotiation_not_exchange_202511_202604.csv"
)
SAMPLE_SIZE = 50
SEED = 20260728

EXCLUDED_CATEGORY = "交換・取引"
CATEGORY_COLUMN = "sentiment_category"
TEXT_COLUMN = "内容"
ID_COLUMN = "投稿ID_文字列"

# These patterns deliberately avoid broad standalone words such as 「希望」,
# 「検討」, or 「お声掛け」, which can occur outside exchange/transaction
# negotiations. The requested examples are covered directly:
# 求めており / 交換希望でしょうか / お取引可能 / 検討させていただ.
NEGOTIATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "求めており系",
        re.compile(r"求めて(?:おり|おります|います|おりまして)"),
    ),
    (
        "交換希望系",
        re.compile(
            r"(?:ご)?交換\s*(?:を)?(?:希望|ご希望)"
            r"(?:です|しております|でしょうか)?"
        ),
    ),
    (
        "交換可能系",
        re.compile(
            r"(?:ご)?交換(?:が|は)?可能"
            r"(?:でしょうか|ですか|です)?"
        ),
    ),
    (
        "交換依頼系",
        re.compile(
            r"(?:ご)?交換(?:して|をして)?"
            r"いただ(?:け|き|けます|けない|けません)"
        ),
    ),
    (
        "お取引可能・希望",
        re.compile(
            r"お取引(?:が|は)?(?:可能|希望)"
            r"|取引可能"
            r"|お取引を希望"
        ),
    ),
    (
        "郵送希望",
        re.compile(r"郵送(?:での)?(?:お取引を)?希望"),
    ),
    (
        "検討させていただ",
        re.compile(r"(?:ご)?検討させていただ"),
    ),
    (
        "募集して系",
        re.compile(r"募集して(?:おり|おります|います)"),
    ),
]


def find_matches(text: str) -> tuple[list[str], list[str]]:
    """Return unique pattern labels and literal substrings in source order."""
    hits: list[tuple[int, str, str]] = []
    for label, pattern in NEGOTIATION_PATTERNS:
        for match in pattern.finditer(text):
            hits.append((match.start(), label, match.group(0)))
    hits.sort(key=lambda item: item[0])

    labels: list[str] = []
    literals: list[str] = []
    for _, label, literal in hits:
        if label not in labels:
            labels.append(label)
        if literal not in literals:
            literals.append(literal)
    return labels, literals


def main() -> None:
    csv.field_size_limit(10**9)
    candidates: list[tuple[dict[str, str], list[str], list[str]]] = []

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if reader.fieldnames is None:
            raise ValueError(f"Missing header: {SOURCE}")

        required = {CATEGORY_COLUMN, TEXT_COLUMN, ID_COLUMN}
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        source_columns = reader.fieldnames
        for row in reader:
            if row[CATEGORY_COLUMN] == EXCLUDED_CATEGORY:
                continue
            labels, literals = find_matches(row[TEXT_COLUMN] or "")
            if labels:
                candidates.append((row, labels, literals))

    if len(candidates) < SAMPLE_SIZE:
        raise ValueError(
            f"Only {len(candidates)} eligible rows; cannot sample {SAMPLE_SIZE}"
        )

    sampled = random.Random(SEED).sample(candidates, SAMPLE_SIZE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output_columns = [
        "抽出順",
        "交渉表現タイプ",
        "マッチした交渉表現",
        *source_columns,
    ]

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_columns)
        writer.writeheader()
        for sequence, (row, labels, literals) in enumerate(sampled, start=1):
            writer.writerow(
                {
                    "抽出順": sequence,
                    "交渉表現タイプ": " | ".join(labels),
                    "マッチした交渉表現": " | ".join(literals),
                    **row,
                }
            )

    selected_categories = Counter(
        row[CATEGORY_COLUMN] for row, _, _ in sampled
    )
    selected_pattern_types = Counter(
        label for _, labels, _ in sampled for label in labels
    )
    selected_ids = [row[ID_COLUMN] for row, _, _ in sampled]

    print(f"output={OUTPUT}")
    print(f"seed={SEED}")
    print(f"eligible={len(candidates)}")
    print(f"sample={len(sampled)}")
    print(f"unique_ids={len(set(selected_ids))}")
    print(f"excluded_category_hits={selected_categories[EXCLUDED_CATEGORY]}")
    print(f"selected_categories={dict(selected_categories)}")
    print(f"selected_pattern_types={dict(selected_pattern_types)}")


if __name__ == "__main__":
    main()
