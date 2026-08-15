#!/usr/bin/env python3
"""Rebuild the locked 2025-11..2026-04 hybrid corpus from monthly exports.

The preserved filter code reproduces ``2511-2604.csv``.  The later ``final``
filter implementation is no longer present, so the recoverable relaxed
keyword cases are expressed here and the remaining final-only decisions are
kept in an inspectable ID lock file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

from filter_ads_202511_202604 import (
    classify_additional_ad,
    keyword_matches,
    load_sources,
    unique_headers,
)

csv.field_size_limit(10**9)

# Rebuilt files are written outside data/output so the preserved baselines are
# never overwritten, and the verifier compares the two directories.
DEFAULT_REBUILD_DIR = Path("rebuild")
DEFAULT_OUTPUT = DEFAULT_REBUILD_DIR / "2511-2604_hybrid.csv"
DEFAULT_SELECTION_LOCK = Path(__file__).resolve().parent / "baselines/hybrid_final_exclusions.csv"
EXPECTED_ROWS = 110_918
EXPECTED_LOCK_COUNTS = {
    "RELAXED_KEYWORD_STILL_EXCLUDED": 257,
    "FINAL_ONLY_EXCLUSION": 134,
}
PROTECTED_BASENAMES = {
    "2511-2604.csv",
    "2511-2604_final.csv",
    "2511-2604_hybrid.csv",
    "removed_additional_ads_with_reasons_202511_202604.csv",
    "sentiment_classified_hybrid.csv",
    "gold_standard_192.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_protected_output(path: Path, root: Path) -> bool:
    protected_dir = (root / "data/output").resolve()
    resolved = path.resolve()
    return resolved.parent == protected_dir and resolved.name in PROTECTED_BASENAMES


def load_selection_lock(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["post_id", "reason"]:
            raise ValueError(
                f"Selection lock schema must be post_id,reason: {reader.fieldnames}"
            )
        rows = list(reader)

    locked: dict[str, str] = {}
    for row in rows:
        post_id = row["post_id"]
        reason = row["reason"]
        if post_id in locked:
            raise ValueError(f"Duplicate post_id in selection lock: {post_id}")
        if reason not in EXPECTED_LOCK_COUNTS:
            raise ValueError(f"Unknown selection-lock reason for {post_id}: {reason}")
        locked[post_id] = reason

    actual_counts = Counter(locked.values())
    if dict(actual_counts) != EXPECTED_LOCK_COUNTS:
        raise ValueError(
            f"Selection-lock counts changed: expected {EXPECTED_LOCK_COUNTS}, "
            f"got {dict(actual_counts)}"
        )
    return locked


def is_relaxed_keyword_case(text: str, matches: list[str]) -> bool:
    """Return the final-filter relaxations recovered from the ID-set delta."""
    match_tuple = tuple(matches)
    if match_tuple in (("第弾",), ("本日抽選開始ラインナップ",)):
        return True
    # One post contains half-width ``ﾘﾎﾟｽﾄ``.  The preserved old filter uses
    # NFKC and removed it, while the final corpus retained it.
    normalized = unicodedata.normalize("NFKC", text)
    return (
        match_tuple == ("リポスト",)
        and "リポスト" not in text
        and "リポスト" in normalized
    )


def build_hybrid(
    root: Path,
    output: Path,
    selection_lock: Path = DEFAULT_SELECTION_LOCK,
) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if is_protected_output(output, root):
        raise ValueError(f"Refusing to overwrite protected baseline: {output}")

    headers, source_rows, source_summary = load_sources(root)
    locked = load_selection_lock(selection_lock)
    source_ids = [row[1] for _, row in source_rows]
    source_id_set = set(source_ids)
    if len(source_ids) != len(source_id_set):
        raise ValueError("Monthly source 投稿ID_文字列 values are not unique")
    missing_locked = set(locked) - source_id_set
    if missing_locked:
        raise ValueError(
            f"{len(missing_locked)} selection-lock IDs are absent from monthly sources"
        )

    kept_rows: list[list[str]] = []
    kept_ids: set[str] = set()
    counts: Counter[str] = Counter()
    for _, row in source_rows:
        post_id = row[1]
        text = row[8]
        lock_reason = locked.get(post_id)
        if lock_reason:
            counts[lock_reason] += 1
            continue

        matches = keyword_matches(text)
        if matches:
            if is_relaxed_keyword_case(text, matches):
                counts["RELAXED_KEYWORD_RESTORED"] += 1
            else:
                counts["KEYWORD_EXCLUDED"] += 1
                continue
        else:
            classified = classify_additional_ad(text)
            if classified is not None:
                counts["ADDITIONAL_AD_EXCLUDED"] += 1
                continue

        if post_id in kept_ids:
            raise ValueError(f"Duplicate output post_id: {post_id}")
        kept_ids.add(post_id)
        kept_rows.append(row)

    expected_counts = {
        "KEYWORD_EXCLUDED": 19_105,
        "RELAXED_KEYWORD_STILL_EXCLUDED": 257,
        "ADDITIONAL_AD_EXCLUDED": 5_874,
        "FINAL_ONLY_EXCLUSION": 134,
        "RELAXED_KEYWORD_RESTORED": 2_015,
    }
    for key, expected in expected_counts.items():
        if counts[key] != expected:
            raise ValueError(
                f"Recovered selection count changed for {key}: "
                f"expected {expected}, got {counts[key]}"
            )
    if len(kept_rows) != EXPECTED_ROWS:
        raise ValueError(
            f"Hybrid row count changed: expected {EXPECTED_ROWS}, got {len(kept_rows)}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(unique_headers(headers))
        writer.writerows(kept_rows)

    return {
        **source_summary,
        "output": str(output),
        "output_rows": len(kept_rows),
        "output_unique_ids": len(kept_ids),
        "selection_counts": dict(counts),
        "sha256": sha256(output),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the locked hybrid corpus from six monthly CSV files."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--selection-lock", type=Path, default=DEFAULT_SELECTION_LOCK)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_hybrid(args.root, args.output, args.selection_lock)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
