#!/usr/bin/env python3
"""Create a reproducible random sample from the six monthly X exports."""

from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path


SOURCE_FILES = [
    "202511.csv",
    "202512.csv",
    "202601.csv",
    "202602.csv",
    "202603.csv",
    "202604.csv",
]
SEED = 20260716
SAMPLE_SIZE = 100


def unique_headers(headers: list[str]) -> list[str]:
    result: list[str] = []
    seen: Counter[str] = Counter()
    preferred = {1: "投稿ID_文字列", 5: "ユーザーID_文字列"}
    for index, header in enumerate(headers):
        if index in preferred and header in result:
            result.append(preferred[index])
        else:
            seen[header] += 1
            result.append(header if seen[header] == 1 else f"{header}_{seen[header]}")
    return result


def main() -> None:
    root = Path(__file__).resolve().parent
    records: list[tuple[str, list[str]]] = []
    source_header: list[str] | None = None

    for file_name in SOURCE_FILES:
        with (root / file_name).open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source)
            header = next(reader)
            if source_header is None:
                source_header = header
            elif header != source_header:
                raise ValueError(f"Schema mismatch: {file_name}")
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    raise ValueError(f"Column count mismatch: {file_name}:{row_number}")
                records.append((file_name, row))

    if source_header is None:
        raise RuntimeError("No source header found")
    if len(records) < SAMPLE_SIZE:
        raise ValueError("Not enough records to sample")

    sampled = random.Random(SEED).sample(records, SAMPLE_SIZE)
    output_dir = root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "random_sample_100_202511_202604.csv"

    with output_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["抽出順", "元ファイル", *unique_headers(source_header)])
        for sequence, (file_name, row) in enumerate(sampled, start=1):
            writer.writerow([sequence, file_name, *row])

    counts = Counter(file_name for file_name, _ in sampled)
    print(f"output={output_path}")
    print(f"population={len(records)} sample={len(sampled)} unique_ids={len({row[0] for _, row in sampled})}")
    print("monthly_counts=" + ",".join(f"{name}:{counts[name]}" for name in SOURCE_FILES))


if __name__ == "__main__":
    main()
