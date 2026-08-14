# Hybrid Corpus Baseline Evaluation (Gold 192)

**Evaluation date**: 2026-07-30

**Gold dataset**: `data/output/gold_standard_192_normalized.csv` (189 rows + 3 supplemental rows; multi-label)

**Predictions**: `data/output/sentiment_classified_hybrid.csv` (SHA-256 `f273c9306507804a`, v2.0.0, **unchanged**)

**Evaluation script**: `evaluate_v2_hybrid_192.py`

---

## 0. Evaluation Conditions

- Gold rows: 192 / matched predictions: **192** (0 missing)
- Deferred rows (`要検討=1`): 0 (the original 11 were already excluded from the 189-row dataset)
- Threshold: `MIN_PRIMARY_SCORE = 1.8` (unchanged from v2)

### Gold-label distribution (192 rows)

The Japanese category names are preserved because they are dataset labels.

| Category | Gold count | Share |
|---|---:|---:|
| 交換・取引 | 54 | 28.1% |
| 中立 | 48 | 25.0% |
| 欲望・執着 | 36 | 18.8% |
| 喜び・満足 | 33 | 17.2% |
| 焦り・競争 | 27 | 14.1% |
| 不満・怒り | 14 | 7.3% |
| 情報共有 | 5 | 2.6% |
| **Total assigned labels** | **217** | |

Labels per post:

- 0 labels (= `中立`): 48 rows
- 1 label: 120 rows
- 2 labels: 23 rows
- 3 labels: 1 row

---

## 1. Criterion 2: Multi-label Evaluation

The prediction set contains every category whose `category_scores` value is at least 1.8. An empty set is treated as `中立`.

### Multi-label results

| Category | Gold | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 不満・怒り | 14 | 32 | 10 | 22 | 4 | 0.312 | 0.714 | **0.435** |
| 焦り・競争 | 27 | 7 | 5 | 2 | 22 | 0.714 | 0.185 | **0.294** |
| 交換・取引 | 54 | 46 | 43 | 3 | 11 | 0.935 | 0.796 | **0.860** |
| 欲望・執着 | 36 | 30 | 15 | 15 | 21 | 0.500 | 0.417 | **0.455** |
| 喜び・満足 | 33 | 42 | 23 | 19 | 10 | 0.548 | 0.697 | **0.613** |
| 情報共有 | 5 | 6 | 1 | 5 | 4 | 0.167 | 0.200 | **0.182** |
| 中立 | 48 | 64 | 35 | 29 | 13 | 0.547 | 0.729 | **0.625** |
| **Micro average** | 217 | 227 | 132 | 95 | 85 | 0.581 | 0.608 | **0.595** |
| **Macro average** | | | | | | 0.532 | 0.534 | **0.495** |

**Exact prediction-set match: 103/192 = 0.536**

---

## 2. Criterion 1: Lenient Primary-label Evaluation

A prediction is counted as correct when the single v2 primary label is included in the Gold label set.

### Lenient results

| Category | Gold | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 不満・怒り | 14 | 20 | 8 | 12 | 6 | 0.400 | 0.571 | **0.471** |
| 焦り・競争 | 27 | 7 | 5 | 2 | 22 | 0.714 | 0.185 | **0.294** |
| 交換・取引 | 54 | 45 | 43 | 2 | 11 | 0.956 | 0.796 | **0.869** |
| 欲望・執着 | 36 | 23 | 11 | 12 | 25 | 0.478 | 0.306 | **0.373** |
| 喜び・満足 | 33 | 29 | 16 | 13 | 17 | 0.552 | 0.485 | **0.516** |
| 情報共有 | 5 | 4 | 0 | 4 | 5 | 0.000 | 0.000 | **0.000** |
| 中立 | 48 | 64 | 35 | 29 | 13 | 0.547 | 0.729 | **0.625** |
| **Micro average** | 217 | 192 | 118 | 74 | 99 | 0.615 | 0.544 | **0.577** |
| **Macro average** | | | | | | 0.521 | 0.439 | **0.450** |

**Lenient hit rate: 118/192 = 0.615** (95% CI 0.546–0.683)

---

## 3. Difference from the 189-row Evaluation

| Metric | 189 rows | 192 rows | Difference |
|---|---:|---:|---:|
| Lenient micro F1 | 0.576 | 0.577 | +0.001 |
| Lenient macro F1 | 0.451 | 0.450 | -0.001 |
| Multi-label micro F1 | 0.594 | 0.595 | +0.001 |
| Multi-label macro F1 | 0.496 | 0.495 | -0.001 |

Each of the three supplemental rows has only `交換・取引` as its Gold label, and v2 predicts `交換・取引` for all three. The only change is therefore TP +3 for `交換・取引`; the values for every other category remain identical to the 189-row evaluation.

Predictions for the existing 189 rows differ by **0 rows** between the old and hybrid corpora. The v2 classifier is deterministic.

---

## 4. Recalculation of the Composition and Confidence Intervals in Specification Section 2-3

| Category | Measured share | Specification 2-3 | 95% CI (normal approximation) | Specification 2-3 | Result |
|---|---:|---:|---|---|---|
| 交換・取引 | 28.1% | 28.1% | 21.8 – 34.5% | 21.8 – 34.5% | ✓ |
| 中立 | 25.0% | 25.0% | 18.9 – 31.1% | 18.9 – 31.1% | ✓ |
| 欲望・執着 | 18.8% | 18.8% | 13.2 – 24.3% | 13.2 – 24.3% | ✓ |
| 喜び・満足 | 17.2% | 17.2% | 11.9 – 22.5% | 11.9 – 22.5% | ✓ |
| 焦り・競争 | 14.1% | 14.1% | 9.1 – 19.0% | 9.1 – 19.0% | ✓ |
| 不満・怒り | 7.3% | 7.3% | 3.6 – 11.0% | 3.6 – 11.0% | ✓ |
| 情報共有 | 2.6% | 2.6% | 0.4 – 4.9% | 0.4 – 4.9% | ✓ |

**Result: every value in Section 2-3 was reproduced.**
