# Project Timeline

## 1. Purpose

This document reconstructs, from evidence in the current repository, how the
Bonbon Drop Seal X/Twitter analysis project identified problems, made
decisions, and produced its outputs.

It records causal relationships rather than only file-creation order:

```text
Problem identified → decision → change or analysis → result → verification → next step
```

The reconstruction is based on a read-only investigation completed on
2026-08-14, the current Git history, and the user's pre-Codex data-analysis
operations guide. The investigation did not run Python scripts or notebooks and
did not modify the existing code, data, or documentation.

## 2. Evidence and Confidence Labels

| Label | Meaning |
| --- | --- |
| `[CODE]` | Confirmed in a Python or Notebook implementation |
| `[GIT]` | Confirmed in a commit, branch, or diff |
| `[DATA]` | Confirmed in an actual CSV, JSON, model, PNG, PPTX, or similar file |
| `[DOC]` | Confirmed in the README or a document under `docs/` |
| `[USER-PROVIDED]` | Confirmed in the user's historical operations guide or work description |
| `[UNCERTAIN]` | Cannot be established from the current repository |

The first Git commit is dated 2026-07-30. Earlier dates are therefore inferred
in this order:

1. Explicit dates in notebook execution logs or documents
2. Contents of dated output directories and files
3. File modification timestamps
4. The historical operations guide and work description supplied by the user

Modification timestamps alone are not used to establish causality. Pre-Git
ordering is reconstructed only as far as the evidence allows; unresolved points
are marked `[UNCERTAIN]`.

## 3. Current Baseline

The best-preserved analysis path with a documented reproduction procedure is:

```text
Six monthly source CSVs, 136,288 records
  → hybrid ad-filtered corpus, 110,918 records
  → v2.0.0 rule-based classification into seven categories
  → evaluation on Gold 192
  → analysis of 24,316 exchange/transaction posts and 10,677 user IDs
  → slide 13–16 candidate generation and verification
```

This document treats that path as the **current authoritative baseline**. The
old 109,037-record, final 114,518-record, and legacy 114,527-record outputs are
historical artifacts and must not be mixed with the current baseline.
[CODE][DOC][DATA]

## 4. Summary

| Period | Stage | Main result | Confidence |
| --- | --- | --- | --- |
| 2025-11–2026-04 | Monthly SNS data acquisition from UserLocal | Six Twitter CSVs, 136,288 records total | Tool and general procedure confirmed; registration conditions and download dates unknown |
| Through 2026-06-04 | Merge, text extraction, cleaning, MeCab, and Word2Vec | `clean.model` with 350 dimensions and a vocabulary of 71,408 | Standard procedure and training run confirmed; some intermediate files uncertain |
| After 2026-06 | Embedding Projector cluster analysis | Exploration using `vector.tsv` and `metadata.tsv` | Procedure confirmed; actual analysis record missing |
| After 2026-06 | Part-of-speech word-occurrence shares | Word occurrences ÷ total posts | Procedure only; no repository output confirmed |
| 2026-07-16 | Legacy emotion-analysis presentation | Four-slide PPTX and review files based on 109,037 records | Outputs confirmed; Office-generation source missing |
| 2026-07-28 | Classifier audit and Gold 189 evaluation | Audit report; micro F1 0.576/0.594 | Confirmed by documents and data |
| 2026-07-29 | Investigation of total-count discrepancies | 136,301 and 33,988 deemed unreproducible | Confirmed by document |
| 2026-07-30 | Hybrid baseline established | 110,918 records, Gold 192, reproduction and verification code | Confirmed by Git, documents, and data |
| 2026-07-30 | Metric definitions and slide redesign | p13–p16 generation and verification procedure | Confirmed by Git |
| 2026-08-14 | Preservation of latest work and creation of learning branch | `80d47c1`, `relearn/sql-rebuild` | Confirmed by Git |
| 2026-08-14 | Portfolio documentation and public-release hygiene | English documentation, Japanese README summary, source-notebook exclusion | Confirmed by Git and documentation |

## 5. Detailed Timeline

