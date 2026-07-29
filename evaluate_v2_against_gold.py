#!/usr/bin/env python3
"""Score the shipped v2 classifier against the manual gold standard.

Gold : data/output/gold_standard_labeled_189of200.csv  (multi-label, 0/1)
Pred : data/output/sentiment_classified_2511-2604.csv  (single label + scores)

Two evaluation modes, per the audit request:
  (1) lenient  - v2's single label counts as a hit if it is anywhere in the
                 gold label set for that post.
  (2) multi    - the prediction set is every category scoring >= 1.8
                 (MIN_PRIMARY_SCORE); empty set means 中立.

No classifier code is modified; this only reads the shipped outputs.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

csv.field_size_limit(10**9)

GOLD = Path("data/output/gold_standard_labeled_189of200.csv")
PRED = Path("data/output/sentiment_classified_2511-2604.csv")

MIN_PRIMARY_SCORE = 1.8

# gold column name -> classifier category name
COLMAP = {
    "喜び満足": "喜び・満足",
    "欲望執着": "欲望・執着",
    "不満怒り": "不満・怒り",
    "焦り競争": "焦り・競争",
    "情報共有": "情報共有",
    "交換取引": "交換・取引",
}
# report order follows the methodology priority list
CATEGORIES = [
    "不満・怒り",
    "焦り・競争",
    "交換・取引",
    "欲望・執着",
    "喜び・満足",
    "情報共有",
    "中立",
]


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def load() -> list[dict]:
    gold_rows = []
    with GOLD.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["要検討"] == "1":
                continue
            gold_set = {cat for col, cat in COLMAP.items() if row[col] == "1"}
            if not gold_set:
                gold_set = {"中立"}
            gold_rows.append(
                {
                    "post_id": row["post_id"],
                    "text": row["clean_text"],
                    "gold": gold_set,
                }
            )

    wanted = {r["post_id"] for r in gold_rows}
    pred_by_id: dict[str, dict] = {}
    with PRED.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pid = (row["投稿ID_文字列"] or "").strip()
            if pid not in wanted:
                continue
            scores = json.loads(row["category_scores"])
            over = {c for c, v in scores.items() if v >= MIN_PRIMARY_SCORE}
            pred_by_id[pid] = {
                "single": row["sentiment_category"],
                "multi": over or {"中立"},
                "scores": scores,
                "score": float(row["sentiment_score"]),
                "confidence": row["sentiment_confidence"],
                "evidence": row["matched_keywords"],
                "legacy": row["legacy_sentiment_category"],
            }

    joined = []
    for r in gold_rows:
        p = pred_by_id.get(r["post_id"])
        if p is None:
            continue
        joined.append({**r, **p})
    return gold_rows, joined


def table(counts: dict[str, dict[str, int]], title: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| カテゴリ | 正解数 | 予測数 | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tp_s = fp_s = fn_s = 0
    macro = []
    for cat in CATEGORIES:
        c = counts[cat]
        p, r, f = prf(c["tp"], c["fp"], c["fn"])
        tp_s += c["tp"]
        fp_s += c["fp"]
        fn_s += c["fn"]
        macro.append((p, r, f))
        lines.append(
            f"| {cat} | {c['tp']+c['fn']} | {c['tp']+c['fp']} | {c['tp']} | "
            f"{c['fp']} | {c['fn']} | {p:.3f} | {r:.3f} | **{f:.3f}** |"
        )
    mp, mr, mf = prf(tp_s, fp_s, fn_s)
    Mp = sum(x[0] for x in macro) / len(macro)
    Mr = sum(x[1] for x in macro) / len(macro)
    Mf = sum(x[2] for x in macro) / len(macro)
    lines += [
        f"| **micro平均** | {tp_s+fn_s} | {tp_s+fp_s} | {tp_s} | {fp_s} | {fn_s} "
        f"| {mp:.3f} | {mr:.3f} | **{mf:.3f}** |",
        f"| **macro平均** | | | | | | {Mp:.3f} | {Mr:.3f} | **{Mf:.3f}** |",
        "",
    ]
    return lines


def main() -> None:
    gold_rows, rows = load()
    n = len(rows)

    lenient = {c: Counter() for c in CATEGORIES}
    multi = {c: Counter() for c in CATEGORIES}
    for r in rows:
        g, s, m = r["gold"], r["single"], r["multi"]
        for cat in CATEGORIES:
            if s == cat:
                lenient[cat]["tp" if cat in g else "fp"] += 1
            elif cat in g:
                lenient[cat]["fn"] += 1
            if cat in m:
                multi[cat]["tp" if cat in g else "fp"] += 1
            elif cat in g:
                multi[cat]["fn"] += 1

    lenient_hits = sum(1 for r in rows if r["single"] in r["gold"])
    strict_pool = [r for r in rows if len(r["gold"]) == 1]
    strict_hits = sum(1 for r in strict_pool if r["single"] in r["gold"])
    exact = sum(1 for r in rows if r["multi"] == r["gold"])

    out = {
        "n_gold_labeled": len(gold_rows),
        "n_joined": n,
        "lenient": lenient,
        "multi": multi,
        "lenient_hits": lenient_hits,
        "strict_pool": len(strict_pool),
        "strict_hits": strict_hits,
        "exact_set_match": exact,
        "rows": rows,
    }
    print(f"joined {n}/{len(gold_rows)}")
    print("\n".join(table(lenient, "lenient")))
    print("\n".join(table(multi, "multi")))
    print(f"lenient hit rate {lenient_hits}/{n} = {lenient_hits/n:.3f}")
    print(f"strict (single-gold only) {strict_hits}/{len(strict_pool)} = {strict_hits/len(strict_pool):.3f}")
    print(f"exact set match {exact}/{n} = {exact/n:.3f}")
    return out


if __name__ == "__main__":
    main()
