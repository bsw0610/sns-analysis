# Task 0: Investigating the Total-count Discrepancy

**Audit date**: 2026-07-29

**Objective**: identify the difference between approximately 136,301 posts in the then-current slides and the 109,037-post evaluation corpus, and select one total for the presentation.

**Policy**: as required by Section 4 of `slide_plan_10-16.md` at the time, neither number was changed during this audit; the work was report-only.

> **Historical status:** this document records the 2026-07-29 conclusion. The later hybrid baseline uses 110,918 posts and supersedes 109,037 as the current authoritative corpus.

---

## 1. Conclusion at the Time

| Item | Conclusion |
|---|---|
| **Total to report in the presentation** | **109,037**, with the caveats in Section 5 |
| Origin of 136,301 | **Not reproducible from any file in this repository.** It appears to be a pre-advertising-removal result from an unavailable older classifier. |
| Origin of 33,988 (`交換・取引`) | Same issue. No available v1/v2 and population combination reproduces it. |
| Slide 3: `13万に減らした` (“reduced to 130,000”) | **Inconsistent with 109,037 (`10.9万`; 109 thousand).** It appears to refer to the pre-filter total of 136,288. |

---

## 2. Count Lineage Reproduced from Preserved Files

```text
Six monthly CSV files                    136,288 posts
  202511:12,907 / 202512:17,037 / 202601:24,721
  202602:31,597 / 202603:20,260 / 202604:29,766
  duplicate IDs: 0 / unique IDs: 136,288
        |
        |  1. keyword advertising removal    -21,377 (-15.7%)
        v
                                            114,911 posts
        |
        |  2. additional removal, 12 reasons  -5,874 (-4.3%)
        v
  data/output/2511-2604.csv                  109,037 posts
        |
        v
  sentiment_classified_2511-2604.csv         109,037 posts
```

- An independent check of `reconciled: true` in `ad_filter_summary_202511_202604.json` confirmed that **136,288 − 21,377 − 5,874 = 109,037** exactly.
- The 27,251 excluded rows were reconstructed from the monthly CSV files and matched the recorded count.
- The total removal rate was **20.0%**, or one in five posts.

### 2.1 The pipeline has two separate branches

`filter_ads_202511_202604.py:17` reads the monthly CSV files directly through `SOURCE_NAMES`. It does **not** use `INPUT.csv`.

| Track | Path | Purpose |
|---|---|---|
| Sentiment and behavior analysis | monthly CSV → advertising removal → `2511-2604.csv` (109,037) | classification and validation |
| Word2Vec | `INPUT.csv` (136,293) → `INPUT_new.csv` (143,921) → `clean.csv` | word vectors |

The two tracks differ from the start: 136,288 vs 136,293. `INPUT.csv` contains 136,289 unique IDs and four duplicate rows, including one ID value not present among the monthly post IDs. Later provenance work showed that the raw `cat *.csv` procedure retained five additional header rows.

> `INPUT_new.csv` contains 143,921 one-column body rows, 7,628 more than `INPUT.csv`. This historical audit reported no multiline post bodies in the monthly sources or `INPUT.csv`, so line splitting did not explain the difference at the time. The Word2Vec input count therefore remained unresolved. This does not affect the sentiment-analysis conclusion, but it prevents a reliable statement about the Word2Vec population.

---

## 3. Tracing 136,301 and 33,988

### 3.1 The values do not exist in the repository evidence

A search for `136301`, `136,301`, `33988`, and `33,988` across JSON, Markdown, Python, HTML, NDJSON, text, and Notebook output found matches only in `slide_plan_10-16.md`.

The older slide data at `outputs/sentiment-analysis-20260716/sentiment_slide_analysis_data.json` already uses `total_posts = 109,037` and `交換・取引 = 23,134`. The Canva figures were therefore older than the July 16, 2026 artifacts.

### 3.2 Available classifiers do not reproduce the values

The audit restored the 27,251 excluded rows and evaluated all available v1/v2 and population combinations.

| Population | Classifier | 交換・取引 | Total |
|---|---|---:|---:|
| 109,037 (then-current) | **v2** | **23,134** | 109,037 |
| 109,037 | v1 (legacy) | 28,950 | 109,037 |
| 136,288 (before filtering) | v2 | 24,552 | 136,288 |
| 136,288 (before filtering) | v1 (legacy) | 40,205 | 136,288 |
| — | — | **33,988: no match** | **136,301: no match** |

