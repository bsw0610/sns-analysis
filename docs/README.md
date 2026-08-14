# Documentation Index

The documents below record how the analysis was rebuilt, verified, and
reported. They are written in English; Japanese appears only where it is a
dataset label, a metric definition, or presentation copy.

Start with the [repository README](../README.md) for the results and figures.

## Read in this order

| # | Document | What it answers |
|---|---|---|
| 1 | [Project Timeline](01_PROJECT_TIMELINE.md) | What happened in this project, reconstructed from preserved files rather than memory, including which parts could not be recovered. |
| 2 | [Hybrid Baseline Rebuild](hybrid_rebuild.md) | How the 110,918-post corpus is rebuilt from the monthly exports, with the exact inputs, hashes, and the verification contract. |
| 3 | [Classifier Baseline Evaluation](baseline_evaluation.md) | How well the rule-based classifier performs against 192 human-labelled posts, why each category fails where it does, and what the earlier 189-row evaluation showed. |
| 4 | [Presentation Metric Audit](slide_metric_audit.md) | Whether every number quoted in the presentation reproduces from the data, and how the page 15 definitions were fixed. |

## Reporting and production

| Document | Purpose |
|---|---|
| [Slide Asset Regeneration](slide_assets_regeneration.md) | Regenerating and verifying the slide 13–16 PNG assets from locked definitions. |
| [Slide 10–16 Replacement Plan](slide_plan_10-16.md) | The presentation specification. It is also the input that `verify_slide_numbers.py` checks its measurements against. |
| [Presentation Script (Japanese)](presentation_script_10-16_ja.md) | Speaker script for the Japanese presentation. Kept in Japanese by intent. |

## Historical

| Document | Status |
|---|---|
| [Task 0: Total-count Discrepancy](task0_total_count.md) | Records the 2026-07-29 investigation that settled the source total at 136,288. Its working corpus of 109,037 posts has since been superseded by the 110,918-post hybrid corpus. |

Section 10 of the [Classifier Baseline Evaluation](baseline_evaluation.md) is
likewise historical: it preserves the 189-row baseline that the Gold 192
evaluation replaced.

## A note on generated reports

`evaluate_v2_hybrid_192.py` and `verify_slide_numbers.py` write their raw
reports to `data/output/`, which is excluded from Git. The curated documents
here carry the same figures in English. Regenerating a report therefore never
overwrites a document in this directory.
