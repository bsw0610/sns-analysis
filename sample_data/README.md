# Sample Data

The datasets this project analyses are not in the repository: they are licensed
exports of real posts, and republishing them is not something the project can
grant. That leaves a fresh clone with nothing to run, so this directory holds a
small synthetic sample that exercises the classifier end to end.

## What this is

`sample_posts.csv` contains 30 posts **written for this repository**. They are
not drawn, quoted, or paraphrased from the collected dataset — every text was
composed from scratch, and each was checked against all 110,918 posts in the
hybrid corpus to confirm it appears nowhere in it. They imitate the shape of
real posts about the product so that the rules have something realistic to act
on, and nothing more.

| Column | Meaning |
| --- | --- |
| `post_id` | Synthetic identifier, `S01` to `S30` |
| `text` | The post body the classifier reads |
| `intended_category` | The category the post was written to express |

`intended_category` is authoring intent, not an annotation from the study's
labelling process. It is not part of the Gold 192 evaluation and no metric in
the README is derived from it.

## Run it

From the repository root, with no dataset and no third-party packages:

```bash
python3 classify_sns_rule_based.py \
  --input sample_data/sample_posts.csv \
  --output sample_output.csv
```

Then check the result:

```bash
python3 sample_data/check_sample_output.py sample_output.csv
```

```text
OK: 30 rows classified, 21/30 match the intended label
OK: 9 known disagreements reproduced exactly
```

## Why 21 out of 30, and not 30 out of 30

The sample was not tuned to make the classifier look good. Its nine failures
are the weaknesses measured against the human-labelled evaluation set, so a
reader can watch them happen instead of taking the numbers on trust. Section
references below are to [`docs/baseline_evaluation.md`](../docs/baseline_evaluation.md).

| Post | Intended | Predicted | Cause |
| --- | --- | --- | --- |
| S21, S23 | `交換・取引` | `中立` | `\b交換\b` does not match `交換して` or `交換したい`, so the post scores 0.00 (6.1) |
| S19 | `焦り・競争` | `中立` | `並びます` is not among the `並んで` / `並ぶ` forms in the rules (6.2) |
| S26, S28 | `情報共有` | `中立` | Information sharing scores F1 0.000 under the lenient criterion (6.3) |
| S09 | `欲望・執着` | `情報共有` | `目撃情報` fires on word presence rather than the writer's intent (6.3) |
| S10, S12, S14 | `不満・怒り` / `欲望・執着` | `中立` | Indirect expressions match no rule, or score below the 1.8 threshold (6.4) |

`check_sample_output.py` pins this exact set. If the classifier's behaviour
changes, the check fails and names what moved, rather than quietly passing with
a different result.

## What this sample does not do

It does not reproduce the study. The corpus construction, advertising-filter
audit, and Gold 192 evaluation all need the private dataset; see the
[repository README](../README.md) for what a fresh clone can and cannot rerun.
