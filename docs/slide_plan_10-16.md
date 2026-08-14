# Bonbon Drop Final Presentation: Slide 10–16 Replacement Plan

This document is written in English for repository readers. Japanese text in
inline code is final or candidate copy intended to appear in the Japanese
presentation and is therefore preserved.

## 0. Scope and Evidence

This plan covers only slides 10–16 of the Canva presentation, which address the
emotion and behavior category analysis. It does not change slides 1–9, slide 17
or later, Canva, the PPTX, reference CSVs, the Gold Standard, classification
outputs, or classification rules.

This section does not present classifier output as the conclusion of the entire
study. It first establishes the usable range through comparison with human
labels, then describes the internal structure of the relatively stable
`交換・取引` category.

The fixed inputs are:

| Purpose | File | SHA-256 |
|---|---|---|
| Source Gold Standard | `data/output/gold_standard_192.csv` | `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815` |
| Normalized Gold Standard | `data/output/gold_standard_192_normalized.csv` | `ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c` |
| Hybrid corpus | `data/output/2511-2604_hybrid.csv` | `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e` |
| Classification output | `data/output/sentiment_classified_hybrid.csv` | `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d` |

The official evaluation input has 192 rows × 12 columns, all 192 post IDs are
unique, and multi-label annotations are allowed. The analysis corpus and
classification output both contain 110,918 records.

Rules that apply to every slide:

- Do not present the final conclusion of the entire study in this section.
- Do not claim to have established the essence of the overall trend, creation
  of social value, or formation of community norms.
- Do not equate F1 with accuracy or a simple agreement rate.
- Do not treat the classifier's single-label composition as the true
  composition.
- Do not use `109,037件`, `最終評価189件`, `焦り・競争3.0%`,
  `交換投稿23,134件`, `定型書式12,181件／50.1%`, `交換比率18件`,
  `リプライ80件`, `交換F1 0.872`, or `実用水準0.80`.
- Do not use the old ad-removal impact values
  `情報共有67.7%／交換5.8%`.

## 1. Slide 10 — Emotion and Behavior Analysis Process

### Purpose

Show the process used to determine the usable range of classification results,
with human labels as the final reference rather than treating automated output
as a conclusion.

### Title

`感情・行動カテゴリ分析の進め方`

### Slide Copy

Main flow:

1. `7カテゴリを設定`
2. `Codexで自動分類`
3. `元投稿を確認`
4. `人手ラベルで性能を評価`

Main statement:

`自動分類の結果をそのまま解釈せず、人手ラベルとの比較を通じて利用可能な範囲を確認した。`

Supporting statement:

`コードと集計定義は別工程でも監査したが、評価の最終基準は人手ラベルとした。`

### Key Values

Display only the four process steps and seven categories. Place performance
values and post counts on later slides.

### Chart and Layout

Use a four-stage left-to-right flow with short verb phrases and simple icons.
Make `人手ラベル` the visual endpoint. Show the code audit as a small supporting
note outside the main flow, not as an independent evaluator.

### Speaker Notes

Explain that the classifier is a tool for exploring overall tendencies, not a
source of ground truth. Original-post review and comparison with the official
Gold Standard determined which category aggregates could be used and to what
extent.

### Interpretation Limits

Human labels also depend on judgment criteria, and the evaluation contains 192
records. The code audit verifies implementation reproducibility; it does not
replace human labels.

### Prohibited Wording

- `AI二つが相互検証したので信頼できる`
- `AI同士の合意を正解とした`
- `自動分類で感情を正確に把握した`

## 2. Slide 11 — Definitions of the Seven Categories

### Purpose

Define the seven categories before presenting performance and composition
charts.

### Title

`投稿を7つの感情・行動カテゴリに分類`

### Slide Copy

| Category | Definition | Short anonymized example |
|---|---|---|
| 喜び・満足 | 入手、使用、見た目などへの喜び・満足 | `「買えた。これで一安心」` |
| 欲望・執着 | 欲しい、探している、集めたいという欲求 | `「ボンドロだけはいつか欲しい」` |
| 不満・怒り | 転売、偽造品、販売方法などへの不満・怒り | `「転売してる人全員敵だわ」` |
| 焦り・競争 | 売切れ、行列、争奪、即時行動への焦り | `「12時になった瞬間にリロードしたらエラー」` |
| 情報共有 | 入荷、在庫、販売場所・時刻などの共有 | `「入荷 セリア ダイソー…1/8 16:14」` |
| 交換・取引 | 譲渡条件、希望品、受渡方法などの提示 | `「【譲】和柄…【求】柴犬…手渡しor郵送」` |
| 中立 | 上記の感情・行動を明確に読み取れない記述 | `「今のボンドロも似たような感じなのかな」` |