### 5.1 2025-11–2026-04 — Monthly Source Data from UserLocal

**Purpose**

Collect Japanese SNS posts about ボンボンドロップシール by month for use as
the source of subsequent text analysis. [DOC][DATA][USER-PROVIDED]

**Inputs**

- X/Twitter posts downloaded from UserLocal's paid Social Insight service
  [USER-PROVIDED]
- The operations guide stated that Social Insight provided Twitter data from
  2014 onward and Instagram text data from 2015 onward. The current project
  folder contains only monthly Twitter CSVs; there is no evidence that Instagram
  data was used in the analysis. [USER-PROVIDED][DATA]

**Processing**

- The documented procedure registered a keyword under `クチコミ分析`, selected
  Twitter, chose a period, and used
  `CSVダウンロード → UTF-8 → 投稿一覧`. The interface accepted at most three
  months per selection, so longer periods had to be split. [USER-PROVIDED]
- Six monthly CSVs were retained for November 2025 through April 2026.
- Each CSV has 30 columns and duplicate `投稿ID`- and `ユーザーID`-family column
  names. Later Python code distinguishes the duplicate names when reading them.
  [CODE][DATA]

**Outputs**

| File | Logical records |
| --- | ---: |
| `202511.csv` | 12,907 |
| `202512.csv` | 17,037 |
| `202601.csv` | 24,721 |
| `202602.csv` | 31,597 |
| `202603.csv` | 20,260 |
| `202604.csv` | 29,766 |
| **Total** | **136,288** |

**Verification**

- The monthly logical record counts sum to 136,288.
- All 136,288 post IDs are unique.
- Post text may contain line breaks, so physical line counts such as `wc -l`
  must not be used as record counts. [DATA][DOC]

**Issues Identified**

- The tool and general download procedure are known, but the exact registered
  keyword, registration date, individual download dates, and selected periods
  are not retained. [USER-PROVIDED][UNCERTAIN]
- The operations guide says data after keyword registration is nearly complete,
  while earlier data is sampled. Without the registration date, monthly
  completeness for 2025-11–2026-04 cannot be assessed. [USER-PROVIDED]
- The service limit at the time was 40 new keywords per month and 20
  concurrently registered keywords. Whether this affected the dataset is
  unknown. [USER-PROVIDED]
- `INPUT.csv` has 136,293 rows and 136,289 unique IDs, inconsistent with the
  monthly total. As confirmed later, this exactly matches the effect of
  `cat *.csv` retaining five additional headers as data rows after the first
  header. [DATA][USER-PROVIDED]

**Security and External Dependencies**

- Login IDs and authentication information are unnecessary for lineage and are
  not recorded here.
- Acquisition depended on a UserLocal paid license costing JPY 320,000 per year
  at the time. Reacquiring the same source requires service access and the
  original keyword-registration conditions. [USER-PROVIDED]
- Detailed operations and error handling depended on step-specific and error
  channels in Slack. Those channels are not in the repository, so the operations
  record is incomplete. [USER-PROVIDED][UNCERTAIN]

**Reason for the Next Stage**

The monthly post text had to be combined, cleaned, and represented at word level
for text analysis. [DOC]

### 5.2 After 2026-04 Through 2026-06-04 — Merge, Cleaning, MeCab, and Word2Vec

The standard sequence is confirmed by the user-provided operations guide.
However, the exact run that produced each current file and the accuracy of some
intermediate results cannot be fully reconstructed.
[USER-PROVIDED][UNCERTAIN]

The two notebooks used in this stage were supplied through a university seminar
or lab. They were inspected locally without execution during the repository
audit, but their redistribution terms could not be verified. Their files,
source cells, and outputs are therefore excluded from the public Git history;
this section records only the observed processing role and evidence needed to
understand the historical data lineage. [CODE][DOC]

**Purpose**

Remove URLs and other unwanted elements from Japanese posts, segment text into
morphemes, and learn semantic relationships between words as Word2Vec vectors.
[CODE][DOC]

**Inputs**

