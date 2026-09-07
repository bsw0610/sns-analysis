#!/usr/bin/env python3
"""Regression tests for observed v1 sentiment-classification failure modes."""

from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import classify_sns_rule_based
from classify_sns_rule_based import classify_csv, classify_detailed


class SentimentClassifierRegressionTests(unittest.TestCase):
    CASES = [
        ("頼んだボンドロがにせもんだった。ちくしょー！", "不満・怒り"),
        ("ボンボンドロップシール買えた！かわいい！", "喜び・満足"),
        ("【交換】譲：クロミ 求：キティ 郵送希望", "交換・取引"),
        ("キティとたまごっちボンドロと交換できますか？", "交換・取引"),
        ("ボンボンドロップシール、完売いたしました。入荷がありましたらポストします", "情報共有"),
        ("たまごっちのボンボンドロップシール入荷してるよ", "情報共有"),
        ("ボンボンドロップもう永遠と買える気がしないよ😭", "不満・怒り"),
        ("ボンドロミニチャームはもう諦めてる…😞", "不満・怒り"),
        ("ボンボンドロップシールが欲し過ぎて夢に出た", "欲望・執着"),
        ("CATSのボンボンドロップシール欲しい", "欲望・執着"),
        ("ボンドロなるものをゲットできた♡", "喜び・満足"),
        ("定価で買えて嬉しい〜🥰", "喜び・満足"),
        ("シール帳から何個も落ちて腹立ちすぎて暴れそう", "不満・怒り"),
        ("ドンキの前にボンドロ待機が大量にいる", "焦り・競争"),
        ("ボンボンドロップシールの行列ができていた", "焦り・競争"),
        # These examples were common false positives in v1.
        ("好きな男の子のノートにボンドロを貼った", "中立"),
        ("昔はスーパーに走ってビックリマンシールを買った", "中立"),
        ("200円かかってないのはどこのより安い", "中立"),
        ("これが大人のボンボンドロップシールかぁ", "中立"),
        ("SNS承認欲求お化けに人気という話", "中立"),
        ("欲しくない", "中立"),
        ("かわいくない", "中立"),
        ("生きてて良かった 平野歩夢選手 ボンボンドロップ", "中立"),
        ("ボンボンドロップは動物園限定なんや😭", "不満・怒り"),
        ("何軒も回ったけど全然見つけられない😭", "不満・怒り"),
        ("どこも在庫ゼロで途方に暮れて心が折れそう", "不満・怒り"),
        ("RT @abc: ボンボンドロップシールってまだ人気なの？ https://x.com/a", "中立"),
        ("ボンボンドロップシール買いに明日は出かける予定", "欲望・執着"),
    ]

    def test_observed_cases(self) -> None:
        failures = []
        for text, expected in self.CASES:
            actual = classify_detailed(text).primary
            if actual != expected:
                failures.append((text, expected, actual))
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()


class SameFileGuardTests(unittest.TestCase):
    """Writing the output over the input truncated it before it was read."""

    def _corpus(self, directory: Path) -> Path:
        path = directory / "posts.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["post_id", "clean_text"])
            for index in range(20):
                writer.writerow([f"ID:{index}", "ボンドロ交換希望です"])
        return path

    def test_same_path_is_refused_and_the_input_survives(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = self._corpus(Path(name))
            before = source.read_bytes()
            with self.assertRaises(ValueError):
                classify_csv(source, source, "clean_text")
            self.assertEqual(source.read_bytes(), before)

    def test_an_alias_of_the_input_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = self._corpus(Path(name))
            before = source.read_bytes()
            alias = Path(name) / "alias.csv"
            os.symlink(source, alias)
            with self.assertRaises(ValueError):
                classify_csv(source, alias, "clean_text")
            self.assertEqual(source.read_bytes(), before)

    def test_a_failed_run_leaves_the_previous_output_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            source = self._corpus(directory)
            output = directory / "out.csv"
            classify_csv(source, output, "clean_text")
            good = output.read_bytes()

            calls = {"count": 0}
            original = classify_sns_rule_based.classify_detailed

            def failing(text: str):
                calls["count"] += 1
                if calls["count"] == 5:
                    raise RuntimeError("injected")
                return original(text)

            with mock.patch.object(classify_sns_rule_based, "classify_detailed", failing):
                with self.assertRaises(RuntimeError):
                    classify_csv(source, output, "clean_text")

            self.assertEqual(output.read_bytes(), good)
            self.assertEqual(list(directory.glob("*.part")), [])