Required note:

`1つの投稿に複数の感情や行動が含まれる場合がある。`

### Key Values

Display only the category count, `7`. Do not show category counts or shares.

### Chart and Layout

Retain the seven-circle structure in the current Canva deck. Place the title in
the center and the seven categories around it. Each circle should contain the
category name, a one-line definition, and a short example in that order. Use a
smaller size for examples and consistent quotation marks.

### Speaker Notes

The categories are not mutually exclusive; multiple emotions or behaviors can
coexist in one post. The displayed examples were shortened from real text in the
official Gold Standard by removing account names, mentions, URLs, and image
links without changing the meaning.

Evidence for examples, not displayed in Canva:

| Category | Evidence |
|---|---|
| 喜び・満足 | `gold_standard_192_normalized.csv` row 38 |
| 欲望・執着 | Same file, row 32 |
| 不満・怒り | Same file, row 78 |
| 焦り・競争 | Same file, row 124 |
| 情報共有 | Same file, row 148 |
| 交換・取引 | Same file, row 135 |
| 中立 | Same file, row 50 |

### Interpretation Limits

The examples explain category definitions. They do not indicate how typical or
frequent the examples are within each category.

### Prohibited Wording

- Language that infers category frequency from the examples
- Claims that the seven categories completely cover the meaning of every post
- Account names, user IDs, mentions, URLs, or image links

## 3. Slide 12 — Human-Labeled Evaluation Set

### Purpose

Make clear that 189 records were an intermediate stage and that the official
evaluation input contains 192 records after supplementation.

### Title

`人手ラベルによる評価データの作成`

### Slide Copy

Display flow:

1. `無作為抽出 200件`
2. `既存の有効ラベル 189件`
3. `追加ラベル 3件`
4. `最終評価データ 192件`
5. `複数ラベルを許容`

Caution:

`広告除去の影響はカテゴリによって異なり、特に情報共有の解釈には注意が必要である。`

### Key Values

Show `200 → 189 + 3 → 192`. Make `192` the largest value and explicitly label
`189` as an intermediate stage.

### Chart and Layout

Use a horizontal evaluation-data flow in which `189` and `3` merge into `192`.
Place `複数ラベルを許容` as a band beneath 192. Put the ad-removal caution in a
separate footnote area.

### Speaker Notes

From the random 200 records, 189 existing valid labels were confirmed and three
pending records were additionally labeled, producing the official 192-record
evaluation input. Every cell in the first 12 source columns matches the
normalized file, and the three supplemental exchange labels are preserved.

### Interpretation Limits

Ad removal affects categories differently. Do not display `66.9%` or `1.0%` on
the slide. If mentioned orally, clarify that these are category-specific
removal rates using pre-removal counts classified by the same classifier as the
denominator, not the removal rate for all posts.

### Prohibited Wording

- `最終評価セット189件`
- `11件を除外したので189件が最終`
- Language presenting a category-specific ad-removal rate as the overall rate
- The old values `情報共有67.7%／交換5.8%`

## 4. Slide 13 — Per-Category Classification Performance

### Purpose

Compare F1 on a common scale for all seven categories and show performance
differences by category.

### Title

`カテゴリによって分類性能に差が見られた`

### Slide Copy

Interpretation:

`交換・取引は比較的安定して判定できた一方、他のカテゴリには改善の余地が残った。`

Supporting values:

- `緩和基準 micro F1 0.577`
- `多ラベル基準 micro F1 0.595`

Footnote:

`評価指標はF1。全体値は7カテゴリを合算したmicro F1。`

### Key Values

| Category | F1 |
|---|---:|
| 不満・怒り | 0.471 |
| 焦り・競争 | 0.294 |
| 交換・取引 | **0.869** |
| 欲望・執着 | 0.373 |
| 喜び・満足 | 0.516 |
| 情報共有 | 0.000 |
| 中立 | 0.625 |

### Chart and Layout

Use seven horizontal bars based on the official 192-record Gold Standard. Start
every bar at zero and do not omit zero values. Use gold with hatching for
交換・取引, light blue with a dot pattern for 中立, and the same neutral gray for
the remaining categories. Add a three-decimal direct label to every category so
the chart does not depend on color. Put the two micro F1 values in small text at
the right of the header.

Generated candidate: `p13_agreement.png`. Evidence: `p13_metrics.json`.

### Speaker Notes

