#!/usr/bin/env python3
"""Regenerate page 13-16 PNG candidates from the locked slide definitions.

Outputs are written only to an explicit directory outside the repository or
to a newly created system temporary directory.  This prevents validation runs
from overwriting the checked final PNG files under ``data/output/slides``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
import textwrap
import statistics
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

from evaluate_v2_hybrid_192 import (
    CATEGORIES,
    MIN_PRIMARY_SCORE,
    calculate_evaluation_metrics,
    load as load_evaluation_rows,
)
from normalize_gold_standard_192 import (
    DEFAULT_OUTPUT as NORMALIZED_GOLD_STANDARD,
    validate_normalized_gold,
)
from slide_number_definitions import (
    EXCHANGE_ACCOUNT_KEY,
    EXCHANGE_CATEGORY,
    WALD_95_Z,
    has_exchange_ratio,
    has_formal_greeting,
    has_honorific_consideration,
    is_exchange_template,
    is_platform_reply,
    top_fraction_account_count,
    wald_interval,
)

csv.field_size_limit(10**9)

PROJECT_ROOT = Path(__file__).resolve().parent
GOLD_STANDARD = NORMALIZED_GOLD_STANDARD
CLASSIFIED = PROJECT_ROOT / "data/output/sentiment_classified_hybrid.csv"
HYBRID_CORPUS = PROJECT_ROOT / "data/output/2511-2604_hybrid.csv"
SOURCE_GOLD = PROJECT_ROOT / "data/output/gold_standard_192.csv"
NEGOTIATION_SAMPLE_PATHS = (
    PROJECT_ROOT
    / (
        "outputs/negotiation-unclassified-20260728/"
        "negotiation_expressions_not_exchange_random50.csv"
    ),
    PROJECT_ROOT
    / "data/output/random_sample_50_negotiation_not_exchange_202511_202604.csv",
)

FIGSIZE = (12, 6.75)
DPI = 160
MIN_WIDTH = 1720

INK = "#182431"
SUBTLE = "#5E6B78"
GRID = "#D8DEE5"
BLUE = "#2467A6"
BLUE_LIGHT = "#A9C8E6"
GOLD_ACCENT = "#C68B2C"
ORANGE = "#C55A2D"
PAPER = "#FFFFFF"
CARD = "#F5F7F9"
NEUTRAL_BAR = "#D9DEE4"

P16_QUOTE_EXCERPTS = (
    (
        "ベイマックス＞ズートピア＞キティ赤＞キティピンクの順番で"
        "求めておりますが、交換可能なものはございますか？"
    ),
    (
        "2:3の交換は可能でしょうか。差額が気になる場合フリマサイトでの"
        "レート計算になりますが差額分お支払い可能です"
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def select_japanese_font() -> tuple[str, str]:
    available = {
        entry.name: entry.fname for entry in font_manager.fontManager.ttflist
    }
    for family in (
        "Hiragino Sans",
        "Hiragino Maru Gothic Pro",
        "Arial Unicode MS",
    ):
        if family in available:
            plt.rcParams.update(
                {
                    "font.family": family,
                    "axes.unicode_minus": False,
                    "font.size": 13,
                    "text.color": INK,
                    "axes.labelcolor": INK,
                    "axes.edgecolor": SUBTLE,
                    "xtick.color": SUBTLE,
                    "ytick.color": INK,
                }
            )
            font_path = font_manager.findfont(
                font_manager.FontProperties(family=family)
            )
            return family, font_path
    raise RuntimeError(
        "No Japanese-capable font found. Install or enable Hiragino Sans, "
        "Hiragino Maru Gothic Pro, or Arial Unicode MS."
    )


def guard_output_directory(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved == project or project in resolved.parents:
        raise ValueError(
            "Refusing to write slide candidates inside the repository. "
            "Pass a temporary directory with --output-dir."
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def save_figure(fig: plt.Figure, path: Path) -> dict[str, object]:
    """Save a PNG and fail on missing glyphs or text outside the canvas."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        width, height = fig.canvas.get_width_height()
        overflow: list[str] = []
        for text_artist in fig.findobj(plt.Text):
            if not text_artist.get_visible() or not text_artist.get_text():
                continue
            bounds = text_artist.get_window_extent(renderer=renderer)
            if (
                bounds.x0 < -1
                or bounds.y0 < -1
                or bounds.x1 > width + 1
                or bounds.y1 > height + 1
            ):
                overflow.append(text_artist.get_text().replace("\n", " / "))
        if overflow:
            raise RuntimeError(
                "Text extends outside the PNG canvas: " + "; ".join(overflow)
            )
        fig.savefig(
            path,
            dpi=DPI,
            facecolor=PAPER,
            metadata={"Software": "Bonbon slide asset generator"},
        )
        missing_glyphs = [
            str(item.message)
            for item in caught
            if "Glyph" in str(item.message)
            and "missing from font" in str(item.message)
        ]
        if missing_glyphs:
            path.unlink(missing_ok=True)
            raise RuntimeError(
                "Japanese glyph validation failed: "
                + "; ".join(missing_glyphs)
            )
    plt.close(fig)
    return {
        "file": path.name,
        "width_px": width,
        "height_px": height,
        "sha256": sha256(path),
        "text_overflow_count": 0,
        "missing_glyph_warning_count": 0,
    }


