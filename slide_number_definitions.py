#!/usr/bin/env python3
"""Shared calculation definitions for the slide-number audit.

This module contains only reporting definitions.  It does not change the
corpus selection or the v2.0.0 sentiment classifier.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

EXCHANGE_CATEGORY = "交換・取引"
EXCHANGE_ACCOUNT_KEY = "ユーザーID"
WALD_95_Z = 1.96

# Operational definition used for page 15:
# - 【交換】【譲】【求】, with optional whitespace inside the brackets
# - 〈譲〉《求》, ASCII/full-width square-bracket variants, likewise allowing
#   whitespace
# - 譲）/求： and ASCII/full-width equivalents, allowing whitespace before
#   the delimiter
# ``\s*`` deliberately includes line breaks.  Standalone words and delivery
# modes (郵送/手渡し) are not sufficient by themselves.
EXCHANGE_TEMPLATE_RE = re.compile(
    r"【\s*(?:交換|譲|求)\s*】"
    r"|[〈《\[［]\s*(?:譲|求)\s*[〉》\]］]"
    r"|(?:譲|求)\s*[)）：:]"
)

HONORIFIC_CONSIDERATION_RE = re.compile(r"(?:ご|御)検討")
EXCHANGE_RATIO_RE = re.compile(r"\d\s*[:：]\s*\d")
FORMAL_GREETING_RE = re.compile(r"検索(?:より|から)")


def is_exchange_template(text: str) -> bool:
    """Return whether a post contains the adopted page-15 formal template."""
    return EXCHANGE_TEMPLATE_RE.search(text or "") is not None


def top_fraction_account_count(account_count: int, fraction: float) -> int:
    """Return whole accounts not exceeding the requested population share."""
    if account_count < 0:
        raise ValueError("account_count must be non-negative")
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    if account_count == 0:
        return 0
    return max(1, math.floor(account_count * fraction))


def is_platform_reply(row: Mapping[str, str]) -> bool:
    """Use X reply metadata; a leading mention alone is not a reply."""
    return bool((row.get("リプライ先の投稿ID") or "").strip())


def has_honorific_consideration(text: str) -> bool:
    """Match the hiragana and kanji spellings of ご検討."""
    return HONORIFIC_CONSIDERATION_RE.search(text or "") is not None


def has_exchange_ratio(text: str) -> bool:
    """Match an explicit Arabic-digit n:m exchange ratio."""
    return EXCHANGE_RATIO_RE.search(text or "") is not None


def has_formal_greeting(text: str) -> bool:
    """Match the fixed-sample greeting beginning with 検索より/から."""
    return FORMAL_GREETING_RE.search(text or "") is not None


def wald_interval(
    successes: int,
    sample_size: int,
    *,
    z: float = WALD_95_Z,
) -> tuple[float, float]:
    """Return a two-sided Wald interval as proportions, clipped to [0, 1]."""
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if not 0 <= successes <= sample_size:
        raise ValueError("successes must be between 0 and sample_size")
    proportion = successes / sample_size
    half_width = z * math.sqrt(proportion * (1 - proportion) / sample_size)
    return max(0.0, proportion - half_width), min(1.0, proportion + half_width)
