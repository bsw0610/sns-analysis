#!/usr/bin/env python3
"""Verify regenerated page 13-16 PNG candidates and their metric evidence."""

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
    NEGOTIATION_SAMPLE_PATHS,
    SOURCE_GOLD,
    load_negotiation_sample,
    page15_metrics,
    page16_metrics,
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
    "p16_expressions.png",
    "p16_metrics.json",
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
    expected_overall = {
        "lenient_micro_f1": metrics["lenient"]["micro"]["f1"],
        "multi_micro_f1": metrics["multi"]["micro"]["f1"],
    }
    actual_overall = {
        item["key"]: item["value"]
        for item in data["overall_metrics"]
    }
    expected_categories = {
        category: item["f1"]
        for category, item in metrics["lenient"]["per_category"].items()
    }
    actual_categories = {
        item["category"]: item["f1"]
        for item in data["category_metrics"]
    }
    assert_equal("page 13 gold rows", gold_count, 192)
    assert_equal("page 13 join", len(rows), 192)
    assert_equal("page 13 score threshold", data["threshold"], 1.8)
    assert_equal(
        "page 13 overall calculated F1 values",
        actual_overall,
        expected_overall,
    )
    assert_equal(
        "page 13 category calculated F1 values",
        actual_categories,
        expected_categories,
    )
    assert_equal(
        "page 13 displayed overall F1 values",
        {
            item["key"]: item["display"]
            for item in data["overall_metrics"]
        },
        {
            "lenient_micro_f1": "0.577",
            "multi_micro_f1": "0.595",
        },
    )
    assert_equal(
        "page 13 displayed category F1 values",
        {
            item["category"]: item["display"]
            for item in data["category_metrics"]
        },
        {
            "不満・怒り": "0.471",
            "焦り・競争": "0.294",
            "交換・取引": "0.869",
            "欲望・執着": "0.373",
            "喜び・満足": "0.516",
            "情報共有": "0.000",
            "中立": "0.625",
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
    assert_equal("page 14 extended labels", data["extended_label_count"], 217)
    assert_equal(
        "page 14 displayed total",
        round(data["sum_of_category_percentages"], 1),
        113.0,
    )
    assert_equal(
        "page 14 classifier urgency count",
        data["classifier_reference"]["numerator"],
        3_272,
    )
    assert_equal(
        "page 14 classifier urgency denominator",
        data["classifier_reference"]["denominator"],
        110_918,
    )
    assert_equal(
        "page 14 classifier urgency display",
        data["classifier_reference"]["display"],
        "2.9%",
    )
    if "情報共有" not in data["visible_copy"]["information_bias_note"]:
        raise AssertionError("Page 14 must show the information-sharing caveat")


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


def validate_page16(
    assets_dir: Path,
    classified_path: Path,
) -> None:
    data = load_json(assets_dir / "p16_metrics.json")
    classified_rows = read_dicts(classified_path)
    expected_p15 = page15_metrics(classified_rows)
    expected = page16_metrics(
        expected_p15,
        load_negotiation_sample(),
    )
    assert_equal("page 16 template", data["template"], expected["template"])
    assert_equal(
        "page 16 fixed sample",
        data["fixed_sample"],
        expected["fixed_sample"],
    )
    assert_equal(
        "page 16 displayed expressions",
        data["displayed_expressions"],
        expected["displayed_expressions"],
    )
    assert_equal("page 16 quotes", data["quotes"], expected["quotes"])
    assert_equal(
        "page 16 sample sources",
        data["sample_sources"],
        expected["sample_sources"],
    )
    sample = data["fixed_sample"]
    checks = [
        ("template posts", data["template"]["posts"], 12_411),
        (
            "template share",
            round(data["template"]["share_percent"], 1),
            51.0,
        ),
        ("fixed sample posts", sample["posts"], 98),
        ("reply posts", sample["reply_posts"], 79),
        ("formal greetings", sample["formal_greeting_posts"], 48),
        (
            "honorific consideration",
            sample["honorific_consideration_posts"],
            42,
        ),
        ("exchange ratios", sample["exchange_ratio_posts"], 17),
    ]
    for label, actual, wanted in checks:
        assert_equal(f"page 16 {label}", actual, wanted)
    assert_equal(
        "page 16 verified quotes",
        [quote["verified"] for quote in data["quotes"]],
        [True, True],
    )
    for path in NEGOTIATION_SAMPLE_PATHS:
        display_keys = data["sample_sources"]["sha256"]
        if not any(value == sha256(path) for value in display_keys.values()):
            raise AssertionError(f"Missing page 16 sample SHA for {path}")
    print("Page 16 verification: 7/7 plus 2/2 quote provenance checks")


def validate_png_files(assets_dir: Path) -> None:
    for filename in (
        "p13_agreement.png",
        "p14_composition.png",
        "p15_new_accounts.png",
        "p16_expressions.png",
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
    p16 = load_json(assets_dir / "p16_metrics.json")
    assert_equal(
        "manifest qualitative sources",
        manifest["qualitative_sample_sources"],
        p16["sample_sources"],
    )
    assert_equal("manifest schema", manifest["schema_version"], 2)
    for page in (13, 14, 15, 16):
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
    print(f"Repeatability: all {len(ASSET_FILES)} output SHA-256 values match")


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
    validate_page16(assets_dir, classified_path)
    validate_png_files(assets_dir)
    validate_manifest(assets_dir)
    compare_repeated_run(assets_dir, comparison_dir)
    print("PASS: page 13-16 slide asset verification")


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
