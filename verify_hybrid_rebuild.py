#!/usr/bin/env python3
"""Integration checks for the locked hybrid baseline rebuild."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Callable

from build_hybrid_corpus import (
    DEFAULT_SELECTION_LOCK,
    build_hybrid,
    is_relaxed_keyword_case,
    load_selection_lock,
)
from classify_sns_rule_based import VERSION, classify_csv
from filter_ads_202511_202604 import (
    classify_additional_ad,
    keyword_matches,
    load_sources,
)
from normalize_gold_standard_192 import GOLD_COLUMNS, normalize_gold

csv.field_size_limit(10**9)

EXPECTED_HYBRID_SHA = "3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e"
EXPECTED_CLASSIFIED_SHA = "f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d"
EXPECTED_GOLD_SOURCE_SHA = "fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815"
EXPECTED_NORMALIZED_GOLD_SHA = "ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c"
EXPECTED_ROWS = 110_918
EXPECTED_GOLD_ROWS = 192
EXPECTED_SUPPLEMENT_ROWS = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        header = next(reader)
        return header, list(reader)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def check_rejects(action: Callable[[], object], message: str) -> None:
    try:
        action()
    except ValueError:
        print(f"PASS: {message}")
        return
    raise AssertionError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify every hybrid-baseline invariant.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--rebuild-dir", type=Path, default=Path("rebuild")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    rebuild_dir = args.rebuild_dir.resolve()
    hybrid = rebuild_dir / "2511-2604_hybrid.csv"
    classified = rebuild_dir / "sentiment_classified_hybrid.csv"
    gold = rebuild_dir / "gold_standard_192_normalized.csv"

    baseline_hybrid = root / "data/output/2511-2604_hybrid.csv"
    baseline_classified = root / "data/output/sentiment_classified_hybrid.csv"
    baseline_gold = root / "data/output/gold_standard_192.csv"
    old_corpus = root / "data/output/2511-2604.csv"
    final_corpus = root / "data/output/2511-2604_final.csv"
    additional_ads = (
        root / "data/output/removed_additional_ads_with_reasons_202511_202604.csv"
    )
    supplement = root / "data/output/gold_supplement_11.csv"

    check(VERSION == "2.0.0", "classifier version is v2.0.0")
    check(
        sha256(baseline_hybrid) == EXPECTED_HYBRID_SHA,
        "protected hybrid baseline SHA-256 is unchanged",
    )
    check(
        sha256(baseline_classified) == EXPECTED_CLASSIFIED_SHA,
        "protected classified baseline SHA-256 is unchanged",
    )
    check(
        sha256(baseline_gold) == EXPECTED_GOLD_SOURCE_SHA,
        "protected gold-standard source SHA-256 is unchanged",
    )
    check_rejects(
        lambda: build_hybrid(root, baseline_hybrid),
        "hybrid builder rejects a protected baseline output path",
    )
    check_rejects(
        lambda: normalize_gold(
            baseline_gold, baseline_gold, supplement, baseline_classified
        ),
        "gold normalizer rejects a protected baseline output path",
    )

    base_h, base_rows = read_csv(baseline_hybrid)
    rebuilt_h, rebuilt_rows = read_csv(hybrid)
    check(len(rebuilt_rows) == EXPECTED_ROWS, "hybrid corpus has 110,918 rows")
    rebuilt_ids = [row[1] for row in rebuilt_rows]
    base_ids = [row[1] for row in base_rows]
    check(len(set(rebuilt_ids)) == EXPECTED_ROWS, "hybrid corpus has zero duplicate IDs")
    check(set(rebuilt_ids) == set(base_ids), "hybrid ID set matches the baseline")
    check(rebuilt_ids == base_ids, "hybrid ID order matches the baseline")
    check(rebuilt_h == base_h, "hybrid columns match the baseline")
    check(rebuilt_rows == base_rows, "hybrid cell values match the baseline")
    check(sha256(hybrid) == EXPECTED_HYBRID_SHA, "hybrid SHA-256 matches the baseline")

    _, old_rows = read_csv(old_corpus)
    _, final_rows = read_csv(final_corpus)
    _, additional_rows = read_csv(additional_ads)
    old_ids = [row[1] for row in old_rows]
    final_ids = [row[1] for row in final_rows]
    additional_ids = {row[1] for row in additional_rows}
    check(
        base_ids == [post_id for post_id in final_ids if post_id not in additional_ids],
        "hybrid is the ordered final-minus-additional-ad ID sequence",
    )
    check(
        set(base_ids) == set(final_ids) - additional_ids,
        "hybrid ID set is exactly final minus the 5,874 additional-ad IDs",
    )

    _, source_rows, _ = load_sources(root)
    reproduced_old_ids = [
        row[1]
        for _, row in source_rows
        if not keyword_matches(row[8]) and classify_additional_ad(row[8]) is None
    ]
    check(old_ids == reproduced_old_ids, "preserved filter code reproduces old corpus IDs")

    old_id_set = set(old_ids)
    final_id_set = set(final_ids)
    selection_lock = load_selection_lock(DEFAULT_SELECTION_LOCK)
    final_only_locked = {
        post_id
        for post_id, reason in selection_lock.items()
        if reason == "FINAL_ONLY_EXCLUSION"
    }
    relaxed_locked = {
        post_id
        for post_id, reason in selection_lock.items()
        if reason == "RELAXED_KEYWORD_STILL_EXCLUDED"
    }
    recovered_relaxed_not_final = {
        row[1]
        for _, row in source_rows
        if is_relaxed_keyword_case(row[8], keyword_matches(row[8]))
        and row[1] not in final_id_set
    }
    check(
        final_only_locked == old_id_set - final_id_set,
        "134 final-only exclusions equal the old-minus-final ID set",
    )
    check(
        relaxed_locked == recovered_relaxed_not_final,
        "257 locked relaxed-keyword exclusions equal the observed ID delta",
    )
    check(
        len(set(base_ids) - old_id_set) == 2_015,
        "hybrid restores exactly 2,015 rows beyond the old filter",
    )

    base_ch, base_crows = read_csv(baseline_classified)
    rebuilt_ch, rebuilt_crows = read_csv(classified)
    check(len(rebuilt_crows) == EXPECTED_ROWS, "classified output has 110,918 rows")
    check(
        [row[1] for row in rebuilt_crows] == rebuilt_ids,
        "classified output preserves hybrid ID order",
    )
    check(rebuilt_ch == base_ch, "classified columns match the baseline")
    check(rebuilt_crows == base_crows, "classified cell values match the baseline")
    check(
        sha256(classified) == EXPECTED_CLASSIFIED_SHA,
        "classified SHA-256 matches the baseline",
    )

    gold_h, gold_rows = read_csv(gold)
    check(gold_h == GOLD_COLUMNS, "normalized gold standard has the expected 12 columns")
    check(len(gold_rows) == EXPECTED_GOLD_ROWS, "normalized gold standard has 192 rows")
    check(
        sha256(gold) == EXPECTED_NORMALIZED_GOLD_SHA,
        "normalized gold SHA-256 matches the locked 12-column result",
    )
    gold_ids = [row[0] for row in gold_rows]
    check(len(set(gold_ids)) == EXPECTED_GOLD_ROWS, "gold standard has zero duplicate IDs")
    classified_ids = {row[1] for row in rebuilt_crows}
    check(
        len(classified_ids & set(gold_ids)) == EXPECTED_GOLD_ROWS,
        "classified/gold join succeeds for 192/192 IDs",
    )

    source_gold_h, source_gold_rows = read_csv(baseline_gold)
    check(
        source_gold_h[: len(GOLD_COLUMNS)] == GOLD_COLUMNS
        and len(source_gold_h) == 20
        and not any(source_gold_h[len(GOLD_COLUMNS) :]),
        "source gold schema is 12 named plus 8 unnamed columns",
    )
    check(
        not any(any(row[len(GOLD_COLUMNS) :]) for row in source_gold_rows),
        "all eight unnamed source columns are empty",
    )
    check(
        gold_rows == [row[: len(GOLD_COLUMNS)] for row in source_gold_rows],
        "all 12 gold fields, including every manual label, are preserved",
    )

    with supplement.open("r", encoding="utf-8-sig", newline="") as source:
        supplement_ids = {row["post_id"] for row in csv.DictReader(source)}
    surviving = supplement_ids & set(gold_ids) & classified_ids
    check(len(surviving) == EXPECTED_SUPPLEMENT_ROWS, "exactly 3 supplement rows survive")
    gold_by_id = {
        row[0]: dict(zip(GOLD_COLUMNS, row, strict=True)) for row in gold_rows
    }
    check(
        all(gold_by_id[post_id]["交換取引"] == "1" for post_id in surviving),
        "all 3 supplement rows preserve 交換取引=1",
    )

    repeat_dir = rebuild_dir / "repeat"
    repeat_hybrid = repeat_dir / "2511-2604_hybrid.csv"
    repeat_classified = repeat_dir / "sentiment_classified_hybrid.csv"
    repeat_gold = repeat_dir / "gold_standard_192_normalized.csv"
    build_hybrid(root, repeat_hybrid)
    repeat_count = classify_csv(repeat_hybrid, repeat_classified, None)
    check(repeat_count == EXPECTED_ROWS, "repeat classifier processed 110,918 rows")
    normalize_gold(baseline_gold, repeat_gold, supplement, repeat_classified)
    check(sha256(repeat_hybrid) == sha256(hybrid), "repeat hybrid output is identical")
    check(
        sha256(repeat_classified) == sha256(classified),
        "repeat classified output is identical",
    )
    check(sha256(repeat_gold) == sha256(gold), "repeat normalized gold is identical")

    check(
        sha256(baseline_hybrid) == EXPECTED_HYBRID_SHA
        and sha256(baseline_classified) == EXPECTED_CLASSIFIED_SHA
        and sha256(baseline_gold) == EXPECTED_GOLD_SOURCE_SHA,
        "all protected baselines remain unchanged after repeat execution",
    )
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
