# Audit of Presentation Metrics and Page 15 Calculation Definitions

Audit date: 2026-07-30

This document resolves the 10 discrepancies previously reported by
`verify_slide_numbers.py` and fixes the calculation definitions used on page 15.
The reference corpus, classification results, Gold Standard labels, and
classification rules were not changed. Sample files containing post text are
created only in `/private/tmp/bonbon_slide_numbers/`, outside the repository.

The Gold Standard files have the following roles:

- `data/output/gold_standard_192.csv`: unchanged 20-column source archive
- `data/output/gold_standard_192_normalized.csv`: authoritative input for
  evaluation, metric verification, and presentation assets
- The normalized file is derived from the source while preserving every cell in
  its first 12 columns. The default evaluation path does not silently fall back
  to the source file. Processing stops with an error that includes the generation
  command if the normalized file is missing or fails any of the following checks:
  12 columns, 192 rows, equality with the source, supplemental labels, and a
  192/192 join.

## Reference Inputs

- `data/output/2511-2604_hybrid.csv`
  - 110,918 rows
  - SHA-256:
    `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e`
- `data/output/sentiment_classified_hybrid.csv`
  - 110,918 rows
  - SHA-256:
    `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d`
- `data/output/gold_standard_192_normalized.csv`
  - 192 rows × 12 columns
  - SHA-256:
    `ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c`

## Root-Cause Analysis of the 10 Discrepancies

“Pre-fix result” refers to the output of `verify_slide_numbers.py` at the
beginning of this audit. Difference = pre-fix result − specification value.

| # | Metric | Specification | Pre-fix result | Difference | Input | Pre-fix rule | Numerator / denominator | Rounding | Root cause and evidence | Adopted value |
|---:|---|---:|---:|---:|---|---|---|---|---|---:|
| 1 | Over-removal by `第弾` | 2,002 | 1,042 | -960 | Six monthly CSVs, `2511-2604_final.csv`, `2511-2604.csv` | After NFKC, remove only Arabic numerals and search for the `第弾` substring | 2,002 / `final-old` 5,615 | None | **Calculation-definition error.** The actual ad filter accepts both Arabic and Japanese numerals. Using the filter's actual `keyword_matches(text)==["第弾"]` condition returns 2,002. | 2,002 |
| 2 | 交換・取引 95% CI | 21.7–34.5% | 21.8–34.5% | lower bound +0.1%p | Normalized Gold Standard | Wald: `p ± 1.96√(p(1-p)/n)` | 54 / 192 | Percentage `.1f` | **Specification typo/rounding mismatch.** The unrounded lower bound is 21.765241…%. | 21.8–34.5% |
| 3 | 喜び・満足 95% CI | 11.8–22.5% | 11.9–22.5% | lower bound +0.1%p | Normalized Gold Standard | Same as above | 33 / 192 | Percentage `.1f` | **Specification typo/rounding mismatch.** The unrounded lower bound is 11.850960…%. | 11.9–22.5% |
| 4 | 焦り・競争 95% CI | 9.2–19.0% | 9.1–19.0% | lower bound -0.1%p | Normalized Gold Standard | Same as above | 27 / 192 | Percentage `.1f` | **Specification typo/rounding mismatch.** The unrounded lower bound is 9.145184…%. | 9.1–19.0% |
| 5 | 情報共有 95% CI | 0.4–4.8% | 0.4–4.9% | upper bound +0.1%p | Normalized Gold Standard | Same as above | 5 / 192 | Percentage `.1f` | **Specification typo/rounding mismatch.** The unrounded upper bound is 4.856901…%. | 0.4–4.9% |
| 6 | Structured exchange-format count | 12,181 | 12,298 | +117 | `交換・取引` rows in the final classification output | Allow whitespace and `〈〉/《》`; exclude square brackets | 12,298 / 24,316 | None | **Definition mismatch with no supporting rule in the specification.** A literal implementation of the specification returns 12,099; the verifier returns 12,298; and the page 15 generator returns 12,411. No rule in the repository produces 12,181. | 12,411 |
| 7 | Structured exchange-format share | 50.1% | 50.6% | +0.5%p | Same as above | Same as above | 12,298 / 24,316 | One decimal place | **Derived mismatch from the count definition.** The shared definition returns 12,411 / 24,316 = 51.040467…%. | 51.0% |
| 8 | Reply count | 79 | 80 | +1 | Two negotiation-expression CSVs | Reply metadata or leading `@` | 80 / 98 deduplicated IDs | None | **String-rule error.** The additional row was a plain mention with no reply metadata. A platform reply is limited to rows where `リプライ先の投稿ID` is not empty. | 79 |
| 9 | “ご検討” count | 42 | 41 | -1 | Two negotiation-expression CSVs | `ご検討` | 41 / 98 deduplicated IDs | None | **Missing orthographic variant.** One `御検討` instance was confirmed. Count both honorific forms with `(?:ご\|御)検討`. | 42 |
| 10 | Exchange ratio `n:m` count | 18 | 17 | -1 | Two negotiation-expression CSVs | `\d\s*[:：]\s*\d` | 17 / 98 deduplicated IDs | None | **Specification aggregation error.** The source has 100 rows and two duplicate IDs; both duplicate posts contain a ratio. There are 19 raw occurrences and 17 after exact deduplication, so no consistent deduplication method produces 18. | 17 |