- `INPUT.csv`: 136,293 logical rows, 136,289 unique IDs
- `INPUT_new.csv`: 143,921 text rows
- `clean.csv`: approximately 847 MB, 3,652,228 physical lines, no header
- `clean.wakati`: approximately 973 MB, 3,652,228 lines

The README explains some relationships between these files, but the code that
creates all of them is not retained. [DOC][DATA][UNCERTAIN]

**Processing**

- Downloaded CSVs and two notebooks were collected in the desktop `data`
  directory.
- `cat *.csv > INPUT.csv` physically concatenated the monthly CSVs. It did not
  remove each CSV's header. The five extra rows, one extra unique ID, and four
  duplicates relative to the monthly total exactly match the combined six
  headers. [USER-PROVIDED][DATA]
- `cat INPUT.csv | cut -d "," -f 9 > INPUT_new.csv` extracted the ninth
  comma-delimited field as post text. [USER-PROVIDED]
- `2026_Twitter用データクリーニング .ipynb` removes punctuation, brackets and
  enclosed text, URLs, hashtags, mentions, Latin letters, and spaces.
- The notebook's actual output is `C_INPUT_new.csv`, which does not match the
  README's described generation of `clean.csv`.
- Ad removal was a repeated manual process: inspect the cleaned file, identify
  characteristic terms in obvious advertisements, and delete posts containing
  those terms in Sakura Editor or the terminal. The operations guide describes
  this as the most difficult step. The current
  `filter_ads_202511_202604.py` is a later preserved implementation and is not
  assumed to reproduce the original manual procedure.
  [USER-PROVIDED][CODE]
- The standard segmentation command used MeCab with
  `mecab-ipadic-neologd`, `-Owakati`, and buffer `81920` to create a `.wakati`
  file. Dictionary paths differed across Intel Mac, Apple Silicon Mac, and
  Windows. [USER-PROVIDED]
- The Word2Vec notebook reads `clean.wakati` and trains a skip-gram model with
  `vector_size=350`, `window=15`, `min_count=5`, `negative=10`, and
  `epochs=10`. [CODE]

**Outputs**

- `clean.model`
- `clean.model.wv.vectors.npy`
- `clean.model.syn1neg.npy`
- `vector.tsv`
- `metadata.tsv`

Notebook logs show that training completed on 2026-06-04 using Python 3.8.20,
gensim 4.3.3, and macOS ARM, with a vocabulary of 71,408.
[CODE][DATA]

**Verification**

- The notebook training log and the model-array shape `(71408, 350)` match.
  [CODE][DATA]

**Issues Identified**

- The five-row difference in `INPUT.csv` is explained by accumulated headers,
  but physical concatenation is not a structural CSV merge and leaves
  intermediate headers in the data.
- `cut -d "," -f 9` does not understand CSV quoting, commas inside fields, or
  multiline fields. The additional 7,628 rows in `INPUT_new.csv` may be related
  to this conversion, but the exact cause cannot be established from current
  evidence. [USER-PROVIDED][DATA][UNCERTAIN]
- `clean.csv` and `clean.wakati` contain at least 31 repeated blocks of 117,153
  lines. The cause is unknown.
- The morphological analyzer family is confirmed as MeCab with
  `mecab-ipadic-neologd`. The exact MeCab and dictionary versions, actual path,
  input filename, and execution log from the project run are missing. The
  notebook fallback also references an undefined `WakatiCorpus`.
  [USER-PROVIDED][CODE][UNCERTAIN]
- The model vocabulary contains 71,408 entries, while the current `vector.tsv`
  and `metadata.tsv` each contain 17,298 rows. This does not match the current
  notebook's full-vocabulary export.
- If the repeated corpus was used for training, word frequencies and the meaning
  of `min_count=5` may be distorted. [CODE][DATA][UNCERTAIN]

**Reason for the Next Stage**

The original next step was to upload the vectors and word labels to Embedding
Projector to explore groups of similar words, and separately calculate
part-of-speech word frequencies. [USER-PROVIDED]

### 5.3 [UNCERTAIN] After 2026-06 — Cluster Analysis and POS Word Shares