def page13_metrics(
    gold_path: Path,
    classified_path: Path,
) -> dict[str, object]:
    rows, gold_count = load_evaluation_rows(gold_path, classified_path)
    evaluation = calculate_evaluation_metrics(rows)
    if (gold_count, len(rows)) != (192, 192):
        raise AssertionError(
            f"Expected gold/join counts 192/192, got {gold_count}/{len(rows)}"
        )

    lenient_micro = evaluation["lenient"]["micro"]
    multi_micro = evaluation["multi"]["micro"]
    overall = [
        {
            "key": "lenient_micro_f1",
            "label": "緩和基準（micro）",
            "definition": "単一予測が人手ラベル集合に含まれれば一致",
            "scope": "全カテゴリのTP・FP・FNを合算",
            "tp": lenient_micro["tp"],
            "fp": lenient_micro["fp"],
            "fn": lenient_micro["fn"],
            "formula": "2TP / (2TP + FP + FN)",
            "value": lenient_micro["f1"],
            "display": f"{lenient_micro['f1']:.3f}",
        },
        {
            "key": "multi_micro_f1",
            "label": "多ラベル基準（micro）",
            "definition": (
                f"score >= {MIN_PRIMARY_SCORE:g} "
                "の全カテゴリを予測集合とする"
            ),
            "scope": "全カテゴリのTP・FP・FNを合算",
            "tp": multi_micro["tp"],
            "fp": multi_micro["fp"],
            "fn": multi_micro["fn"],
            "formula": "2TP / (2TP + FP + FN)",
            "value": multi_micro["f1"],
            "display": f"{multi_micro['f1']:.3f}",
        },
    ]
    categories = []
    for category in CATEGORIES:
        item = evaluation["lenient"]["per_category"][category]
        categories.append(
            {
                "category": category,
                "criterion": "lenient",
                "tp": item["tp"],
                "fp": item["fp"],
                "fn": item["fn"],
                "precision": item["precision"],
                "recall": item["recall"],
                "f1": item["f1"],
                "display": f"{item['f1']:.3f}",
            }
        )
    exchange = next(
        item for item in categories if item["category"] == EXCHANGE_CATEGORY
    )
    return {
        "page": 13,
        "sample_size": len(rows),
        "gold_rows": gold_count,
        "classification_join": len(rows),
        "threshold": MIN_PRIMARY_SCORE,
        "overall_metrics": overall,
        "category_metrics": categories,
        "highlight": {
            "primary_category": EXCHANGE_CATEGORY,
            "primary_display": exchange["display"],
            "secondary_category": "中立",
        },
        "visible_copy": {
            "title": "カテゴリによって分類性能に差が見られた",
            "subtitle": (
                f"人手ラベル{len(rows)}件との比較・"
                f"{len(categories)}カテゴリ別F1（緩和基準）"
            ),
            "interpretation": (
                "交換・取引は比較的安定して判定できた一方、"
                "他のカテゴリには改善の余地が残った。"
            ),
            "footnote": (
                "評価指標はF1。全体値は7カテゴリを合算したmicro F1。"
            ),
        },
    }


def render_page13(
    metrics: dict[str, object],
    output_path: Path,
) -> dict[str, object]:
    categories = sorted(
        metrics["category_metrics"],
        key=lambda item: item["f1"],
    )
    labels = [item["category"] for item in categories]
    values = [item["f1"] for item in categories]
    colors = []
    hatches = []
    for item in categories:
        if item["category"] == metrics["highlight"]["primary_category"]:
            colors.append(GOLD_ACCENT)
            hatches.append("///")
        elif item["category"] == metrics["highlight"]["secondary_category"]:
            colors.append(BLUE_LIGHT)
            hatches.append("..")
        else:
            colors.append(NEUTRAL_BAR)
            hatches.append("")

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, layout="constrained")
    grid = fig.add_gridspec(3, 1, height_ratios=[1.0, 4.8, 0.8])
    header_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1])
    note_ax = fig.add_subplot(grid[2])
    header_ax.axis("off")
    note_ax.axis("off")
    header_ax.text(
        0,
        0.96,
        metrics["visible_copy"]["title"],
        ha="left",
        va="top",
        fontsize=24,
        fontweight="bold",
    )
    header_ax.text(
        0,
        0.08,
        metrics["visible_copy"]["subtitle"],
        ha="left",
        va="bottom",
        fontsize=12.5,
        color=SUBTLE,
    )
    for index, item in enumerate(metrics["overall_metrics"]):
        header_ax.text(
            0.72 + index * 0.19,
            0.5,
            f"{item['label']}\nF1 {item['display']}",
            ha="center",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=BLUE if index else INK,
        )
    positions = list(range(len(categories)))
    bars = ax.barh(
        positions,
        values,
        color=colors,
        edgecolor=INK,
        linewidth=1.2,
        height=0.58,
    )
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    for position, value, item in zip(positions, values, categories):
        ax.text(
            max(value + 0.018, 0.018),
            position,
            item["display"],
            va="center",
            fontsize=15,
            fontweight="bold",
            color=INK,
        )
    ax.set_yticks(positions, labels=labels, fontsize=14.5)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("F1（1.000 が完全一致）", fontsize=12.5, labelpad=8)
    ax.grid(axis="x", color=GRID, linewidth=0.9)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=10)
    note_ax.text(
        0,
        0.72,
        metrics["visible_copy"]["interpretation"],
        va="center",
        fontsize=12.5,
        fontweight="bold",
        color=INK,
    )
    note_ax.text(
        0,
        0.18,
        metrics["visible_copy"]["footnote"],
        va="center",
        fontsize=10.5,
        color=SUBTLE,
    )
    return save_figure(fig, output_path)


