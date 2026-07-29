#!/usr/bin/env python3
"""Regression tests for observed v1 sentiment-classification failure modes."""

from __future__ import annotations

import unittest

from classify_sns_rule_based import classify_detailed


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
