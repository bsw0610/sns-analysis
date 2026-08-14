# Regenerating and Verifying Slide 13–16 PNG Assets

> **Provenance.** The Bonbon Drop presentation itself was produced by the
> four-person seminar team, and this document does not claim authorship of it.
> What is recorded here is the later individual follow-up: auditing the metrics
> quoted on these slides, correcting the calculation definitions, and
> regenerating the analytical assets from validated data.

## Purpose

`regenerate_slide_assets.py` regenerates the data visuals required for slides
13–16 of the Canva “ボンドロ最終発表” slide 10–16 replacement plan from the
same fixed inputs.

The generated files are candidates only. The script does not automatically
replace existing repository PNGs, Canva assets, or PPTX content, and it accepts
only output directories outside the repository.

## Fixed Inputs

| Purpose | File | SHA-256 |
|---|---|---|
| Source Gold Standard | `data/output/gold_standard_192.csv` | `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815` |
| Normalized Gold Standard | `data/output/gold_standard_192_normalized.csv` | `ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c` |
| Hybrid corpus | `data/output/2511-2604_hybrid.csv` | `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e` |
| Classification output | `data/output/sentiment_classified_hybrid.csv` | `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d` |

The fixed 98-record sample for slide 16 is the post-ID-deduplicated union of
these two files. Their actual SHA values are recorded in `p16_metrics.json` and
the manifest, then checked again during verification.

- `outputs/negotiation-unclassified-20260728/negotiation_expressions_not_exchange_random50.csv`
- `data/output/random_sample_50_negotiation_not_exchange_202511_202604.csv`

## Outputs

Each run creates the following nine files:

- `p13_agreement.png`
- `p13_metrics.json`
- `p14_composition.png`
- `p14_metrics.json`
- `p15_new_accounts.png`
- `p15_metrics.json`
- `p16_expressions.png`
- `p16_metrics.json`
- `slide_assets_manifest.json`

Every PNG is 1920×1080. The metrics JSON files retain calculated values,
denominators, definitions, display strings, and input hashes. The manifest
records the hashes of each PNG and JSON file together with render-check results.

## Calculations by Slide

### Slide 13

`evaluate_v2_hybrid_192.calculate_evaluation_metrics()` calculates lenient
per-category F1 for all seven categories on the authoritative 192-record set.
The visualization emphasizes 交換・取引 at 0.869 and secondarily emphasizes 中立
at 0.625. It does not hide 情報共有 at 0.000. Lenient micro F1 of 0.577 and
multi-label micro F1 of 0.595 are shown as supporting values.

### Slide 14

Each category in the authoritative 192 records is treated as an independent
binary proportion. Wald 95% intervals with `z=1.96` are calculated using
`slide_number_definitions.wald_interval()`. The same evidence JSON stores the
217 total labels, the 113.0% combined share, and the classifier's 焦り・競争
count of 3,272/110,918 = 2.9%. The PNG includes a note about ad-removal bias for
情報共有.

### Slide 15

The 24,316 `交換・取引` rows in the classification output are aggregated by
`ユーザーID`. The displayed KPIs are 24,316 posts, 10,677 accounts, 7,198
one-time accounts / 67.4%, and 3,619 posts / 14.9% from the top 106 accounts
(top 1%). The 51.0% structured-format share is not used as a slide 15 KPI; it
is moved to slide 16.

### Slide 16

`slide_number_definitions.is_exchange_template()` identifies 12,411 structured
exchange-format posts, or 51.0% of exchange posts. Shared definition functions
calculate the following values from the fixed 98-record sample: 79 replies, 48
formulaic greetings, 42 `ご検討／御検討` instances, and 17 exchange ratios.

The two source-text examples are not displayed. `p16_metrics.json` alone retains
their exact-match evidence against contiguous strings in the fixed sample and
the basis for anonymization.

## Generation

If `--output-dir` is omitted, `tempfile.mkdtemp()` creates a new temporary
directory.

```bash
python3 regenerate_slide_assets.py
```

To use an explicit temporary directory:

```bash
python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slides_10_16_rework_run1
```

The script stops if `--output-dir` points inside the repository, preventing an
accidental overwrite of existing PNGs.

## Verification

Run the verifier on one output directory:

```bash
python3 verify_slide_assets.py \
  --assets-dir /private/tmp/bonbon_slides_10_16_rework_run1
```

Verify reproducibility across two runs:

```bash
python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slides_10_16_rework_run2

python3 verify_slide_assets.py \
  --assets-dir /private/tmp/bonbon_slides_10_16_rework_run1 \
  --comparison-dir /private/tmp/bonbon_slides_10_16_rework_run2
```

Verification covers:

- 192×12 Gold Standard shape, 192 unique IDs, and a 192/192 join to the
  classification output
- Exact equality of every cell in the source file's first 12 columns and
  preservation of the three supplemental exchange labels
- SHA-256 matches for all four fixed inputs
- Two micro F1 values and all seven category F1 values for slide 13
- Seven intervals, 217 labels, 113.0%, and 焦り・競争 at 2.9% for slide 14
- All 12 slide 15 metrics
- Seven slide 16 values and source evidence for two anonymized quotations
- PNG format, 1920×1080 dimensions, nonempty output, and content width of at
  least 1,720 px
- 0 missing Japanese glyphs and 0 text elements outside the canvas
- Manifest hashes for every PNG and JSON file
- Exact SHA matches for all nine files in the two output directories

Additional regression checks:

```bash
python3 verify_slide_numbers.py \
  --output /private/tmp/slide_numbers_check_after.md

python3 -m unittest -v \
  test_slide_number_definitions.py test_sentiment_classifier.py

ruff check \
  regenerate_slide_assets.py verify_slide_assets.py \
  slide_number_definitions.py verify_slide_numbers.py \
  test_slide_number_definitions.py test_sentiment_classifier.py

git diff --check
```

After generation, open the slide 13–16 PNG files and visually inspect titles,
values, axes, notes, quotations, margins, wrapping, and overlaps before using
them as replacement candidates in Canva.
