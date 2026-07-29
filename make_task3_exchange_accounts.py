#!/usr/bin/env python3
"""Task 3 — page 15 data: 交換・取引 aggregated per account.

Corpus: data/output/sentiment_classified_hybrid.csv (slide_plan 2-0, SHA verified)
Account key: ユーザーID (slide_plan 2-4 — the only key stable per person)

Outputs:
  data/output/exchange_accounts.csv
  data/output/slides/p15_new_accounts.png
It also re-checks every figure quoted in slide_plan 2-4.
"""

from __future__ import annotations

import csv
import hashlib
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

csv.field_size_limit(10**9)

SOURCE = Path("data/output/sentiment_classified_hybrid.csv")
OUT_CSV = Path("data/output/exchange_accounts.csv")
OUT_PNG = Path("data/output/slides/p15_new_accounts.png")

CATEGORY = "交換・取引"
ACCOUNT_KEY = "ユーザーID"

# slide_plan 2-4 wording: 【交換】【譲】【求】 / 〈譲〉〈求〉 / 譲）求：
TEMPLATE_RE = re.compile(
    r"【\s*(?:交換|譲|求)\s*】|[〈《\[［]\s*(?:譲|求)\s*[〉》\]］]|(?:譲|求)\s*[)）：:]"
)

for name in ("Hiragino Sans", "Hiragino Maru Gothic Pro", "Arial Unicode MS"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False


def main() -> None:
    posts = defaultdict(list)
    total = 0
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["sentiment_category"] != CATEGORY:
                continue
            total += 1
            posts[row[ACCOUNT_KEY].strip()].append(row)

    accounts = []
    for uid, rows in posts.items():
        rows.sort(key=lambda r: r["投稿時間"])
        texts = [" ".join(r["内容"].split()) for r in rows]
        first, last = rows[0]["投稿時間"][:10], rows[-1]["投稿時間"][:10]
        span = (
            (int(last[:4]) * 12 + int(last[5:7])) - (int(first[:4]) * 12 + int(first[5:7]))
        )
        accounts.append(
            {
                "user_id": uid,
                "account_id": rows[-1]["アカウントID"],
                "display_name": rows[-1]["名前"],
                "posts": len(rows),
                "first_post_date": first,
                "last_post_date": last,
                "active_months": span + 1,
                "first_post_month": first[:7],
                "unique_texts": len({hashlib.sha1(t.encode()).hexdigest() for t in texts}),
                "template_posts": sum(1 for t in texts if TEMPLATE_RE.search(t)),
                "repost_posts": sum(1 for t in texts if t.lstrip().lower().startswith("rt @")),
            }
        )
    accounts.sort(key=lambda a: (-a["posts"], a["first_post_date"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(accounts[0]))
        writer.writeheader()
        writer.writerows(accounts)

    counts = [a["posts"] for a in accounts]
    n_acc = len(accounts)
    template_total = sum(a["template_posts"] for a in accounts)
    singles = sum(1 for c in counts if c == 1)
    top30 = sum(counts[:30])
    k1 = max(1, round(n_acc * 0.01))
    k10 = max(1, round(n_acc * 0.10))

    checks = [
        ("投稿数", total, 24316),
        ("アカウント数", n_acc, 10677),
        ("平均投稿数", round(total / n_acc, 2), 2.28),
        ("中央値", statistics.median(counts), 1),
        ("1件のみのアカウント", singles, 7198),
        ("1件のみの割合(%)", round(singles / n_acc * 100, 1), 67.4),
        ("上位30の合計", top30, 1796),
        ("上位30シェア(%)", round(top30 / total * 100, 1), 7.4),
        ("上位1%シェア(%)", round(sum(counts[:k1]) / total * 100, 1), 14.9),
        ("上位10%シェア(%)", round(sum(counts[:k10]) / total * 100, 1), 45.6),
        ("定型書式件数", template_total, 12181),
        ("定型書式割合(%)", round(template_total / total * 100, 1), 50.1),
    ]
    print(f"{'項目':<22}{'実測':>10}{'仕様書2-4':>12}  判定")
    for label, got, want in checks:
        ok = "一致" if abs(float(got) - float(want)) < 0.06 else "★不一致"
        print(f"{label:<22}{got:>10}{want:>12}  {ok}")

    new_by_month = Counter(a["first_post_month"] for a in accounts)
    months = sorted(new_by_month)
    values = [new_by_month[m] for m in months]

    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
    bars = ax.bar(range(len(months)), values, color="#2E6FBE", width=0.62)
    for i, v in enumerate(values):
        ax.text(i, v + max(values) * 0.02, f"{v:,}", ha="center", va="bottom", fontsize=11)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([m.replace("-", "/") for m in months], fontsize=11)
    ax.set_ylabel("新規アカウント数", fontsize=12)
    ax.set_title(
        f"「交換・取引」に初めて投稿したアカウント数（月別・計 {n_acc:,}）",
        fontsize=13, pad=12,
    )
    ax.set_ylim(0, max(values) * 1.16)
    # データ切断注記: 収集は 2026-04-30 で終わっており、以降は観測されていない。
    ax.axvspan(len(months) - 1.5, len(months) - 0.5, color="#C0392B", alpha=0.06)
    ax.text(len(months) - 1, max(values) * 1.10, "データはここで終了",
            ha="center", fontsize=10.5, color="#C0392B")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0.085, 1, 1))
    fig.text(0.012, 0.028,
             "※ 収集期間は2026年4月30日まで。4月が最大なのは観測の終端であり、"
             "その後に減少したかどうかは本データからは判断できない",
             fontsize=10, color="#5A6570")
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, facecolor="white")
    plt.close(fig)

    print()
    print("月別 新規交換アカウント数")
    for m, v in zip(months, values):
        print(f"  {m}  {v:>6,}  ({v / n_acc * 100:>4.1f}%)")
    print(f"\n{OUT_CSV} / {OUT_PNG}")


if __name__ == "__main__":
    main()
