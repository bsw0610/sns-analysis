#!/usr/bin/env python3
"""Task 6 (partial) and Task 5 output files for slide_plan_10-16.md.

Task 6: merge the 189 labelled gold rows with the 3 supplement rows that
        survive into the hybrid corpus -> data/output/gold_standard_192.csv
        The 3 supplement rows are emitted BLANK; they have never been
        labelled by hand and this script must not guess them.

Task 5: draw 30 posts at random from the 25,370 removed by ad filtering,
        tagged with which removal stage caught them, for manual review
        -> data/output/ad_filter_check_30.csv

Removal stages, reproduced exactly against slide_plan_10-16.md 2-0:
  (1) final keyword removal            19,362  = (all - final) - additional - (old - final)
  (2) old additional ad classification  5,874  = removed_additional_ads_with_reasons
  (3) newly removed by final              134  = old - final
                                       ------
                                       25,370
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

csv.field_size_limit(10**9)

MONTHS = ["202511", "202512", "202601", "202602", "202603", "202604"]
HYBRID = Path("data/output/sentiment_classified_hybrid.csv")
FINAL = Path("data/output/2511-2604_final.csv")
OLD = Path("data/output/2511-2604.csv")
ADDITIONAL = Path("data/output/removed_additional_ads_with_reasons_202511_202604.csv")
GOLD189 = Path("data/output/gold_standard_labeled_189of200.csv")
SUPPLEMENT = Path("data/output/gold_supplement_11.csv")

OUT_GOLD192 = Path("data/output/gold_standard_192.csv")
OUT_ADCHECK = Path("data/output/ad_filter_check_30.csv")

SEED_ADCHECK = 20260730
N_ADCHECK = 30

GOLD_COLUMNS = [
    "post_id", "投稿日", "clean_text",
    "喜び満足", "欲望執着", "不満怒り", "焦り競争", "情報共有", "交換取引",
    "中立", "要検討", "メモ",
]


def id_set(path: Path, column: str = "投稿ID_文字列") -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {row[column] for row in csv.DictReader(f)}


def build_gold_192() -> tuple[int, int]:
    with GOLD189.open("r", encoding="utf-8-sig", newline="") as f:
        labelled = [r for r in csv.DictReader(f) if r["要検討"] != "1"]

    hybrid_ids = id_set(HYBRID)
    with SUPPLEMENT.open("r", encoding="utf-8-sig", newline="") as f:
        supplement = [r for r in csv.DictReader(f) if r["post_id"] in hybrid_ids]

    with OUT_GOLD192.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GOLD_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in labelled:
            writer.writerow(row)
        for row in supplement:
            # Emitted blank on purpose: these three have no manual label yet.
            record = {c: "" for c in GOLD_COLUMNS}
            record["post_id"] = row["post_id"]
            record["投稿日"] = row["投稿日"]
            record["clean_text"] = row["clean_text"]
            writer.writerow(record)

    return len(labelled), len(supplement)


def build_ad_check() -> dict[str, int]:
    all_rows: dict[str, tuple[str, str]] = {}
    for month in MONTHS:
        with Path(f"{month}.csv").open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                all_rows[row[1]] = (row[7], row[8])  # 投稿時間, 内容

    hybrid_ids = id_set(HYBRID)
    final_ids = id_set(FINAL)
    old_ids = id_set(OLD)
    additional_ids = id_set(ADDITIONAL)

    stage3 = old_ids - final_ids
    stage2 = additional_ids
    stage1 = (set(all_rows) - final_ids) - additional_ids - stage3

    stage_of: dict[str, str] = {}
    for pid in stage1:
        stage_of[pid] = "①キーワード"
    for pid in stage2:
        stage_of[pid] = "②追加広告分類"
    for pid in stage3:
        stage_of[pid] = "③最終版追加"

    removed = sorted(set(all_rows) - hybrid_ids)
    assert set(removed) == set(stage_of), "removal stages do not partition the removed set"

    rng = random.Random(SEED_ADCHECK)
    picked = rng.sample(removed, N_ADCHECK)

    with OUT_ADCHECK.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "投稿日", "本文", "除去段階", "判定", "理由メモ"])
        for pid in picked:
            timestamp, text = all_rows[pid]
            writer.writerow(
                [pid, timestamp[:10], " ".join(text.split()), stage_of[pid], "", ""]
            )

    counts = {"①キーワード": len(stage1), "②追加広告分類": len(stage2), "③最終版追加": len(stage3)}
    counts["除去合計"] = len(removed)
    from collections import Counter

    counts["標本内訳"] = dict(Counter(stage_of[p] for p in picked))
    return counts


def main() -> None:
    OUT_GOLD192.parent.mkdir(parents=True, exist_ok=True)
    n_labelled, n_supplement = build_gold_192()
    print(f"[task6] {OUT_GOLD192}: {n_labelled} labelled + {n_supplement} blank = {n_labelled + n_supplement}")
    counts = build_ad_check()
    print(f"[task5] {OUT_ADCHECK}: seed={SEED_ADCHECK}, n={N_ADCHECK}")
    for k, v in counts.items():
        print(f"         {k}: {v}")


if __name__ == "__main__":
    main()
