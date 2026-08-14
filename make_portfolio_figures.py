#!/usr/bin/env python3
"""Render the README portfolio figures from the preserved analysis outputs.

The figures are derived from ``data/output`` rather than from hard-coded
report values.  Every derived quantity is checked against the published
baseline before anything is drawn, so a silent drift between the documents
and the figures fails loudly instead of shipping a wrong picture.

This module only reads existing outputs.  It never rebuilds the corpus and
never reruns the classifier.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

DPI = 160

INK = "#1B1B1B"
MUTED = "#6E6E68"
RULE = "#D9D9D3"
CANVAS = "#FFFFFF"
PANEL = "#F6F5F1"
ACCENT = "#1F6F5C"
ACCENT_SOFT = "#A8CCC1"
LOCK = "#B4532A"
GREYS = ("#C6C6C0", "#B0B0A9", "#9B9B94")

EXCHANGE_CATEGORY = "交換・取引"

# Published baseline.  Sources: docs/hybrid_rebuild.md, docs/baseline_evaluation.md
# and the repository README.  The renderer refuses to draw if the data no
# longer reproduces these values.
EXPECTED = {
    "source_rows": 136288,
    "old_rows": 109037,
    "final_rows": 114518,
    "hybrid_rows": 110918,
    "keyword_excluded": 19105,
    "relaxation_locked": 257,
    "additional_ad_excluded": 5874,
    "final_only_locked": 134,
    "restored_vs_old": 2015,
    "dropped_vs_old": 134,
    "gold_rows": 192,
    "exchange_posts": 24316,
    "exchange_accounts": 10677,
    "single_post_accounts": 7198,
    "top1_posts": 3619,
    "top10_posts": 11082,
    "template_posts": 12411,
}


@dataclass(frozen=True)
class Metrics:
    values: dict[str, int]
    buckets: list[tuple[str, int]]
    lorenz: list[tuple[float, float]]

    def __getitem__(self, key: str) -> int:
        return self.values[key]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_japanese_font() -> str:
    available = {entry.name for entry in font_manager.fontManager.ttflist}
    for family in ("Hiragino Sans", "Hiragino Maru Gothic Pro", "Arial Unicode MS"):
        if family in available:
            plt.rcParams.update({"font.family": family, "font.size": 12})
            return family
    raise SystemExit(
        "No Japanese-capable font found. Install or enable Hiragino Sans, "
        "Hiragino Maru Gothic Pro, or Arial Unicode MS."
    )


def count_rows(path: Path) -> int:
    csv.field_size_limit(1 << 30)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def top_fraction_count(account_count: int, fraction: float) -> int:
    """Whole accounts not exceeding the requested population share."""
    return max(1, math.floor(account_count * fraction))


def collect_metrics(root: Path) -> Metrics:
    output = root / "data" / "output"
    summary = json.loads(
        (output / "ad_filter_summary_202511_202604.json").read_text(encoding="utf-8")
    )

    accounts = list(
        csv.DictReader(
            (output / "exchange_accounts.csv").open(encoding="utf-8-sig", newline="")
        )
    )
    posts = sorted((int(row["posts"]) for row in accounts), reverse=True)
    account_count = len(posts)
    exchange_posts = sum(posts)

    locks = Counter(
        row["reason"]
        for row in csv.DictReader(
            (root / "baselines" / "hybrid_final_exclusions.csv").open(
                encoding="utf-8-sig", newline=""
            )
        )
    )

    old_rows = count_rows(output / "2511-2604.csv")
    hybrid_rows = count_rows(output / "2511-2604_hybrid.csv")
    final_rows = count_rows(output / "2511-2604_final.csv")

    relaxation_locked = locks["RELAXED_KEYWORD_STILL_EXCLUDED"]
    final_only_locked = locks["FINAL_ONLY_EXCLUSION"]

    # The hybrid corpus differs from the previous result in both directions:
    # relaxed keyword rules restore posts, while the final-only ID lock removes
    # a smaller set.  Both sides are recovered from the row counts and the lock
    # file rather than restated from the report.
    restored = hybrid_rows - old_rows + final_only_locked

    # The previous run deleted `keyword_deleted` posts with the original rules.
    # Relaxing those rules re-admits `restored` posts and leaves
    # `relaxation_locked` still excluded, so the remainder is the count the
    # hybrid rebuild attributes to unchanged keyword rules.
    keyword_excluded = summary["keyword_deleted"] - restored - relaxation_locked

    values = {
        "source_rows": sum(item["rows"] for item in summary["source_files"]),
        "old_rows": old_rows,
        "final_rows": final_rows,
        "hybrid_rows": hybrid_rows,
        "keyword_excluded": keyword_excluded,
        "relaxation_locked": relaxation_locked,
        "additional_ad_excluded": summary["additional_ad_deleted"],
        "final_only_locked": final_only_locked,
        "restored_vs_old": restored,
        "dropped_vs_old": final_only_locked,
        "gold_rows": count_rows(output / "gold_standard_192.csv"),
        "exchange_posts": exchange_posts,
        "exchange_accounts": account_count,
        "single_post_accounts": sum(1 for value in posts if value == 1),
        "top1_posts": sum(posts[: top_fraction_count(account_count, 0.01)]),
        "top10_posts": sum(posts[: top_fraction_count(account_count, 0.10)]),
        "template_posts": sum(int(row["template_posts"]) for row in accounts),
    }

    selection = (
        values["keyword_excluded"]
        + values["relaxation_locked"]
        + values["additional_ad_excluded"]
        + values["final_only_locked"]
        + values["hybrid_rows"]
    )
    if selection != values["source_rows"]:
        raise SystemExit(
            f"Selection segments sum to {selection:,}, "
            f"not the {values['source_rows']:,} source posts."
        )

    mismatches = [
        f"  {key}: data={values[key]:,} baseline={expected:,}"
        for key, expected in EXPECTED.items()
        if values[key] != expected
    ]
    if mismatches:
        raise SystemExit(
            "Derived metrics no longer match the published baseline:\n"
            + "\n".join(mismatches)
        )

    bucket_counts: Counter[str] = Counter()
    for value in posts:
        if value == 1:
            bucket_counts["1"] += 1
        elif value == 2:
            bucket_counts["2"] += 1
        elif value <= 5:
            bucket_counts["3-5"] += 1
        elif value <= 10:
            bucket_counts["6-10"] += 1
        else:
            bucket_counts["11+"] += 1
    buckets = [(label, bucket_counts[label]) for label in ("1", "2", "3-5", "6-10", "11+")]

    lorenz: list[tuple[float, float]] = [(0.0, 0.0)]
    running = 0
    step = max(1, account_count // 400)
    for index, value in enumerate(posts, start=1):
        running += value
        if index % step == 0 or index == account_count:
            lorenz.append((index / account_count, running / exchange_posts))

    return Metrics(values=values, buckets=buckets, lorenz=lorenz)


def new_figure(width: float, height: float) -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=(width, height), dpi=DPI)
    fig.patch.set_facecolor(CANVAS)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def title_block(ax: plt.Axes, title: str, subtitle: str) -> None:
    ax.text(4, 92, title, fontsize=17, fontweight="bold", color=INK, va="top")
    ax.text(4, 84.5, subtitle, fontsize=11.5, color=MUTED, va="top")
    ax.plot([4, 96], [79.5, 79.5], color=RULE, lw=1)


def footnote(ax: plt.Axes, text: str) -> None:
    ax.text(4, 7.0, text, fontsize=9.5, color=MUTED, va="center")


def node(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    value: str,
    label: str,
    *,
    emphasis: bool = False,
) -> None:
    face = ACCENT if emphasis else PANEL
    edge = ACCENT if emphasis else RULE
    text_color = "#FFFFFF" if emphasis else INK
    label_color = "#D9EAE4" if emphasis else MUTED
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=1.4",
            facecolor=face,
            edgecolor=edge,
            linewidth=1.2,
        )
    )
    ax.text(
        x + width / 2,
        y + height * 0.60,
        value,
        fontsize=16,
        fontweight="bold",
        color=text_color,
        ha="center",
        va="center",
    )
    ax.text(
        x + width / 2,
        y + height * 0.26,
        label,
        fontsize=10,
        color=label_color,
        ha="center",
        va="center",
    )


def arrow(ax: plt.Axes, x1: float, x2: float, y: float, label: str = "") -> None:
    ax.annotate(
        "",
        xy=(x2, y),
        xytext=(x1, y),
        arrowprops={"arrowstyle": "-|>", "color": MUTED, "linewidth": 1.3},
    )
    if label:
        ax.text(
            (x1 + x2) / 2,
            y + 3.4,
            label,
            fontsize=9,
            color=MUTED,
            ha="center",
            va="bottom",
        )


def render_pipeline(metrics: Metrics, path: Path) -> None:
    fig, ax = new_figure(13.5, 3.7)
    title_block(
        ax,
        "Analysis pipeline",
        "Monthly X exports through advertising removal, rule-based classification, "
        "and exchange-account aggregation.",
    )

    stages = [
        (f"{metrics['source_rows']:,}", "raw posts", False),
        (f"{metrics['hybrid_rows']:,}", "hybrid corpus", True),
        (f"{metrics['exchange_posts']:,}", f"{EXCHANGE_CATEGORY} posts", False),
        (f"{metrics['exchange_accounts']:,}", "unique user IDs", False),
    ]
    width, height, gap = 18.0, 24.0, 7.0
    y = 42.0
    x = 4.0
    labels = ["advertising\nremoval", "rule-based\nclassification", "aggregate by\nuser ID"]
    for index, (value, label, emphasis) in enumerate(stages):
        node(ax, x, y, width, height, value, label, emphasis=emphasis)
        if index < len(stages) - 1:
            arrow(ax, x + width + 1.2, x + width + gap - 1.2, y + height / 2, labels[index])
        x += width + gap

    branch_x = 50.5
    ax.plot([branch_x, branch_x], [54.0, 26.0], color=RULE, lw=1.1)
    ax.plot([branch_x, branch_x + 4.0], [26.0, 26.0], color=RULE, lw=1.1)
    ax.text(
        branch_x + 5.5,
        26.0,
        f"classifier evaluated against {metrics['gold_rows']} human-labelled posts "
        f"(Gold {metrics['gold_rows']})",
        fontsize=10.5,
        color=MUTED,
        va="center",
    )

    footnote(
        ax,
        "User IDs are export account identifiers. They do not establish unique people "
        "and do not separate automated accounts.",
    )
    fig.savefig(path, dpi=DPI, facecolor=CANVAS)
    plt.close(fig)


def render_filter_audit(metrics: Metrics, path: Path) -> None:
    fig, ax = new_figure(13.5, 5.6)
    title_block(
        ax,
        "Advertising filter audit and hybrid rebuild",
        "The original filter was not reproducible. Its decisions were re-derived, "
        "and the 391 whose source code is missing were locked by post ID.",
    )

    segments = [
        ("keyword_excluded", "existing keyword rules", GREYS[0], False),
        ("relaxation_locked", "relaxation candidates (ID lock)", LOCK, True),
        ("additional_ad_excluded", "additional-advertising rules", GREYS[2], False),
        ("final_only_locked", "final-only decisions (ID lock)", LOCK, True),
        ("hybrid_rows", "retained hybrid corpus", ACCENT, False),
    ]
    total = metrics["source_rows"]
    bar_x, bar_w, bar_y, bar_h = 4.0, 92.0, 55.0, 9.0
    cursor = bar_x
    for key, _, color, _ in segments:
        span = bar_w * metrics[key] / total
        ax.add_patch(
            FancyBboxPatch(
                (cursor, bar_y),
                span,
                bar_h,
                boxstyle="square,pad=0",
                facecolor=color,
                edgecolor=CANVAS,
                linewidth=0.8,
            )
        )
        cursor += span

    ax.text(
        bar_x,
        bar_y + bar_h + 3.0,
        f"{total:,} source posts",
        fontsize=11,
        color=INK,
        fontweight="bold",
        va="bottom",
    )
    ax.text(
        bar_x + bar_w,
        bar_y + bar_h + 3.0,
        f"{metrics['hybrid_rows']:,} retained ({metrics['hybrid_rows'] / total * 100:.1f}%)",
        fontsize=11,
        color=ACCENT,
        fontweight="bold",
        ha="right",
        va="bottom",
    )

    legend_y = 44.0
    for key, label, color, is_lock in segments:
        ax.add_patch(
            FancyBboxPatch(
                (bar_x, legend_y - 1.0),
                1.6,
                2.4,
                boxstyle="square,pad=0",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(
            bar_x + 3.0,
            legend_y + 0.2,
            f"{metrics[key]:,}",
            fontsize=10.5,
            fontweight="bold",
            color=LOCK if is_lock else INK,
            va="center",
        )
        ax.text(bar_x + 13.0, legend_y + 0.2, label, fontsize=10.5, color=MUTED, va="center")
        legend_y -= 6.2

    panel_x = 52.0
    ax.add_patch(
        FancyBboxPatch(
            (panel_x, 12.0),
            44.0,
            32.0,
            boxstyle="round,pad=0,rounding_size=1.4",
            facecolor=PANEL,
            edgecolor=RULE,
            linewidth=1.0,
        )
    )
    ax.text(
        panel_x + 3.0,
        40.0,
        "Correction against the previous result",
        fontsize=11,
        fontweight="bold",
        color=INK,
        va="center",
    )
    steps = [
        (f"{metrics['old_rows']:,}", "previous filter result", MUTED),
        (f"+{metrics['restored_vs_old']:,}", "over-filtered posts restored", ACCENT),
        (f"-{metrics['dropped_vs_old']:,}", "newly excluded by the ID lock", LOCK),
        (f"{metrics['hybrid_rows']:,}", "hybrid corpus", INK),
    ]
    step_y = 33.0
    for index, (value, label, color) in enumerate(steps):
        if index == len(steps) - 1:
            ax.plot(
                [panel_x + 3.0, panel_x + 41.0],
                [step_y + 3.0, step_y + 3.0],
                color=RULE,
                lw=1,
            )
        ax.text(
            panel_x + 14.0,
            step_y,
            value,
            fontsize=12,
            fontweight="bold",
            color=color,
            ha="right",
            va="center",
        )
        ax.text(panel_x + 16.0, step_y, label, fontsize=10, color=MUTED, va="center")
        step_y -= 6.0

    footnote(
        ax,
        "The restored posts were disproportionately ones the classifier labels "
        "情報共有 (information sharing), which the over-broad keywords had removed.",
    )
    fig.savefig(path, dpi=DPI, facecolor=CANVAS)
    plt.close(fig)


def render_exchange_concentration(metrics: Metrics, path: Path) -> None:
    fig = plt.figure(figsize=(13.5, 5.4), dpi=DPI)
    fig.patch.set_facecolor(CANVAS)
    head = fig.add_axes((0, 0, 1, 1))
    head.set_xlim(0, 100)
    head.set_ylim(0, 100)
    head.axis("off")
    title_block(
        head,
        "Exchange activity is spread across many one-off accounts",
        f"{metrics['exchange_posts']:,} {EXCHANGE_CATEGORY} posts from "
        f"{metrics['exchange_accounts']:,} unique user IDs.",
    )
    footnote(
        head,
        "User IDs are ranked by post count; ties are ordered arbitrarily, which does "
        "not change the cumulative shares.",
    )

    left = fig.add_axes((0.055, 0.20, 0.36, 0.50))
    labels = [label for label, _ in metrics.buckets]
    counts = [count for _, count in metrics.buckets]
    total_accounts = metrics["exchange_accounts"]
    colors = [ACCENT] + [ACCENT_SOFT] * (len(counts) - 1)
    bars = left.bar(labels, counts, color=colors, width=0.68, zorder=3)
    for rect, count in zip(bars, counts, strict=True):
        left.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + total_accounts * 0.02,
            f"{count / total_accounts * 100:.1f}%",
            ha="center",
            fontsize=10,
            color=INK,
            fontweight="bold",
        )
    left.set_ylim(0, total_accounts * 0.82)
    left.set_xlabel("posts per user ID", fontsize=10.5, color=MUTED, labelpad=7)
    left.set_ylabel("user IDs", fontsize=10.5, color=MUTED, labelpad=7)
    left.tick_params(labelsize=10, colors=MUTED, length=0)
    left.grid(axis="y", color=RULE, lw=0.8, zorder=0)
    left.set_axisbelow(True)
    for side in ("top", "right", "left"):
        left.spines[side].set_visible(False)
    left.spines["bottom"].set_color(RULE)
    left.set_title(
        f"{metrics['single_post_accounts'] / total_accounts * 100:.1f}% posted exactly once",
        fontsize=11,
        color=INK,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    right = fig.add_axes((0.575, 0.20, 0.375, 0.50))
    xs = [point[0] * 100 for point in metrics.lorenz]
    ys = [point[1] * 100 for point in metrics.lorenz]
    right.plot([0, 100], [0, 100], color=RULE, lw=1.2, ls=(0, (4, 3)), zorder=2)
    right.plot(xs, ys, color=ACCENT, lw=2.2, zorder=4)
    right.fill_between(xs, ys, color=ACCENT, alpha=0.10, zorder=1)

    callouts = ((1, "top1_posts", (26.0, 10.0)), (10, "top10_posts", (44.0, 28.0)))
    for fraction, key, text_xy in callouts:
        share = metrics[key] / metrics["exchange_posts"] * 100
        right.plot([fraction, fraction], [0, share], color=MUTED, lw=1, ls=":", zorder=3)
        right.plot([fraction], [share], "o", color=ACCENT, markersize=6, zorder=5)
        right.annotate(
            f"top {fraction}% of user IDs\n{metrics[key]:,} posts ({share:.1f}%)",
            xy=(fraction, share),
            xytext=text_xy,
            fontsize=9.5,
            color=INK,
            zorder=6,
            arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.9},
        )

    right.set_xlim(0, 100)
    right.set_ylim(0, 100)
    right.set_xlabel("user IDs, ranked by post count (%)", fontsize=10.5, color=MUTED, labelpad=7)
    right.set_ylabel("cumulative share of posts (%)", fontsize=10.5, color=MUTED, labelpad=7)
    right.tick_params(labelsize=10, colors=MUTED, length=0)
    right.grid(color=RULE, lw=0.8, zorder=0)
    right.set_axisbelow(True)
    for side in ("top", "right"):
        right.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        right.spines[side].set_color(RULE)
    right.set_title(
        "Concentration is real but moderate",
        fontsize=11,
        color=INK,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    fig.savefig(path, dpi=DPI, facecolor=CANVAS)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir or root / "assets" / "portfolio"
    output_dir.mkdir(parents=True, exist_ok=True)

    font_family = select_japanese_font()
    metrics = collect_metrics(root)

    renderers = (
        ("01_pipeline.png", render_pipeline),
        ("02_filter_audit.png", render_filter_audit),
        ("03_exchange_concentration.png", render_exchange_concentration),
    )
    manifest: list[dict[str, object]] = []
    for name, renderer in renderers:
        target = output_dir / name
        renderer(metrics, target)
        manifest.append(
            {
                "file": name,
                "sha256": sha256(target),
                "bytes": target.stat().st_size,
            }
        )
        print(f"wrote {target.relative_to(root)}")

    (output_dir / "figure_metrics.json").write_text(
        json.dumps(
            {
                "font_family": font_family,
                "dpi": DPI,
                "metrics": metrics.values,
                "post_count_buckets": dict(metrics.buckets),
                "figures": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {(output_dir / 'figure_metrics.json').relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
