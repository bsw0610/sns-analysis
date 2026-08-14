# v2 Classifier Baseline Evaluation

**Evaluation date**: 2026-07-28

**Gold dataset**: `data/output/gold_standard_labeled_189of200.csv` (human labels; multi-label 0/1 columns)

**Predictions**: `data/output/sentiment_classified_2511-2604.csv` (output from `classify_sns_rule_based.py` v2.0.0, **unchanged**)

**Evaluation script**: `evaluate_v2_against_gold.py`

> **Historical status:** this is the 189-row evaluation from 2026-07-28. The
> current authoritative evaluation is `docs/baseline_hybrid.md`, based on Gold
> 192. Interpretive wording such as “near operational quality” records the view
> at this stage; the current presentation does not claim a fixed operational F1
> threshold.

---

## 0. Evaluation Conditions

| Item | Value |
|---|---|
| Sampling frame | 109,037 rows in `sentiment_classified_2511-2604.csv` |
| Sampling method | Simple random sample: `random.Random(20260728).sample(frame, 200)` |
| Exclusions before sampling | All IDs in `random_sample_100_202511_202604.csv`; 83 were present in the frame |
| Sample size | 200 |
| **Deferred: `要検討=1`** | **11 rows, excluded from evaluation** |
| **Evaluated rows** | **189**, matched predictions 189/189, 0 missing |
| Threshold | `MIN_PRIMARY_SCORE = 1.8` (unchanged from v2) |

All Gold-data consistency checks passed:

- label values are `0` or `1`; only the 11 deferred rows contain empty labels
- the `中立` column equals “all six active categories are 0” for all 189 rows
- no duplicate `post_id`

### Gold-label distribution (189 rows)

The Japanese category names are preserved because they are dataset labels.

| Category | Gold count | Share |
|---|---:|---:|
| 交換・取引 | 51 | 27.0% |
| 中立 | 48 | 25.4% |
| 欲望・執着 | 36 | 19.0% |
| 喜び・満足 | 33 | 17.5% |
| 焦り・競争 | 27 | 14.3% |
| 不満・怒り | 14 | 7.4% |
| 情報共有 | 5 | 2.6% |
| **Total assigned labels** | **214** | |

Labels per post: 48 rows with 0 labels (= `中立`), 117 with 1, 23 with 2, and 1 with 3. **Multi-label rows account for 12.7%** (24/189).

> **Caution:** only five Gold rows have the `情報共有` label. The confidence interval is extremely wide, so this evaluation cannot support a definitive conclusion about that category.

---

## 1. Criterion 1: Lenient Primary-label Evaluation

v2 produces one primary label per post. Under the lenient criterion, a prediction is correct when it matches any label in the Gold set.

Precision is lenient because any Gold label can count as correct. Recall has a structural ceiling because the classifier returns only one primary label.

| Category | Gold | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 不満・怒り | 14 | 20 | 8 | 12 | 6 | 0.400 | 0.571 | **0.471** |
| 焦り・競争 | 27 | 7 | 5 | 2 | 22 | 0.714 | 0.185 | **0.294** |
| 交換・取引 | 51 | 43 | 41 | 2 | 10 | 0.953 | 0.804 | **0.872** |
| 欲望・執着 | 36 | 23 | 11 | 12 | 25 | 0.478 | 0.306 | **0.373** |
| 喜び・満足 | 33 | 29 | 16 | 13 | 17 | 0.552 | 0.485 | **0.516** |
| 情報共有 | 5 | 4 | 0 | 4 | 5 | 0.000 | 0.000 | **0.000** |
| 中立 | 48 | 63 | 35 | 28 | 13 | 0.556 | 0.729 | **0.631** |
| **Micro average** | 214 | 189 | 116 | 73 | 98 | 0.614 | 0.542 | **0.576** |
| **Macro average** | | | | | | 0.522 | 0.440 | **0.451** |

**Lenient hit rate: 116/189 = 0.614** (95% CI [0.543, 0.680])

For the 165 rows with exactly one Gold label, exact match is 103/165 = 0.624. Accuracy falls to 0.522 for the 23 rows with two Gold labels, reflecting the structural limitation of single-label output.

---

## 2. Criterion 2: Multi-label Evaluation

The prediction set contains every category whose `category_scores` value is at least 1.8. An empty prediction set is treated as `中立`.