**Purpose**

- Explore semantic groups by automatically grouping similar words without
  predefined labels.
- Divide word occurrence count by total post count to estimate how often a word
  appears in the full corpus. [USER-PROVIDED]

**Inputs**

- `vector.tsv`
- `metadata.tsv`
- Cleaned output from which part-of-speech occurrence counts and the total post
  count could be calculated [USER-PROVIDED][UNCERTAIN]

**Processing**

- Upload `vector.tsv` and `metadata.tsv` to TensorFlow Embedding Projector and
  inspect the word-vector space visually.
- Calculate each part-of-speech word share as
  `word occurrence count ÷ total post count`. [USER-PROVIDED]

**Output and Verification Status**

- The repository contains 17,298-row projector TSV files, but the selection
  criterion for this subset of the 71,408-word model vocabulary is unknown.
- No record of selected clusters, interpretations, screenshots, or result tables
  was found.
- No code or output for the POS word-occurrence analysis was found. The original
  instructions referred to the `#2_embedding_projector` and
  `#エディタ_クリーニング` Slack channels. [DATA][USER-PROVIDED][UNCERTAIN]

**Reason for the Next Stage**

Word-centered analysis alone could not directly measure post-level emotion and
behavior, exchange activity, or account concentration. A separate rule-based
post-classification path appears to have been added later, but the decision
record linking the two analyses is missing. [UNCERTAIN]

### 5.4 [UNCERTAIN] 2026-06–2026-07-16 — Legacy Ad Removal and Emotion/Behavior Analysis

**Problem or Objective**

The source posts contained advertising and commercial content. The project
needed to remove these posts and classify the remainder into seven emotion and
behavior categories. [CODE][DOC]

**Inputs**

- Six monthly CSVs, 136,288 records
- `filter_ads_202511_202604.py`
- `classify_sns_rule_based.py`

**Processing**

1. Deduplicate post IDs.
2. Remove advertisements using user keywords and additional regular
   expressions.
3. Classify the remaining posts into seven categories: dissatisfaction,
   urgency, exchange/transaction, desire, joy, information sharing, and neutral.
4. Create monthly and category aggregates and review samples. [CODE]

**Outputs**

- Legacy ad-filtered corpus `data/output/2511-2604.csv`: 109,037 records
- `data/output/sentiment_classified_2511-2604.csv`
- `data/output/sentiment_summary_2511-2604.csv`
- `data/output/sentiment_validation_sample_2511-2604.csv`
- Four-slide PPTX, PNG, Excel, JSON, and Notebook under
  `outputs/sentiment-analysis-20260716/` [DATA]

**Decision at the Time**

The 2026-07-16 outputs used 109,037 records as the analysis baseline. Removing
21,377 keyword matches and 5,874 additional-rule matches from 136,288 gives
109,037. [DOC][DATA]

**Verification**

- The ad-removal summary satisfies
  `136,288 − 21,377 − 5,874 = 109,037`.
- The artifacts remain, but the source code that directly creates the PPTX and
  Excel files is absent.
- Every cell in the preserved presentation notebook is unexecuted, so that
  notebook is not evidence of a successful run. [DATA][CODE][DOC]

**Issues Identified**

- Broad keywords such as `お知らせ`, `リポスト`, and `再入荷情報` also remove
  non-advertising informational posts.
- The ad filter removes 67.7% of information-sharing posts but only 5.8% of
  exchange/transaction posts, creating selection bias in category composition.
- The manual-decision column in the 210-record review sheet is empty, so no
  measured accuracy was available at that stage. [CODE][DOC][DATA]

**Reason for the Next Stage**

Trustworthy presentation metrics required an audit of ad-removal and classifier
bias and a performance evaluation against human-labeled Gold labels. [DOC]

### 5.5 2026-07-28 — Classifier Audit and Gold 189 Evaluation

**Problem Identified**

The rule-based classifications had not been validated against actual meaning,
and the priorities documented in the guide did not match the code's behavior.
[DOC][CODE]

**Inputs**

