# Documentation Index

Start with the [repository README](../README.md) for the research, results,
synthetic sample, contributions, and limitations. The original seminar work was
collaborative; the later audit and reproducibility work was the owner's
individual phase, carried out with AI coding agents.

## Understand the results

| Document | What it covers |
| --- | --- |
| [Classifier Baseline Evaluation](baseline_evaluation.md) | Gold 192 and the earlier Gold 189, evaluation criteria and category errors. |
| [Classifier Benchmark](classifier_benchmark.md) | Comparison with guessing and a trained model; aggregate results only, with code unpublished. |
| [Hybrid Baseline Rebuild](hybrid_rebuild.md) | The 110,918-post corpus, inputs, hashes and verification contract. |
| [Presentation Metric Audit](slide_metric_audit.md) | Definitions and verification of presentation numbers. |
| [Sentiment Analysis Methodology](../sns_sentiment_analysis_guide.md) | Classifier methodology and labels. |

## Run and inspect

| Document | What it covers |
| --- | --- |
| [Reproducibility and execution](reproducibility.md) | Environments, required private inputs, commands and historical methods. |
| [Script reference](scripts.md) | Roles of the Python files in the repository root. |
| [Synthetic sample](../sample_data/README.md) | Running 30 synthetic posts and understanding the nine known disagreements. |
| [R3 Input Validation](r3_input_validation.md) | Evaluation input validation and its verification. |
| [R5 Sample Validation](r5_sample_validation.md) | The synthetic sample checker and its validation. |
| [Slide Asset Regeneration](slide_assets_regeneration.md) | Regenerating and verifying slide 13–16 PNG assets. |

The generated reports from `evaluate_v2_hybrid_192.py` and
`verify_slide_numbers.py` go to the Git-ignored `data/output/`, not this directory.
A fresh clone lacks the research data; the synthetic sample and CI do not
reproduce the full study.

## Research history and attribution

| Document | What it covers |
| --- | --- |
| [Contributions, source material, and AI workflow](contributions.md) | Team, owner and AI roles, source boundaries, and review limitations. |
| [Project Timeline](01_PROJECT_TIMELINE.md) | Evidence-backed reconstruction and gaps in the project history. |
| [Task 0: Total-count Discrepancy](task0_total_count.md) | Historical investigation of the 136,288 total; its 109,037-post corpus was superseded. |
| [Slide 10–16 Replacement Plan](slide_plan_10-16.md) | Presentation specification; the verification script uses transcribed expected values, not the document itself. |
| [Presentation Script (Japanese)](presentation_script_10-16_ja.md) | Japanese speaker script. |

Section 10 of the [Classifier Baseline Evaluation](baseline_evaluation.md)
preserves the historical Gold 189 baseline alongside the later Gold 192 results.