| Category | Gold | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 不満・怒り | 14 | 32 | 10 | 22 | 4 | 0.312 | 0.714 | **0.435** |
| 焦り・競争 | 27 | 7 | 5 | 2 | 22 | 0.714 | 0.185 | **0.294** |
| 交換・取引 | 51 | 44 | 41 | 3 | 10 | 0.932 | 0.804 | **0.863** |
| 欲望・執着 | 36 | 30 | 15 | 15 | 21 | 0.500 | 0.417 | **0.455** |
| 喜び・満足 | 33 | 42 | 23 | 19 | 10 | 0.548 | 0.697 | **0.613** |
| 情報共有 | 5 | 6 | 1 | 5 | 4 | 0.167 | 0.200 | **0.182** |
| 中立 | 48 | 63 | 35 | 28 | 13 | 0.556 | 0.729 | **0.631** |
| **Micro average** | 214 | 224 | 130 | 94 | 84 | 0.580 | 0.607 | **0.594** |
| **Macro average** | | | | | | 0.533 | 0.535 | **0.496** |

**Exact prediction-set match: 101/189 = 0.534** (95% CI [0.463, 0.604])

### 2.1 Comparison of the two criteria

| Metric | Lenient | Multi-label | Difference |
|---|---:|---:|---:|
| Micro F1 | 0.576 | 0.594 | +0.018 |
| Macro F1 | 0.451 | 0.496 | +0.045 |
| Micro precision | 0.614 | 0.580 | −0.034 |
| Micro recall | 0.542 | 0.607 | +0.065 |

Switching to the multi-label criterion increases recall by +0.065 and decreases precision by −0.034.

- **喜び・満足**: F1 0.516 → 0.613; recall 0.485 → 0.697. Signals that lost to another primary category are recovered.
- **欲望・執着**: F1 0.373 → 0.455; recall 0.306 → 0.417.
- **不満・怒り**: recall 0.571 → 0.714, but precision 0.400 → 0.312 and F1 **falls from 0.471 to 0.435**. Many posts with a dissatisfaction score above 1.8 are not labeled as dissatisfaction in Gold.
- **焦り・競争 / 中立**: no change. Only seven posts exceed the urgency threshold, so multi-label output does not recover additional cases.

**Conclusion:** multi-label output recovers some suppressed category scores, but the missing `焦り・競争` and `情報共有` cases are caused by missing rules rather than the threshold. Multi-label output alone does not fix them.

---

## 3. Category-level Findings

### 3.1 交換・取引: the only category near operational quality (F1 0.87)

Precision is 0.953 (95% CI [0.845, 0.987]); 41 of 43 predictions are correct. The relatively strong weighting of `exchange_header` at 3.0 and `structured_pair` at 2.2 contributes to this result.

There are still 10 false negatives. The Gold data includes direct examples of the `\b交換\b` issue identified in the audit:

```text
gold=[交換・取引]  pred=中立(score 0.00)
「@m0jsm スタンダードとボンドロキティ交換していただくこと可能でしょうか？」
```

`と交換して` does not satisfy `\b`, and it does not match `交換して(?:ください|下さい)`, so the post receives score 0 and falls into `中立`.

```text
gold=[交換・取引]  pred=中立(score 0.00)
「…定価でまとめて買い取ってくれる方いないですか」
```

`買取|買い取り` does not match `買い取って`.

### 3.2 焦り・競争: the largest weakness (recall 0.185)

Only **5 of 27** Gold rows are recovered (95% CI [0.082, 0.367]). The other 22 receive these primary labels:

| v2 label | Count |
|---|---:|
| 不満・怒り | 9 |
| 中立 | 5 |
| 喜び・満足 | 5 |
| 欲望・執着 | 2 |
| 情報共有 | 1 |

`焦り・競争` is the third-largest Gold category at 14.3%, while v2 assigns it to only 3.0% of the complete corpus. The audit estimated that multi-label counting would increase this category by 1.74×; in the Gold dataset, the effective gap is 4.8×.

Recall remains 0.185 under multi-label evaluation. This confirms that the cause is missing rules, not only the threshold.

False-negative examples:

```text
gold=[焦り・競争]  pred=中立(0.00)
「しまむら、シール見えました！ しまむら並び始めました！！ いつメンです！ 朝早くから大変だなー。」
   -> 「並び始めました」 does not match `並んで|並ぶ`

gold=[不満・怒り, 焦り・競争]  pred=中立(0.00)
「だめだボンボンドロップシール 全く無い。。アベイルとか行こうかな」

gold=[焦り・競争]  pred=中立(0.00)
「…出会ったらどんな絵柄でもとりあえず買う人が多くて品薄なんだと思う。落ち着くまで…」
   -> 「品薄」 is not in the dictionary
```

### 3.3 情報共有: zero true positives under the lenient criterion

The five Gold rows and four predictions do not overlap under the lenient criterion: P=R=F1=0.000. The multi-label criterion recovers one row.

