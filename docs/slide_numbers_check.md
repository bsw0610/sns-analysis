# Specification Chapter 2 Metric Verification Results (Task 4)

**Verification date**: 2026-07-30

**Verified specification**: `docs/slide_plan_10-16.md` (SHA-256 prefix
`ddc11216e18865e7`, recorded for the pre-translation file audited on
2026-07-30)

**Corpus**: `data/output/2511-2604_hybrid.csv` / `data/output/sentiment_classified_hybrid.csv`

**Gold Standard**: `gold_standard_192_normalized.csv`

## Summary: 96 Matched / 0 Mismatched / 0 Unverifiable (96 Total)

| Section | Metric | Specification | Measured | Result | Evidence |
|---|---|---:|---:|---|---|
| 2-0 | Corpus SHA-256 | 3bf78817892b356b | 3bf78817892b356b | Match | File |
| 2-0 | Classification-output SHA-256 | f273c9306507804a | f273c9306507804a | Match | File |
| 2-0 | Monthly source records (unique post IDs) | 136288 | 136288 | Match | Six monthly CSVs |
| 2-0 | ① Final keyword removals | 19362 | 19362 | Match | Set operation |
| 2-0 | ② Additional ad classification by the old version | 5874 | 5874 | Match | removed_additional_ads_with_reasons_202511_202604.csv |
| 2-0 | ③ New removals by the final version | 134 | 134 | Match | old − final |
| 2-0 | Remaining after ① | 116926 | 116926 | Match | Calculation |
| 2-0 | Remaining after ② | 111052 | 111052 | Match | Calculation |
| 2-0 | Analysis corpus | 110918 | 110918 | Match | sentiment_classified_hybrid.csv |
| 2-0 | Total removed | 25370 | 25370 | Match | Calculation |
| 2-0 | Removal rate (%) | 18.61 | 18.61 | Match | Calculation |
| 2-0 | Three sets are mutually exclusive | 0 overlap | 0 overlap | Match | Set operation |
| 2-0 | ①+②+③ = total removed | 25370 | 25370 | Match | Calculation |
| 2-0 | Restored (old-version removal → retained by final version) | 5615 | 5615 | Match | final − old |
| 2-0 | Over-removal by `第弾` | 2002 | 2002 | Match | Rows in final − old for which the only old-filter match is `第弾` |
| 2-0 | Ads missed by the final version | 3600 | 3600 | Match | addl ∩ final |
| 2-0 | Pre-removal 情報共有 | 12392 | 12392 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 情報共有 | 4106 | 4106 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 情報共有 removal rate (%) | 66.87 | 66.87 | Match | Calculation |
| 2-0 | Pre-removal 中立 | 58294 | 58294 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 中立 | 45418 | 45418 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 中立 removal rate (%) | 22.09 | 22.09 | Match | Calculation |
| 2-0 | Pre-removal 焦り・競争 | 4148 | 4148 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 焦り・競争 | 3272 | 3272 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 焦り・競争 removal rate (%) | 21.12 | 21.12 | Match | Calculation |
| 2-0 | Pre-removal 喜び・満足 | 15131 | 15131 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 喜び・満足 | 13002 | 13002 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 喜び・満足 removal rate (%) | 14.07 | 14.07 | Match | Calculation |
| 2-0 | Pre-removal 欲望・執着 | 10185 | 10185 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 欲望・執着 | 9513 | 9513 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 欲望・執着 removal rate (%) | 6.6 | 6.6 | Match | Calculation |
| 2-0 | Pre-removal 不満・怒り | 11586 | 11586 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 不満・怒り | 11291 | 11291 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 不満・怒り removal rate (%) | 2.55 | 2.55 | Match | Calculation |
| 2-0 | Pre-removal 交換・取引 | 24552 | 24552 | Match | v2 classification of 136,288 records |
| 2-0 | Hybrid 交換・取引 | 24316 | 24316 | Match | sentiment_classified_hybrid.csv |
| 2-0 | 交換・取引 removal rate (%) | 0.96 | 0.96 | Match | Calculation |
| 2-0 | Slide 3 collected (10,000 posts) | 13.6 | 13.6 | Match | Calculation |
| 2-0 | Slide 3 ads (10,000 posts) | 2.5 | 2.5 | Match | Calculation |
| 2-0 | Slide 3 analysis corpus (10,000 posts) | 11.1 | 11.1 | Match | Calculation |
| 2-1 | 焦り・競争 reviewed | 30 | 30 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 焦り・競争 green | 24 | 24 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 焦り・競争 yellow | 4 | 4 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 焦り・競争 red | 2 | 2 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 焦り・競争 agreement rate (%) | 80 | 80 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 喜び・満足 reviewed | 30 | 30 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 喜び・満足 green | 14 | 14 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 喜び・満足 yellow | 15 | 15 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 喜び・満足 red | 1 | 1 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 喜び・満足 agreement rate (%) | 47 | 47 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 情報共有 reviewed | 23 | 23 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 情報共有 green | 10 | 10 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 情報共有 yellow | 1 | 1 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 情報共有 red | 12 | 12 | Match | category_random_sample_30_each.xlsx |
| 2-1 | 情報共有 agreement rate (%) | 43 | 43 | Match | category_random_sample_30_each.xlsx |
| 2-3 | Gold Standard records | 192 | 192 | Match | gold_standard_192_normalized.csv |
| 2-3 | 交換・取引 share (%) | 28.1 | 28.1 | Match | gold_standard_192_normalized.csv |
| 2-3 | 交換・取引 95% CI | 21.8 – 34.5% | 21.8 – 34.5% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 中立 share (%) | 25.0 | 25.0 | Match | gold_standard_192_normalized.csv |
| 2-3 | 中立 95% CI | 18.9 – 31.1% | 18.9 – 31.1% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 欲望・執着 share (%) | 18.8 | 18.8 | Match | gold_standard_192_normalized.csv |
| 2-3 | 欲望・執着 95% CI | 13.2 – 24.3% | 13.2 – 24.3% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 喜び・満足 share (%) | 17.2 | 17.2 | Match | gold_standard_192_normalized.csv |
| 2-3 | 喜び・満足 95% CI | 11.9 – 22.5% | 11.9 – 22.5% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 焦り・競争 share (%) | 14.1 | 14.1 | Match | gold_standard_192_normalized.csv |
| 2-3 | 焦り・競争 95% CI | 9.1 – 19.0% | 9.1 – 19.0% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 不満・怒り share (%) | 7.3 | 7.3 | Match | gold_standard_192_normalized.csv |
| 2-3 | 不満・怒り 95% CI | 3.6 – 11.0% | 3.6 – 11.0% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | 情報共有 share (%) | 2.6 | 2.6 | Match | gold_standard_192_normalized.csv |
| 2-3 | 情報共有 95% CI | 0.4 – 4.9% | 0.4 – 4.9% | Match | Wald normal approximation (95%, z=1.96, n=192, per-category binary variable) |
| 2-3 | Records added by the hybrid corpus | 2015 | 2015 | Match | hybrid − old |
| 2-4 | 交換・取引 posts | 24316 | 24316 | Match | sentiment_classified_hybrid.csv |
| 2-4 | Unique ユーザーID | 10677 | 10677 | Match | sentiment_classified_hybrid.csv |
| 2-4 | Unique アカウントID | 10715 | 10715 | Match | sentiment_classified_hybrid.csv |
| 2-4 | Unique (アカウントID, 名前) | 10894 | 10894 | Match | sentiment_classified_hybrid.csv |
| 2-4 | Unique 名前 | 8907 | 8907 | Match | sentiment_classified_hybrid.csv |
| 2-4 | Mean posts per account | 2.28 | 2.28 | Match | Calculation |
| 2-4 | Median | 1 | 1 | Match | Calculation |
| 2-4 | One-post accounts | 7198 | 7198 | Match | Calculation |
| 2-4 | One-post account share (%) | 67.4 | 67.4 | Match | Calculation |
| 2-4 | Top-30 total | 1796 | 1796 | Match | Calculation |
| 2-4 | Top-30 share (%) | 7.4 | 7.4 | Match | Calculation |
| 2-4 | Top-1% account count | 106 | 106 | Match | floor(10,677 × 0.01) |
| 2-4 | Top-1% share (%) | 14.9 | 14.9 | Match | 3,619 / 24,316 |
| 2-4 | Top-10% share (%) | 45.6 | 45.6 | Match | 11,082 / 24,316 |
| 2-4 | Structured-format count | 12411 | 12411 | Match | Shared structured-format definition |
| 2-4 | Structured-format share (%) | 51.0 | 51.0 | Match | 12,411 / 24,316 |
| 2-5 | Effective record count | 98 | 98 | Match | negotiation_expressions_not_exchange_random50.csv+random_sample_50_negotiation_not_exchange_202511_202604.csv |
| 2-5 | Reply count | 79 | 79 | Match | Nonempty リプライ先の投稿ID |
| 2-5 | Classified as 中立 | 90 | 90 | Match | sentiment_classified_hybrid.csv |
| 2-5 | “検索より/から失礼いたします” | 48 | 48 | Match | 検索(?:より\|から) |
| 2-5 | “ご検討” | 42 | 42 | Match | (?:ご\|御)検討 |
| 2-5 | “初めまして” | 31 | 31 | Match | 初めまして\|はじめまして |
| 2-5 | 🙇 | 31 | 31 | Match | 🙇 in post text |
| 2-5 | Exchange ratio (n:m) | 17 | 17 | Match | \d\s*[:：]\s*\d |
| 2-5 | “比率違い” | 3 | 3 | Match | 比率違い in post text |
