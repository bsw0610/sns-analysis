# SNS Sentiment and Behavior Analysis Guide

## 1. Define the Analysis Objective

Start by deciding what the sentiment analysis should explain.

This study examines SNS posts about Bonbon Drop Seal. Its purpose is not limited to positive and negative sentiment. It also investigates how emotions relate to behavior.

### Example research objective

Analyze SNS posts about Bonbon Drop Seal to determine how favorable reactions such as “cute” and “I bought it,” as well as desire, inability to purchase, resale, exchange, and searching behavior, relate to the spread of the trend.

---

## 2. Define the Classification Categories

Conventional sentiment analysis often uses positive, negative, and neutral labels. Those labels alone are insufficient for this study.

Analyzing the Bonbon Drop Seal trend requires categories for purchasing behavior, competition, and exchange culture in addition to emotion.

### Classification categories

The Japanese category names are preserved because they are values used in the datasets and classifier outputs.

| Category | Description | Examples |
|---|---|---|
| 喜び・満足 | Joy, satisfaction, or favorable reactions after obtaining the product | 買えた, かわいい, 嬉しい, 最高 |
| 欲望・執着 | Desire for the product or a strong collecting impulse | 欲しい, 探してる, 集めたい, 沼, 中毒 |
| 不満・怒り | Dissatisfaction with scarcity, resale, or purchasing conditions | 買えない, 売り切れ, 転売, 買い占め |
| 焦り・競争 | Competition or urgency around purchasing | 行列, 開店ダッシュ, 争奪戦, 即完 |
| 情報共有 | Sharing stock, restock, or sales-location information | 入荷, 再入荷, 在庫, ロフト, 目撃情報 |
| 交換・取引 | Exchanges or trades between users | 求, 譲, 交換, 郵送, レート |
| 中立 | No clear emotion or behavior can be inferred | A post that only mentions the product name |

---

## 3. Inspect the Source Data

Open the CSV files and identify what each column contains.

Check the following fields in particular:

- post text
- posting date and time
- SNS type
- URL
- user information
- engagement measures such as likes and reposts, if available

The post-text column is the most important input for this analysis.

---

## 4. Start with a Sample of 100 Posts

Do not begin by classifying the full dataset. First draw a random sample of about 100 posts and read them manually.

This step reveals the language used in actual posts and provides evidence for the category definitions.

### Example instruction for Codex

```text
This project analyzes sentiment and behavior in SNS posts.
First inspect the columns in data/processed/cleaned.csv.
Then draw a random sample of 100 posts from the post-text column.
Include the posting date when it is available, and save the sample as
data/output/manual_check_sample_100.csv.
Never overwrite the source data.
```

---

## 5. Apply Human Labels

Read the sampled posts and assign a classification label to each one.

### Examples

| Original post | Label |
|---|---|
| ボンボンドロップシール買えた！かわいい | 喜び・満足 |
| 欲しいのにどこにも売ってない | 不満・怒り |
| 転売ヤー多すぎて無理 | 不満・怒り |
| ロフト再入荷してた | 情報共有 |
| 求：いちご　譲：くま　郵送希望 | 交換・取引 |

A post may express more than one emotion. A simplified analysis can assign one primary label per post, but this choice creates a structural limitation that must be documented.

---

## 6. Define Category Priority

Some posts match more than one category, so the original guide proposed the following priority order:

1. 不満・怒り
2. 焦り・競争
3. 交換・取引
4. 欲望・執着
5. 喜び・満足
6. 情報共有
7. 中立

For example, “欲しいけど転売ばっかりで買えない” contains both desire and dissatisfaction. Under this policy, it is classified as `不満・怒り` because that label better represents the problem structure.

The preserved v2.0.0 implementation uses score order first and this priority only to break ties. The difference is documented in the evaluation and audit reports.

---

## 7. Build a Keyword Dictionary

Use expressions found in the 100-post review to build a keyword dictionary for each category.

### Example keyword dictionary

| Category | Example keywords |
|---|---|
| 喜び・満足 | 買えた, ゲット, 嬉しい, かわいい, 最高, 好き |
| 欲望・執着 | 欲しい, 探してる, 集めたい, コンプ, 沼, 中毒 |
| 不満・怒り | 買えない, 売ってない, 売り切れ, 転売, 買い占め, 最悪 |
| 焦り・競争 | 行列, 並ぶ, 開店, ダッシュ, 争奪戦, 即完 |
| 情報共有 | 入荷, 再入荷, 在庫, 販売, ロフト, しまむら, 目撃 |
| 交換・取引 | 交換, 求, 譲, 郵送, 手渡し, レート, 買取 |

Short expressions such as `求` and `譲` can cause false positives. Prefer conditional rules, such as requiring both expressions before assigning `交換・取引`.

---

## 8. Run Rule-Based Classification in Python

Use the keyword dictionary to identify matching expressions in each post and assign a category.

Store the triggering expressions in a `matched_keywords` column rather than recording only the final category. This makes each classification easier to explain and audit.

---

## 9. Recommended Sequence for Codex Tasks

Give Codex one bounded task at a time.

### 1. Inspect the data structure

```text
Inspect data/processed/cleaned.csv and identify the post-text column,
posting-date column, and any other useful fields.
Do not modify the data. Save the findings in docs/data_structure.md.
```

### 2. Draw a sample of 100 posts

```text
Draw a random sample of 100 rows from cleaned.csv.
Include the post text, clean_text, and posting date.
Save the result as data/output/manual_check_sample_100.csv.
```

### 3. Create the sentiment classifier

```text
Create a Python script that classifies SNS posts into the following categories:

- 喜び・満足
- 欲望・執着
- 不満・怒り
- 焦り・競争
- 情報共有
- 交換・取引
- 中立

Add a matched_keywords column so the reason for each classification is visible.
If a post matches more than one category, use this priority:
不満・怒り, 焦り・競争, 交換・取引, 欲望・執着, 喜び・満足,
情報共有, 中立.
```

### 4. Aggregate the results

```text
Use sentiment_result.csv to calculate the count and share of each category.
If a posting-date column is available, also calculate monthly counts by category.
Save the result as data/output/sentiment_summary.csv.
```

### 5. Create a validation sample

```text
Draw a random sample of 30 posts from each category for human review.
Include the posting date, clean_text, sentiment_label, and matched_keywords.
Save the file as data/output/sentiment_validation_sample.csv.
```

---

## 10. Review the Analysis Results

After classification, inspect:

- count by category
- share by category
- monthly changes
- periods with more complaints about resale or sellouts
- periods with more exchange or trade posts
- store names that appear often in information-sharing posts
- misclassified posts

Do not accept the classifier output without review. Resample posts from every category and return to the original text to validate the intended meaning.

---

## 11. How to Explain the Method as Research

The method can be summarized as follows:

> Before classifying the complete SNS dataset, I manually reviewed a random sample of 100 posts and designed categories that reflected the context of the posts. I then implemented a Python rule-based classifier using a keyword dictionary and retained the matched expressions as classification evidence. Finally, I resampled posts from each category to inspect errors. The analysis therefore used AI and code as tools while retaining human review of the original text.

---

## 12. Summary

The first step in SNS sentiment and behavior analysis is not writing code. It is reading posts and defining defensible categories.

The core workflow is:

1. define the analysis objective
2. define the categories
3. inspect the source columns
4. sample 100 posts
5. apply human labels
6. build a keyword dictionary
7. classify posts in Python
8. aggregate results
9. inspect misclassifications
10. return to the source text for sociological interpretation

This process allows AI and Codex to support the analysis without replacing human judgment.
