#!/usr/bin/env python3
"""Regression tests for the shared slide-number calculation definitions."""

from __future__ import annotations

import unittest

from slide_number_definitions import (
    has_exchange_ratio,
    has_honorific_consideration,
    is_exchange_template,
    is_platform_reply,
    top_fraction_account_count,
    wald_interval,
)


class SlideNumberDefinitionTests(unittest.TestCase):
    def test_exchange_template_inclusions(self) -> None:
        for text in (
            "【交換】",
            "【\n譲\n】",
            "〈 求 〉",
            "《譲》",
            "[譲]",
            "［ 求 ］",
            "譲 ）",
            "求　：",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_exchange_template(text))

    def test_exchange_template_exclusions(self) -> None:
        for text in (
            "交換希望です",
            "求めています",
            "譲ります",
            "郵送でお願いします",
            "手渡し可能です",
            "[交換]",
        ):
            with self.subTest(text=text):
                self.assertFalse(is_exchange_template(text))

    def test_top_fraction_uses_floor(self) -> None:
        self.assertEqual(top_fraction_account_count(10677, 0.01), 106)
        self.assertEqual(top_fraction_account_count(10677, 0.10), 1067)
        self.assertEqual(top_fraction_account_count(1, 0.01), 1)
        self.assertEqual(top_fraction_account_count(0, 0.01), 0)

    def test_reply_uses_platform_metadata_only(self) -> None:
        self.assertTrue(is_platform_reply({"リプライ先の投稿ID": "123"}))
        self.assertFalse(is_platform_reply({"リプライ先の投稿ID": ""}))
        self.assertFalse(
            is_platform_reply(
                {"リプライ先の投稿ID": "", "内容": "@user information"}
            )
        )

    def test_qualitative_string_variants(self) -> None:
        self.assertTrue(has_honorific_consideration("ご検討ください"))
        self.assertTrue(has_honorific_consideration("御検討ください"))
        self.assertFalse(has_honorific_consideration("検討します"))
        self.assertTrue(has_exchange_ratio("2 : 2"))
        self.assertTrue(has_exchange_ratio("1：3"))
        self.assertFalse(has_exchange_ratio("n:m"))

    def test_wald_interval_rounding(self) -> None:
        expected = {
            54: "21.8 – 34.5%",
            33: "11.9 – 22.5%",
            27: "9.1 – 19.0%",
            5: "0.4 – 4.9%",
        }
        for successes, interval in expected.items():
            with self.subTest(successes=successes):
                low, high = wald_interval(successes, 192)
                self.assertEqual(
                    f"{low * 100:.1f} – {high * 100:.1f}%",
                    interval,
                )


if __name__ == "__main__":
    unittest.main()
