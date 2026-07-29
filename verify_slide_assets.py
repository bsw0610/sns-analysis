#!/usr/bin/env python3
"""Verify regenerated page 13-15 PNG candidates and their metric evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from evaluate_v2_hybrid_192 import (
    calculate_evaluation_metrics,
    load as load_evaluation_rows,
)
from normalize_gold_standard_192 import (
    DEFAULT_OUTPUT as NORMALIZED_GOLD_STANDARD,
    validate_normalized_gold,
)
from regenerate_slide_assets import (
    CLASSIFIED,
    HYBRID_CORPUS,
    MIN_WIDTH,
    SOURCE_GOLD,
    page15_metrics,
    read_dicts,
    sha256,
)

EXPECTED_SHA256 = {
    "source_gold": (
        "fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815"
    ),
    "normalized_gold": (
        "ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c"
    ),
    "hybrid_corpus": (
        "3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e"
    ),
    "classified": (
        "f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d"
    ),
}
EXPECTED_CI = {
    "交換・取引": "21.8–34.5%",
    "中立": "18.9–31.1%",
    "欲望・執着": "13.2–24.3%",
    "喜び・満足": "11.9–22.5%",
    "焦り・競争": "9.1–19.0%",
    "不満・怒り": "3.6–11.0%",
    "情報共有": "0.4–4.9%",
}
ASSET_FILES = (
    "p13_agreement.png",
    "p13_metrics.json",
    "p14_composition.png",
    "p14_metrics.json",
    "p15_new_accounts.png",
    "p15_metrics.json",
    "slide_assets_manifest.json",
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_equal(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(
            f"{label}: expected {expected!r}, got {actual!r}"
        )


def validate_sources(
    gold_path: Path,
    classified_path: Path,
    hybrid_path: Path,
) -> dict[str, object]:
    gold = validate_normalized_gold(gold_path)
    assert_equal("normalized gold rows", gold["rows"], 192)
    assert_equal("normalized gold columns", gold["columns"], 12)
    assert_equal("normalized gold unique IDs", gold["unique_ids"], 192)
    assert_equal("classification join", gold["classification_join"], 192)
    assert_equal(
        "supplement labels",
        gold["supplement_exchange_labels_preserved"],
        True,
    )
    assert_equal(
        "first 12 fields",
        gold["source_first_12_cells_preserved"],
        True,
    )

    actual_sha = {
        "source_gold": sha256(SOURCE_GOLD),
        "normalized_gold": sha256(gold_path),
        "hybrid_corpus": sha256(hybrid_path),
        "classified": sha256(classified_path),
    }
    assert_equal("locked source SHA-256", actual_sha, EXPECTED_SHA256)
    return gold


def validate_page13(
    assets_dir: Path,
    gold_path: Path,
    classified_path: Path,
) -> None:
    data = load_json(assets_dir / "p13_metrics.json")
    rows, gold_count = load_evaluation_rows(gold_path, classified_path)
    metrics = calculate_evaluation_metrics(rows)
    expected = {
        "lenient_micro_f1": metrics["lenient"]["micro"]["f1"],
        "multi_micro_f1": metrics["multi"]["micro"]["f1"],
        "exchange_lenient_f1": (
            metrics["lenient"]["per_category"]["交換・取引"]["f1"]
        ),
    }
    actual = {
        item["key"]: item["value"]
        for item in data["displayed_metrics"]
    }
    assert_equal("page 13 gold rows", gold_count, 192)
    assert_equal("page 13 join", len(rows), 192)
    assert_equal("page 13 score threshold", data["threshold"], 1.8)
    assert_equal("page 13 calculated F1 values", actual, expected)
    assert_equal(
        "page 13 displayed F1 values",
        {
            item["key"]: item["display"]
            for item in data["displayed_metrics"]
        },
        {
            "lenient_micro_f1": "0.577",
            "multi_micro_f1": "0.595",
            "exchange_lenient_f1": "0.869",
        },
    )


def validate_page14(assets_dir: Path) -> None:
    data = load_json(assets_dir / "p14_metrics.json")
    assert_equal("page 14 sample size", data["sample_size"], 192)
    interval_by_category = {
        item["category"]: item["ci_display"]
        for item in data["categories"]
    }
    assert_equal("page 14 Wald intervals", interval_by_category, EXPECTED_CI)
    assert_equal(
        "page 14 interval method",
        data["confidence_interval"],
        {
            "method": "Wald",
            "confidence_level": 0.95,
            "z": 1.96,
            "sample_size": 192,
            "rounding": "displayed to 1 decimal place",
            "clipped_to_unit_interval": True,
        },
    )
    if data["sum_of_category_percentages"] <= 100:
        raise AssertionError("Page 14 must document multi-label total > 100%")


def validate_page15(
    assets_dir: Path,
    classified_path: Path,
) -> None:
    data = load_json(assets_dir / "p15_metrics.json")
    expected = page15_metrics(read_dicts(classified_path))
    assert_equal("page 15 computed evidence", data["summary"], expected["summary"])
    assert_equal(
        "page 15 monthly evidence",
        data["monthly_new_accounts"],
        expected["monthly_new_accounts"],
    )
    assert_equal(
        "page 15 observation end",
        data["observation_end_date"],
        expected["observation_end_date"],
    )
    assert_equal(
        "page 15 locked observation end",
        data["observation_end_date"],
        "2026-04-30",
    )
    summary = data["summary"]
    top_1 = summary["top_1_percent"]
    top_10 = summary["top_10_percent"]
    template = summary["template"]
    checks = [
        ("posts", summary["exchange_posts"], 24_316),
        ("accounts", summary["accounts"], 10_677),
        (
            "mean",
            round(summary["mean_posts_per_account"], 2),
            2.28,
        ),
        ("median", summary["median_posts_per_account"], 1),
        ("single accounts", summary["single_post_accounts"], 7_198),
        (
            "single share",
            round(summary["single_post_account_share_percent"], 1),
            67.4,
        ),
        ("top 30 posts", summary["top_30_posts"], 1_796),
        (
            "top 30 share",
            round(summary["top_30_share_percent"], 1),
            7.4,
        ),
        ("top 1 share", round(top_1["share_percent"], 1), 14.9),
        ("top 10 share", round(top_10["share_percent"], 1), 45.6),
        ("template posts", template["posts"], 12_411),
        (
            "template share",
            round(template["share_percent"], 1),
            51.0,
        ),
    ]
    passed = 0
    for label, actual, wanted in checks:
        assert_equal(f"page 15 {label}", actual, wanted)
        passed += 1
    assert_equal("page 15 top 1 account count", top_1["accounts"], 106)
    assert_equal("page 15 top 1 post count", top_1["posts"], 3_619)
    assert_equal(
        "page 15 template definition",
        template["definition"],
        "slide_number_definitions.is_exchange_template",
    )
    assert_equal("page 15 checks", passed, 12)
    print("Page 15 verification: 12/12")


def validate_png_files(assets_dir: Path) -> None:
    for filename in (
        "p13_agreement.png",
        "p14_composition.png",
        "p15_new_accounts.png",
    ):
        path = assets_dir / filename
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            assert_equal(f"{filename} format", image.format, "PNG")
            width, height = image.size
            if width < MIN_WIDTH:
                raise AssertionError(
                    f"{filename} width {width}px is below {MIN_WIDTH}px"
                )
            if height < 900:
                raise AssertionError(
                    f"{filename} height {height}px is below 900px"
                )
            if image.getbbox() is None:
                raise AssertionError(f"{filename} is blank")
            print(f"{filename}: valid PNG, {width}x{height}")


def validate_manifest(assets_dir: Path) -> None:
    manifest = load_json(assets_dir / "slide_assets_manifest.json")
    assert_equal(
        "manifest source SHA-256",
        manifest["sources"]["sha256"],
        EXPECTED_SHA256,
    )
    for page in (13, 14, 15):
        asset = manifest["assets"][f"page_{page}"]
        png = assets_dir / asset["png"]["file"]
        metrics = assets_dir / asset["metrics_json"]["file"]
        assert_equal(
            f"page {page} PNG manifest SHA",
            asset["png"]["sha256"],
            sha256(png),
        )
        assert_equal(
            f"page {page} metrics manifest SHA",
            asset["metrics_json"]["sha256"],
            sha256(metrics),
        )
        assert_equal(
            f"page {page} glyph warnings",
            asset["png"]["missing_glyph_warning_count"],
            0,
        )
        assert_equal(
            f"page {page} text overflow",
            asset["png"]["text_overflow_count"],
            0,
        )


def compare_repeated_run(
    assets_dir: Path,
    comparison_dir: Path | None,
) -> None:
    if comparison_dir is None:
        return
    for filename in ASSET_FILES:
        assert_equal(
            f"repeat SHA {filename}",
            sha256(assets_dir / filename),
            sha256(comparison_dir / filename),
        )
    print("Repeatability: all 7 output SHA-256 values match")


def verify(
    assets_dir: Path,
    gold_path: Path,
    classified_path: Path,
    hybrid_path: Path,
    comparison_dir: Path | None = None,
) -> None:
    validate_sources(gold_path, classified_path, hybrid_path)
    validate_page13(assets_dir, gold_path, classified_path)
    validate_page14(assets_dir)
    validate_page15(assets_dir, classified_path)
    validate_png_files(assets_dir)
    validate_manifest(assets_dir)
    compare_repeated_run(assets_dir, comparison_dir)
    print("PASS: page 13-15 slide asset verification")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--comparison-dir", type=Path)
    parser.add_argument("--gold", type=Path, default=NORMALIZED_GOLD_STANDARD)
    parser.add_argument("--classified", type=Path, default=CLASSIFIED)
    parser.add_argument("--hybrid-corpus", type=Path, default=HYBRID_CORPUS)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    verify(
        arguments.assets_dir,
        arguments.gold,
        arguments.classified,
        arguments.hybrid_corpus,
        arguments.comparison_dir,
    )