The per-category values are lenient-criterion F1. 交換・取引 is relatively high
at 0.869, but values such as 0.625 for 中立 show a range of performance; do not
reduce the finding to “only exchange was correct.” Overall micro F1 and
per-category F1 use different aggregation units.

### Interpretation Limits

F1 is the harmonic mean of precision and recall, not simple accuracy. The
情報共有 value of zero is the result on the official sample. Given preprocessing
effects and the small number of sample records, do not extrapolate it to actual
frequency or existence in the population.

### Prohibited Wording

- `交換・取引だけが正しかった`
- `実用水準0.80`
- `交換F1 0.872`
- Referring to F1 as `正解率`, `一致率`, or `accuracy`

## 5. Slide 14 — Human-Labeled Category Composition

### Purpose

Show the composition and uncertainty based on the 192 human-labeled records,
not the classifier's single-label composition.

### Title

`人手ラベルから見えたカテゴリ構成`

### Slide Copy

Main callout:

`焦り・競争：人手ラベル14.1%／自動分類2.9%`

Required notes:

`1投稿に複数ラベルを付与したため、構成比の合計は113.0%。`

`「情報共有」は広告除去条件の影響が大きく、低い実態比率とは断定できない。`

### Key Values

| Category | Numerator / 192 | Share | Wald 95% CI |
|---|---:|---:|---:|
| 交換・取引 | 54 | 28.1% | 21.8–34.5% |
| 中立 | 48 | 25.0% | 18.9–31.1% |
| 欲望・執着 | 36 | 18.8% | 13.2–24.3% |
| 喜び・満足 | 33 | 17.2% | 11.9–22.5% |
| 焦り・競争 | 27 | 14.1% | 9.1–19.0% |
| 不満・怒り | 14 | 7.3% | 3.6–11.0% |
| 情報共有 | 5 | 2.6% | 0.4–4.9% |

The human labels total 217. The classifier's 焦り・競争 count is
`3,272 / 110,918 = 2.9%`.

### Chart and Layout

Use a horizontal dot plot of point estimates and Wald 95% confidence intervals
by category. Display count, share, and interval directly on each row. Use an
orange point for 焦り・競争, gray for 情報共有, and blue tones for the other
categories. Mark the classifier's 2.9% for 焦り・競争 with an × on the same row.
Embed both required notes in the bottom of the PNG; do not overlay separate text
in Canva.

Generated candidate: `p14_composition.png`. Evidence:
`p14_metrics.json`.

### Speaker Notes

Treat each category as an independent binary proportion and display Wald
intervals with `z=1.96` and `n=192`. Multi-label annotation gives 217 numerator
labels and a combined share of 113.0%.

### Interpretation Limits

The Wald approximation can be unstable for sparse proportions such as 5/192.
Because 情報共有 at 2.6% is strongly affected by ad-removal conditions, do not
treat it as evidence that information sharing is rare in the population. Human
labels and the classifier's 2.9% use different measurement methods; compare only
the direction of the difference.

### Prohibited Wording

- `焦り・競争は実態として3.0%`
- `情報共有はほとんど存在しない`
- Statements that the category shares are mutually exclusive and sum to 100%
- Claims that a Wald interval contains the true population value with 95%
  probability

## 6. Slide 15 — Quantitative Structure of the Exchange Category

### Purpose

Within the relatively stable `交換・取引` category, show the concentration and
long tail of posts and accounts.

### Title

`「交換・取引」カテゴリの投稿構造`

### Slide Copy

Transition:

`7カテゴリの中で比較的安定していた「交換・取引」を対象に、投稿とアカウントの構造を確認した。`

Interpretation:

`投稿は一部の活発なアカウントに集中しつつ、多数の単発参加アカウントにも広がっていた。`

Required note:

`※2026年4月は収集終了月であり、その後の増減は判断できない。`

### Key Values

- `交換投稿 24,316件`
- `参加アカウント 10,677`
- `1回のみ投稿 7,198 / 67.4%`
- `上位1% 106アカウント / 3,619件 / 投稿の14.9%`
- New accounts by month: `732, 1,365, 1,759, 1,774, 1,254, 3,793`

### Chart and Layout

Place four KPI cards above a monthly new-account bar chart. Order the KPIs as
post count, account count, one-time accounts at 67.4%, and top 1% at 14.9%.
Remove the old `定型書式51.0%` card. Use an outline with hatching for the final
month to show, without relying on color, that it is the collection end month.

Generated candidate: `p15_new_accounts.png`. Evidence:
`p15_metrics.json`.

### Speaker Notes

The account unit is `ユーザーID`, which is stable during the period. The top 1%
is `floor(10,677×0.01)=106` accounts and represents 3,619 posts, or 14.9%.
At the same time, 7,198 accounts posted only once. Monthly new counts use the
month of each user ID's first exchange post.

