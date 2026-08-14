# Reproducing the Final Hybrid Baseline

This document fixes the procedure for rebuilding the final hybrid corpus and the v2.0.0 classification output from the November 2025 through April 2026 monthly exports. The procedure verifies rebuilt outputs without overwriting the preserved baseline files.

## Inputs and Baseline Files

Rebuild inputs:

- `202511.csv` through `202604.csv`: six monthly source exports
- `filter_ads_202511_202604.py`: preserved keyword and additional-advertising filters
- `baselines/hybrid_final_exclusions.csv`: an ID lock for 391 final-filter decisions whose source implementation is missing
- `classify_sns_rule_based.py`: unchanged v2.0.0 classifier
- `data/output/gold_standard_192.csv`: source Gold dataset whose human labels must be preserved
- `data/output/gold_supplement_11.csv`: provenance for the supplemental sample IDs

Read-only comparison baselines:

- `data/output/2511-2604_hybrid.csv`
  - SHA-256:
    `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e`
- `data/output/sentiment_classified_hybrid.csv`
  - SHA-256:
    `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d`
- `data/output/gold_standard_192.csv`
  - SHA-256:
    `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815`

The build and normalization scripts stop if asked to write to any of these baseline paths. Rebuilt files are written only to `/private/tmp/bonbon_rebuild/` and then compared with the baselines.

## Evidence for the Reconstructed Hybrid Selection Rules

All 136,288 rows in the monthly exports have unique `投稿ID_文字列` values. The old, final, and hybrid datasets all preserve the source order. Comparing the actual ID sets establishes the following relationships:

- preserved advertising-filter result (old): 109,037 rows
- `final − old`: 5,615 rows
- `old − final`: 134 rows
- existing additional-advertising IDs: 5,874
- `additional ∩ final`: 3,600
- `hybrid = final − additional`: 110,918 rows, with identical order
- `hybrid − old`: 2,015 rows

A row-by-row comparison with the preserved keyword filter divides the 2,015 rows restored by hybrid into exactly three cases:

- rows matched only by the expanded `第弾` keyword rule: 2,002
- rows matched only by the expanded `本日…抽選開始…ラインナップ` rule: 12
- a half-width string that becomes `リポスト` only after NFKC normalization: 1

The repository does not contain the filter version that created `2511-2604_final.csv`. The missing rules were therefore not guessed and reimplemented as regular expressions. Instead, the following 391 decisions established from the actual ID differences are locked in `baselines/hybrid_final_exclusions.csv`:

- relaxation candidates that were still excluded from final: 257 IDs
- IDs retained by old but newly excluded from final: 134 IDs

The final rebuild produces these mutually exclusive selection counts:

- excluded by existing keywords: 19,105
- relaxation candidates excluded by the ID lock: 257
- excluded by the existing additional-advertising classification: 5,874
- excluded by the final-only ID lock: 134
- retained: 110,918

The first two exclusions total 19,362, matching the “final keyword exclusions” recorded in the existing documentation. The build script checks every selection count and each reason count in the lock file. It refuses to write output if any value differs.

## Normalizing the Gold Dataset to 12 Columns

The baseline `gold_standard_192.csv` has 20 CSV columns. The first 12 are meaningful, while all values in the eight unnamed trailing columns are empty.

`normalize_gold_standard_192.py` copies the first 12 columns only when all of the following conditions hold:

- 192 rows
- the expected 12 column names and order
- empty names and values for all eight trailing columns
- no duplicate `post_id`

The three supplemental IDs are:

- `ID:2013861610389966862`
- `ID:2015459135006126271`
- `ID:2046838197989282094`

The human labels for these IDs are empty in `gold_supplement_11.csv`, but all three rows have `交換取引=1` in the current `gold_standard_192.csv` baseline. No separate evidence identifying when or by whom these labels were assigned was found in the repository.

The normalization script does not recreate labels from the supplemental file. It preserves the 12 values already present in the baseline Gold dataset. The older `make_task5_task6_files.py` writes the three supplemental rows with empty labels and is therefore not used in this normalization procedure.

## Execution

Run the following commands from the repository root with the specified Python interpreter.

```bash
python3 build_hybrid_corpus.py \
  --output /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv

python3 classify_sns_rule_based.py \
  --input /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv \
  --output /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv

python3 normalize_gold_standard_192.py \
  --input data/output/gold_standard_192.csv \
  --output /private/tmp/bonbon_rebuild/gold_standard_192_normalized.csv \
  --supplement data/output/gold_supplement_11.csv \
  --hybrid /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv

python3 verify_hybrid_rebuild.py \
  --rebuild-dir /private/tmp/bonbon_rebuild
```

The verifier compares row counts, columns, every cell, ID sets, ID order, and full SHA-256 hashes for the rebuilt corpus and classification output. It also checks:

- 192 rows × 12 columns in the normalized Gold dataset
- unique IDs
- a 192/192 join with predictions
- `交換取引=1` for the three supplemental rows
- preservation of all existing human labels

Finally, it reruns the complete process in a separate `repeat/` directory and verifies that the SHA-256 values of all three outputs match the first run.

The fixed SHA-256 for the normalized output is:

`ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c`
