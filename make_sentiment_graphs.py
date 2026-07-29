#!/usr/bin/env python3
"""Create easy-to-read sentiment summary graphs from sentiment_summary.csv."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INPUT = Path("data/output/sentiment_summary.csv")
OUTPUT_DIR = Path("data/output")

CATEGORIES = [
    "不満・怒り",
    "焦り・競争",
    "交換・取引",
    "欲望・執着",
    "喜び・満足",
    "情報共有",
    "中立",
]

COLORS = {
    "不満・怒り": "#D84A3A",
    "焦り・競争": "#F39C34",
    "交換・取引": "#8E63B0",
    "欲望・執着": "#E05C95",
    "喜び・満足": "#39A96B",
    "情報共有": "#2F80C9",
    "中立": "#8A8F98",
}

FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    preferred = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc" if bold else None
    paths = ([preferred] if preferred else []) + FONT_PATHS
    for path in paths:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def read_summary() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    overall = [row for row in rows if row["集計種別"] == "カテゴリ別"]
    monthly = [row for row in rows if row["集計種別"] == "月別カテゴリ別"]
    return overall, monthly


def draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str, width: int) -> None:
    title_font = font(34, bold=True)
    subtitle_font = font(18)
    draw.text((50, 34), title, fill="#20242A", font=title_font)
    draw.text((50, 82), subtitle, fill="#5F6670", font=subtitle_font)
    draw.line((50, 120, width - 50, 120), fill="#D8DDE3", width=2)


def save_overall_bar(overall: list[dict[str, str]]) -> None:
    data = {row["カテゴリ"]: (int(row["件数"]), float(row["割合"])) for row in overall}
    width, height = 1200, 780
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw_title(draw, "カテゴリ別 件数と割合", "全期間の分類結果。棒の長さは件数、右端の数値は割合です。", width)

    label_font = font(22)
    value_font = font(20)
    axis_font = font(16)
    left, top, bar_w, bar_h, gap = 210, 165, 760, 48, 30
    max_count = max(count for count, _ in data.values())

    for index, category in enumerate(CATEGORIES):
        count, pct = data.get(category, (0, 0.0))
        y = top + index * (bar_h + gap)
        draw.text((50, y + 8), category, fill="#20242A", font=label_font)
        draw.rounded_rectangle((left, y, left + bar_w, y + bar_h), radius=8, fill="#EEF1F4")
        fill_w = int(bar_w * count / max_count) if max_count else 0
        draw.rounded_rectangle(
            (left, y, left + fill_w, y + bar_h),
            radius=8,
            fill=hex_to_rgb(COLORS[category]),
        )
        draw.text((left + bar_w + 24, y + 6), f"{count:,}件  ({pct:.2f}%)", fill="#20242A", font=value_font)

    draw.text((left, 720), "0", fill="#5F6670", font=axis_font)
    max_label = f"{max_count:,}件"
    label_w, _ = text_size(draw, max_label, axis_font)
    draw.text((left + bar_w - label_w, 720), max_label, fill="#5F6670", font=axis_font)
    img.save(OUTPUT_DIR / "sentiment_overall_bar.png")


def monthly_table(monthly: list[dict[str, str]], value_col: str) -> dict[str, dict[str, float]]:
    table: dict[str, dict[str, float]] = defaultdict(dict)
    for row in monthly:
        table[row["月"]][row["カテゴリ"]] = float(row[value_col])
    return table


def draw_legend(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    legend_font = font(16)
    cursor_x = x
    for category in CATEGORIES:
        color = hex_to_rgb(COLORS[category])
        draw.rounded_rectangle((cursor_x, y, cursor_x + 18, y + 18), radius=4, fill=color)
        draw.text((cursor_x + 25, y - 2), category, fill="#20242A", font=legend_font)
        label_w, _ = text_size(draw, category, legend_font)
        cursor_x += 25 + label_w + 26


def save_monthly_stacked(monthly: list[dict[str, str]], *, percent: bool) -> None:
    value_col = "割合" if percent else "件数"
    table = monthly_table(monthly, value_col)
    months = sorted(table)
    width, height = 1280, 820
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    if percent:
        title = "月別カテゴリ構成比"
        subtitle = "各月を100%として、カテゴリ比率の変化を表示しています。"
        max_value = 100.0
        suffix = "%"
        out = "sentiment_monthly_percentage_stacked.png"
    else:
        title = "月別カテゴリ件数"
        subtitle = "月ごとの投稿件数をカテゴリ別に積み上げています。"
        max_value = max(sum(table[month].values()) for month in months)
        suffix = "件"
        out = "sentiment_monthly_count_stacked.png"

    draw_title(draw, title, subtitle, width)
    draw_legend(draw, 50, 132)

    chart_left, chart_top, chart_right, chart_bottom = 100, 210, 1180, 690
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top
    axis_font = font(16)
    label_font = font(18)

    for i in range(6):
        value = max_value * i / 5
        y = chart_bottom - int(chart_h * i / 5)
        draw.line((chart_left, y, chart_right, y), fill="#E4E8ED", width=1)
        label = f"{value:.0f}{suffix}"
        label_w, label_h = text_size(draw, label, axis_font)
        draw.text((chart_left - label_w - 12, y - label_h // 2), label, fill="#5F6670", font=axis_font)

    bar_gap = 32
    bar_w = int((chart_w - bar_gap * (len(months) - 1)) / len(months))
    for index, month in enumerate(months):
        x0 = chart_left + index * (bar_w + bar_gap)
        y_cursor = chart_bottom
        total = sum(table[month].get(category, 0.0) for category in CATEGORIES)
        for category in CATEGORIES:
            value = table[month].get(category, 0.0)
            segment_h = int(chart_h * value / max_value) if max_value else 0
            y0 = y_cursor - segment_h
            draw.rectangle((x0, y0, x0 + bar_w, y_cursor), fill=hex_to_rgb(COLORS[category]))
            y_cursor = y0
        draw.rectangle((x0, chart_top, x0 + bar_w, chart_bottom), outline="#FFFFFF", width=1)

        month_w, month_h = text_size(draw, month, label_font)
        draw.text((x0 + (bar_w - month_w) / 2, chart_bottom + 18), month, fill="#20242A", font=label_font)
        total_label = f"{total:.0f}{suffix}"
        total_w, _ = text_size(draw, total_label, axis_font)
        draw.text((x0 + (bar_w - total_w) / 2, chart_top - 28), total_label, fill="#5F6670", font=axis_font)

    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#AEB6C0", width=2)
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#AEB6C0", width=2)
    img.save(OUTPUT_DIR / out)


def main() -> None:
    overall, monthly = read_summary()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_overall_bar(overall)
    if monthly:
        save_monthly_stacked(monthly, percent=False)
        save_monthly_stacked(monthly, percent=True)
    else:
        for name in [
            "sentiment_monthly_count_stacked.png",
            "sentiment_monthly_percentage_stacked.png",
        ]:
            path = OUTPUT_DIR / name
            if path.exists():
                path.unlink()
    print("created sentiment graph PNG files in data/output")


if __name__ == "__main__":
    main()
