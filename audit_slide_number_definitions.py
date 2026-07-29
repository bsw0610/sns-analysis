#!/usr/bin/env python3
"""Audit competing slide-number definitions without modifying baseline files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import tempfile
from collections import Counter
from pathlib import Path

from filter_ads_202511_202604 import keyword_matches
from normalize_gold_standard_192 import (
    DEFAULT_OUTPUT as NORMALIZED_GOLD_STANDARD,
    validate_normalized_gold,
)
from slide_number_definitions import (
    EXCHANGE_ACCOUNT_KEY,
    EXCHANGE_CATEGORY,
    EXCHANGE_TEMPLATE_RE,
    has_exchange_ratio,
    has_honorific_consideration,
    is_platform_reply,
    top_fraction_account_count,
    wald_interval,
)

csv.field_size_limit(10**9)

PROJECT_ROOT = Path(__file__).resolve().parent
CLASSIFIED = PROJECT_ROOT / "data/output/sentiment_classified_hybrid.csv"
HYBRID_CORPUS = PROJECT_ROOT / "data/output/2511-2604_hybrid.csv"
FINAL_CORPUS = PROJECT_ROOT / "data/output/2511-2604_final.csv"
OLD_CORPUS = PROJECT_ROOT / "data/output/2511-2604.csv"
DEFAULT_GOLD = NORMALIZED_GOLD_STANDARD
NEGOTIATION_SOURCES = (
    PROJECT_ROOT
    / "outputs/negotiation-unclassified-20260728/"
    "negotiation_expressions_not_exchange_random50.csv",
    PROJECT_ROOT
    / "data/output/random_sample_50_negotiation_not_exchange_202511_202604.csv",
)
SAMPLE_SEED = 20260730

# Definitions found before unification.  They remain here only to reproduce
# their ID differences; production reporting uses EXCHANGE_TEMPLATE_RE.
LITERAL_SPEC_RE = re.compile(
    r"【(?:交換|譲|求)】|[〈《](?:譲|求)[〉》]|(?:譲|求)[)）：:]"
)
LEGACY_VERIFY_RE = re.compile(
    r"【\s*(?:交換|譲|求)\s*】"
    r"|[〈《]\s*(?:譲|求)\s*[〉》]"
    r"|(?:譲|求)\s*[)）：:]"
)
GOLD_COLUMNS = {
    "交換・取引": "交換取引",
    "中立": "中立",
    "欲望・執着": "欲望執着",
    "喜び・満足": "喜び満足",
    "焦り・競争": "焦り競争",
    "不満・怒り": "不満怒り",
    "情報共有": "情報共有",
}


def read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corpus_ids(path: Path) -> set[str]:
    return {row["投稿ID_文字列"] for row in read_dicts(path)}


def monthly_texts() -> dict[str, str]:
    result: dict[str, str] = {}
    for month in ("202511", "202512", "202601", "202602", "202603", "202604"):
        with (PROJECT_ROOT / f"{month}.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            reader = csv.reader(source)
            next(reader)
            for row in reader:
                result[row[1]] = row[8]
    return result


def write_template_evidence(
    output_dir: Path,
    exchange_rows: list[dict[str, str]],
) -> dict[str, object]:
    sets = {
        "literal_spec": {
            row["投稿ID_文字列"]
            for row in exchange_rows
            if LITERAL_SPEC_RE.search(row["内容"])
        },
        "legacy_verify": {
            row["投稿ID_文字列"]
            for row in exchange_rows
            if LEGACY_VERIFY_RE.search(row["内容"])
        },
        "adopted": {
            row["投稿ID_文字列"]
            for row in exchange_rows
            if EXCHANGE_TEMPLATE_RE.search(row["内容"])
        },
    }
    difference_groups = {
        "whitespace_variant": sorted(
            sets["legacy_verify"] - sets["literal_spec"]
        ),
        "square_bracket_variant": sorted(
            sets["adopted"] - sets["legacy_verify"]
        ),
    }

    id_output = output_dir / "template_definition_id_differences.csv"
    with id_output.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["difference_group", "post_id"])
        for group, post_ids in difference_groups.items():
            writer.writerows((group, post_id) for post_id in post_ids)

    by_id = {row["投稿ID_文字列"]: row for row in exchange_rows}
    rng = random.Random(SAMPLE_SEED)
    samples: list[dict[str, str]] = []
    for group, post_ids in difference_groups.items():
        pattern = (
            LEGACY_VERIFY_RE
            if group == "whitespace_variant"
            else EXCHANGE_TEMPLATE_RE
        )
        for post_id in rng.sample(post_ids, 20):
            text = by_id[post_id]["内容"]
            match = pattern.search(text)
            samples.append(
                {
                    "difference_group": group,
                    "post_id": post_id,
                    "matched_fragment": match.group(0) if match else "",
                    "text": text,
                }
            )
    sample_output = output_dir / "template_definition_review_sample_40.csv"
    with sample_output.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)

    denominator = len(exchange_rows)
    counts = {name: len(post_ids) for name, post_ids in sets.items()}
    differences = {
        name: len(post_ids) for name, post_ids in difference_groups.items()
    }
    assert counts == {
        "literal_spec": 12099,
        "legacy_verify": 12298,
        "adopted": 12411,
    }
    assert differences == {
        "whitespace_variant": 199,
        "square_bracket_variant": 113,
    }
    assert len(samples) == 40
    return {
        "denominator": denominator,
        "counts": counts,
        "rates_percent": {
            name: count / denominator * 100 for name, count in counts.items()
        },
        "difference_counts": differences,
        "id_output": id_output.name,
        "sample_output": sample_output.name,
        "sample_seed": SAMPLE_SEED,
        "sample_size": len(samples),
    }


def account_summary(exchange_rows: list[dict[str, str]]) -> dict[str, object]:
    counts: Counter[str] = Counter(
        row[EXCHANGE_ACCOUNT_KEY].strip() for row in exchange_rows
    )
    descending = sorted(counts.values(), reverse=True)
    k1 = top_fraction_account_count(len(counts), 0.01)
    k10 = top_fraction_account_count(len(counts), 0.10)
    result = {
        "accounts": len(counts),
        "posts": len(exchange_rows),
        "top_1_percent_accounts": k1,
        "top_1_percent_numerator": sum(descending[:k1]),
        "top_1_percent_share": sum(descending[:k1]) / len(exchange_rows) * 100,
        "top_10_percent_accounts": k10,
        "top_10_percent_numerator": sum(descending[:k10]),
        "top_10_percent_share": sum(descending[:k10]) / len(exchange_rows) * 100,
    }
    assert (result["accounts"], result["posts"]) == (10677, 24316)
    assert (k1, result["top_1_percent_numerator"]) == (106, 3619)
    assert (k10, result["top_10_percent_numerator"]) == (1067, 11082)
    return result


def negotiation_summary() -> dict[str, object]:
    occurrences: list[dict[str, str]] = []
    for source_path in NEGOTIATION_SOURCES:
        occurrences.extend(read_dicts(source_path))
    unique = {row["投稿ID_文字列"]: row for row in occurrences}
    duplicate_counts = Counter(row["投稿ID_文字列"] for row in occurrences)
    duplicate_ids = sorted(
        post_id for post_id, count in duplicate_counts.items() if count > 1
    )
    result = {
        "source_rows": len(occurrences),
        "unique_posts": len(unique),
        "duplicate_ids": duplicate_ids,
        "reply_metadata_count": sum(
            is_platform_reply(row) for row in unique.values()
        ),
        "leading_mention_count": sum(
            row["内容"].lstrip().startswith("@") for row in unique.values()
        ),
        "reply_union_count": sum(
            is_platform_reply(row) or row["内容"].lstrip().startswith("@")
            for row in unique.values()
        ),
        "honorific_consideration_count": sum(
            has_honorific_consideration(row["内容"])
            for row in unique.values()
        ),
        "exchange_ratio_unique_count": sum(
            has_exchange_ratio(row["内容"]) for row in unique.values()
        ),
        "exchange_ratio_source_occurrences": sum(
            has_exchange_ratio(row["内容"]) for row in occurrences
        ),
    }
    assert result == {
        "source_rows": 100,
        "unique_posts": 98,
        "duplicate_ids": [
            "ID:2036404178151678416",
            "ID:2047577298866704791",
        ],
        "reply_metadata_count": 79,
        "leading_mention_count": 75,
        "reply_union_count": 80,
        "honorific_consideration_count": 42,
        "exchange_ratio_unique_count": 17,
        "exchange_ratio_source_occurrences": 19,
    }
    return result


def dai_summary() -> dict[str, int]:
    texts = monthly_texts()
    old_ids = corpus_ids(OLD_CORPUS)
    final_restored = corpus_ids(FINAL_CORPUS) - old_ids
    hybrid_added = corpus_ids(HYBRID_CORPUS) - old_ids
    final_count = sum(
        keyword_matches(texts[post_id]) == ["第弾"]
        for post_id in final_restored
    )
    hybrid_count = sum(
        keyword_matches(texts[post_id]) == ["第弾"]
        for post_id in hybrid_added
    )
    assert (len(final_restored), final_count) == (5615, 2002)
    assert (len(hybrid_added), hybrid_count) == (2015, 2002)
    return {
        "final_minus_old": len(final_restored),
        "final_only_dai_keyword": final_count,
        "hybrid_minus_old": len(hybrid_added),
        "hybrid_only_dai_keyword": hybrid_count,
    }


def confidence_interval_summary(gold_path: Path) -> dict[str, object]:
    rows = read_dicts(gold_path)
    result: dict[str, object] = {}
    for category, column in GOLD_COLUMNS.items():
        successes = sum(row[column] == "1" for row in rows)
        low, high = wald_interval(successes, len(rows))
        result[category] = {
            "numerator": successes,
            "denominator": len(rows),
            "percent": f"{successes / len(rows) * 100:.1f}",
            "wald_95_percent": f"{low * 100:.1f} – {high * 100:.1f}%",
        }
    assert len(rows) == 192
    assert {
        category: values["wald_95_percent"]
        for category, values in result.items()
    } == {
        "交換・取引": "21.8 – 34.5%",
        "中立": "18.9 – 31.1%",
        "欲望・執着": "13.2 – 24.3%",
        "喜び・満足": "11.9 – 22.5%",
        "焦り・競争": "9.1 – 19.0%",
        "不満・怒り": "3.6 – 11.0%",
        "情報共有": "0.4 – 4.9%",
    }
    return result


def run(output_dir: Path, gold_path: Path) -> dict[str, object]:
    output_dir = output_dir.resolve()
    protected = (PROJECT_ROOT / "data/output").resolve()
    if output_dir == protected or protected in output_dir.parents:
        raise ValueError(f"Refusing to write audit output under {protected}")
    output_dir.mkdir(parents=True, exist_ok=True)
    gold_path = Path(validate_normalized_gold(gold_path)["path"])

    classified = read_dicts(CLASSIFIED)
    exchange_rows = [
        row
        for row in classified
        if row["sentiment_category"] == EXCHANGE_CATEGORY
    ]
    result = {
        "input_sha256": {
            "hybrid_corpus": sha256(HYBRID_CORPUS),
            "classified": sha256(CLASSIFIED),
            "gold": sha256(gold_path),
        },
        "accounts": account_summary(exchange_rows),
        "templates": write_template_evidence(output_dir, exchange_rows),
        "negotiation": negotiation_summary(),
        "dai": dai_summary(),
        "confidence_intervals": confidence_interval_summary(gold_path),
    }
    summary_path = output_dir / "slide_number_definition_audit.json"
    summary_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result["summary_output"] = str(summary_path)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: a new temporary directory)",
    )
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="bonbon_slide_numbers_"))
    result = run(output_dir, args.gold)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PASS: all slide-number definition assertions")


if __name__ == "__main__":
    main()
