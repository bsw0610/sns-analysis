# Script reference

Run commands from the repository root. [Reproducibility and execution](reproducibility.md) describes inputs and commands.

### Scripts

Every Python file in the repository root is listed here, so that no file is
left ambiguous between current and legacy code.

**Pipeline** — building and classifying the corpus.

| File | Role |
| --- | --- |
| `filter_ads_202511_202604.py` | Advertising rules and monthly-export loading; the shared source of the filter definitions. |
| `build_hybrid_corpus.py` | Rebuilds the 110,918-post hybrid corpus, applying the ID lock for the decisions whose original code is missing. |
| `classify_sns_rule_based.py` | The v2.0.0 rule-based classifier. |
| `normalize_gold_standard_192.py` | Produces the authoritative Gold 192 evaluation set from the 20-column source archive. |
| `evaluate_v2_hybrid_192.py` | Scores the classifier against Gold 192 under both criteria. |
| `slide_number_definitions.py` | Shared metric definitions used by the reporting and verification scripts. |

**Verification** — checking that results still reproduce.

| File | Role |
| --- | --- |
| `verify_hybrid_rebuild.py` | Row counts, ID sets and order, SHA-256 hashes, label preservation, and repeat-run determinism for the rebuild. |
| `verify_slide_numbers.py` | Recomputes 96 slide figures from the data and compares them with expected values written into the script, transcribed from the 2026-07-30 specification. It does not read the specification, so later edits to it are not checked; see [the audit](slide_metric_audit.md). |
| `verify_slide_assets.py` | Checks the regenerated slide PNGs against their locked definitions. |
| `audit_slide_number_definitions.py` | The one-off audit that produced [Presentation Metric Audit](slide_metric_audit.md). |

**Tests** — run in CI on every push.

| File | Role |
| --- | --- |
| `test_sentiment_classifier.py` | 28 regression cases recording real misclassifications that were found and fixed. |
| `test_slide_number_definitions.py` | Unit tests for the shared metric definitions. |
| `test_evaluation_report.py` | Regression tests for the Gold 192 evaluation report, on a 192-row corpus it builds itself. |
| `test_evaluation_inputs.py` | Runs the evaluation script on missing, duplicated, empty or invalid predictions and checks that it refuses them, while valid extra rows leave the report unchanged. |
| `test_sample_output.py` | Checks the sample checker in `sample_data/` against altered copies of the sample output. |

**Environment.**

| File | Role |
| --- | --- |
| `research_environment.py` | Stops a research script at once, with a message, when it is run on Python older than 3.10. |

**Figures and slides.**

| File | Role |
| --- | --- |
| `make_portfolio_figures.py` | The four README figures, re-derived from `data/output` with a drift guard. The two guessing baselines in the evaluation figure are copied from [Classifier Benchmark](classifier_benchmark.md), not re-derived. |
| `regenerate_slide_assets.py` | Slide 13–16 PNG candidates from the locked definitions. |
| `make_task3_exchange_accounts.py` | Produces `exchange_accounts.csv`, the per-account aggregation the exchange figure reads. |

**Sampling and provenance.** These ran once. They are kept because they are the
record of how the preserved inputs under `data/output/` were produced, not
because the current pipeline calls them.

| File | Produced |
| --- | --- |
| `make_gold_standard_200.py` | The original 200-post annotation sample. |
| `make_task5_task6_files.py` | `gold_standard_192.csv`, the 20-column source archive that the normalizer reads, and a 30-row advertising-filter check sample. |
| `sample_100_posts.py` | A 100-post random sample for manual review. |
| `sample_negotiation_nonexchange_50.py` | The 50-post negotiation sample used by the slide 16 assets. |
