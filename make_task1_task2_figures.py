#!/usr/bin/env python3
"""Task 1 and Task 2 — the page 13 and page 14 figures.

Task 1: per-category agreement with the manual gold standard (page 13).
        Uses the lenient criterion, which is what page 13's text quotes.
Task 2: composition of the 192-item gold standard with 95% intervals (page 14).

Sources: data/output/gold_standard_192.csv
         data/output/sentiment_classified_hybrid.csv (SHA f273c9306507804a)
Per slide_plan 1-1 / page 13, the word "F1" never appears in the output.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

csv.field_size_limit(10**9)

GOLD = Path("data/output/gold_standard_192.csv")
PRED = Path("data/output/sentiment_classified_hybrid.csv")
OUT13 = Path("data/output/slides/p13_agreement.png")
OUT14 = Path("data/output/slides/p14_composition.png")

MIN_PRIMARY_SCORE = 1.8
COLMAP = {
    "喜び満足": "喜び・満足", "欲望執着": "欲望・執着", "不満怒り": "不満・怒り",
    "焦り競争": "焦り・競争", "情報共有": "情報共有", "交換取引": "交換・取引",
}
CATEGORIES = ["不満・怒り", "焦り・競争", "交換・取引", "欲望・執着",
              "喜び・満足", "情報共有", "中立"]

ACCENT = "#1F5FA9"      # 強調
GREY = "#9AA3AC"        # 通常
FAINT = "#CDD3D9"       # 解釈しない項目

for name in ("Hiragino Sans", "Hiragino Maru Gothic Pro", "Arial Unicode MS"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False


def normal_ci(k: int, n: int) -> tuple[float, float]:
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return max(0.0, p - h), min(1.0, p + h)


def load():
    gold = []
    with GOLD.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["要検討"] == "1":
                continue
            labels = {c for col, c in COLMAP.items() if row[col] == "1"}
            gold.append({"post_id": row["post_id"], "gold": labels or {"中立"}})
    wanted = {g["post_id"] for g in gold}
    pred, hybrid_counts, hybrid_total = {}, {c: 0 for c in CATEGORIES}, 0
    with PRED.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            hybrid_total += 1
            hybrid_counts[row["sentiment_category"]] += 1
            if row["投稿ID_文字列"] in wanted:
                pred[row["投稿ID_文字列"]] = row["sentiment_category"]
    rows = [{**g, "single": pred[g["post_id"]]} for g in gold if g["post_id"] in pred]
    return rows, hybrid_counts, hybrid_total


def main() -> None:
    rows, hybrid_counts, hybrid_total = load()
    n = len(rows)

    # ---- Task 1: agreement (lenient F1, never named "F1" in the output) ----
    agreement = {}
    for cat in CATEGORIES:
        tp = sum(1 for r in rows if r["single"] == cat and cat in r["gold"])
        fp = sum(1 for r in rows if r["single"] == cat and cat not in r["gold"])
        fn = sum(1 for r in rows if r["single"] != cat and cat in r["gold"])
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        agreement[cat] = 2 * p * rc / (p + rc) if p + rc else 0.0

    order = sorted(CATEGORIES, key=lambda c: agreement[c])
    vals = [agreement[c] for c in order]
    colors = [ACCENT if c == "交換・取引" else (FAINT if c == "中立" else GREY) for c in order]

    fig, ax = plt.subplots(figsize=(8.6, 4.9), dpi=200)
    bars = ax.barh(range(len(order)), vals, color=colors, height=0.66)
    for i, (c, v) in enumerate(zip(order, vals)):
        ax.text(v + 0.014, i, f"{v:.2f}", va="center", fontsize=12,
                fontweight="bold" if c == "交換・取引" else "normal",
                color="#1F5FA9" if c == "交換・取引" else "#333333")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=12)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("正解との一致度（1.00 が完全一致）", fontsize=12)
    ax.set_title(f"カテゴリ別 正解との一致度（手作業ラベル {n}件との照合）",
                 fontsize=13, pad=12)
    ax.axvline(0.8, color="#C0392B", linestyle="--", linewidth=1.1, alpha=0.75)
    ax.text(0.805, len(order) - 0.32, "実用水準の目安 0.80", color="#C0392B", fontsize=10.5)

    # 「残り6カテゴリ」= 交換・取引を除く6カテゴリ。中立(0.62)を含む実測レンジを示す。
    rest = [agreement[c] for c in CATEGORIES if c != "交換・取引"]
    i_top = order.index("交換・取引")
    ax.plot([0.955, 0.985, 0.985, 0.955], [-0.34, -0.34, i_top - 0.66, i_top - 0.66],
            color="#5A6570", linewidth=1.2, clip_on=False)
    ax.text(0.995, (i_top - 1) / 2, f"残り6カテゴリ\n{min(rest):.2f} 〜 {max(rest):.2f}",
            fontsize=11, color="#5A6570", va="center", ha="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0, 0.83, 1))
    OUT13.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT13, facecolor="white")
    plt.close(fig)

    # ---- Task 2: composition of the gold standard ----
    counts = {c: sum(1 for r in rows if c in r["gold"]) for c in CATEGORIES}
    order2 = sorted(CATEGORIES, key=lambda c: counts[c])
    shares = [counts[c] / n * 100 for c in order2]
    los, his = zip(*[normal_ci(counts[c], n) for c in order2])
    err = [[s - lo * 100 for s, lo in zip(shares, los)],
           [hi * 100 - s for s, hi in zip(shares, his)]]
    colors2 = [ACCENT if c == "焦り・競争" else (FAINT if c == "情報共有" else GREY)
               for c in order2]

    fig, ax = plt.subplots(figsize=(8.6, 5.1), dpi=200)
    ax.barh(range(len(order2)), shares, color=colors2, height=0.64,
            xerr=err, error_kw={"ecolor": "#5A6570", "elinewidth": 1.2, "capsize": 4})
    for i, (c, s) in enumerate(zip(order2, shares)):
        ax.text(his[i] * 100 + 1.0, i, f"{s:.1f}%", va="center", fontsize=11.5,
                fontweight="bold" if c == "焦り・競争" else "normal",
                color="#1F5FA9" if c == "焦り・競争" else "#333333")
    labels = [f"{c} ※" if c == "情報共有" else c for c in order2]
    ax.set_yticks(range(len(order2)))
    ax.set_yticklabels(labels, fontsize=12)
    i_ase = order2.index("焦り・競争")
    ax.plot([3.0, 3.0], [i_ase - 0.34, i_ase + 0.34],
            color="#C0392B", linewidth=2.2, solid_capstyle="butt", zorder=5)
    ax.text(3.9, i_ase - 0.52, "↑ 分類器の判定：3.0%",
            fontsize=10.5, color="#C0392B", va="center")
    ax.set_xlim(0, 42)
    ax.set_xlabel("構成比（％、エラーバーは95%信頼区間）", fontsize=12, labelpad=8)
    ax.set_title(f"手作業ラベルによる実際の構成比\n（広告を除いた一般ユーザーの投稿 {n}件）",
                 fontsize=13, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0.075, 1, 1))
    fig.text(0.012, 0.028,
             "※ 情報共有は広告除去の段階で66.9%が除かれているため、この比率は解釈しない",
             fontsize=10, color="#5A6570")
    fig.savefig(OUT14, facecolor="white")
    plt.close(fig)

    print("一致度（ページ13）")
    for c in reversed(order):
        print(f"   {c:<7} {agreement[c]:.3f}")
    print()
    print("構成比（ページ14）")
    for c in reversed(order2):
        lo, hi = normal_ci(counts[c], n)
        print(f"   {c:<7} {counts[c]:>3}件 {counts[c]/n*100:>5.1f}%  CI {lo*100:.1f}–{hi*100:.1f}%")
    print()
    ase = hybrid_counts["焦り・競争"] / hybrid_total * 100
    print(f"焦り・競争 分類器判定: {hybrid_counts['焦り・競争']:,}/{hybrid_total:,} = {ase:.2f}%"
          f"  -> ページ14の「3.0%」{'は妥当' if abs(ase-3.0)<0.06 else 'と要確認'}")
    for p in (OUT13, OUT14):
        print(f"{p}")


if __name__ == "__main__":
    main()
