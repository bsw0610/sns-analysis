# Reproducibility and execution

[Back to the repository README](../README.md) · [Documentation index](README.md)

## Reproducibility and How to Run

### Requirements

Install the dependencies used by the current repository scripts:

```bash
python3 -m pip install -r requirements.txt
```

The reproducible hybrid path requires the six monthly CSV exports and local files under `data/output/`. These files are ignored by Git and are therefore not available in a fresh clone.

The historical cleaning and Word2Vec notebooks are also excluded because their redistribution terms could not be verified. The current public repository therefore documents that legacy path but does not claim that a fresh clone can rerun it end to end.

#### Execution environments

Three different environments are involved and they are not interchangeable.

| Path | Interpreter | Verified on |
| --- | --- | --- |
| Public sample (classifier and sample check) | Python 3.9 or newer | 3.9.6 locally; CI runs 3.11, 3.12 and 3.13 |
| Unit tests | **Python 3.10 or newer** | CI runs 3.11, 3.12 and 3.13. `test_evaluation_inputs.py` runs the evaluation script itself, so on 3.9.6 it fails at that script's 3.10 check |
| Research reproduction scripts | **Python 3.10 or newer** | 3.13.9 locally |
| Historical Word2Vec workflow | not reproducible here | excluded, see above |

Two separate things put the research floor at Python 3.10, and neither can be worked
around by installing something:

- The scripts use `zip(..., strict=True)`, which Python 3.10 added. On 3.9 they now stop
  immediately with a message naming the requirement instead of failing part way through
  with `TypeError: zip() takes no keyword arguments`, which reads as a data problem
  rather than an environment one.
- `requirements.txt` pins `matplotlib==3.10.6`, which declares `Requires-Python >= 3.10`.
  On 3.9 that version is not installable at all — the 3.9-compatible line stops at 3.9.4
  — so the pinned dependency set is itself a 3.10 requirement. **A working sample run does not mean the
research scripts will run on the same interpreter** — the sample path is the one CI
exercises, and it is the more permissive of the two.

Run the commands below from the repository root with `python3`. The paths shown for `--output` and `--rebuild-dir` are the script defaults, so they can be omitted; `rebuild/` is ignored by Git and is kept separate from `data/output/` so the preserved baselines are never overwritten.

### Rebuild the hybrid corpus

```bash
python3 build_hybrid_corpus.py \
  --output rebuild/2511-2604_hybrid.csv
```

### Run the classifier

```bash
python3 classify_sns_rule_based.py \
  --input rebuild/2511-2604_hybrid.csv \
  --output rebuild/sentiment_classified_hybrid.csv
```

### Normalize the Gold 192 dataset

```bash
python3 normalize_gold_standard_192.py \
  --input data/output/gold_standard_192.csv \
  --output rebuild/gold_standard_192_normalized.csv \
  --supplement data/output/gold_supplement_11.csv \
  --hybrid rebuild/sentiment_classified_hybrid.csv
```

### Verify the rebuild

```bash
python3 verify_hybrid_rebuild.py \
  --rebuild-dir rebuild
```

The verification checks row counts, columns, values, ID sets, ID order, full SHA-256 hashes, Gold label preservation, and repeat-run determinism.

### Regenerate the README figures

```bash
python3 make_portfolio_figures.py
```

The generator reads only existing outputs under `data/output/`. It re-derives the
numbers it draws and refuses to render if any value stops matching the published
baseline, so the figures cannot drift away from the documented results. The one
exception is the two guessing baselines in the evaluation figure (0.281 and 0.206):
the benchmark code is not published, so they are copied from
[Classifier Benchmark](classifier_benchmark.md).

### Run unit tests

```bash
python3 -m unittest \
  test_sentiment_classifier.py \
  test_slide_number_definitions.py \
  test_evaluation_report.py \
  test_evaluation_inputs.py \
  test_sample_output.py
```

These are the same five files CI runs.

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
- AI coding agents (Codex, later Claude Code), which wrote the code, tests, and documents in this repository and were used for repository inspection, pipeline tracing, and verification

A pinned `requirements.txt` is provided for the current repository scripts. It does not reconstruct the historical notebook-based Word2Vec environment.


## Historical data and methods

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


## Future Work

- Rebuild the pipeline as explicit provenance-preserving tables, from raw posts through filtering, classification, evaluation, and exchange aggregation.
- Replace shell-based CSV concatenation and field extraction with schema-aware parsing.
- Create a representative evaluation sample directly from the hybrid corpus and document the annotation policy.
- Improve Japanese linguistic coverage. One trained classifier has been compared with the rules ([Classifier Benchmark](classifier_benchmark.md)); models that read the text, such as a large language model, have not.
- Reconstruct and separately pin the historical MeCab and Word2Vec environment, and investigate the repeated corpus blocks.
- Replace the legacy notebook-dependent cleaning and Word2Vec steps with independently authored, documented implementations if that workflow is continued.
- Add a fully resolved lockfile for the current scripts if exact transitive dependency reproduction is required, and add a manifest for local, non-Git data assets.