## Page 15 Definition Comparison and Adopted Values

### Share of Top Accounts

The account key is `ユーザーID`, which does not change during the period. The
denominator is 24,316 `交換・取引` posts.

| Implementation | Top 1% account count | Post numerator | Unrounded share | One decimal place |
|---|---:|---:|---:|---:|
| `floor(10,677×0.01)` | 106 | 3,619 | 14.883204…% | **14.9%** |
| `round(10,677×0.01)` | 107 | 3,638 | 14.961342…% | 15.0% |

`floor` was adopted to represent the largest whole number of accounts that does
not exceed 1%. The same definition gives 1,067 accounts and
11,082/24,316 = 45.6% for the top 10%.

### Structured Exchange Format

| Implementation | Whitespace | `〈〉/《》` | `[]/［］` | Count | Share |
|---|---|---|---|---:|---:|
| Literal implementation of the specification wording | Not allowed | Allowed | Excluded | 12,099 | 49.8% |
| Pre-fix `verify_slide_numbers.py` | `\s*` | Allowed | Excluded | 12,298 | 50.6% |
| Pre-fix `make_task3_exchange_accounts.py` and final adopted rule | `\s*` | Allowed | Allowed for `譲/求` | **12,411** | **51.0%** |

The final regular expression is defined only once, in
`slide_number_definitions.py`.

```regex
【\s*(?:交換|譲|求)\s*】|[〈《\[［]\s*(?:譲|求)\s*[〉》\]］]|(?:譲|求)\s*[)）：:]
```

The inclusion criteria are:

| Expression | Inclusion criterion |
|---|---|
| `求`, `譲` | Count as a structured format only when enclosed in an allowed bracket pair or followed by a closing bracket or colon. |
| `交換` | Count as a structured format only in the `【交換】` pattern family. |
| `郵送`, `手渡し` | Describe transaction methods and do not independently increase the structured-format or negotiation-expression counts. |
| Separators and line breaks | Allow `【】`, `〈〉`, `《》`, `[]`, `［］`, `)`, `）`, `:`, and `：`. Allow internal spaces, full-width spaces, tabs, and line breaks through `\s*`. |
| Reply | Include only when `リプライ先の投稿ID` is not empty. A leading `@` alone is insufficient. |
| “ご検討” | Include both variants defined by `(?:ご\|御)検討`. |
| Exchange ratio | After ID deduplication, include posts matching `\d\s*[:：]\s*\d`. |
| Negotiation-expression sample | Fix the union of IDs from the two existing 50-row files at 98 records. The currently reproducible extractor uses narrow expressions such as `求めて…`, requests or offers for exchange, transaction availability or intent, `郵送…希望`, and requests for consideration. It does not use standalone `求/譲/交換/手渡し`. |

## ID Differences and Sample Review

`audit_slide_number_definitions.py` creates the following temporary evidence
files:

- `template_definition_id_differences.csv`: 312 IDs on which the rules differ
  - 199 whitespace variants
  - 113 square-bracket variants
- `template_definition_review_sample_40.csv`: fixed seed `20260730`
  - 20 whitespace variants
  - 20 square-bracket variants

Manual review of the text and matching fragments found that 40/40 were structured
exchange posts using `譲/求` fields, with 0 false positives. The sample contained
18 `郵送` posts and 19 `手渡し` posts, but every post was already included by the
bracket or separator rule; none was included because of a delivery-method word.

Boundary cases for the qualitative metrics were also reviewed:

- One post with a leading `@` but no reply metadata:
  `ID:2010721471329706079` — excluded from replies because it recruits a partner
  for a simple information exchange
- One `御検討` variant:
  `ID:2029913067061137884` — included in the “ご検討” metric
- Duplicate IDs in the two sample files:
  `ID:2036404178151678416` and `ID:2047577298866704791` — both contain `n:m`,
  giving 19 raw occurrences and 17 unique IDs

## Confidence-Interval Definition

- Method: Wald normal approximation
- Confidence level: 95%
- Parameter: `z=1.96`
- Sample size: 192 records in the normalized Gold Standard
- Multi-label treatment: calculate each category as a separate binary variable;
  one post may contribute to multiple numerators
- Rounding: calculate the interval, convert to a percentage, and display one
  decimal place with Python `.1f`

