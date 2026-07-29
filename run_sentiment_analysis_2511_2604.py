#!/usr/bin/env python3
"""Run the improved sentiment analysis on data/output/2511-2604.csv.

Outputs are deterministic and do not overwrite the source file.  The script
creates a row-level classified CSV, long-form summary CSV, a stratified manual
review sample, and a JSON QA/analysis bundle used by the HTML report.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from classify_sns_rule_based import (
    ACTIVE_CATEGORIES,
    OUTPUT_COLUMNS,
    PRIORITY,
    VERSION,
    classify_detailed,
    classify_legacy,
    normalize_text,
)


SOURCE = Path("data/output/2511-2604.csv")
OUTPUT_DIR = Path("data/output")
CLASSIFIED = OUTPUT_DIR / "sentiment_classified_2511-2604.csv"
SUMMARY_CSV = OUTPUT_DIR / "sentiment_summary_2511-2604.csv"
VALIDATION_CSV = OUTPUT_DIR / "sentiment_validation_sample_2511-2604.csv"
ANALYSIS_JSON = OUTPUT_DIR / "sentiment_analysis_2511-2604.json"

SEED = 20260716
SAMPLE_PER_CATEGORY = 30

RESULT_COLUMNS = OUTPUT_COLUMNS + [
    "legacy_sentiment_category",
    "legacy_matched_keywords",
    "classification_changed_from_v1",
]


def parse_number(value: str | None) -> int:
    if value is None:
        return 0
    text = str(value).replace(",", "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def month_of(value: str) -> str:
    text = (value or "").strip()
    if len(text) >= 7 and text[4] in "-/" and text[0:4].isdigit():
        return text[:7].replace("/", "-")
    return "日付不明"


def post_type(row: dict[str, str]) -> str:
    content = (row.get("内容") or "").lstrip().casefold()
    repost_kind = (row.get("リポストの種類") or "").strip()
    if content.startswith("rt @") or repost_kind:
        return "リポスト"
    return "オリジナル"


def share(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def safe_mean(values: list[int]) -> float:
    return round(statistics.fmean(values), 3) if values else 0.0


def safe_median(values: list[int]) -> float:
    return round(float(statistics.median(values)), 3) if values else 0.0


def append_reservoir(
    reservoirs: dict[str, list[dict[str, str]]],
    seen: Counter[str],
    category: str,
    row: dict[str, str],
    rng: random.Random,
) -> None:
    seen[category] += 1
    bucket = reservoirs[category]
    if len(bucket) < SAMPLE_PER_CATEGORY:
        bucket.append(row)
        return
    candidate = rng.randrange(seen[category])
    if candidate < SAMPLE_PER_CATEGORY:
        bucket[candidate] = row


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source not found: {SOURCE}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    monthly_counts: dict[str, Counter[str]] = defaultdict(Counter)
    monthly_original_counts: dict[str, Counter[str]] = defaultdict(Counter)
    monthly_unique_text_counts: dict[str, Counter[str]] = defaultdict(Counter)
    monthly_seen_text_hashes: dict[str, set[str]] = defaultdict(set)
    polarity_counts = Counter()
    confidence_counts = Counter()
    post_type_counts = Counter()
    category_post_types: dict[str, Counter[str]] = defaultdict(Counter)
    secondary_counts = Counter()
    legacy_counts = Counter()
    transition_counts = Counter()
    evidence_counts: dict[str, Counter[str]] = defaultdict(Counter)
    confidence_by_category: dict[str, Counter[str]] = defaultdict(Counter)
    category_users: dict[str, set[str]] = defaultdict(set)
    likes: dict[str, list[int]] = defaultdict(list)
    reposts: dict[str, list[int]] = defaultdict(list)
    replies: dict[str, list[int]] = defaultdict(list)
    views: dict[str, list[int]] = defaultdict(list)
    month_totals = Counter()

    total_rows = 0
    blank_text = 0
    invalid_month = 0
    duplicate_ids = 0
    duplicate_texts = 0
    changed_from_v1 = 0
    seen_ids: set[str] = set()
    seen_text_hashes: set[str] = set()
    text_hash_counts = Counter()
    unique_text_category_counts = Counter()
    min_date = ""
    max_date = ""
    rng = random.Random(SEED)
    reservoirs: dict[str, list[dict[str, str]]] = defaultdict(list)
    reservoir_seen = Counter()

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        if not reader.fieldnames:
            raise ValueError(f"Source has no header: {SOURCE}")
        if "内容" not in reader.fieldnames or "投稿時間" not in reader.fieldnames:
            raise ValueError("Source must contain 内容 and 投稿時間 columns")

        source_headers = list(reader.fieldnames)
        result_headers = [h for h in source_headers if h not in RESULT_COLUMNS] + RESULT_COLUMNS

        with CLASSIFIED.open("w", encoding="utf-8-sig", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=result_headers, extrasaction="ignore")
            writer.writeheader()

            for row in reader:
                total_rows += 1
                text = row.get("内容") or ""
                result = classify_detailed(text)
                legacy_category, legacy_matched = classify_legacy(text)
                changed = result.primary != legacy_category

                row.update(
                    {
                        "sentiment_category": result.primary,
                        "sentiment_secondary": result.secondary,
                        "sentiment_polarity": result.polarity,
                        "sentiment_score": f"{result.score:.2f}",
                        "sentiment_confidence": result.confidence,
                        "matched_keywords": result.matched_keywords,
                        "category_scores": json.dumps(
                            result.scores, ensure_ascii=False, separators=(",", ":")
                        ),
                        "classification_version": VERSION,
                        "legacy_sentiment_category": legacy_category,
                        "legacy_matched_keywords": legacy_matched,
                        "classification_changed_from_v1": "1" if changed else "0",
                    }
                )
                writer.writerow(row)

                category = result.primary
                month = month_of(row.get("投稿時間") or "")
                kind = post_type(row)
                counts[category] += 1
                monthly_counts[month][category] += 1
                month_totals[month] += 1
                polarity_counts[result.polarity] += 1
                confidence_counts[result.confidence] += 1
                confidence_by_category[category][result.confidence] += 1
                post_type_counts[kind] += 1
                category_post_types[category][kind] += 1
                if kind == "オリジナル":
                    monthly_original_counts[month][category] += 1
                legacy_counts[legacy_category] += 1
                transition_counts[(legacy_category, category)] += 1
                if result.secondary:
                    secondary_counts[result.secondary] += 1
                if changed:
                    changed_from_v1 += 1

                for item in result.evidence:
                    evidence_counts[category][item] += 1

                user_id = (row.get("ユーザーID_文字列") or row.get("ユーザーID") or "").strip()
                if user_id:
                    category_users[category].add(user_id)
                likes[category].append(parse_number(row.get("いいね数")))
                reposts[category].append(parse_number(row.get("リポスト数")))
                replies[category].append(parse_number(row.get("返信数")))
                views[category].append(parse_number(row.get("表示回数")))

                timestamp = (row.get("投稿時間") or "").strip()
                if timestamp:
                    min_date = timestamp if not min_date or timestamp < min_date else min_date
                    max_date = timestamp if not max_date or timestamp > max_date else max_date
                if month == "日付不明":
                    invalid_month += 1
                if not normalize_text(text):
                    blank_text += 1

                post_id = (row.get("投稿ID_文字列") or row.get("投稿ID") or "").strip()
                if post_id:
                    if post_id in seen_ids:
                        duplicate_ids += 1
                    seen_ids.add(post_id)
                text_hash = hashlib.sha1(normalize_text(text).encode("utf-8")).hexdigest()
                if text_hash not in monthly_seen_text_hashes[month]:
                    monthly_unique_text_counts[month][category] += 1
                    monthly_seen_text_hashes[month].add(text_hash)
                if text_hash in seen_text_hashes:
                    duplicate_texts += 1
                else:
                    unique_text_category_counts[category] += 1
                seen_text_hashes.add(text_hash)
                text_hash_counts[text_hash] += 1

                append_reservoir(reservoirs, reservoir_seen, category, dict(row), rng)

    category_rows: list[dict[str, Any]] = []
    for category in PRIORITY:
        count = counts[category]
        if not count:
            continue
        category_rows.append(
            {
                "category": category,
                "count": count,
                "share": share(count, total_rows),
                "unique_users": len(category_users[category]),
                "original_posts": category_post_types[category]["オリジナル"],
                "reposts": category_post_types[category]["リポスト"],
                "repost_share": share(category_post_types[category]["リポスト"], count),
                "likes_sum": sum(likes[category]),
                "likes_mean": safe_mean(likes[category]),
                "likes_median": safe_median(likes[category]),
                "reposts_sum": sum(reposts[category]),
                "replies_sum": sum(replies[category]),
                "views_sum": sum(views[category]),
                "top_evidence": [
                    {"evidence": item, "count": n}
                    for item, n in evidence_counts[category].most_common(10)
                ],
            }
        )

    monthly_rows: list[dict[str, Any]] = []
    for month in sorted(monthly_counts):
        total = month_totals[month]
        for category in PRIORITY:
            count = monthly_counts[month][category]
            monthly_rows.append(
                {
                    "month": month,
                    "category": category,
                    "count": count,
                    "share": share(count, total),
                    "month_total": total,
                }
            )

    monthly_deduplicated_rows: list[dict[str, Any]] = []
    monthly_original_rows: list[dict[str, Any]] = []
    for month in sorted(monthly_counts):
        dedup_total = sum(monthly_unique_text_counts[month].values())
        original_total = sum(monthly_original_counts[month].values())
        for category in PRIORITY:
            monthly_deduplicated_rows.append(
                {
                    "month": month,
                    "category": category,
                    "count": monthly_unique_text_counts[month][category],
                    "share": share(monthly_unique_text_counts[month][category], dedup_total),
                    "month_total": dedup_total,
                }
            )
            monthly_original_rows.append(
                {
                    "month": month,
                    "category": category,
                    "count": monthly_original_counts[month][category],
                    "share": share(monthly_original_counts[month][category], original_total),
                    "month_total": original_total,
                }
            )

    with SUMMARY_CSV.open("w", encoding="utf-8-sig", newline="") as dst:
        fieldnames = [
            "集計種別", "期間", "カテゴリ", "件数", "割合", "月間総投稿数",
            "ユニークユーザー数", "オリジナル投稿数", "リポスト投稿数", "リポスト割合",
            "いいね合計", "いいね平均", "いいね中央値", "リポスト数合計",
            "返信数合計", "表示回数合計",
        ]
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()
        for row in category_rows:
            writer.writerow(
                {
                    "集計種別": "全期間_カテゴリ",
                    "期間": "2025-11~2026-04",
                    "カテゴリ": row["category"],
                    "件数": row["count"],
                    "割合": row["share"],
                    "月間総投稿数": total_rows,
                    "ユニークユーザー数": row["unique_users"],
                    "オリジナル投稿数": row["original_posts"],
                    "リポスト投稿数": row["reposts"],
                    "リポスト割合": row["repost_share"],
                    "いいね合計": row["likes_sum"],
                    "いいね平均": row["likes_mean"],
                    "いいね中央値": row["likes_median"],
                    "リポスト数合計": row["reposts_sum"],
                    "返信数合計": row["replies_sum"],
                    "表示回数合計": row["views_sum"],
                }
            )
        by_cat = {row["category"]: row for row in category_rows}
        for row in monthly_rows:
            overall = by_cat.get(row["category"], {})
            writer.writerow(
                {
                    "集計種別": "月別_カテゴリ",
                    "期間": row["month"],
                    "カテゴリ": row["category"],
                    "件数": row["count"],
                    "割合": row["share"],
                    "月間総投稿数": row["month_total"],
                    "ユニークユーザー数": "",
                    "オリジナル投稿数": "",
                    "リポスト投稿数": "",
                    "リポスト割合": "",
                    "いいね合計": "",
                    "いいね平均": "",
                    "いいね中央値": "",
                    "リポスト数合計": "",
                    "返信数合計": "",
                    "表示回数合計": "",
                }
            )

    validation_rows: list[dict[str, str]] = []
    validation_id = 0
    for category in PRIORITY:
        for row in reservoirs.get(category, []):
            validation_id += 1
            validation_rows.append(
                {
                    "確認ID": f"V{validation_id:03d}",
                    "投稿ID_文字列": row.get("投稿ID_文字列", ""),
                    "投稿時間": row.get("投稿時間", ""),
                    "内容": row.get("内容", ""),
                    "分類カテゴリ": row.get("sentiment_category", ""),
                    "副カテゴリ": row.get("sentiment_secondary", ""),
                    "極性": row.get("sentiment_polarity", ""),
                    "信頼度": row.get("sentiment_confidence", ""),
                    "スコア": row.get("sentiment_score", ""),
                    "分類根拠": row.get("matched_keywords", ""),
                    "旧コード分類": row.get("legacy_sentiment_category", ""),
                    "手動正解ラベル": "",
                    "分類正誤": "",
                    "確認メモ": "",
                }
            )
    with VALIDATION_CSV.open("w", encoding="utf-8-sig", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=list(validation_rows[0]))
        writer.writeheader()
        writer.writerows(validation_rows)

    top_transitions = [
        {"legacy": old, "improved": new, "count": count}
        for (old, new), count in transition_counts.most_common()
        if old != new
    ][:20]

    unique_text_total = sum(unique_text_category_counts.values())
    deduplicated_text_summary = [
        {
            "category": category,
            "count": unique_text_category_counts[category],
            "share": share(unique_text_category_counts[category], unique_text_total),
        }
        for category in PRIORITY
    ]
    original_only_total = post_type_counts["オリジナル"]
    original_only_summary = [
        {
            "category": category,
            "count": category_post_types[category]["オリジナル"],
            "share": share(category_post_types[category]["オリジナル"], original_only_total),
        }
        for category in PRIORITY
    ]

    analysis = {
        "metadata": {
            "source": str(SOURCE),
            "source_rows": total_rows,
            "date_min": min_date,
            "date_max": max_date,
            "timezone": "Asia/Tokyo (source timezone assumed)",
            "classifier_version": VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "seed": SEED,
            "categories": PRIORITY,
            "source_scope": "広告除去後に結合した2025-11〜2026-04の投稿",
        },
        "quality": {
            "blank_text_rows": blank_text,
            "invalid_month_rows": invalid_month,
            "duplicate_post_ids": duplicate_ids,
            "duplicate_normalized_texts": duplicate_texts,
            "duplicate_normalized_text_share": share(duplicate_texts, total_rows),
            "duplicate_text_groups": sum(1 for n in text_hash_counts.values() if n > 1),
            "max_duplicate_text_frequency": max(text_hash_counts.values(), default=0),
            "unique_post_ids": len(seen_ids),
            "classification_changed_from_v1": changed_from_v1,
            "classification_changed_share": share(changed_from_v1, total_rows),
            "manual_validation_rows": len(validation_rows),
            "manual_validation_status": "未実施：手動正解ラベル列は未入力",
        },
        "category_summary": category_rows,
        "monthly_summary": monthly_rows,
        "monthly_deduplicated_summary": monthly_deduplicated_rows,
        "monthly_original_only_summary": monthly_original_rows,
        "polarity_summary": [
            {"polarity": key, "count": value, "share": share(value, total_rows)}
            for key, value in polarity_counts.most_common()
        ],
        "confidence_summary": [
            {"confidence": key, "count": value, "share": share(value, total_rows)}
            for key, value in confidence_counts.most_common()
        ],
        "post_type_summary": [
            {"post_type": key, "count": value, "share": share(value, total_rows)}
            for key, value in post_type_counts.most_common()
        ],
        "deduplicated_text_summary": deduplicated_text_summary,
        "original_only_summary": original_only_summary,
        "confidence_by_category": {
            category: dict(confidence_by_category[category]) for category in PRIORITY
        },
        "legacy_summary": [
            {"category": key, "count": value, "share": share(value, total_rows)}
            for key, value in legacy_counts.most_common()
        ],
        "top_changed_pairs": top_transitions,
        "secondary_category_counts": dict(secondary_counts),
        "outputs": {
            "classified_csv": str(CLASSIFIED),
            "summary_csv": str(SUMMARY_CSV),
            "validation_csv": str(VALIDATION_CSV),
        },
    }
    ANALYSIS_JSON.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "source_rows": total_rows,
        "changed_from_v1": changed_from_v1,
        "category_counts": dict(counts),
        "classified": str(CLASSIFIED),
        "summary": str(SUMMARY_CSV),
        "validation": str(VALIDATION_CSV),
        "analysis": str(ANALYSIS_JSON),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