| Gold | v2 prediction | Post excerpt |
|---|---|---|
| 情報共有 | 中立(0.00) | ヘルムさんが…ねこきんぎょさんの店舗を借りてやってるみたいです |
| 情報共有 | 中立(0.00) | 3️⃣新宿ドンキ ぷくぷくシール？…少しありました |
| 情報共有 | 中立(0.45) | ＼ボンドロ**新作情報**が発表❣／…新シール22種が発表されました |
| 情報共有+喜び満足 | 喜び・満足(2.35) | …**入荷** セリア ダイソー ドンキ |
| 情報共有 | 中立(1.50) | ボンボンドロップシール、どこにも売ってません。現場からは以上です |

All four primary `情報共有` predictions are false positives and are labeled as `喜び・満足` or `欲望・執着` in Gold:

```text
gold=[喜び・満足]  pred=情報共有  「Amazonで…定価で再入荷して、迷わずポチっちゃった！」
gold=[喜び・満足]  pred=情報共有  「昨日のボンドロ再入荷に出遅れたけれど今日は…出会えた嬉しい🩶」
gold=[欲望・執着]  pred=情報共有  「釧路で…の目撃情報ないですかー？」
```

Expressions such as `再入荷` and `目撃情報` trigger the category based on word presence rather than the speaker's intent. A post about successfully buying a restocked product is a joy post, not necessarily inventory information.

> The category has only n=5 and a 95% CI of [0.036, 0.624]. Its performance is therefore **indeterminate in this evaluation**. A dedicated additional sample is required.

### 3.4 中立: 28 of 63 predictions are incorrect (44.4%)

| Direction | Count |
|---|---:|
| v2=`中立`, Gold is active (**false neutral**) | **28** |
| v2 is active, Gold=`中立` (false positive) | 13 |

The 28 false-neutral rows have these Gold labels, counted with overlap: `欲望・執着` 8, `交換・取引` 7, `焦り・競争` 5, `情報共有` 4, `喜び・満足` 4, and `不満・怒り` 3.

Of these rows, **18 have score 0.00**, meaning that no rule fires. The remaining 10 have a score between 0 and 1.8 and do not reach the threshold.

> Audit Section 1 estimated a 64% error rate from a 50-row neutral sample. The Gold data measures **44.4%**. The audit estimate was too high, although more than four in ten v2 neutral predictions are still incorrect. A rough estimate of the effective neutral share is 41.4% × 0.556 ≈ **23%**.

Examples of score-0.00 false-neutral posts:

```text
gold=[欲望・執着]  「プリティーシリーズのボンボンドロップシール出して〜〜〜〜〜〜〜」
gold=[欲望・執着]  「嵐のツアーグッズでボンドロ出ないかな〜」
gold=[欲望・執着]  「@seal_ya_san ボンドロ シナモロール♡ ご縁がありますように」
gold=[喜び・満足]  「ボンボンドロップシールを手に入れてしまった…🤭🤍」
gold=[喜び・満足]  「…ハチワレのボンドロを貼ることに成功 別にいいよ〜って感じなの神」
gold=[不満+焦り]   「…今の状況辛すぎる…出会えたら奇跡みたいになってる」
```

The rules omit indirect desire expressions such as `出して〜`, `出ないかな`, and `ますように`, as well as alternative expressions of achievement such as `手に入れてしまった` and `成功`.

---

## 4. Validating and Correcting Claims from the Audit

### 4.1 Correction: restoring the documented priority does not improve accuracy

Audit Section 2 marked the missing priority behavior from Guide Section 6 as P0. Testing the change against Gold shows that **it does not improve accuracy**.

Of the 189 rows, 31 exceed the threshold for at least two categories, and 15 would change under the documented priority:

| Outcome | Count |
|---|---:|
| Priority makes the row correct (v2 incorrect → documented priority correct) | 3 |
| Priority makes the row incorrect (v2 correct → documented priority incorrect) | 4 |
| Correct under both | 1 |
| Incorrect under both | 7 |

The net effect is −1 row. Priority reversals mainly promote `不満・怒り`, but only 14 Gold rows have that label and the category is already overpredicted, with 12–22 false positives.

The issue remains a mismatch between documentation and implementation, but it should be reduced from P0 to P2 as an accuracy fix. The changed subset is only n=15, so this conclusion is also uncertain.

### 4.2 Correction: the confidence label is informative

Audit Section 4.3 questioned assigning medium confidence to neutral posts with no evidence. In the Gold data, confidence is monotonic with accuracy:

| Confidence | Rows | Lenient accuracy |
|---|---:|---:|
| High | 44 | **0.886** |
| Medium | 119 | 0.597 |
| Low | 26 | **0.231** |