def page14_metrics(
    evaluation_rows: list[dict],
    classified_rows: list[dict[str, str]],
) -> dict[str, object]:
    sample_size = len(evaluation_rows)
    if sample_size != 192:
        raise AssertionError(f"Expected 192 evaluation rows, got {sample_size}")
    categories = []
    for category in CATEGORIES:
        count = sum(
            category in row["gold"] for row in evaluation_rows
        )
        low, high = wald_interval(count, sample_size, z=WALD_95_Z)
        categories.append(
            {
                "category": category,
                "numerator": count,
                "denominator": sample_size,
                "percent": count / sample_size * 100,
                "percent_display": f"{count / sample_size * 100:.1f}%",
                "ci_low_percent": low * 100,
                "ci_high_percent": high * 100,
                "ci_display": f"{low * 100:.1f}–{high * 100:.1f}%",
            }
        )
    classifier_count = sum(
        row["sentiment_category"] == "焦り・競争"
        for row in classified_rows
    )
    classifier_total = len(classified_rows)
    extended_label_count = sum(
        category["numerator"] for category in categories
    )
    sum_of_category_percentages = sum(
        category["percent"] for category in categories
    )
    urgency = next(
        item for item in categories if item["category"] == "焦り・競争"
    )
    classifier_percent = classifier_count / classifier_total * 100
    return {
        "page": 14,
        "sample_size": sample_size,
        "multi_label": True,
        "extended_label_count": extended_label_count,
        "sum_of_category_percentages": sum_of_category_percentages,
        "confidence_interval": {
            "method": "Wald",
            "confidence_level": 0.95,
            "z": WALD_95_Z,
            "sample_size": sample_size,
            "rounding": "displayed to 1 decimal place",
            "clipped_to_unit_interval": True,
        },
        "categories": categories,
        "classifier_reference": {
            "category": "焦り・競争",
            "numerator": classifier_count,
            "denominator": classifier_total,
            "percent": classifier_percent,
            "display": f"{classifier_percent:.1f}%",
            "definition": "分類器の単一ラベル判定",
        },
        "visible_copy": {
            "title": "人手ラベルから見えたカテゴリ構成",
            "subtitle": (
                f"人手ラベル{sample_size}件・カテゴリ別二値比率・"
                f"Wald 95%信頼区間（z={WALD_95_Z:.2f}）"
            ),
            "callout": (
                "焦り・競争：人手ラベル"
                f"{urgency['percent']:.1f}%／自動分類"
                f"{classifier_percent:.1f}%"
            ),
            "multi_label_note": (
                "1投稿に複数ラベルを付与したため、構成比の合計は"
                f"{sum_of_category_percentages:.1f}%。"
            ),
            "information_bias_note": (
                "「情報共有」は広告除去条件の影響が大きく、"
                "低い実態比率とは断定できない。"
            ),
        },
    }