### Interpretation Limits

10,677 is the number of unique user IDs, not the number of real people. No bot
detection or identity verification was performed. April 2026 is a partial
collection endpoint, so later changes are unknown. These findings apply only
within the exchange category and are not generalized to the whole trend.

### Prohibited Wording

- `1万人が参加した`
- `10,677人`
- `上位アカウントもbotではなく実在の個人`
- `少数のヘビーユーザーが支えた構造ではない`
- Statements that infer the structure of the whole trend from the exchange
  category

## 7. Slide 16 — Formulaic Expressions in Exchange Posts

### Purpose

Show structured condition statements used in the exchange category and
negotiation expressions observed in the fixed 98-record sample without
confusing them with population estimates.

### Title

`「交換・取引」投稿に見られた定型表現`

### Slide Copy

Main conclusion:

`交換投稿の多くで、条件を簡潔に提示する共通の表現形式が使われていた。`

Displayed terms:

`譲／求／郵送／手渡し／交換比率／差額精算／ご検討・御検討`

Scope limitation:

`固定標本の分析であり、すべての交換投稿を代表するものではない。`

Transition to the next section:

`次に、これらの結果を他の分析と合わせて検討する。`

### Key Values

- Structured exchange format: `12,411件`
- Share of exchange posts: `51.0%`
- Fixed sample containing negotiation expressions: `98件`
- Replies: `79件`
- Formulaic greetings: `48件`
- `ご検討／御検討`: `42件`
- Exchange ratios: `17件`

### Chart and Layout

Place `12,411件／51.0%` prominently on the left and a large four-row table for
the fixed 98-record sample on the right. Do not place source-text examples in
the lower section. Instead, prominently show the main conclusion, a summary of
condition statements, and the role of the fixed sample. Limit oversized values
to `12,411`, `51.0%`, and `98`; keep 79, 48, 42, and 17 in a supporting table.
Embed the scope limitation and transition in the bottom of the PNG.

Generated candidate: `p16_expressions.png`. Evidence:
`p16_metrics.json`.

Do not display the original examples. To support reproducibility,
`p16_metrics.json` alone retains the already verified exact-source matches for
two records and the rationale for anonymization.

### Speaker Notes

The shared regular expression identifies 12,411 structured formats among all
24,316 exchange posts, or 51.0%. The 98 records, however, are a fixed
qualitative sample extracted for negotiation expressions. Do not estimate a
population share such as 79/98 for all exchange posts; display these only as
supporting counts.

### Interpretation Limits

The 12,411 structured-format count is an automated operational definition, not
a manually reviewed census. The fixed 98 records are not a random sample and do
not represent every exchange post. The presence of common expressions does not
establish value creation or norm formation.

### Prohibited Wording

- `社会的価値が形成された`
- `コミュニティ規範が形成された`
- `運営も規約もないのに作法が共有された`
- `これが流行全体の本質である`
- `研究全体の結論である`
- Language generalizing proportions from the fixed 98 records to all exchange
  posts

## 8. Generation and Verification Contract

`regenerate_slide_assets.py` generates slides 13–16 in one run and outputs a PNG
and metrics JSON for each slide plus a combined manifest. If no output path is
given, `tempfile.mkdtemp()` creates a new system temporary directory. If
`--output-dir` is provided, that path is used. Output inside the repository is
rejected to prevent accidental overwriting of existing final PNGs.

Output files:

- `p13_agreement.png` / `p13_metrics.json`
- `p14_composition.png` / `p14_metrics.json`
- `p15_new_accounts.png` / `p15_metrics.json`
- `p16_expressions.png` / `p16_metrics.json`
- `slide_assets_manifest.json`

Every PNG must be 1920×1080, at least 1,720 px wide in content, with 0 missing
Japanese glyphs and 0 text elements outside the canvas. Generating from the same
inputs in two different temporary directories must produce matching SHA-256
values for all nine files.

Verification includes:

- Gold Standard shape of 192 rows × 12 columns, 192 unique IDs, and a 192/192
  join with classification results
- Cell-for-cell equality with the first 12 source columns and preservation of
  the three supplemental exchange labels
- Matching SHA-256 values for the four reference datasets
- `verify_slide_numbers.py`: 96/96
- Slide 15: 12/12 metrics
- Slide 16: seven metrics and source matching for two anonymized quotations
- Unit and regression tests, Ruff, and `git diff --check`
- PNG format, resolution, nonempty content, and metric/manifest hash checks
- Exact match of PNG, JSON, and manifest files across two runs