- Legacy 109,037-record classification output
- 200 records drawn with fixed seed 20260728
- IDs overlapping the existing 100-record sample were excluded before sampling

**Processing**

- Human review of 200 records
- Exclusion of 11 unresolved cases to create Gold 189
- Evaluation using both a lenient criterion, where the single prediction could
  match any Gold label, and a multi-label criterion using every category scoring
  at least 1.8
- Audit of classification rules, missing inflections, negation and desire
  expressions, the Japanese `\b交換\b` problem, and the priority mismatch between
  documentation and implementation [CODE][DOC][DATA]

**Outputs**

- `data/output/gold_standard_200.csv`
- `data/output/gold_standard_labeled_189of200.csv`
- `docs/baseline_v2.md`
- `data/output/classification_audit_report.md`
- Non-exchange negotiation-expression sample [DATA][DOC]

**Results and Verification**

- Lenient evaluation: micro F1 0.576, macro F1 0.451, hit rate 0.614
- Multi-label evaluation: micro F1 0.594, macro F1 0.496, exact match 0.534
- Exchange/transaction was relatively strong; urgency and information sharing
  had low recall.
- No statistically confirmed accuracy improvement from v1 to v2. [DOC]

**Issues Identified**

- Gold 189 was sampled from the legacy 109,037-record corpus.
- Some of the 11 unresolved records were noted as ads, indicating that ads may
  remain after ad filtering.
- Single-label classification cannot fully represent posts containing multiple
  simultaneous emotion or behavior signals. [DOC]

**Reason for the Next Stage**

Beyond classifier performance, the team needed to determine whether the total
and exchange-post counts used in the presentation were reproducible from actual
files. [DOC]

### 5.6 2026-07-29 — Investigation of Presentation-Count Discrepancies

**Problem Identified**

The approximately 136,301 total and 33,988 exchange posts in the slides
conflicted with the 109,037 total and 23,134 exchange posts then under
verification. [DOC]

**Processing**

- Compare record counts and IDs across monthly source files, `INPUT.csv`, and
  ad-filtered outputs.
- Check reproduction of 109,037 and its ad-removal arithmetic.
- Compare the retained v1 and v2 classifiers on both 109,037 and 136,288
  records.
- Separate the Word2Vec and emotion-analysis input lineages. [CODE][DOC][DATA]

**Output**

- `docs/task0_total_count.md`

**Decision and Result**

- No dataset/classifier combination in the current repository reproduces
  136,301 or 33,988.
- The document recommended 109,037 as the presentation baseline at that time,
  with a required disclosure that the legacy ad filter over-removed
  information-sharing posts. [DOC]

**Reason for the Next Stage**

A new baseline was needed that reduced the old filter's over-removal while
preserving decisions embodied in the existing `final` output. [DOC][GIT]

### 5.7 Around 01:00 on 2026-07-30 — Hybrid 110,918 and Gold 192

The outputs from this stage were created shortly before the first Git commit.
The original hybrid-generation code from that run is not retained. A later Git
commit added a reproduction procedure based on the actual ID differences.
[DATA][GIT][UNCERTAIN]

**Problems Identified**

- The legacy 109,037-record corpus over-removed information-sharing posts.
- The 114,518-record `final` file existed without its filter source.
- Gold 189 represented only the legacy corpus and omitted restored hybrid
  records. [DOC][DATA]

**Relationships Confirmed from the Outputs**

- Hybrid matches, by ID and order, the 110,918 records obtained by excluding
  5,874 additional ads from `final`.
- Hybrid contains 2,015 more records than the legacy 109,037-record corpus.
- File comparison confirms these relationships, but not the exact code or
  judgment that originally created hybrid. [DATA][DOC][UNCERTAIN]

**Confirmed Processing**

- A 110,918-record hybrid corpus was created in the monthly source ID order.
- The same v2.0.0 classifier was applied.
- Gold 192 was created by adding three surviving restored-hybrid records to
  Gold 189. [CODE][DOC][DATA]

**Outputs**