def render_page14(
    metrics: dict[str, object],
    output_path: Path,
) -> dict[str, object]:
    categories = sorted(
        metrics["categories"],
        key=lambda item: item["percent"],
    )
    labels = [item["category"] for item in categories]
    values = [item["percent"] for item in categories]
    lows = [item["ci_low_percent"] for item in categories]
    highs = [item["ci_high_percent"] for item in categories]
    lower_errors = [value - low for value, low in zip(values, lows)]
    upper_errors = [high - value for value, high in zip(values, highs)]

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, layout="constrained")
    grid = fig.add_gridspec(3, 1, height_ratios=[0.7, 5.0, 0.5])
    header_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1])
    note_ax = fig.add_subplot(grid[2])
    header_ax.axis("off")
    note_ax.axis("off")
    header_ax.text(
        0,
        0.98,
        metrics["visible_copy"]["title"],
        ha="left",
        va="top",
        fontsize=24,
        fontweight="bold",
    )
    header_ax.text(
        0,
        0.02,
        metrics["visible_copy"]["subtitle"],
        ha="left",
        va="bottom",
        fontsize=12.5,
        color=SUBTLE,
    )
    header_ax.text(
        1,
        0.08,
        metrics["visible_copy"]["callout"],
        ha="right",
        va="bottom",
        fontsize=12.5,
        fontweight="bold",
        color=ORANGE,
    )
    y_positions = range(len(categories))
    for index, item in enumerate(categories):
        point_color = ORANGE if item["category"] == "焦り・競争" else BLUE
        if item["category"] == "情報共有":
            point_color = SUBTLE
        ax.errorbar(
            [values[index]],
            [index],
            xerr=[[lower_errors[index]], [upper_errors[index]]],
            fmt="o",
            markersize=10,
            markerfacecolor=PAPER,
            markeredgecolor=point_color,
            markeredgewidth=2.5,
            ecolor=INK,
            elinewidth=1.8,
            capsize=5,
            capthick=1.8,
            zorder=3,
        )
    for index, item in enumerate(categories):
        ax.text(
            item["ci_high_percent"] + 0.9,
            index,
            f"{item['percent_display']}（{item['numerator']}件）"
            f"  [{item['ci_display']}]",
            va="center",
            fontsize=12.5,
            color=INK,
        )

    classifier = metrics["classifier_reference"]
    focus_index = labels.index("焦り・競争")
    ax.scatter(
        [classifier["percent"]],
        [focus_index],
        marker="x",
        s=115,
        linewidth=2.5,
        color=ORANGE,
        zorder=4,
    )
    ax.plot(
        [classifier["percent"], 6.0],
        [focus_index, focus_index - 0.38],
        color=ORANGE,
        linewidth=1.5,
    )
    ax.text(
        6.2,
        focus_index - 0.45,
        f"自動分類 {classifier['display']}",
        fontsize=11,
        color=ORANGE,
        va="center",
    )
    ax.set_yticks(y_positions, labels=labels, fontsize=15)
    ax.set_xlim(0, 47)
    ax.set_xticks(range(0, 46, 5))
    ax.set_xlabel("構成比（%）", fontsize=14, labelpad=10)
    ax.grid(axis="x", color=GRID, linewidth=0.9)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=10)
    note_ax.text(
        0,
        0.7,
        metrics["visible_copy"]["multi_label_note"],
        va="center",
        fontsize=10.8,
        color=SUBTLE,
    )
    note_ax.text(
        0,
        0.2,
        metrics["visible_copy"]["information_bias_note"],
        va="center",
        fontsize=10.8,
        color=ORANGE,
    )
    return save_figure(fig, output_path)


def page15_metrics(
    classified_rows: list[dict[str, str]],
) -> dict[str, object]:
    exchange_rows = [
        row
        for row in classified_rows
        if row["sentiment_category"] == EXCHANGE_CATEGORY
    ]
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in exchange_rows:
        by_account[row[EXCHANGE_ACCOUNT_KEY].strip()].append(row)

    account_counts = sorted(
        (len(rows) for rows in by_account.values()),
        reverse=True,
    )
    account_total = len(by_account)
    post_total = len(exchange_rows)
    top_1_count = top_fraction_account_count(account_total, 0.01)
    top_10_count = top_fraction_account_count(account_total, 0.10)
    top_1_posts = sum(account_counts[:top_1_count])
    top_10_posts = sum(account_counts[:top_10_count])
    single_accounts = sum(count == 1 for count in account_counts)
    template_posts = sum(
        is_exchange_template(row["内容"]) for row in exchange_rows
    )
    first_month_counts = Counter(
        min(row["投稿時間"][:7] for row in rows)
        for rows in by_account.values()
    )
    observation_end_date = max(
        row["投稿時間"][:10] for row in exchange_rows
    )
    monthly = [
        {"month": month, "new_accounts": first_month_counts[month]}
        for month in sorted(first_month_counts)
    ]

    summary = {
        "exchange_posts": post_total,
        "accounts": account_total,
        "mean_posts_per_account": post_total / account_total,
        "median_posts_per_account": statistics.median(account_counts),
        "single_post_accounts": single_accounts,
        "single_post_account_share_percent": (
            single_accounts / account_total * 100
        ),
        "top_30_posts": sum(account_counts[:30]),
        "top_30_share_percent": sum(account_counts[:30])
        / post_total
        * 100,
        "top_1_percent": {
            "method": "floor(account_count * 0.01)",
            "accounts": top_1_count,
            "posts": top_1_posts,
            "denominator_posts": post_total,
            "share_percent": top_1_posts / post_total * 100,
        },
        "top_10_percent": {
            "method": "floor(account_count * 0.10)",
            "accounts": top_10_count,
            "posts": top_10_posts,
            "denominator_posts": post_total,
            "share_percent": top_10_posts / post_total * 100,
        },
        "template": {
            "definition": (
                "slide_number_definitions.is_exchange_template"
            ),
            "posts": template_posts,
            "denominator_posts": post_total,
            "share_percent": template_posts / post_total * 100,
        },
    }
    observation_year = int(observation_end_date[:4])
    observation_month = int(observation_end_date[5:7])
    return {
        "page": 15,
        "account_key": EXCHANGE_ACCOUNT_KEY,
        "exchange_category": EXCHANGE_CATEGORY,
        "summary": summary,
        "monthly_new_accounts": monthly,
        "monthly_total": sum(
            item["new_accounts"] for item in monthly
        ),
        "observation_end_date": observation_end_date,
        "visible_copy": {
            "title": "「交換・取引」カテゴリの投稿構造",
            "connection": (
                "7カテゴリの中で比較的安定していた「交換・取引」を対象に、"
                "投稿とアカウントの構造を確認した。"
            ),
            "interpretation": (
                "投稿は一部の活発なアカウントに集中しつつ、"
                "多数の単発参加アカウントにも広がっていた。"
            ),
            "partial_period_note": (
                f"※{observation_year}年{observation_month}月は収集終了月であり、"
                "その後の増減は判断できない。"
            ),
            "monthly_definition": (
                "月別新規数はユーザーIDごとの最初の交換・取引投稿月。"
            ),
        },
    }


