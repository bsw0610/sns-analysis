# R3 prediction input validation — verification record

## Scope and baseline

Remote `git ls-remote origin refs/heads/main` returned
`3199ca9e9ec04932f3bb7d75e973a34b3dec405e` (includes T1).
Created `research/r3-input-validation` in `/private/tmp/sns-r3` directly from
that SHA. The original main was 137 commits ahead and 7 behind the cached
remote; its untracked diagram files and `tasks/` were left in place.
No private worker ref, benchmark commits, classifier rules, Gold labels,
metric definitions, or benchmark structure were imported or changed.

Changed files: evaluator, `test_evaluation_inputs.py`, T1 fixture in
`test_evaluation_report.py`, `.github/workflows/test.yml`, and this record.
The fixture now explicitly supplies six scores, retaining all previous
threshold outcomes and expected totals. Each new test builds the T1 corpus;
only a separate predictions CSV is mutated. Every subprocess checks that
Gold, source, supplement, hybrid, and Gold-189 fixture bytes stay unchanged.

## Baseline reproduction

Before editing the evaluator, the new five test methods produced 94 failing
subtests. Separate baseline entry-point runs confirmed:

| Corruption | Exit | Report | Observed result |
|---|---:|---|---|
| One Gold prediction missing | 0 | written | n=191, hit=190/191 |
| Duplicate Gold prediction | 0 | written | n=192, hit=191/192 |
| Invalid primary outside Gold | 0 | written | n=192, hit=191/192 |

Missing rows were filtered out of evaluation; duplicate rows overwrote earlier
rows; rows outside Gold bypassed value validation. Some malformed values
already raised exceptions, but lacked the required prediction-ID diagnostic.

## Commands and environment

Working directory: `/private/tmp/sns-r3`.
Interpreter: `/opt/anaconda3/bin/python3.13`, Python **3.13.9**.
The system `/usr/bin/python3` is 3.9.6 and was not used for evaluation tests.

Executed (test logs were redirected to temporary files):

```sh
/opt/anaconda3/bin/python3.13 -m unittest -v test_evaluation_inputs.py
/opt/anaconda3/bin/python3.13 -m unittest -v test_sentiment_classifier.py test_slide_number_definitions.py test_evaluation_report.py test_evaluation_inputs.py
/opt/anaconda3/bin/python3.13 /private/tmp/r3-verify.py
/opt/anaconda3/bin/python3.13 /private/tmp/r3-more-probes.py
/opt/anaconda3/bin/python3.13 -m unittest -v test_sentiment_classifier.py test_slide_number_definitions.py test_evaluation_report.py test_evaluation_inputs.py
/opt/anaconda3/bin/python3.13 classify_sns_rule_based.py --input sample_data/sample_posts.csv --output /private/tmp/r3-sample-output.csv
/opt/anaconda3/bin/python3.13 sample_data/check_sample_output.py /private/tmp/r3-sample-output.csv
git diff --check
```

The two temporary scripts performed raw-data comparison, negative-exit
collection, disposable-copy mutations, and baseline reproduction; they are
local investigation helpers, not additional CI dependencies.
Final suite: **21 tests passed**, including five new methods. Public sample:
30 rows, 21 matches and all nine recorded disagreements reproduced.
CI's actual unittest list now includes the new file for Python 3.11/3.12/3.13.

## Negative cases and output preservation

Each case ran twice through the real `__main__` entry point in a subprocess.
The test harness sets only the normalizer's source/supplement/hybrid defaults
to synthetic paths before `runpy`; evaluator logic and interpreter guard run
normally. Assertions require nonzero exit, the intended prediction-validation
reason, and the ID (or CSV record number including header for empty IDs).

A: no report initially; no report created. B: an existing binary sentinel
report; exact bytes and `st_mtime_ns` unchanged. Both states passed for every
case below. All **94 subprocess exits were 1** (47 cases × two states).

| Cases | Count | Exit each | A / B |
|---|---:|---:|---|
| Missing Gold prediction | 1 | 1 | preserved |
| Duplicate ID inside / outside Gold | 2 | 1 | preserved |
| Empty / whitespace ID | 2 | 1 | preserved |
| Unknown / empty primary, inside and outside | 4 | 1 | preserved |
| Invalid JSON, array, null, number, string, inside and outside | 10 | 1 | preserved |
| Empty object, missing, unknown, duplicate key, inside and outside | 8 | 1 | preserved |
| true, false, null, numeric string, NaN, +Infinity, -Infinity, array, object score, inside and outside | 18 | 1 | preserved |
| Overflowing exponent 1e999, inside and outside | 2 | 1 | preserved |

The valid 192-row fixture passes, including all-zero neutral predictions.
Appending a valid outside-Gold row to the same predictions path leaves the
entire report byte-identical, covering both metric tables and supplement note.

## Preserved-data comparison

Both implementations used the same absolute paths for all six preserved input
files and the same temporary output path. No display-path normalization or
string replacement was applied. The baseline module was loaded from `git show
3199ca9:evaluate_v2_hybrid_192.py`; the final module came from this branch.
All paths are outside both modules' project roots, so both display the same
absolute paths.

Result: **4,689 report bytes identical**, complete calculated metrics equal,
and complete supplemental delta equal. Input bytes and `st_mtime_ns` were
unchanged. No real IDs or bodies were printed or placed in fixtures/logs.

## Mutation probes actually performed

Each probe copied Python files to a disposable temporary directory. The final
working evaluator was never mutated. Each named test command returned exit 1:

| Disabled check | Corresponding method | Failing A/B subtests |
|---|---|---:|
| Missing check plus restored baseline omission filter | `test_missing` | 2 |
| Duplicate-ID check | `test_duplicates` | 4 |
| Primary membership | `test_invalid_values_inside_and_outside_gold` | 8 |
| Finite numeric score check | same | 40 |
| Exact six-key check | same | 12 |
| Duplicate JSON-key check | same | 4 |

These are six targeted probes, not exhaustive mutation testing. The final
21-test suite and sample checks were rerun after all probes.

## Review and limitations

Review checked tests first, validation before Gold filtering, duplicate JSON
handling, no writes before successful load, and the final diff's scope.
No new dependency or validation framework was added. Memory overhead is a
set of all prediction IDs; only selected Gold predictions are retained.
Local execution covered Python 3.13.9; remote CI and other matrix versions
were not executed. Public tests require neither preserved data nor private
refs. Raw-data equality was a separate local check, not a public CI test.
No push, force push, or remote history rewrite was performed.

Public-material check: `/opt/anaconda3/bin/python3.13
/private/tmp/r3-public-scan.py` inspected all five changed files. No preserved
ID or full `clean_text` of at least 20 characters matched; no private-key,
GitHub-token, AWS-access-key, or quoted password/API-key/secret pattern matched.
Manual diff review found only synthetic fixture IDs/text. This targeted check
does not certify every possible privacy or secret pattern. The publication
scope is these five files and one new commit directly above the remote SHA;
the 137 unpublished local-main commits are outside that ancestry.
