#!/usr/bin/env python3
"""Regression test for the supplemental-row delta in the Gold 192 report.

The published write-up asserted that all three supplemental rows are predicted
`交換・取引`, so the only change against the 189-row evaluation was TP +3.  That
was never checked against the predictions, and it is wrong: one of the three is
predicted `中立`.  The generator now derives the delta instead of asserting it,
and this test fails if that assumption comes back.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from evaluate_v2_hybrid_192 import supplement_delta, supplement_note


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
        {"post_id": "extra-hit-2", "gold": {"交換・取引"}, "single": "交換・取引"},
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
        """The defect this guards: three extra rows read as TP +3."""
        delta = self.delta()
        self.assertEqual(delta["tp"], {"交換・取引": 2})
        self.assertEqual(delta["fn"], {"交換・取引": 1})
        self.assertEqual(delta["fp"], {"中立": 1})

    def test_the_sentence_reports_the_miss_rather_than_hiding_it(self) -> None:
        note = supplement_note(self.delta())
        self.assertIn("交換・取引のTP+2", note)
        self.assertIn("交換・取引のFN+1", note)
        self.assertIn("中立のFP+1", note)
        self.assertNotIn("TP+3", note)


if __name__ == "__main__":
    unittest.main()
