# Classifier Benchmark: Rules Against a Trained Text Model

Date: 2026-09-26. The benchmark is closed at this step.

This page reports aggregate results only. The benchmark code, its per-post outputs
and its working history are not in this repository (see
[What is not published](#what-is-not-published)), so a fresh clone cannot rerun
these numbers.

## The question

The [baseline evaluation](baseline_evaluation.md) measures the rule-based classifier
against the human-labelled posts. Under the lenient primary-label criterion it has a
hit rate of 118/192 = 0.615 and a macro F1 of 0.450. Those figures alone do not say
whether that is good or poor for this task. This benchmark asks two questions of the
same labelled posts:

1. Does the rule-based classifier do better than guessing?
2. Does a standard text classifier, trained on these labels, do better than the rules?

## What was compared

| Method | What it does |
|---|---|
| Rule | `classify_sns_rule_based.py` v2.0.0, unchanged. It is not trained. |
| TF-IDF + logistic regression | Splits each post into overlapping 2–4 character sequences, weights them with TF-IDF, and trains one logistic regression per category. Character sequences need no word segmentation, which Japanese text would otherwise require. The settings were fixed before the first run and never tuned. |
| `dummy_majority` | Always predicts the most frequent category in the training part. |
| `dummy_prior` | Guesses at random in proportion to the category frequencies in the training part. Run with 1,000 seeds and reported as the mean with the 2.5–97.5 percentile range. |

## How it was measured

- **Cross-validation.** The labelled posts are split into five parts (folds). TF-IDF
  is trained on four parts and predicts the fifth, five times over, so every post is
  predicted once by a model that never saw it. The scores are computed on all of those
  predictions together.
- **Duplicates stay together.** Posts whose text is identical, or nearly so, after
  normalization are grouped, and a group is never split across folds. Otherwise the
  model could be tested on text it was trained on. One group of four identical posts
  was found; every other post stands alone.
- **Metrics.** The two headline metrics are the lenient criterion of the baseline
  evaluation, so Rule's scores here equal the figures published there.
  - *Hit rate*: the share of posts whose single predicted category is one of the
    post's Gold labels.
  - *Macro F1*: the F1 of that single prediction for each of the seven categories,
    averaged with equal weight, so a small category counts as much as a large one.
- **Decision rule, fixed in advance.** A method is called better or worse than another
  only when the 95% interval of their difference lies wholly on one side of zero.
  Otherwise no winner is declared. The interval comes from a paired bootstrap: 10,000
  resamples of the duplicate groups, each one scoring both methods on the same posts.
- **Order of work.** The TF-IDF settings and the scoring rules were committed before
  any TF-IDF code was written. The remaining bootstrap details were fixed after the
  point scores had been seen but before any bootstrap code existed, each in its
  simplest form.

## Results

Gold 189 is the set labelled for the first evaluation. Gold 192 adds three
supplemental posts (see the README's
[human-label evaluation](../README.md#human-label-evaluation)). No conclusion below
differs between the two.

| Method | Gold 189 hit rate | Gold 189 macro F1 | Gold 192 hit rate | Gold 192 macro F1 |
|---|---:|---:|---:|---:|
| `dummy_majority` | 0.270 | 0.061 | 0.281 | 0.063 |
| `dummy_prior` | 0.204 (0.153–0.259) | 0.151 (0.108–0.203) | 0.206 (0.151–0.266) | 0.151 (0.108–0.200) |
| Rule | 116/189 = 0.614 | 0.451 | 118/192 = 0.615 | 0.450 |
| TF-IDF + LR | 101/189 = 0.534 | 0.339 | 104/192 = 0.542 | 0.340 |

TF-IDF minus Rule, with the 95% bootstrap interval:

| Metric | Gold 189 | Gold 192 | Verdict |
|---|---|---|---|
| Hit rate | −0.079 [−0.164, +0.005] | −0.073 [−0.154, +0.010] | No winner: the interval includes zero |
| Macro F1 | −0.112 [−0.180, −0.041] | −0.110 [−0.177, −0.039] | TF-IDF lower: the whole interval is below zero |

In words:

1. Rule and TF-IDF both score above the top of the `dummy_prior` range, on both
   metrics and both sets. Both do better than guessing.
2. TF-IDF did not beat the rules on either metric.
3. On macro F1 it is clearly lower. On hit rate it is 7–8 points lower, but the
   interval includes zero, so no winner is declared.

## Where the gap comes from

Single-prediction F1 by category on Gold 192. Rule's column equals the lenient
per-category table in the README. On Gold 189 the values differ by 0.008 or less.

| Category | Gold posts | Rule | TF-IDF |
|---|---:|---:|---:|
| `交換・取引` | 54 | 0.869 | 0.879 |
| `中立` | 48 | 0.625 | 0.491 |
| `欲望・執着` | 36 | 0.373 | 0.361 |
| `喜び・満足` | 33 | 0.516 | 0.452 |
| `焦り・競争` | 27 | 0.294 | 0.195 |
| `不満・怒り` | 14 | 0.471 | 0.000 |
| `情報共有` | 5 | 0.000 | 0.000 |

- **`不満・怒り` carries most of the macro-F1 gap.** TF-IDF's single prediction was
  never `不満・怒り` for any of the 14 posts carrying that label, and the one time it
  chose the category, the post did not carry it. Macro F1 weights
  the seven categories equally, so this one category contributes 0.067 of the 0.112
  gap on Gold 189, about 60%. This breakdown was not planned in advance. It is
  arithmetic on the table and was not bootstrapped.
- **On the largest category, `交換・取引`, the two methods are level** (0.869 and
  0.879).
- **`情報共有` (5 posts) supports no conclusion.** Neither method finds it.

The clear macro-F1 result therefore rests largely on one 14-post category.

## What this does and does not show

It shows that on these posts, with about 150 training posts per fold, one standard
untuned text classifier did not do better than the hand-written rules, and that the
rules' lead is concentrated in `不満・怒り`.

It does not show that rules beat trained models in general. Only one configuration was
run, without tuning, on a small set.

## Limits

- **Small data.** Each fold trains on about 150 posts. Two categories have few posts
  carrying the label: `不満・怒り` 14 and `情報共有` 5.
- **One TF-IDF configuration**, untuned. It says nothing about what a tuned or larger
  model could do.
- **The rules' history.** Rerunning the current rules reproduces the preserved
  predictions for all 192 posts. Whether the rules were changed after the Gold 189
  labels were first used on 2026-07-28 is not recorded and cannot be established. If
  they were, Rule's scores are partly fitted to these posts, while TF-IDF's always come
  from posts it did not see. This benchmark cannot rule out that advantage.
- **The labels.** All 192 posts were labelled by one annotator, the repository owner,
  so there is no measure of agreement between annotators. The set is not a random
  sample of the corpus. For the three supplemental posts, no record remains of when or
  under which procedure they were labelled, which is why Gold 189 is reported alongside
  Gold 192.
- **Built and checked with AI agents.** The benchmark was designed, implemented and
  mostly audited with AI coding agents, largely the same model. One review by a
  different model covered the TF-IDF stage before its first run. It found seven gaps,
  all of which were fixed; the fixes were not re-reviewed. The repository owner
  approved each stage before it ran, had the TF-IDF stage reviewed by the second
  model, and closed the benchmark at this step.
- **Not reproducible from this repository.** See below.

## Not done

A comparison with a large language model given a few labelled examples was planned.
It addressed the clearest open question: whether a model that reads the text, rather
than counting character sequences, recovers `不満・怒り` and `中立`. It was not run,
because the local model it depended on was retired. A BERT comparison was not pursued:
with about 150 training posts per fold, more model capacity was not expected to help.
The benchmark ends at this step.

## What is not published

The code, the per-post predictions and the fold assignments are kept out of this
repository. The per-post outputs are tied to individual posts and their labels, and
the labelled dataset itself is not tracked here. The benchmark's working history also
contains commits with material that must stay private, so it
cannot be published as it is, and a cleaned snapshot of the code was not prepared.
The figures on this page are copied from the benchmark's aggregate result file, which
holds no per-post values.
