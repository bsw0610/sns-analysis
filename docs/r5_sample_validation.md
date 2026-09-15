# R5 sample identity validation

Baseline: public main `ca9d63e84e0668627907b60f656d54c0d4a43102`, verified
with `git ls-remote`. Worktree: `/private/tmp/sns-r5`; branch:
`research/r5-sample-input-validation`. Existing local main and its unpublished
137 commits, untracked files, and source data were preserved.

## Contract

There is no separate expected-output CSV in the public baseline. The existing
`sample_data/sample_posts.csv` supplies expected IDs and intended categories;
`EXPECTED_DISAGREEMENTS` supplies the nine recorded exceptions. The checker
now reads that sibling sample file, rejects empty/duplicate IDs on both sides,
checks exact ID-set equality, then compares each intended/predicted pair to
that established expectation. It retains the seven-label check, agreement
count, and exact nine-disagreement check. Row order is unrestricted.
Empty IDs use CSV record positions including the header, not physical line
numbers inside quoted multiline fields. The CLI remains unchanged.

## Actual baseline CLI observations

Normal classified output was generated from the public sample into temporary
files. Each test used an isolated copy of the checker, classifier, and sample.
No private data or mock validation was used.

| Mutation | Baseline exit | Baseline diagnostic / observation |
|---|---:|---|
| Delete one expected row | 1 | expected 30 rows, found 29 |
| Append duplicate ID | 1 | expected 30 rows, found 31 |
| Delete one row and duplicate another, retaining 30 | 0 | normal success messages |
| Add unknown ID | 1 | expected 30 rows, found 31 |
| Replace ID with unknown ID | 0 | normal success messages |
| Empty / whitespace actual ID | 0 / 0 | normal success messages |
| Empty / whitespace expected ID | 0 / 0 | sample file not read |
| Duplicate expected ID | 0 | sample file not read |
| Change both intended and prediction on an agreeing row | 0 | aggregate results unchanged |
| Change a known disagreement to agreement | 1 | recorded outcome changed; newly right |

The original checker already rejected the count-changing cases and the changed
known disagreement. Those are not claimed as silent baseline acceptance.
The new tests ran before implementation: 11 methods, 12 failing assertions
(including cases already rejected but missing the required ID diagnostic).

## Local validation performed

Interpreter: `/opt/anaconda3/bin/python3.13`, Python 3.13.9.
From the worktree, executed:

```sh
/opt/anaconda3/bin/python3.13 -m unittest -v test_sample_output.py
/opt/anaconda3/bin/python3.13 /private/tmp/r5-baseline.py
/opt/anaconda3/bin/python3.13 /private/tmp/r5-probes.py
/opt/anaconda3/bin/python3.13 -m unittest -v test_sentiment_classifier.py test_slide_number_definitions.py test_evaluation_report.py test_evaluation_inputs.py test_sample_output.py
/opt/anaconda3/bin/python3.13 classify_sns_rule_based.py --input sample_data/sample_posts.csv --output /private/tmp/r5-sample.csv
/opt/anaconda3/bin/python3.13 sample_data/check_sample_output.py /private/tmp/r5-sample.csv
git diff --check
```

The temporary baseline helper recorded CLI exits/diagnostics before and after;
the probe helper operated only on disposable copies. Neither is a test or CI
dependency. Final suite: 32 methods passed, including all R3 tests. The 11 new
methods cover 12 negative executions (all exit 1 with intended reason and ID
or row position), plus normal and reversed order (both exit 0). Each checks
both input files' bytes and `st_mtime_ns`. The public sample pipeline retained
21/30 agreement and all nine recorded disagreements. CI now includes the new
file; remote CI and Python versions other than 3.13.9 were not run.

## Targeted detection probes

- Actual duplicate: disable duplicate rejection and restore dictionary-collapse
  consumption (`rows = list(actual.values())`). An appended duplicate is then
  accepted with exit 0; `test_duplicate` fails. This restores a loss path rather
  than counting a later row-count rejection as evidence.
- Expected duplicate: disable duplicate rejection alone. A repeated expected
  row is hidden by the dictionary; CLI exit 0, corresponding test fails.
- ID set: disable set validation and skip unknown IDs in per-post comparison.
  Unknown replacement then retains all aggregates and exits 0; the replacement
  test fails. Unknown addition still hits the row-count guard, so that subcase
  is not counted as proof of acceptance detection.
- Per-post comparison: disable pair comparison. Changing both cells on an
  agreeing row exits 0; `test_changed_prediction` fails despite unchanged totals.

All four probe test commands exited 1 and included an assertion that the
corrupted CLI unexpectedly returned 0. The working checker stayed unchanged;
the complete suite and sample pipeline ran afterward. These are targeted
probes, not exhaustive mutation coverage.

## Publication scope

Only the checker, new tests, CI list, and this record change. Sample contents,
classifier rules, Gold, study metrics, and benchmark files remain unchanged.
The existing local `benchmark/check_artifact_policy.py` is used only as an
external verification tool against each new commit's entire tracked tree:

```sh
/opt/anaconda3/bin/python3.13 /Users/bsw0610/Desktop/data/benchmark/check_artifact_policy.py --repo-root /private/tmp/sns-r5 --data-output /Users/bsw0610/Desktop/data/data/output --strict
```

The policy scan checks exact Gold/supplement fragments of at least 32 Unicode
characters, handle heuristics and recognized row-output schemas. It does not
scan the original full corpus or certify all possible secrets. Supplementary
review checks added text against available preserved IDs and common credential
patterns. The tool and private material are not included in this branch.
