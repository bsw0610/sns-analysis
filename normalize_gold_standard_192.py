#!/usr/bin/env python3
"""Safely normalize gold_standard_192.csv to its 12 meaningful columns."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shlex
import sys
from pathlib import Path

csv.field_size_limit(10**9)

GOLD_COLUMNS = [
    "post_id",
    "投稿日",
    "clean_text",
    "喜び満足",
    "欲望執着",
    "不満怒り",
    "焦り競争",
    "情報共有",
    "交換取引",
    "中立",
    "要検討",
    "メモ",
]
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = PROJECT_ROOT / "data/output/gold_standard_192.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/output/gold_standard_192_normalized.csv"
DEFAULT_SUPPLEMENT = PROJECT_ROOT / "data/output/gold_supplement_11.csv"
DEFAULT_HYBRID = PROJECT_ROOT / "data/output/sentiment_classified_hybrid.csv"
EXPECTED_ROWS = 192
EXPECTED_SUPPLEMENT_ROWS = 3
PROTECTED_DIR = (PROJECT_ROOT / "data/output").resolve()
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


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"Empty CSV: {path}") from None
        rows = list(reader)
    return header, rows


def read_id_set(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise ValueError(f"Missing {column} in {path}")
        return {row[column] for row in reader}


def normalization_command(output: Path = DEFAULT_OUTPUT) -> str:
    """Return the command that creates a validated normalized gold standard."""
    args = [
        sys.executable,
        str(PROJECT_ROOT / "normalize_gold_standard_192.py"),
        "--input",
        str(DEFAULT_SOURCE),
        "--output",
        str(output),
        "--supplement",
        str(DEFAULT_SUPPLEMENT),
        "--hybrid",
        str(DEFAULT_HYBRID),
    ]
    return " ".join(shlex.quote(arg) for arg in args)


def validate_normalized_gold(
    path: Path,
    source: Path = DEFAULT_SOURCE,
    supplement: Path = DEFAULT_SUPPLEMENT,
    hybrid: Path = DEFAULT_HYBRID,
) -> dict[str, object]:
    """Validate the official 12-column derivative against its preserved source."""
    path = path.resolve()
    source = source.resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Normalized gold standard not found: {path}\n"
            "Generate it with:\n"
            f"  {normalization_command(path)}"
        )

    output_header, output_rows = read_csv(path)
    if output_header != GOLD_COLUMNS:
        raise ValueError(
            f"Normalized gold standard must have exactly 12 columns: {path}"
        )
    if len(output_rows) != EXPECTED_ROWS:
        raise ValueError(
            f"Normalized gold standard must have {EXPECTED_ROWS} rows, "
            f"got {len(output_rows)}: {path}"
        )
    if any(len(row) != len(GOLD_COLUMNS) for row in output_rows):
        raise ValueError(f"Normalized row width is not 12 columns: {path}")

    post_ids = [row[0] for row in output_rows]
    if len(set(post_ids)) != EXPECTED_ROWS:
        raise ValueError(f"Normalized gold standard contains duplicate IDs: {path}")

    source_header, source_rows = read_csv(source)
    if source_header[: len(GOLD_COLUMNS)] != GOLD_COLUMNS:
        raise ValueError(f"Unexpected preserved-source columns: {source}")
    source_first_12 = [row[: len(GOLD_COLUMNS)] for row in source_rows]
    if output_rows != source_first_12:
        raise ValueError(
            "Normalized gold standard differs from the preserved source's "
            f"first 12 fields: {path}"
        )

    hybrid_ids = read_id_set(hybrid, "投稿ID_文字列")
    joined_ids = set(post_ids) & hybrid_ids
    if len(joined_ids) != EXPECTED_ROWS:
        raise ValueError(
            f"Gold/classification join must be 192/192, got {len(joined_ids)}/192"
        )

    supplement_ids = read_id_set(supplement, "post_id")
    surviving_supplement_ids = supplement_ids & set(post_ids) & hybrid_ids
    if len(surviving_supplement_ids) != EXPECTED_SUPPLEMENT_ROWS:
        raise ValueError(
            "Expected exactly three supplement rows in normalized gold/hybrid, "
            f"got {len(surviving_supplement_ids)}"
        )
    by_id = {
        row[0]: dict(zip(GOLD_COLUMNS, row, strict=True)) for row in output_rows
    }
    for post_id in surviving_supplement_ids:
        if by_id[post_id]["交換取引"] != "1":
            raise ValueError(
                f"Supplement label is not preserved as 交換取引=1: {post_id}"
            )

    return {
        "path": str(path),
        "rows": len(output_rows),
        "columns": len(output_header),
        "unique_ids": len(set(post_ids)),
        "source_first_12_cells_preserved": True,
        "supplement_ids": sorted(surviving_supplement_ids),
        "supplement_exchange_labels_preserved": True,
        "classification_join": len(joined_ids),
        "sha256": sha256(path),
    }


def normalize_gold(
    source: Path,
    output: Path,
    supplement: Path = DEFAULT_SUPPLEMENT,
    hybrid: Path = DEFAULT_HYBRID,
) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if output.parent == PROTECTED_DIR and output.name in PROTECTED_BASENAMES:
        raise ValueError(f"Refusing to overwrite protected baseline: {output}")

    header, rows = read_csv(source)
    if header[: len(GOLD_COLUMNS)] != GOLD_COLUMNS:
        raise ValueError(f"Unexpected gold-standard columns: {header}")
    if len(header) not in (len(GOLD_COLUMNS), 20):
        raise ValueError(f"Expected 12 or 20 input columns, got {len(header)}")
    if any(header[len(GOLD_COLUMNS) :]):
        raise ValueError("Columns after the 12 gold-standard columns must be unnamed")
    if any(len(row) != len(header) for row in rows):
        raise ValueError("Gold-standard row width does not match its header")
    if any(any(row[len(GOLD_COLUMNS) :]) for row in rows):
        raise ValueError("Unnamed trailing columns contain data; refusing to discard it")
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(rows)}")

    normalized_rows = [row[: len(GOLD_COLUMNS)] for row in rows]
    post_ids = [row[0] for row in normalized_rows]
    if len(set(post_ids)) != len(post_ids):
        raise ValueError("Duplicate post_id in gold standard")

    hybrid_ids = read_id_set(hybrid, "投稿ID_文字列")
    supplement_ids = read_id_set(supplement, "post_id")
    surviving_supplement_ids = supplement_ids & hybrid_ids & set(post_ids)
    if len(surviving_supplement_ids) != EXPECTED_SUPPLEMENT_ROWS:
        raise ValueError(
            "Expected exactly three supplement rows in gold/hybrid, got "
            f"{len(surviving_supplement_ids)}"
        )

    by_id = {
        row[0]: dict(zip(GOLD_COLUMNS, row, strict=True)) for row in normalized_rows
    }
    for post_id in surviving_supplement_ids:
        if by_id[post_id]["交換取引"] != "1":
            raise ValueError(
                f"Supplement label is not preserved as 交換取引=1: {post_id}"
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(GOLD_COLUMNS)
        writer.writerows(normalized_rows)

    output_header, output_rows = read_csv(output)
    if output_header != GOLD_COLUMNS or output_rows != normalized_rows:
        raise AssertionError("Normalized output differs from the source's first 12 fields")

    validation = validate_normalized_gold(output, source, supplement, hybrid)
    return {
        "source": str(source),
        "output": str(output),
        "rows": validation["rows"],
        "columns": validation["columns"],
        "unique_ids": validation["unique_ids"],
        "all_12_fields_preserved": True,
        "supplement_ids": validation["supplement_ids"],
        "supplement_exchange_labels_preserved": True,
        "classification_join": validation["classification_join"],
        "sha256": validation["sha256"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove only the eight empty unnamed columns from gold_standard_192.csv."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument("--hybrid", type=Path, default=DEFAULT_HYBRID)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = normalize_gold(args.input, args.output, args.supplement, args.hybrid)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