The design remains unintuitive for score-zero neutral rows, but confidence is useful as a selection signal. Restricting use to high-confidence rows gives 0.886 accuracy. The audit claim is withdrawn.

### 4.3 Confirmation: v2 is not significantly better than v1

| Classifier | Lenient hits | 95% CI |
|---|---:|---|
| v2 (current) | 116/189 = **0.614** | [0.543, 0.680] |
| v1 (legacy) | 111/189 = **0.587** | [0.516, 0.655] |

The difference is +2.7 percentage points. An exact McNemar/binomial test with 26 v2-only correct rows and 21 v1-only correct rows gives **p = 0.560**.

There is no evidence that the v2 rewrite improved accuracy. This supports the audit finding that 31.2% of labels changed without validation.

### 4.4 Confirmation: missing dictionary coverage is the main error source

Among the 73 single-label errors:

| Missing pattern | Matching errors among 73 |
|---|---:|
| desire and negation forms (`〜たい`, `ますように`, `ないかな`, `ほしい`) | 19 |
| exchange (`\b` does not fire) | 8 |
| inflection (past tense, `すぎ`, stem changes) | 6 |
| missing terms (`品薄`, `抽選`, `流通`, `目撃情報`) | 5 |

A row can match more than one pattern, so the counts do not sum to 73.

---

## 5. Summary

### 5.1 Baseline metrics

| Metric | Value |
|---|---:|
| **Lenient micro F1** | **0.576** |
| **Multi-label micro F1** | **0.594** |
| Lenient macro F1 | 0.451 |
| Multi-label macro F1 | 0.496 |
| Lenient hit rate | 0.614 [0.543, 0.680] |
| Exact prediction-set match | 0.534 [0.463, 0.604] |

The large gap between macro and micro F1 (0.451 vs 0.576) indicates highly uneven performance. The classifier is close to usable only for `交換・取引`.

| Category | Lenient F1 | Status |
|---|---:|---|
| 交換・取引 | 0.872 | Near operational quality |
| 中立 | 0.631 | Overpredicted; more than 40% incorrect |
| 喜び・満足 | 0.516 | Needs improvement |
| 不満・怒り | 0.471 | Overpredicted; precision 0.400 |
| 欲望・執着 | 0.373 | Needs improvement |
| 焦り・競争 | 0.294 | **Barely functional**; recall 0.185 |
| 情報共有 | 0.000 | **Indeterminate**; n=5, requires more samples |

### 5.2 Revised improvement priorities

The priorities below incorporate the measured Gold results. **The classifier code was not modified.**

| Priority | Target | Evidence |
|---|---|---|
| **P0** | Redesign the `焦り・競争` rules | Recall 0.185. The third-largest Gold category (14.3%) is almost entirely missed; multi-label output does not help. |
| **P0** | Add indirect desire forms (`〜出して`, `出ないかな`, `ますように`, `〜たい`, `ほしい`) | Present in 19 of 73 errors and the largest source of false-neutral rows. |
| **P0** | Fix `\b交換\b` in `classify_sns_rule_based.py:129` | Present in 8 of 73 errors; score-zero misses appear in Gold. |
| **P1** | Classify `情報共有` by speaker intent rather than word presence | All four primary predictions are wrong; `再入荷` and `目撃情報` attract joy and desire posts. |
| **P1** | Reduce overprediction of `不満・怒り` | Precision 0.400, or 0.312 under multi-label evaluation; 12–22 false positives. |
| **P1** | Generalize inflection handling | Six of 73 errors plus many false-neutral rows. |
| **P1** | Add missing terms (`品薄`, `抽選`, `流通`, `買い取って`, `並び始め`) | Five of 73 errors. |
| **P2** | Move to multi-label output | Micro F1 +0.018 and macro F1 +0.045. The benefit is limited, but 12.7% of Gold rows are multi-label. |
| **P2** | Implement the Guide Section 6 priority | Net −1 correct row; useful only for documentation consistency. |
| **Do not change** | Confidence labels | Measured accuracy is monotonic: high 0.886, medium 0.597, low 0.231. |

### 5.3 Measurement limitations

1. **n=189.** The overall hit-rate 95% CI is approximately ±0.07; category-level intervals are wider.
2. **`情報共有` n=5 and `不満・怒り` n=14.** These categories require stratified additional samples.
3. **Eleven deferred rows were excluded.** Seven were noted as advertising and two as off-topic. This suggests that advertising remains in the 109,037-post corpus (7/200 ≈ 3.5%). Excluding these rows may make the measured accuracy higher than practical deployment accuracy.
4. The Gold dataset reflects one annotator. Inter-annotator agreement was not measured.