- `data/output/2511-2604_hybrid.csv`: 110,918 records
- `data/output/sentiment_classified_hybrid.csv`: 110,918 records
- `data/output/gold_standard_192.csv`: 192 records
- `data/output/gold_standard_192_normalized.csv`: 192 records × 12 columns
- `data/output/exchange_accounts.csv`

**Results**

- Primary category 交換・取引: 24,316 records
- Related unique user IDs: 10,677
- Gold 192 lenient micro F1: 0.577
- Gold 192 multi-label micro F1: 0.595
- Exact match: 103/192, 0.536 [DOC][DATA]

**Issues Identified**

- `gold_supplement_11.csv` has empty labels, while all three supplements in
  Gold 192 have `交換取引=1`. The annotator, time, and rationale are unknown.
- Gold 192 is not a direct simple random sample of the full hybrid corpus.
  [CODE][DOC][UNCERTAIN]

**Reason for the Next Stage**

Retaining only output files was insufficient to rebuild the baseline. Instead
of guessing the original final filter, the actual old/final/hybrid ID
differences had to lock the selection decisions. Gold normalization also needed
to be preserved through code, hashes, and repeated-run verification.
[DOC][GIT]

### 5.8 2026-07-30 03:07 — First Git Snapshot

**Commit**: `9545d4e chore: preserve existing Claude Code project`

**Purpose and Decision**

Preserve the existing code, analysis documents, generation procedures, and the
then-local reference notebooks developed or used before Git so the project
could be audited. The two lab-provided notebooks were later removed from all
public-release history because redistribution permission was not established.
[GIT][DOC]

**Major Preserved Areas**

- Historical Word2Vec and cleaning workflow evidence
- Ad-removal and rule-based classification code
- Gold generation and evaluation code
- Sentiment-analysis guide and baseline documents
- Slide-metric verification and planning documents

**Limitation**

This commit does not reconstruct individual commits for the earlier work. Work
from May through July entered Git as one initial snapshot, and most large data
and output files are ignored by `.gitignore`. [GIT]

### 5.9 2026-07-30 03:46 — Reproducible Hybrid Baseline

**Commit**: `f033a26 feat: make hybrid analysis baseline reproducible`

**Problem Identified**

Hybrid output files existed, but the final ad-filter source was missing. The
non-normalized 20-column Gold 192 structure and supplement-provenance issue also
made an exact rebuild difficult. [DOC][GIT]

**Changes**

- `baselines/hybrid_final_exclusions.csv`: lock decisions for 391 IDs
- `build_hybrid_corpus.py`: rebuild hybrid from the monthly sources
- `normalize_gold_standard_192.py`: preserve existing manual labels in a
  normalized 12-column file
- `verify_hybrid_rebuild.py`: verify rows, columns, IDs, order, cells, SHA-256,
  and repeated-run determinism
- `docs/hybrid_rebuild.md`: record reproduction procedure and limitations
  [GIT][DOC]

**Verification**

The document records fixed SHA-256 values for hybrid, classified, and Gold
reference files and for normalized outputs. The build script writes only to a
temporary directory and does not overwrite reference files. [CODE][DOC]

**Reason for the Next Stage**

Even after fixing the data baseline, slides differed in denominator, Gold
source, percentage rounding, and top-account definitions. The metric definitions
needed to be standardized. [GIT][DOC]

### 5.10 2026-07-30 04:38 — Standardized Slide Metrics and Gold Source

**Commit**: `cdc6226 fix: standardize slide metrics and gold dataset source`

**Problem Identified**

The slide specification, generators, and verifier differed in their definitions
of structured exchange format, top-account scope, and Gold-file fallback.
[DOC][GIT]

**Changes**

- Centralized shared proportion, CI, and verification definitions in
  `slide_number_definitions.py`.
- Fixed the normalized Gold 192 file as the authoritative source and removed
  implicit fallback.
- Added a metric-definition audit and regression tests.
- Aligned related generators, evaluators, verifiers, and documents to the same
  definitions. [GIT]

**Outputs and Verification**

- `docs/slide_number_definition_audit.md`
- `test_slide_number_definitions.py`
- Updated `docs/slide_numbers_check.md`

