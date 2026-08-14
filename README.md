# Bonbon Drop Seal Social Media Analysis

[![tests](https://github.com/bsw0610/sns-analysis/actions/workflows/test.yml/badge.svg)](https://github.com/bsw0610/sns-analysis/actions/workflows/test.yml)

An analysis of Japanese X posts about Bonbon Drop Seal, covering text preprocessing, Word2Vec, rule-based behavior classification, evaluation, and reproducible presentation metrics.

## Key Results

- **136,288** Japanese X posts analyzed
- **110,918** posts retained after advertising-filter audit
- Classifier evaluated against **192 human-labelled posts**
- **24,316** exchange posts across **10,677 user IDs**
- **Micro F1: 0.595** with documented category-level failure analysis
- Reproducibility verified with regression tests, SHA-256 checks, and CI

## 日本語概要

本プロジェクトでは、2025年11月から2026年4月までに収集した「ボンボンドロップシール」関連のX投稿136,288件を対象に、広告除去、テキスト前処理、Word2Vec、感情・行動カテゴリ分類、交換投稿の分析を行いました。

当初の分析では、研究室で共有されていたNotebookとUserLocal Social Insightのデータを利用し、MeCabによる分かち書き、Word2Vec学習、TensorFlow Embedding Projectorでの探索を実施しました。その後、広告除去や集計方法によって結果が大きく変わることが分かったため、既存コードとデータの流れを再調査しました。研究室提供Notebookは再配布条件を確認できないため公開せず、処理内容とデータ系譜のみを文書化しています。

私が行った主な作業は、既存Notebookを利用した前処理・単語分析、ルールベース分類結果の検証、Gold label 192件による評価、交換投稿とアカウント集中度の分析、スライド指標の再確認、再現手順の整備です。既存の処理を調査し改善する際にはAIコーディングエージェントも使用し、Notebookの確認、分析パイプラインの追跡、コード修正、再現性検証を行いました。

現在の基準データは、月別原票136,288件から広告を除去したhybrid corpus 110,918件です。ルールベース分類では「交換・取引」が24,316件、関連するユニークユーザーIDが10,677件でした。分類器はGold label 192件に対して、多重ラベル基準のmicro F1が0.595、macro F1が0.495でした。特に「焦り・競争」と「情報共有」の性能が低く、広告除去の偏りや日本語表現の取りこぼしが課題として残っています。

## Overview

This repository documents two related analysis tracks:

1. A historical word-level workflow based on lab-provided cleaning and Word2Vec notebooks, MeCab tokenization, and TensorFlow Embedding Projector.
2. A post-level workflow that removes advertising content, assigns one of seven emotion or behavior categories, evaluates the classifier against human labels, and analyzes exchange activity.

The most reproducible path currently available is:

![Analysis pipeline: 136,288 raw posts, 110,918 posts after advertising removal, 24,316 exchange posts from 10,677 unique user IDs, with the classifier evaluated against 192 human-labelled posts.](assets/portfolio/01_pipeline.png)

The classification step also produces the validated slide metrics and candidate presentation assets.

## Try It Without the Dataset

The collected posts are not in this repository, so a fresh clone cannot rerun
the study. It can still run the classifier: `sample_data/` holds 30 synthetic
posts written for this purpose. No dataset and no third-party packages are
needed.

```bash
python3 classify_sns_rule_based.py \
  --input sample_data/sample_posts.csv \
  --output sample_output.csv

python3 sample_data/check_sample_output.py sample_output.csv
```

```text
OK: 30 rows classified, 21/30 match the intended label
OK: 9 known disagreements reproduced exactly
```

The nine failures are deliberate. They are the weaknesses measured against the
human-labelled evaluation set — the `\b交換\b` word-boundary defect, the
information-sharing category scoring F1 0.000, and indirect expressions that
match no rule — so the limitations described below can be watched happening
rather than taken on trust. [`sample_data/README.md`](sample_data/README.md)
maps each one to its cause, and `check_sample_output.py` pins the exact outcome
so a behaviour change fails loudly instead of passing unnoticed. CI runs this
same sequence on every push.

The older Word2Vec path and several legacy presentation artifacts are documented for provenance, but parts of their preprocessing history are incomplete. The two lab-provided notebooks are intentionally excluded from the public repository because their redistribution terms could not be verified. See [Project Timeline](docs/01_PROJECT_TIMELINE.md) for the evidence-backed reconstruction.

## Motivation and Background

The project began as a Japanese social media analysis workflow for posts about ボンボンドロップシール. The original process used UserLocal Social Insight exports and notebooks shared for text cleaning and Word2Vec analysis.

Later analysis focused on questions that word embeddings alone could not answer directly:

- How much advertising content should be removed before analysis?
- What emotions or behaviors appear in the posts?
- How accurately can a rule-based classifier identify those categories?
- How large is the exchange and trade segment?
- Is exchange activity concentrated among a small number of user IDs?
- Can the reported numbers and slide assets be reproduced from preserved inputs?

The repository therefore includes both exploratory research artifacts and later reproducibility work.

## Source Material and Contribution Boundaries

Two reference notebooks used in the original workflow were supplied through a university seminar or lab and were not authored from scratch by the repository owner. One cleaned extracted post text with regular expressions; the other trained a Gensim Word2Vec model and exported `vector.tsv` and `metadata.tsv` for TensorFlow Embedding Projector.

Their redistribution terms could not be verified, so the notebook files and their full source code or cell outputs are not included in the public Git history. This repository documents only their observed role in the historical workflow. The later advertising-filter audit, hybrid-corpus reconstruction, rule-based evaluation, exchange-account analysis, slide-metric verification, and reproducibility work are represented by the scripts and documents retained here.

## Data Scope

The monthly X exports cover November 2025 through April 2026.

| File | Logical records |
| --- | ---: |
| `202511.csv` | 12,907 |
| `202512.csv` | 17,037 |
| `202601.csv` | 24,721 |
| `202602.csv` | 31,597 |
| `202603.csv` | 20,260 |
| `202604.csv` | 29,766 |
| **Total** | **136,288** |

The raw datasets are not tracked by Git. They may also contain line breaks inside fields, so physical line counts such as `wc -l` must not be treated as post counts.

## Methodology

### Original word-level workflow

The original workflow used the following sequence:

```text
UserLocal Social Insight CSV exports
  -> INPUT.csv
  -> INPUT_new.csv
  -> cleaning notebook
  -> clean.csv
  -> MeCab / mecab-ipadic-neologd
  -> clean.wakati
  -> Word2Vec
  -> clean.model
  -> vector.tsv / metadata.tsv
  -> TensorFlow Embedding Projector
```

During a read-only local audit, the lab-provided Word2Vec notebook recorded a model trained on June 4, 2026 with the following parameters. The notebook itself is not redistributed in this repository.

| Parameter | Value |
| --- | ---: |
| Architecture | skip-gram (`sg=1`) |
| Vector size | 350 |
| Window | 15 |
| Minimum count | 5 |
| Negative samples | 10 |
| Epochs | 10 |
| Vocabulary | 71,408 |

The current `metadata.tsv` and `vector.tsv` contain 17,298 rows, so they do not represent the full 71,408-word vocabulary. The export rule for this subset is unknown.

### Advertising removal and hybrid corpus

The older advertising filter retained 109,037 of 136,288 posts. An audit found that broad keywords disproportionately removed posts that the classifier would label as `情報共有`.

The current hybrid baseline retains 110,918 posts. It restores 2,015 posts from the old result while continuing to exclude the existing 5,874 additional-advertising IDs. Because the original source code for `2511-2604_final.csv` is missing, 391 final-filter decisions are preserved as an ID lock in `baselines/hybrid_final_exclusions.csv` rather than reconstructed from guessed rules.

![Advertising filter audit: of 136,288 source posts, 19,105 are excluded by existing keyword rules, 5,874 by additional-advertising rules, and 391 by an ID lock covering decisions whose source code is missing, leaving 110,918 retained. Against the previous 109,037-post result, 2,015 over-filtered posts are restored and 134 newly excluded.](assets/portfolio/02_filter_audit.png)

See [Hybrid Baseline Rebuild](docs/hybrid_rebuild.md) for the exact inputs, hashes, and verification contract.

### Rule-based classification

`classify_sns_rule_based.py` normalizes text with NFKC and case folding, removes URLs and mentions, applies weighted regular expressions, and assigns one primary category.

The seven labels are preserved in Japanese because they are dataset and output column values:

| Label | English description |
| --- | --- |
| `不満・怒り` | dissatisfaction or anger |
| `焦り・競争` | urgency or competition |
| `交換・取引` | exchange or trade |
| `欲望・執着` | desire or fixation |
| `喜び・満足` | joy or satisfaction |
| `情報共有` | information sharing |
| `中立` | neutral / no active rule |

### Human-label evaluation

The current evaluation set contains 192 posts:

- 189 labeled posts sampled from the older 109,037-post corpus
- 3 supplemental posts retained by the hybrid corpus

This is not a simple random sample of all 110,918 hybrid posts. The three supplemental labels are preserved in the baseline, but their original annotation provenance is not available.

### Exchange analysis

The exchange analysis aggregates posts whose primary category is `交換・取引` by `ユーザーID`.

![Exchange account concentration: 67.4% of the 10,677 user IDs posted exactly once, while the top 1% account for 14.9% of posts and the top 10% for 45.6%.](assets/portfolio/03_exchange_concentration.png)

| Metric | Result |
| --- | ---: |
| Exchange posts | 24,316 |
| Unique user IDs | 10,677 |
| Mean posts per user ID | 2.28 |
| Median posts per user ID | 1 |
| User IDs with one post | 7,198 (67.4%) |
| Top 1% of user IDs | 3,619 posts (14.9%) |
| Top 10% of user IDs | 11,082 posts (45.6%) |
| Template-like exchange posts | 12,411 (51.0%) |

`ユーザーID` identifies an account in the export. It does not establish a unique person or distinguish human accounts from automated accounts.

## Results

### Gold 192 classifier evaluation

| Evaluation | Micro F1 | Macro F1 | Additional result |
| --- | ---: | ---: | --- |
| Multi-label threshold | 0.595 | 0.495 | Exact match: 103/192 (0.536) |
| Lenient primary-label match | 0.577 | 0.450 | Hit rate: 118/192 (0.615) |

Lenient per-category F1 scores:

| Category | F1 |
| --- | ---: |
| `交換・取引` | 0.869 |
| `中立` | 0.625 |
| `喜び・満足` | 0.516 |
| `不満・怒り` | 0.471 |
| `欲望・執着` | 0.373 |
| `焦り・競争` | 0.294 |
| `情報共有` | 0.000 |

The classifier is most reliable for exchange posts. It performs poorly on urgency and information sharing, mainly because of missing Japanese inflections and synonyms, incomplete negation handling, and rule interactions.

## Tech Stack

Current repository scripts:

- Python 3
- Matplotlib 3.10.6
- Pillow 12.0.0
- CSV and JSON processing with the Python standard library

Historical notebook workflow, documented but not redistributed or reconstructed:

- Jupyter Notebook
- Gensim / Word2Vec
- MeCab with `mecab-ipadic-neologd`
- TensorFlow Embedding Projector

Supporting tools:

- Git for provenance and reproducibility work
- AI coding agents for repository inspection, pipeline tracing, code revision, and verification

A pinned `requirements.txt` is provided for the current repository scripts. It does not reconstruct the historical notebook-based Word2Vec environment.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── .github/workflows/test.yml      # runs the tests and the sample on every push
├── assets/portfolio/               # README figures, regenerated from data/output
├── baselines/
│   └── hybrid_final_exclusions.csv
├── data/output/                    # local generated data; ignored by Git
├── sample_data/                    # synthetic posts; runnable without the dataset
│   ├── sample_posts.csv
│   └── check_sample_output.py
├── docs/
│   ├── README.md                   # documentation index and reading order
│   ├── 01_PROJECT_TIMELINE.md
│   ├── hybrid_rebuild.md
│   ├── baseline_evaluation.md
│   └── slide_metric_audit.md
├── outputs/                        # local presentation artifacts; ignored by Git
├── build_hybrid_corpus.py
├── classify_sns_rule_based.py
├── evaluate_v2_hybrid_192.py
├── make_portfolio_figures.py
├── normalize_gold_standard_192.py
├── regenerate_slide_assets.py
├── verify_hybrid_rebuild.py
├── verify_slide_assets.py
└── verify_slide_numbers.py
```

Important documentation, with a full index and reading order in
[docs/README.md](docs/README.md):

- [Project Timeline](docs/01_PROJECT_TIMELINE.md)
- [Sentiment Analysis Methodology](sns_sentiment_analysis_guide.md)
- [Hybrid Baseline Rebuild](docs/hybrid_rebuild.md)
- [Classifier Baseline Evaluation](docs/baseline_evaluation.md)
- [Presentation Metric Audit](docs/slide_metric_audit.md)

## Reproducibility and How to Run

### Requirements

Install the dependencies used by the current repository scripts:

```bash
python3 -m pip install -r requirements.txt
```

The reproducible hybrid path requires the six monthly CSV exports and local files under `data/output/`. These files are ignored by Git and are therefore not available in a fresh clone.

The historical cleaning and Word2Vec notebooks are also excluded because their redistribution terms could not be verified. The current public repository therefore documents that legacy path but does not claim that a fresh clone can rerun it end to end.

Run the commands below from the repository root with `python3`.

### Rebuild the hybrid corpus

```bash
python3 build_hybrid_corpus.py \
  --output /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv
```

### Run the classifier

```bash
python3 classify_sns_rule_based.py \
  --input /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv \
  --output /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv
```

### Normalize the Gold 192 dataset

```bash
python3 normalize_gold_standard_192.py \
  --input data/output/gold_standard_192.csv \
  --output /private/tmp/bonbon_rebuild/gold_standard_192_normalized.csv \
  --supplement data/output/gold_supplement_11.csv \
  --hybrid /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv
```

### Verify the rebuild

```bash
python3 verify_hybrid_rebuild.py \
  --rebuild-dir /private/tmp/bonbon_rebuild
```

The verification checks row counts, columns, values, ID sets, ID order, full SHA-256 hashes, Gold label preservation, and repeat-run determinism.

### Regenerate the README figures

```bash
python3 make_portfolio_figures.py
```

The generator reads only existing outputs under `data/output/`. It re-derives every
number it draws and refuses to render if any value stops matching the published
baseline, so the figures cannot drift away from the documented results.

### Run unit tests

```bash
python3 -m unittest \
  test_sentiment_classifier.py \
  test_slide_number_definitions.py
```

## Limitations

- The original Social Insight query, keyword registration date, and export timestamps are not preserved.
- The raw and generated datasets are excluded from Git, so a fresh clone cannot reproduce the analysis by itself.
- `INPUT.csv`, `INPUT_new.csv`, `clean.csv`, and `clean.wakati` contain unresolved lineage or duplication issues.
- The exact MeCab and `mecab-ipadic-neologd` versions used for the historical run are unknown.
- The original source code for the final advertising filter is missing; 391 decisions are preserved as an ID lock.
- Gold 192 is not a simple random sample of the hybrid corpus.
- The rule-based classifier has known weaknesses in Japanese inflection, negation, synonym coverage, and category interactions.
- Word2Vec training used repeated text blocks and an unlocked environment, so exact retraining equivalence is not guaranteed.
- The lab-provided cleaning and Word2Vec notebooks are documented but not redistributed; the historical word-level workflow is therefore not independently runnable from this repository alone.
- The repository does not contain the code that originally generated some legacy Office and Canva artifacts.

## Future Work

- Rebuild the pipeline as explicit provenance-preserving tables, from raw posts through filtering, classification, evaluation, and exchange aggregation.
- Replace shell-based CSV concatenation and field extraction with schema-aware parsing.
- Create a representative evaluation sample directly from the hybrid corpus and document the annotation policy.
- Improve Japanese linguistic coverage and compare the rule-based baseline with alternative classifiers.
- Reconstruct and separately pin the historical MeCab and Word2Vec environment, and investigate the repeated corpus blocks.
- Replace the legacy notebook-dependent cleaning and Word2Vec steps with independently authored, documented implementations if that workflow is continued.
- Add a fully resolved lockfile for the current scripts if exact transitive dependency reproduction is required, and add a manifest for local, non-Git data assets.
- Reimplement suitable extraction and aggregation steps in SQL while retaining Python for NLP and visualization.