None of the four combinations matches, and 136,301 is 13 rows higher than 136,288.

The conclusion was that the slide figures came from an unavailable older classifier applied to an unavailable population with 13 additional rows. They cannot be reproduced with the current code and data.

`LEGACY_KEYWORDS` in `classify_sns_rule_based.py` is documented as a reconstruction for comparison with an older implementation. It is not the original historical output. Its failure to produce 33,988 suggests that it differs from the unavailable implementation.

---

## 4. Consistency with Slide 3: “Reduced to 130,000”

| Candidate | Count | Reasonably described as 130,000? |
|---|---:|---|
| Monthly-source total | 136,288 | Yes (`13.6万`; 136 thousand) |
| `INPUT.csv` | 136,293 | Yes (`13.6万`; 136 thousand) |
| After keyword removal | 114,911 | Marginal (`11.5万`; 115 thousand) |
| **After all advertising removal** | **109,037** | **No (`10.9万`; 109 thousand)** |

“Reduced to 130,000” cannot refer to 109,037. The most natural interpretation is the pre-filter total of 136,288.

This means that the then-current slide did not represent the advertising-removal step. Neither the 20.0% removal rate nor the 27,251 excluded posts appeared in the explanation.

---

## 5. Required Caveats When Reporting 109,037

The audit recommended 109,037 at the time, but this population is not a neutral set of “all posts.”

### 5.1 Breakdown of 21,377 keyword removals

Hits overlap across keywords.

| Keyword | Hits |
|---|---:|
| 名様 | 9,839 |
| リポスト | 8,343 |
| 大還元祭 | 4,415 |
| **お知らせ** | 3,457 |
| プレオープン大還元祭 | 2,777 |
| ころじいちゃん | 1,855 |
| 参加方法 | 1,650 |
| フォロワー様 | 890 |
| **詳しくは** | 843 |
| 人達成企画 | 515 |
| **ご来店** | 505 |
| 日間限定 | 186 |
| 会計につき | 129 |
| **再入荷情報** | 108 |
| 準備資金 | 1 |

`お知らせ`, `詳しくは`, `ご来店`, `再入荷情報`, and `リポスト` can also appear in non-advertising posts. `再入荷情報` is especially central to the `情報共有` category.

### 5.2 Advertising removal disproportionately reduces 情報共有

Classifying the 27,251 excluded posts with v2 produced:

| Category | Excluded | Retained (109,037) | Removal rate |
|---|---:|---:|---:|
| **情報共有** | **8,395** | **3,997** | **67.7%** |
| 中立 | 13,183 | 45,111 | 22.6% |
| 喜び・満足 | 2,262 | 12,869 | 14.9% |
| 交換・取引 | 1,418 | 23,134 | 5.8% |
| 焦り・競争 | 893 | 3,255 | 21.5% |
| 欲望・執着 | 752 | 9,433 | 7.4% |
| 不満・怒り | 348 | 11,238 | 3.0% |

More than two thirds of posts classified as `情報共有` were removed before analysis. Additional-removal reasons also include `RESTOCK_STORE_NOTICE` for 432 rows and `SALES_INFORMATION` for 531 rows.

This affects two presentation claims:

- Page 13: “情報共有 accuracy 43%” and “not posts that convey information”
- Page 14: “情報共有 2.6%”

The 2.6% share reflects both classifier behavior and the removal of information-sharing posts before classification. Attributing the result only to classifier failure would be incorrect.

`交換・取引` has the lowest removal rate at 5.8%. The advertising filter's selectivity also contributes to exchange becoming the largest retained category.

---

## 6. Decisions Requested at the Time

1. **Should the total be fixed at 109,037?** This document recommended it, provided that the conflict with `13万` on Slide 3 was resolved, for example: `13.6万件を収集し、広告2.0万件を除いた10.9万件を分析対象とした` (“Collected 136 thousand posts and analyzed 109 thousand after removing 20 thousand advertising posts”).
2. **136,301 and 33,988 are not reproducible.** If they appeared outside replacement pages 10–16, those pages also required correction.
3. **Should the information-sharing bias in Section 5.2 be reflected on Pages 13 and 14?** Omitting it would incorrectly attribute the result only to the classifier.
4. Section 1-1 of `slide_plan_10-16.md` prohibited raw monthly category counts, but did not list the information-sharing bias caused by advertising removal. The audit asked whether it should be added.
