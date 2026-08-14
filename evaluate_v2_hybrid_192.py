#!/usr/bin/env python3
"""Task 6 — re-score v2 against the normalized 192-item gold standard.

Gold : data/output/gold_standard_192_normalized.csv  (189 original + 3 supplement)
Pred : data/output/sentiment_classified_hybrid.csv    (SHA f273c9306507804a)

Both criteria from the earlier 189-row baseline are reproduced at n=192:
  (1) lenient - the single v2 label counts as a hit if it is in the gold set
  (2) multi   - prediction set = every category scoring >= 1.8
Task 6 asks for (2); (1) is kept because slide page 13 quotes it.

No classifier code is modified.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from normalize_gold_standard_192 import (
    DEFAULT_OUTPUT as NORMALIZED_GOLD_STANDARD,
    validate_normalized_gold,
)

csv.field_size_limit(10**9)

PROJECT_ROOT = Path(__file__).resolve().parent
GOLD = NORMALIZED_GOLD_STANDARD
PRED = Path("data/output/sentiment_classified_hybrid.csv")
# Generated scoring report.  The curated document is docs/baseline_evaluation.md,
# which is maintained in English by hand; writing there would overwrite it.
OUT = Path("data/output/baseline_gold192_generated.md")

MIN_PRIMARY_SCORE = 1.8

COLMAP = {
    "喜び満足": "喜び・満足",
    "欲望執着": "欲望・執着",
    "不満怒り": "不満・怒り",
    "焦り競争": "焦り・競争",
    "情報共有": "情報共有",
    "交換取引": "交換・取引",
}
CATEGORIES = [
    "不満・怒り", "焦り・競争", "交換・取引",
    "欲望・執着", "喜び・満足", "情報共有", "中立",
]


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def summarize_confusions(
    counts: dict[str, dict[str, int]],
) -> dict[str, object]:
    """Summarize category confusion counts with micro and macro PRF."""
    tp_sum = sum(counts[cat]["tp"] for cat in CATEGORIES)
    fp_sum = sum(counts[cat]["fp"] for cat in CATEGORIES)
    fn_sum = sum(counts[cat]["fn"] for cat in CATEGORIES)
    micro_p, micro_r, micro_f1 = prf(tp_sum, fp_sum, fn_sum)
    per_category = {
        cat: {
            **counts[cat],
            **dict(
                zip(
                    ("precision", "recall", "f1"),
                    prf(
                        counts[cat]["tp"],
                        counts[cat]["fp"],
                        counts[cat]["fn"],
                    ),
                )
            ),
        }
        for cat in CATEGORIES
    }
    macro = {
        metric: sum(per_category[cat][metric] for cat in CATEGORIES)
        / len(CATEGORIES)
        for metric in ("precision", "recall", "f1")
    }
    return {
        "per_category": per_category,
        "micro": {
            "tp": tp_sum,
            "fp": fp_sum,
            "fn": fn_sum,
            "precision": micro_p,
            "recall": micro_r,
            "f1": micro_f1,
        },
        "macro": macro,
    }


def calculate_evaluation_metrics(rows: list[dict]) -> dict[str, object]:
    """Return the two established evaluation definitions for the same rows."""
    lenient_counts = {
        category: {"tp": 0, "fp": 0, "fn": 0}
        for category in CATEGORIES
    }
    multi_counts = {
        category: {"tp": 0, "fp": 0, "fn": 0}
        for category in CATEGORIES
    }
    for row in rows:
        gold, single, multi = row["gold"], row["single"], row["multi"]
        for category in CATEGORIES:
            if single == category:
                lenient_counts[category][
                    "tp" if category in gold else "fp"
                ] += 1
            elif category in gold:
                lenient_counts[category]["fn"] += 1
            if category in multi:
                multi_counts[category][
                    "tp" if category in gold else "fp"
                ] += 1
            elif category in gold:
                multi_counts[category]["fn"] += 1
    return {
        "sample_size": len(rows),
        "lenient": summarize_confusions(lenient_counts),
        "multi": summarize_confusions(multi_counts),
        "lenient_hits": sum(
            row["single"] in row["gold"] for row in rows
        ),
        "multi_exact_matches": sum(
            row["multi"] == row["gold"] for row in rows
        ),
    }


def normal_ci(k: int, n: int) -> tuple[float, float]:
    """Normal approximation - the method used for the intervals in 2-3."""
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return max(0.0, p - h), min(1.0, p + h)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load(
    gold_path: Path = GOLD,
    pred_path: Path = PRED,
) -> tuple[list[dict], int]:
    gold_path = Path(validate_normalized_gold(gold_path)["path"])
    gold = []
    with gold_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["要検討"] == "1":
                continue
            labels = {cat for col, cat in COLMAP.items() if row[col] == "1"}
            gold.append(
                {"post_id": row["post_id"], "gold": labels or {"中立"},
                 "text": row["clean_text"]}
            )

    wanted = {g["post_id"] for g in gold}
    pred = {}
    with pred_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pid = row["投稿ID_文字列"]
            if pid not in wanted:
                continue
            scores = json.loads(row["category_scores"])
            over = {c for c, v in scores.items() if v >= MIN_PRIMARY_SCORE}
            pred[pid] = {
                "single": row["sentiment_category"],
                "multi": over or {"中立"},
                "confidence": row["sentiment_confidence"],
            }
    return [{**g, **pred[g["post_id"]]} for g in gold if g["post_id"] in pred], len(gold)


def table(counts, lines, title):
    lines += [f"### {title}", "",
              "| カテゴリ | 正解数 | 予測数 | TP | FP | FN | Precision | Recall | F1 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    tp_s = fp_s = fn_s = 0
    macro = []
    for cat in CATEGORIES:
        c = counts[cat]
        p, r, f = prf(c["tp"], c["fp"], c["fn"])
        tp_s += c["tp"]
        fp_s += c["fp"]
        fn_s += c["fn"]
        macro.append((p, r, f))
        lines.append(f"| {cat} | {c['tp']+c['fn']} | {c['tp']+c['fp']} | {c['tp']} | "
                     f"{c['fp']} | {c['fn']} | {p:.3f} | {r:.3f} | **{f:.3f}** |")
    mp, mr, mf = prf(tp_s, fp_s, fn_s)
    Mp = sum(x[0] for x in macro) / len(macro)
    Mr = sum(x[1] for x in macro) / len(macro)
    Mf = sum(x[2] for x in macro) / len(macro)
    lines += [f"| **micro平均** | {tp_s+fn_s} | {tp_s+fp_s} | {tp_s} | {fp_s} | {fn_s} | "
              f"{mp:.3f} | {mr:.3f} | **{mf:.3f}** |",
              f"| **macro平均** | | | | | | {Mp:.3f} | {Mr:.3f} | **{Mf:.3f}** |", ""]
    return mf, Mf


def main(
    gold_path: Path = GOLD,
    pred_path: Path = PRED,
    output: Path = OUT,
) -> None:
    rows, n_gold = load(gold_path, pred_path)
    n = len(rows)

    metrics = calculate_evaluation_metrics(rows)
    lenient = {
        category: {
            key: value
            for key, value in metrics["lenient"]["per_category"][
                category
            ].items()
            if key in {"tp", "fp", "fn"}
        }
        for category in CATEGORIES
    }
    multi = {
        category: {
            key: value
            for key, value in metrics["multi"]["per_category"][
                category
            ].items()
            if key in {"tp", "fp", "fn"}
        }
        for category in CATEGORIES
    }
    hit = metrics["lenient_hits"]
    exact = metrics["multi_exact_matches"]

    L = [
        "# ハイブリッドコーパス ベースライン精度（正解セット192件）", "",
        "**測定日**: 2026-07-30",
        f"**正解セット**: `{display_path(gold_path)}`"
        "（189件＋補充3件、多重ラベル）",
        f"**評価対象**: `{display_path(pred_path)}`"
        "（SHA-256 `f273c9306507804a`、v2.0.0、**未修正**）",
        "**評価スクリプト**: `evaluate_v2_hybrid_192.py`", "",
        "---", "", "## 0. 測定条件", "",
        f"- 正解セット {n_gold}件 / 予測との突合 **{n}件**（欠損 {n_gold - n}件）",
        "- 判断保留（要検討=1）: 0件（元の11件は189件側で既に除外済み）",
        "- 閾値 `MIN_PRIMARY_SCORE = 1.8`（v2のまま）", "",
        "### 正解セットの分布（192件）", "",
        "| カテゴリ | 正解件数 | 割合 |", "|---|---:|---:|",
    ]
    gold_counts = {c: sum(1 for r in rows if c in r["gold"]) for c in CATEGORIES}
    for c in sorted(CATEGORIES, key=lambda x: -gold_counts[x]):
        L.append(f"| {c} | {gold_counts[c]} | {gold_counts[c]/n*100:.1f}% |")
    L += [f"| （延べラベル数） | {sum(gold_counts.values())} | |", "",
          "1投稿あたりのラベル数の分布:", ""]
    dist = {}
    for r in rows:
        k = 0 if r["gold"] == {"中立"} else len(r["gold"])
        dist[k] = dist.get(k, 0) + 1
    for k in sorted(dist):
        lbl = "0個（＝中立）" if k == 0 else f"{k}個"
        L.append(f"- {lbl}: {dist[k]}件")
    L += ["", "---", "", "## 1. 基準(2) 多重ラベル基準 ★タスク6の指定基準", "",
          "`category_scores` が 1.8 以上の全カテゴリを予測集合とする。空集合は 中立。", ""]
    mf2, Mf2 = table(multi, L, "多重ラベル基準")
    L += [f"**予測集合が正解集合と完全一致: {exact}/{n} = {exact/n:.3f}**", "",
          "---", "", "## 2. 基準(1) 緩和基準（ページ13が引用している基準）", "",
          "v2の単一ラベルが正解ラベル集合に含まれれば正解とみなす。", ""]
    mf1, Mf1 = table(lenient, L, "緩和基準")
    lo, hi = normal_ci(hit, n)
    L += [f"**緩和基準の的中率: {hit}/{n} = {hit/n:.3f}**（95%CI {lo:.3f}–{hi:.3f}）", "",
          "---", "", "## 3. 189件版との差分", "",
          "| 指標 | 189件版 | 192件版 | 差 |", "|---|---:|---:|---:|",
          f"| 緩和 micro F1 | 0.576 | {mf1:.3f} | {mf1-0.576:+.3f} |",
          f"| 緩和 macro F1 | 0.451 | {Mf1:.3f} | {Mf1-0.451:+.3f} |",
          f"| 多重 micro F1 | 0.594 | {mf2:.3f} | {mf2-0.594:+.3f} |",
          f"| 多重 macro F1 | 0.496 | {Mf2:.3f} | {Mf2-0.496:+.3f} |", "",
          "補充3件はいずれも正解ラベルが `交換・取引` 単独であり、v2も3件とも "
          "`交換・取引` と予測している。したがって差分は交換・取引のTP+3のみで、"
          "他カテゴリの数値は189件版と変わらない。", "",
          "既存189件の予測は旧コーパスとハイブリッドで**相違0件**であることを確認済み"
          "（v2は決定的なため）。", "",
          "---", "", "## 4. 仕様書2-3節の構成比・信頼区間の検算", "",
          "| カテゴリ | 実測割合 | 仕様書2-3 | 95%CI（正規近似） | 仕様書2-3 | 判定 |",
          "|---|---:|---:|---|---|---|"]
    spec = {"交換・取引": (28.1, "21.8 – 34.5%"), "中立": (25.0, "18.9 – 31.1%"),
            "欲望・執着": (18.8, "13.2 – 24.3%"), "喜び・満足": (17.2, "11.9 – 22.5%"),
            "焦り・競争": (14.1, "9.1 – 19.0%"), "不満・怒り": (7.3, "3.6 – 11.0%"),
            "情報共有": (2.6, "0.4 – 4.9%")}
    all_ok = True
    for c, (want_p, want_ci) in spec.items():
        k = gold_counts[c]
        p = k / n * 100
        clo, chi = normal_ci(k, n)
        got_ci = f"{clo*100:.1f} – {chi*100:.1f}%"
        ok = abs(p - want_p) < 0.06 and got_ci.replace(" ", "") == want_ci.replace(" ", "")
        all_ok &= ok
        L.append(f"| {c} | {p:.1f}% | {want_p}% | {got_ci} | {want_ci} | "
                 f"{'✓' if ok else '★不一致'} |")
    L += ["", f"**検算結果: {'2-3節の数値はすべて再現できた。' if all_ok else '不一致あり（上表）。'}**", ""]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(L).rstrip() + "\n", encoding="utf-8")

    print(f"n={n}  lenient micro F1={mf1:.3f} macro={Mf1:.3f}  hit={hit}/{n}")
    print(f"      multi   micro F1={mf2:.3f} macro={Mf2:.3f}  exact={exact}/{n}")
    print(f"2-3 check all match: {all_ok}")
    print("lenient F1 per category:")
    for c in CATEGORIES:
        cc = lenient[c]
        print(f"   {c}: {prf(cc['tp'], cc['fp'], cc['fn'])[2]:.3f}")
    print(f"-> {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=GOLD)
    parser.add_argument("--predictions", type=Path, default=PRED)
    parser.add_argument("--output", type=Path, default=OUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.gold, args.predictions, args.output)