**Reason for the Next Stage**

After standardizing definitions, p13–p16 visuals had to be regenerated with
consistent dimensions and evidence files. [GIT][DOC]

### 5.11 2026-07-30 04:58–13:50 — Regenerated Slide Candidates and Redesigned Slides 10–16

**Commits**

- `4c1fb30 feat: regenerate validated slide assets`
- `3fd5759 chore: update gitignore`
- `8fbc218 feat: rework emotion analysis slides 10-16`

**Purpose**

Generate 1920×1080 p13–p16 candidates from the locked hybrid, Gold, and sample
inputs, and ensure that the presentation narrative and visuals use the same
metric definitions. [GIT][DOC]

**Changes**

- Added and revised p13–p16 candidate generation in
  `regenerate_slide_assets.py`.
- Added source-hash, metrics-JSON, PNG-dimension, and manifest checks in
  `verify_slide_assets.py`.
- Reworked `docs/slide_assets_regeneration.md` and
  `docs/slide_plan_10-16.md` around the 110,918-record hybrid baseline.
- Added temporary exports, handoff files, and Canva files to `.gitignore`. [GIT]

**Verification and Limitations**

- The documents record successful earlier verification.
- The current repository contains only older-size p13–p15 PNGs. The latest
  1920×1080 p13–p16 candidates, metrics JSON, and manifest are absent because
  the generator writes them to external temporary directories.
- There is no code that automatically updates Canva. [CODE][DOC][DATA]

**Reason for the Next Stage**

The latest document and generator changes created during presentation editing
had to be preserved, followed by a separate branch for relearning the existing
project. [GIT][DOC]

### 5.12 2026-08-14 — Preserved Latest Slide Work and Created SQL Relearning Branch

**Commit**: `80d47c1 wip: preserve latest slide regeneration work`

**Processing**

- Preserved the Japanese presentation script
  `docs/presentation_script_10-16_ja.md`.
- Removed on-screen quotations from slide 16 and adjusted the related plan and
  generation code.
- Preserved the then-uncommitted slide work in one WIP commit. [GIT]

### 5.13 2026-08-14 — Prepared the Repository for Public Portfolio Use

**Commit**: `5a518d7 docs: internationalize portfolio documentation`

**Changes and Decisions**

- Standardized public Markdown documentation in English and added a concise
  Japanese overview to the root README.
- Fast-forwarded `main` to the completed analysis and documentation history and
  removed fully merged stale local branches.
- Rewrote author and committer metadata to use the repository owner's GitHub
  noreply address.
- Removed the two lab-provided cleaning and Word2Vec notebooks from every
  reachable local branch before the first public push because redistribution
  permission was not established.
- Retained a factual description of the notebooks' observed roles without
  copying their source code or cell outputs. [GIT][DOC]

**Current Branch Relationships**

```text
main
└─ relearn/sql-rebuild
   (aligned before the first public push)
```

The public `origin` points to `git@github.com:bsw0610/sns-analysis.git`. The
remote repository was empty when public-release preparation began. No stale
feature branches or notebook paths remain in the reachable local history.
[GIT]

**Purpose of the Current Stage**

Before immediately recalculating results or replacing them with SQL, reconstruct
the actual work order and uncertainties scattered across code, Git, data, and
documentation.

## 6. Established Decisions

### Decision 1: Use the 136,288 Monthly CSV Records as Emotion-Analysis Sources

`INPUT.csv` was physically combined with `cat *.csv` and contains five
intermediate headers. `INPUT_new.csv` was created with
`cut -d "," -f 9` rather than a CSV-aware parser. Their record structures do not
match the monthly sources, so the six monthly CSVs are the source for emotion
analysis and future SQL reconstruction. The Word2Vec path is treated as a
separate legacy workflow. [USER-PROVIDED][DOC][DATA]

### Decision 2: Use Hybrid 110,918 as the Current Analysis Baseline

Retain the legacy 109,037-record and final 114,518-record files, but do not use
them as the current denominator. Hybrid restores 2,015 over-removed records and
reproducibly locks both additional-ad exclusions and 391-ID decisions.
[CODE][DOC][GIT]