def add_kpi_card(
    ax: plt.Axes,
    left: float,
    width: float,
    title: str,
    value: str,
    detail: str,
    *,
    accent: str,
    hatch: str = "",
) -> None:
    card = FancyBboxPatch(
        (left, 0.08),
        width,
        0.8,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=1.4,
        edgecolor=accent,
        facecolor=CARD,
        hatch=hatch,
        transform=ax.transAxes,
    )
    ax.add_patch(card)
    ax.text(
        left + 0.025,
        0.72,
        title,
        transform=ax.transAxes,
        fontsize=12,
        color=SUBTLE,
        va="top",
    )
    ax.text(
        left + 0.025,
        0.48,
        value,
        transform=ax.transAxes,
        fontsize=22,
        fontweight="bold",
        color=INK,
        va="center",
    )
    ax.text(
        left + 0.025,
        0.2,
        detail,
        transform=ax.transAxes,
        fontsize=10.5,
        color=SUBTLE,
        va="bottom",
    )


def render_page15(
    metrics: dict[str, object],
    output_path: Path,
) -> dict[str, object]:
    summary = metrics["summary"]
    monthly = metrics["monthly_new_accounts"]
    months = [item["month"] for item in monthly]
    values = [item["new_accounts"] for item in monthly]
    top_1 = summary["top_1_percent"]
    single_accounts = summary["single_post_accounts"]
    single_share = summary["single_post_account_share_percent"]
    observation_end_date = metrics["observation_end_date"]

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, layout="constrained")
    grid = fig.add_gridspec(
        4,
        1,
        height_ratios=[0.9, 1.25, 3.4, 0.75],
    )
    header_ax = fig.add_subplot(grid[0])
    cards_ax = fig.add_subplot(grid[1])
    chart_ax = fig.add_subplot(grid[2])
    note_ax = fig.add_subplot(grid[3])
    header_ax.axis("off")
    cards_ax.axis("off")
    note_ax.axis("off")
    header_ax.text(
        0,
        0.96,
        metrics["visible_copy"]["title"],
        ha="left",
        va="top",
        fontsize=24,
        fontweight="bold",
    )
    header_ax.text(
        0,
        0.05,
        metrics["visible_copy"]["connection"],
        ha="left",
        va="bottom",
        fontsize=11.5,
        color=SUBTLE,
    )
    card_width = 0.225
    add_kpi_card(
        cards_ax,
        0.0,
        card_width,
        "交換・取引の投稿",
        f"{summary['exchange_posts']:,}件",
        "分類結果の単一ラベル",
        accent=BLUE,
    )
    add_kpi_card(
        cards_ax,
        0.255,
        card_width,
        "投稿したアカウント",
        f"{summary['accounts']:,}",
        f"{metrics['account_key']}で集計",
        accent=BLUE,
        hatch="..",
    )
    add_kpi_card(
        cards_ax,
        0.51,
        card_width,
        "1回のみ投稿",
        f"{single_share:.1f}%",
        f"{single_accounts:,} / {summary['accounts']:,}アカウント",
        accent=GOLD_ACCENT,
        hatch="///",
    )
    add_kpi_card(
        cards_ax,
        0.765,
        card_width,
        "上位1%の投稿比率",
        f"{top_1['share_percent']:.1f}%",
        f"{top_1['accounts']}アカウント・{top_1['posts']:,}件",
        accent=ORANGE,
        hatch="xx",
    )

    bars = chart_ax.bar(
        range(len(months)),
        values,
        color=BLUE_LIGHT,
        edgecolor=BLUE,
        linewidth=1.5,
        width=0.62,
    )
    bars[-1].set_hatch("///")
    bars[-1].set_facecolor(PAPER)
    for index, value in enumerate(values):
        chart_ax.text(
            index,
            value + max(values) * 0.025,
            f"{value:,}",
            ha="center",
            va="bottom",
            fontsize=13,
            fontweight="bold",
        )
    chart_ax.set_xticks(
        range(len(months)),
        labels=[month.replace("-", "/") for month in months],
        fontsize=13,
    )
    chart_ax.set_ylabel("新規アカウント数", fontsize=13)
    chart_ax.set_title(
        "交換・取引に初めて投稿したアカウント（月別）",
        loc="left",
        fontsize=16,
        pad=12,
    )
    chart_ax.set_ylim(0, max(values) * 1.18)
    chart_ax.grid(axis="y", color=GRID, linewidth=0.9)
    chart_ax.set_axisbelow(True)
    chart_ax.spines[["top", "right"]].set_visible(False)
    chart_ax.plot(
        [len(months) - 1.02, len(months) - 1.44],
        [values[-1] * 1.01, max(values) * 1.07],
        color=ORANGE,
        linewidth=1.5,
    )
    chart_ax.text(
        len(months) - 1.65,
        max(values) * 1.09,
        f"収集終了：{observation_end_date}",
        fontsize=11.5,
        color=ORANGE,
        ha="center",
        va="bottom",
    )
    note_ax.text(
        0,
        0.78,
        metrics["visible_copy"]["interpretation"],
        va="center",
        fontsize=11.5,
        fontweight="bold",
        color=INK,
    )
    note_ax.text(
        0,
        0.24,
        metrics["visible_copy"]["monthly_definition"]
        + metrics["visible_copy"]["partial_period_note"],
        va="center",
        fontsize=10.4,
        color=SUBTLE,
    )
    return save_figure(fig, output_path)