| Category | Numerator / denominator | Final 95% CI |
|---|---:|---:|
| 交換・取引 | 54 / 192 | 21.8–34.5% |
| 中立 | 48 / 192 | 18.9–31.1% |
| 欲望・執着 | 36 / 192 | 13.2–24.3% |
| 喜び・満足 | 33 / 192 | 11.9–22.5% |
| 焦り・競争 | 27 / 192 | 9.1–19.0% |
| 不満・怒り | 14 / 192 | 3.6–11.0% |
| 情報共有 | 5 / 192 | 0.4–4.9% |

The Wald method has limitations, especially for sparse proportions such as
5/192. This audit does not replace it with Wilson intervals or bootstrap
intervals because the existing evaluation code and the page 13 calculation both
use Wald intervals. It documents and aligns the calculation and display rules.

## Execution and Automated Verification

```bash
/opt/anaconda3/bin/python3 normalize_gold_standard_192.py \
  --input data/output/gold_standard_192.csv \
  --output data/output/gold_standard_192_normalized.csv

/opt/anaconda3/bin/python3 audit_slide_number_definitions.py \
  --output-dir /private/tmp/bonbon_slide_numbers/run1 \
  --gold data/output/gold_standard_192_normalized.csv

/opt/anaconda3/bin/python3 verify_slide_numbers.py \
  --output /private/tmp/bonbon_slide_numbers/slide_numbers_check_after.md

/opt/anaconda3/bin/python3 make_task3_exchange_accounts.py \
  --input data/output/sentiment_classified_hybrid.csv \
  --output-csv /private/tmp/bonbon_slide_numbers/exchange_accounts_after.csv \
  --output-png /private/tmp/bonbon_slide_numbers/p15_after.png

/opt/anaconda3/bin/python3 -m unittest -v \
  test_slide_number_definitions.py test_sentiment_classifier.py

/opt/anaconda3/bin/ruff check \
  normalize_gold_standard_192.py make_task1_task2_figures.py \
  slide_number_definitions.py audit_slide_number_definitions.py \
  make_task3_exchange_accounts.py verify_slide_numbers.py \
  evaluate_v2_hybrid_192.py test_slide_number_definitions.py
```

Verification results:

- Definition-audit assertions: all passed
- Authoritative Gold Standard: 192 rows × 12 columns, 0 duplicate IDs
- Every source cell in the first 12 columns matched; three supplemental
  `交換取引=1` labels were preserved
- Classification-to-Gold join: 192/192
- Specification metric verification: 96 matched / 0 mismatched / 0 unverifiable
- When the normalized file is missing, processing stops with the generation
  command instead of falling back to the source
- SHA-256 of the pre-translation `docs/slide_numbers_check.md` artifact was
  unchanged before and after the default metric-verification rerun:
  `e4f500d1ef133067b3ab17849208bf09f382698e43503d4f250386d47754c2bf`
- Page 15 generator self-check: all 12 metrics matched
- Unit and classifier regression tests: 7 passed
- Ruff: 0 errors
- SHA-256 of temporary `exchange_accounts_after.csv`:
  `f3f49ccf04b8ad3213310b654954f5fea451dfddd9ac7518a2b47808807075c6`
- SHA-256 matched the existing `data/output/exchange_accounts.csv`
- Audit artifacts generated in two different temporary directories had
  identical SHA-256 values:
  - JSON:
    `9b979ee26097a9611be10f46b7fcec6a4ea422e4b421f5d76fabc98f30c1ccca`
  - 312-ID difference set:
    `5850f4f6439ce8fc788a850763cc2da998dd087fd1ffae9db0cc332f21e0f199`
  - 40-record review sample:
    `24c0af75f71f4e1b5bb6d5aeddb844bf8a94a657fe24bab414fae3bb7d1b7f61`

## Presentation-Document Replacements

The following values were replaced in `docs/slide_plan_10-16.md`:

- 交換・取引 CI: 21.7–34.5% → **21.8–34.5%**
- 喜び・満足 CI: 11.8–22.5% → **11.9–22.5%**
- 焦り・競争 CI: 9.2–19.0% → **9.1–19.0%**
- 情報共有 CI: 0.4–4.8% → **0.4–4.9%**
- Structured format: 12,181 / 50.1% → **12,411 / 51.0%**
- Exchange ratio `n:m`: 18 → **17**

The specification values for 2,002 `第弾` removals, 79 replies, and 42
“ご検討” posts were already correct, so only the verification rules were fixed.
The top 1% value of 14.9% was also retained, and the generator's account-count
rounding was standardized on `floor`.

## Remaining Limitations

- The repository contains neither the code nor the ID set that originally
  produced 12,181. No new regular expression was guessed merely to reproduce it.
- The final structured-format count of 12,411 is an operational definition, not
  a manually labeled census of all 12,411 records. Only a fixed sample of 40 from
  the 312 rule differences was manually reviewed.
- The source code that created the first 50-row negotiation-expression file
  could not be found in the repository. This audit fixes the 98 unique IDs in the
  two existing files as a qualitative sample; it does not regenerate the sample.