### Decision 3: Use Gold 192 for Current Evaluation with Representativeness Limits

Gold 192 adds three supplements to Gold 189 from the legacy corpus. It is not a
simple probability sample of the full hybrid corpus, and the manual-annotation
provenance of the three supplements is unclear. Report these limitations with
performance values. [DOC][DATA]

### Decision 4: Separate Classifier Output from Classifier Quality

Preserve v2.0.0 classification output to reproduce the current baseline, but do
not treat it as ground truth. Missing Japanese inflections, `\b交換\b`, negation
and desire expressions, priority-implementation differences, and low
per-category performance remain separate improvement targets. [CODE][DOC]

### Decision 5: Do Not Guess Unclear Historical Rules

For source-less processes such as the final ad filter and manual supplement
decisions, and for clean/wakati generation where only a general procedure is
known, preserve outputs and ID/hash evidence and mark the link `[UNCERTAIN]`.
Do not overwrite historical decisions with a guessed implementation.
[USER-PROVIDED][DOC][GIT]

## 7. Open Questions

### Source Data and Preprocessing

- Exact Social Insight search keyword, keyword registration date, download
  dates, and selected periods
- Pre-registration sampling rate and monthly completeness
- Exact reason `INPUT_new.csv` reached 143,921 rows and extent of CSV structural
  damage
- Whether a corpus exists from before the 117,153-line repetition
- Exact MeCab and `mecab-ipadic-neologd` versions, execution paths, and input
  mapping

### Ad Removal and Classification

- Original ad-filter rules that created `2511-2604_final.csv`
- Annotator and rationale for the three Gold supplement decisions
- Multi-label policy, neutral definition, and annotator-disagreement resolution
- Whether a new sample representative of the full hybrid corpus is needed

### Word2Vec and Artifacts

- Source of the 17,298-row `metadata.tsv` and `vector.tsv` files
- Effect of the repeated corpus on Word2Vec
- Clusters selected in Embedding Projector and their interpretations
- Code, denominator, and output for POS word-occurrence shares
- Source code for the legacy PPTX and Excel files
- Latest p13–p16 candidates and record of Canva application

### Reproduction Environment

- Requirements or lockfile fixing Python and library versions
- Schema, hash, and manifest policy for source data excluded from Git

## 8. Handoff Criteria

This document provides the backbone of the project history. The next data-lineage
document should follow these principles:

1. Fix the current baseline as
   `136,288 → 110,918 → classification → Gold 192 → exchange analysis`.
2. Do not combine Word2Vec and emotion-analysis paths into one continuous
   pipeline.
3. Record logical count, ID key, generator, input, status, and hash-retention
   state for every dataset.
4. Distinguish old, final, and hybrid roles as `legacy`, `comparison`, and
   `authoritative`.
5. Do not draw a solid lineage edge where code is absent; mark it
   `[UNCERTAIN]`.

## 9. Primary Evidence

- `README.md`
- `docs/task0_total_count.md`
- `data/output/classification_audit_report.md`
- `docs/baseline_v2.md`
- `docs/baseline_hybrid.md`
- `docs/hybrid_rebuild.md`
- `docs/slide_number_definition_audit.md`
- `docs/slide_numbers_check.md`
- `docs/slide_assets_regeneration.md`
- `docs/slide_plan_10-16.md`
- `filter_ads_202511_202604.py`
- `classify_sns_rule_based.py`
- `build_hybrid_corpus.py`
- `normalize_gold_standard_192.py`
- `verify_hybrid_rebuild.py`
- `regenerate_slide_assets.py`
- `verify_slide_assets.py`
- Two lab-provided Word2Vec and cleaning notebooks, inspected locally without
  execution and intentionally excluded from the public Git history
- User-provided `データ分析タイムライン` operations guide
- Social Insight keyword configuration manual:
  <https://press-files.userlocal.jp/pdf/social_keyword_setting.pdf>
- Git commits `9545d4e` through `5a518d7`