def load_negotiation_sample(
    paths: tuple[Path, ...] = NEGOTIATION_SAMPLE_PATHS,
) -> list[dict[str, str]]:
    """Load and deduplicate the fixed negotiation-expression sample."""
    deduplicated: dict[str, dict[str, str]] = {}
    for path in paths:
        for row_number, row in enumerate(read_dicts(path), start=2):
            post_id = (
                row.get("投稿ID_文字列")
                or row.get("post_id")
                or row.get("投稿ID")
                or ""
            ).strip()
            if not post_id:
                raise AssertionError(f"Missing post ID in {path}:{row_number}")
            enriched = dict(row)
            enriched["_source_path"] = display_path(path)
            enriched["_source_row_number"] = str(row_number)
            deduplicated[post_id] = enriched
    return list(deduplicated.values())


def verified_anonymized_quotes(
    sample_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Return exact source excerpts with account-identifying fields omitted."""
    quotes = []
    for excerpt in P16_QUOTE_EXCERPTS:
        matching_rows = [
            row
            for row in sample_rows
            if excerpt in (row.get("内容") or row.get("clean_text") or "")
        ]
        if not matching_rows:
            quotes.append(
                {
                    "text": "［匿名化した原文例を確認後に挿入］",
                    "verified": False,
                    "source_path": None,
                    "source_row_number": None,
                    "anonymization": (
                        "原文照合ができないため、内容を推測せず"
                        "プレースホルダーを表示"
                    ),
                }
            )
            continue
        row = matching_rows[0]
        quotes.append(
            {
                "text": excerpt,
                "verified": True,
                "source_path": row["_source_path"],
                "source_row_number": int(row["_source_row_number"]),
                "anonymization": (
                    "原文の連続部分をそのまま抜粋し、アカウント名・"
                    "相手メンション・URL・画像リンクを表示対象から除外"
                ),
            }
        )
    return quotes


def page16_metrics(
    page15_data: dict[str, object],
    sample_rows: list[dict[str, str]],
    sample_paths: tuple[Path, ...] = NEGOTIATION_SAMPLE_PATHS,
) -> dict[str, object]:
    """Calculate page 16 full-corpus and fixed-sample evidence."""
    texts = [
        row.get("内容") or row.get("clean_text") or ""
        for row in sample_rows
    ]
    sample_size = len(sample_rows)
    fixed_sample = {
        "posts": sample_size,
        "reply_posts": sum(is_platform_reply(row) for row in sample_rows),
        "formal_greeting_posts": sum(
            has_formal_greeting(text) for text in texts
        ),
        "honorific_consideration_posts": sum(
            has_honorific_consideration(text) for text in texts
        ),
        "exchange_ratio_posts": sum(
            has_exchange_ratio(text) for text in texts
        ),
        "definitions": {
            "reply_posts": "slide_number_definitions.is_platform_reply",
            "formal_greeting_posts": (
                "slide_number_definitions.has_formal_greeting"
            ),
            "honorific_consideration_posts": (
                "slide_number_definitions.has_honorific_consideration"
            ),
            "exchange_ratio_posts": (
                "slide_number_definitions.has_exchange_ratio"
            ),
        },
    }
    template = page15_data["summary"]["template"]
    return {
        "page": 16,
        "template": template,
        "fixed_sample": fixed_sample,
        "displayed_expressions": [
            "譲",
            "求",
            "郵送",
            "手渡し",
            "交換比率",
            "差額精算",
            "ご検討／御検討",
        ],
        "quotes": verified_anonymized_quotes(sample_rows),
        "sample_sources": {
            "paths": [display_path(path) for path in sample_paths],
            "sha256": {
                display_path(path): sha256(path) for path in sample_paths
            },
            "deduplication_key": (
                "投稿ID_文字列（なければpost_idまたは投稿ID）"
            ),
        },
        "visible_copy": {
            "title": "「交換・取引」投稿に見られた定型表現",
            "conclusion": (
                "交換投稿の多くで、条件を簡潔に提示する"
                "共通の表現形式が使われていた。"
            ),
            "scope_limit": (
                "固定標本の分析であり、すべての交換投稿を"
                "代表するものではない。"
            ),
            "anonymization": "アカウント情報は匿名化した。",
            "transition": (
                "次に、これらの結果を他の分析と合わせて検討する。"
            ),
        },
    }


def add_quote_panel(
    ax: plt.Axes,
    quote: dict[str, object],
    index: int,
) -> None:
    """Draw one verified quote or a non-speculative placeholder."""
    panel = FancyBboxPatch(
        (0.03, 0.05),
        0.94,
        0.88,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=GRID,
        facecolor=CARD,
        transform=ax.transAxes,
    )
    ax.add_patch(panel)
    ax.text(
        0.05,
        0.82,
        f"匿名化した原文例 {index}",
        transform=ax.transAxes,
        fontsize=11,
        color=SUBTLE,
        va="top",
    )
    wrapped = "\n".join(textwrap.wrap(str(quote["text"]), width=32))
    ax.text(
        0.05,
        0.52,
        f"「{wrapped}」",
        transform=ax.transAxes,
        fontsize=12.2,
        color=INK,
        va="center",
        linespacing=1.35,
    )


def render_page16(
    metrics: dict[str, object],
    output_path: Path,
) -> dict[str, object]:
    template = metrics["template"]
    sample = metrics["fixed_sample"]
    copy = metrics["visible_copy"]

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, layout="constrained")
    grid = fig.add_gridspec(
        4,
        1,
        height_ratios=[0.72, 2.25, 1.75, 1.0],
    )
    header_ax = fig.add_subplot(grid[0])
    evidence_grid = grid[1].subgridspec(1, 2, width_ratios=[0.9, 1.1])
    main_ax = fig.add_subplot(evidence_grid[0])
    sample_ax = fig.add_subplot(evidence_grid[1])
    quote_grid = grid[2].subgridspec(1, 2, wspace=0.08)
    quote_axes = [
        fig.add_subplot(quote_grid[0]),
        fig.add_subplot(quote_grid[1]),
    ]
    footer_ax = fig.add_subplot(grid[3])
    for ax in (header_ax, main_ax, sample_ax, *quote_axes, footer_ax):
        ax.axis("off")

    header_ax.text(
        0.03,
        0.9,
        copy["title"],
        ha="left",
        va="top",
        fontsize=24,
        fontweight="bold",
    )
    main_ax.text(
        0.03,
        0.95,
        "定型的な交換形式",
        fontsize=13,
        color=SUBTLE,
        va="top",
    )
    main_ax.text(
        0.03,
        0.62,
        f"{template['posts']:,}件",
        fontsize=31,
        fontweight="bold",
        color=BLUE,
        va="center",
    )
    main_ax.text(
        0.03,
        0.34,
        f"交換投稿の {template['share_percent']:.1f}%",
        fontsize=18,
        fontweight="bold",
        color=INK,
        va="center",
    )
    main_ax.text(
        0.03,
        0.08,
        "主な表現："
        + "／".join(metrics["displayed_expressions"]),
        fontsize=11,
        color=SUBTLE,
        va="bottom",
        wrap=True,
    )

    sample_ax.text(
        0.03,
        0.95,
        f"交渉表現を含む固定標本 {sample['posts']}件",
        transform=sample_ax.transAxes,
        fontsize=14,
        fontweight="bold",
        color=INK,
        va="top",
    )
    sample_rows = (
        ("リプライ", sample["reply_posts"]),
        ("定型的な挨拶", sample["formal_greeting_posts"]),
        ("ご検討／御検討", sample["honorific_consideration_posts"]),
        ("交換比率", sample["exchange_ratio_posts"]),
    )
    for index, (label, value) in enumerate(sample_rows):
        y = 0.71 - index * 0.2
        sample_ax.text(
            0.03,
            y,
            label,
            transform=sample_ax.transAxes,
            fontsize=12.5,
            color=SUBTLE,
            va="center",
        )
        sample_ax.text(
            0.92,
            y,
            f"{value}件",
            transform=sample_ax.transAxes,
            fontsize=16,
            fontweight="bold",
            color=INK,
            va="center",
            ha="right",
        )
        sample_ax.plot(
            [0.03, 0.92],
            [y - 0.09, y - 0.09],
            color=GRID,
            linewidth=0.8,
            transform=sample_ax.transAxes,
        )

    for index, (ax, quote) in enumerate(
        zip(quote_axes, metrics["quotes"]),
        start=1,
    ):
        add_quote_panel(ax, quote, index)

    footer_ax.text(
        0.03,
        0.86,
        copy["conclusion"],
        fontsize=12,
        fontweight="bold",
        color=INK,
        va="center",
    )
    footer_ax.text(
        0.03,
        0.53,
        copy["scope_limit"] + " " + copy["anonymization"],
        fontsize=10.4,
        color=SUBTLE,
        va="center",
    )
    footer_ax.text(
        0.03,
        0.17,
        copy["transition"],
        fontsize=11,
        color=BLUE,
        va="center",
    )
    return save_figure(fig, output_path)


def build_assets(
    output_dir: Path,
    gold_path: Path = GOLD_STANDARD,
    classified_path: Path = CLASSIFIED,
    hybrid_corpus_path: Path = HYBRID_CORPUS,
) -> dict[str, object]:
    output_dir = guard_output_directory(output_dir)
    gold_validation = validate_normalized_gold(gold_path)
    gold_path = Path(gold_validation["path"])
    classified_path = classified_path.resolve()
    hybrid_corpus_path = hybrid_corpus_path.resolve()

    classified_rows = read_dicts(classified_path)
    hybrid_rows = read_dicts(hybrid_corpus_path)
    if len(classified_rows) != 110_918:
        raise AssertionError(
            "Expected 110,918 classified rows, got "
            f"{len(classified_rows):,}"
        )
    if len(hybrid_rows) != 110_918:
        raise AssertionError(
            f"Expected 110,918 corpus rows, got {len(hybrid_rows):,}"
        )

    font_family, font_file = select_japanese_font()
    evaluation_rows, gold_count = load_evaluation_rows(
        gold_path,
        classified_path,
    )
    if (gold_count, len(evaluation_rows)) != (192, 192):
        raise AssertionError(
            f"Expected gold/join counts 192/192, got "
            f"{gold_count}/{len(evaluation_rows)}"
        )

    source_sha = {
        "source_gold": sha256(SOURCE_GOLD),
        "normalized_gold": sha256(gold_path),
        "hybrid_corpus": sha256(hybrid_corpus_path),
        "classified": sha256(classified_path),
    }
    common_sources = {
        "paths": {
            "source_gold": display_path(SOURCE_GOLD),
            "normalized_gold": display_path(gold_path),
            "hybrid_corpus": display_path(hybrid_corpus_path),
            "classified": display_path(classified_path),
        },
        "sha256": source_sha,
    }

    p13_data = page13_metrics(gold_path, classified_path)
    p14_data = page14_metrics(evaluation_rows, classified_rows)
    p15_data = page15_metrics(classified_rows)
    negotiation_rows = load_negotiation_sample()
    p16_data = page16_metrics(p15_data, negotiation_rows)
    page_data = {
        13: p13_data,
        14: p14_data,
        15: p15_data,
        16: p16_data,
    }
    for data in page_data.values():
        data["sources"] = common_sources
        data["render"] = {
            "font_family": font_family,
            "font_file": font_file,
            "width_px": int(FIGSIZE[0] * DPI),
            "height_px": int(FIGSIZE[1] * DPI),
            "dpi": DPI,
        }

    metric_paths = {
        13: output_dir / "p13_metrics.json",
        14: output_dir / "p14_metrics.json",
        15: output_dir / "p15_metrics.json",
        16: output_dir / "p16_metrics.json",
    }
    for page, data in page_data.items():
        write_json(metric_paths[page], data)

    png_paths = {
        13: output_dir / "p13_agreement.png",
        14: output_dir / "p14_composition.png",
        15: output_dir / "p15_new_accounts.png",
        16: output_dir / "p16_expressions.png",
    }
    renders = {
        13: render_page13(p13_data, png_paths[13]),
        14: render_page14(p14_data, png_paths[14]),
        15: render_page15(p15_data, png_paths[15]),
        16: render_page16(p16_data, png_paths[16]),
    }
    if any(render["width_px"] < MIN_WIDTH for render in renders.values()):
        raise AssertionError(f"All PNG files must be at least {MIN_WIDTH}px")

    manifest = {
        "schema_version": 2,
        "sources": common_sources,
        "qualitative_sample_sources": p16_data["sample_sources"],
        "gold_validation": {
            key: gold_validation[key]
            for key in (
                "rows",
                "columns",
                "unique_ids",
                "classification_join",
                "supplement_ids",
                "supplement_exchange_labels_preserved",
                "source_first_12_cells_preserved",
            )
        },
        "render": {
            "font_family": font_family,
            "font_file": font_file,
            "figsize_inches": list(FIGSIZE),
            "dpi": DPI,
            "minimum_width_px": MIN_WIDTH,
        },
        "assets": {
            f"page_{page}": {
                "png": renders[page],
                "metrics_json": {
                    "file": metric_paths[page].name,
                    "sha256": sha256(metric_paths[page]),
                },
            }
            for page in (13, 14, 15, 16)
        },
    }
    manifest_path = output_dir / "slide_assets_manifest.json"
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"PASS: slide candidates written to {output_dir}")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Output directory outside the repository. If omitted, a new "
            "system temporary directory is created."
        ),
    )
    parser.add_argument("--gold", type=Path, default=GOLD_STANDARD)
    parser.add_argument("--classified", type=Path, default=CLASSIFIED)
    parser.add_argument("--hybrid-corpus", type=Path, default=HYBRID_CORPUS)
    arguments = parser.parse_args()
    if arguments.output_dir is None:
        arguments.output_dir = Path(
            tempfile.mkdtemp(prefix="bonbon_slides_10_16_rework_")
        )
    return arguments


if __name__ == "__main__":
    arguments = parse_args()
    build_assets(
        arguments.output_dir,
        arguments.gold,
        arguments.classified,
        arguments.hybrid_corpus,
    )
