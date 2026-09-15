#!/usr/bin/env python3
"""Regression tests for the Gold 192 evaluation report.

Two defects are covered, both of which were published before they were measured.

1.  The write-up asserted that all three supplemental rows are predicted
    `交換・取引`, so the only change against the 189-row evaluation was TP +3.
    Read from the preserved files, one of the three is predicted `中立`.

2.  The first fix derived the delta but counted a false negative only when the
    prediction missed the Gold set entirely.  A row whose top category is right
    and whose remaining Gold labels are unpredicted also owes a false negative
    for each of those labels, which is how the report's own table counts them.
    Omitting them undercounts the corpus total: 84 rather than 98 at n=189.

The report test runs `main` over a synthetic 192-row corpus and reads the file
it writes, so restoring the old sentence to the generator turns it red even
though the helpers stay correct.  The expected strings below are worked out by
hand from the fixture, not produced by calling the code under test.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate_v2_hybrid_192 import COLMAP, main, supplement_delta, supplement_note
from normalize_gold_standard_192 import GOLD_COLUMNS
from research_environment import MINIMUM, REASON

BASE_ROWS = 189
NEUTRAL_ROWS = 180
MULTI_LABEL_ROWS = 9


def write_ids(path: Path, post_ids: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["post_id"])
        for post_id in post_ids:
            writer.writerow([post_id])


class SupplementDeltaTests(unittest.TestCase):
    ROWS = [
        {"post_id": "shared-1", "gold": {"交換・取引"}, "single": "交換・取引"},
        {"post_id": "extra-hit-1", "gold": {"交換・取引"}, "single": "交換・取引"},
        {
            "post_id": "extra-hit-2",
            "gold": {"交換・取引", "喜び・満足"},
            "single": "交換・取引",
        },
        {"post_id": "extra-miss", "gold": {"交換・取引"}, "single": "中立"},
    ]

    def delta(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        gold_189 = Path(directory.name) / "gold_189.csv"
        write_ids(gold_189, ["shared-1"])
        return supplement_delta(self.ROWS, gold_189)

    def test_only_rows_outside_the_189_set_are_counted(self) -> None:
        delta = self.delta()
        self.assertEqual(
            {row["post_id"] for row in delta["rows"]},
            {"extra-hit-1", "extra-hit-2", "extra-miss"},
        )

    def test_a_missed_supplemental_row_is_not_counted_as_a_true_positive(self) -> None:
        """The first defect: three extra rows read as TP +3."""
        delta = self.delta()
        self.assertEqual(delta["tp"], {"交換・取引": 2})
        self.assertEqual(delta["fp"], {"中立": 1})

    def test_an_unpredicted_gold_label_on_a_hit_row_is_a_false_negative(self) -> None:
        """The second defect: `extra-hit-2` owes 喜び・満足 a false negative."""
        self.assertEqual(self.delta()["fn"], {"交換・取引": 1, "喜び・満足": 1})

    def test_the_sentence_reports_the_miss_rather_than_hiding_it(self) -> None:
        note = supplement_note(self.delta())
        self.assertIn("交換・取引のTP+2", note)
        self.assertIn("交換・取引のFN+1", note)
        self.assertIn("喜び・満足のFN+1", note)
        self.assertIn("中立のFP+1", note)
        self.assertNotIn("TP+3", note)


@unittest.skipUnless(
    sys.version_info >= MINIMUM,
    f"the research scripts need Python {MINIMUM[0]}.{MINIMUM[1]}+: {REASON}",
)
class GeneratedReportTests(unittest.TestCase):
    """Run the generator over a synthetic corpus and read what it wrote.

    The corpus is built to make every total checkable by hand:

        180 rows  gold 中立             predicted 中立          TP 180
          9 rows  gold 喜び満足+欲望執着  predicted 喜び・満足     TP 9, FN 欲望・執着 9
        ----------------------------------------------------------------
        189 base rows: 198 label occurrences, TP 189, FP 0, FN 9

          1 row   gold 交換取引          predicted 交換・取引     TP 1
          1 row   gold 交換取引+喜び満足  predicted 交換・取引     TP 1, FN 喜び・満足 1
          1 row   gold 交換取引          predicted 中立          FP 1, FN 交換・取引 1
        ----------------------------------------------------------------
        192 rows:      202 label occurrences, TP 191, FP 1, FN 11

    The lenient criterion charges a false negative to every Gold label the single
    prediction did not cover, so the totals satisfy occurrences - TP = FN both at
    189 (198 - 189 = 9) and at 192 (202 - 191 = 11).  That identity is what the
    corpus figures obey too: 217 - 118 = 99.

    One of the nine multi-label rows scores both its Gold categories over the
    threshold, so the multi-label table is not a copy of the lenient one.  Without
    that row the two are identical on this fixture, and an assertion meant for the
    lenient totals matches the multi-label table instead -- which is how a probe
    that neutered the lenient false-negative branch first came back green.
    """

    LENIENT_MICRO_ROW = "| **micro平均** | 202 | 192 | 191 | 1 | 11 |"
    MULTI_MICRO_ROW = "| **micro平均** | 202 | 193 | 192 | 1 | 10 |"
    NOTE = (
        "補充3件のうち、正解ラベルと一致した予測は2件、外れた予測は1件である。"
        "差分は 交換・取引のTP+2、中立のFP+1、交換・取引のFN+1、喜び・満足のFN+1 "
        "であり、それ以外のカテゴリは189件版と変わらない。"
        "外れた1件は正解 `交換・取引` に対し `中立` と予測。"
    )

    @classmethod
    def gold_row(cls, post_id: str, labels: set[str]) -> list[str]:
        cells = {name: "" for name in GOLD_COLUMNS}
        cells["post_id"] = post_id
        cells["投稿日"] = "2026-01-01"
        cells["clean_text"] = f"synthetic text for {post_id}"
        cells["要検討"] = "0"
        for label in labels:
            cells[label] = "1"
        return [cells[name] for name in GOLD_COLUMNS]

    @classmethod
    def prediction_row(
        cls, post_id: str, category: str, also_over_threshold: str | None = None
    ) -> dict[str, str]:
        # One category over MIN_PRIMARY_SCORE, so the multi-label prediction set
        # is the single prediction.  `中立` is expressed as an empty set, which
        # the loader turns back into 中立.
        scores = dict.fromkeys(COLMAP.values(), 0.0)
        if category != "中立":
            scores[category] = 2.0
        if also_over_threshold is not None:
            scores[also_over_threshold] = 2.0
        return {
            "投稿ID_文字列": post_id,
            "sentiment_category": category,
            "sentiment_confidence": "0.9",
            "category_scores": json.dumps(scores, ensure_ascii=False),
        }

    @classmethod
    def build(cls, directory: Path) -> dict[str, Path]:
        gold_rows: list[list[str]] = []
        predictions: list[dict[str, str]] = []
        base_ids: list[str] = []

        for index in range(NEUTRAL_ROWS):
            post_id = f"base-neutral-{index:03d}"
            base_ids.append(post_id)
            gold_rows.append(cls.gold_row(post_id, {"中立"}))
            predictions.append(cls.prediction_row(post_id, "中立"))
        for index in range(MULTI_LABEL_ROWS):
            post_id = f"base-multi-{index:03d}"
            base_ids.append(post_id)
            gold_rows.append(cls.gold_row(post_id, {"喜び満足", "欲望執着"}))
            predictions.append(
                cls.prediction_row(
                    post_id,
                    "喜び・満足",
                    # Exactly one row predicts both Gold categories, which is what
                    # separates the multi-label table from the lenient one.
                    "欲望・執着" if index == 0 else None,
                )
            )
        assert len(base_ids) == BASE_ROWS

        supplements = [
            ("supplement-hit", {"交換取引"}, "交換・取引"),
            ("supplement-hit-multi", {"交換取引", "喜び満足"}, "交換・取引"),
            ("supplement-miss", {"交換取引"}, "中立"),
        ]
        for post_id, labels, category in supplements:
            gold_rows.append(cls.gold_row(post_id, labels))
            predictions.append(cls.prediction_row(post_id, category))

        normalized = directory / "gold_normalized.csv"
        with normalized.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(GOLD_COLUMNS)
            writer.writerows(gold_rows)

        # The preserved source carries columns the 12-column derivative drops, so
        # the validator's "first twelve fields are unchanged" check has something
        # to compare rather than two identical files.
        source = directory / "gold_source.csv"
        with source.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow([*GOLD_COLUMNS, "作業メモ"])
            writer.writerows([[*row, "dropped"] for row in gold_rows])

        hybrid = directory / "hybrid.csv"
        with hybrid.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "投稿ID_文字列",
                    "sentiment_category",
                    "sentiment_confidence",
                    "category_scores",
                ],
            )
            writer.writeheader()
            writer.writerows(predictions)

        # The supplement pool holds more candidates than survived into the Gold
        # set, as the real one does; only three of these are gold rows.
        supplement = directory / "supplement_pool.csv"
        write_ids(
            supplement,
            [post_id for post_id, _, _ in supplements]
            + [f"pool-only-{index}" for index in range(8)],
        )

        gold_189 = directory / "gold_189.csv"
        write_ids(gold_189, base_ids)

        return {
            "gold": normalized,
            "source": source,
            "hybrid": hybrid,
            "supplement": supplement,
            "gold_189": gold_189,
            "output": directory / "report.md",
        }

    def section(self, report: str, heading: str) -> str:
        """The one table under `heading`, so an assertion cannot match the other."""
        self.assertIn(heading, report)
        after = report.split(heading, 1)[1]
        return after.split("###", 1)[0]

    def report(self) -> str:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        paths = self.build(Path(directory.name))
        with contextlib.redirect_stdout(io.StringIO()):
            main(
                gold_path=paths["gold"],
                pred_path=paths["hybrid"],
                output=paths["output"],
                gold_189_path=paths["gold_189"],
                source_path=paths["source"],
                supplement_path=paths["supplement"],
                hybrid_path=paths["hybrid"],
            )
        return paths["output"].read_text(encoding="utf-8")

    def test_the_report_counts_every_uncovered_gold_label_as_a_false_negative(
        self,
    ) -> None:
        """202 label occurrences minus 191 lenient true positives is 11, not 2."""
        report = self.report()
        self.assertIn(
            self.LENIENT_MICRO_ROW, self.section(report, "### 緩和基準")
        )
        self.assertIn(
            self.MULTI_MICRO_ROW, self.section(report, "### 多重ラベル基準")
        )

    def test_the_report_states_the_measured_supplemental_delta(self) -> None:
        """Restoring the asserted sentence to `main` fails here, not in the helpers."""
        report = self.report()
        self.assertIn(self.NOTE, report)
        self.assertNotIn("TP+3", report)


if __name__ == "__main__":
    unittest.main()
