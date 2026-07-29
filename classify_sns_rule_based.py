#!/usr/bin/env python3
"""Explainable Japanese SNS sentiment/behaviour classifier (v2.0).

This module keeps the seven project categories used by the earlier classifier,
but replaces its "first keyword wins" rule with weighted, context-aware scoring.

Main improvements over v1:
  * score every category before selecting the primary label;
  * ignore URLs and user mentions as sentiment evidence;
  * avoid ambiguous one-character triggers such as 欲, 神, 走;
  * recognise structured exchange posts (譲/求, postal/hand delivery);
  * handle common Japanese negation after positive/desire expressions;
  * use emoji only as supporting evidence, never as a strong label by itself;
  * retain secondary category, polarity, confidence, scores, and evidence.

The classifier remains deterministic and dependency-free so that results are
reproducible and every decision can be audited from the output columns.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Pattern


VERSION = "2.0.0"

PRIORITY = [
    "不満・怒り",
    "焦り・競争",
    "交換・取引",
    "欲望・執着",
    "喜び・満足",
    "情報共有",
    "中立",
]

ACTIVE_CATEGORIES = PRIORITY[:-1]
MIN_PRIMARY_SCORE = 1.8


# Kept only for a reproducible comparison with the previous implementation.
LEGACY_KEYWORDS: dict[str, list[str]] = {
    "不満・怒り": [
        "腹立つ", "腹がたつ", "ムカつく", "むかつく", "ブチギレ", "怒",
        "キレ", "ふざけ", "最悪", "ひどい", "酷い", "嫌", "うざ", "怖い",
        "しんど", "だる", "疲れ", "泣", "ちくしょ", "落選", "敗北", "全滅",
        "鬱", "後悔", "外れ", "イライラ", "偽物", "にせもん", "転売", "高すぎ",
        "買えない", "当たらない", "手に入らない", "在庫ない", "売ってない",
        "売り切れ", "完売",
    ],
    "焦り・競争": [
        "焦", "急げ", "急い", "早く", "はやく", "今すぐ", "待機", "並ぶ",
        "行列", "走", "ダッシュ", "殺到", "瞬殺", "争奪戦", "戦争", "競争",
        "先着", "当落", "倍率", "再入荷待ち", "入荷待ち", "残り",
    ],
    "交換・取引": [
        "交換", "譲渡", "譲ります", "譲って", "お譲り", "求)", "求：", "求:",
        "求めて", "買取", "買い取り", "売ります", "買います", "取引", "DM", "リプ",
        "メルカリ", "ラクマ", "PayPay", "定価", "送料", "代行",
    ],
    "欲望・執着": [
        "欲しい", "ほしい", "欲し", "ほし", "ください", "欲", "買いたい", "買う",
        "買わなきゃ", "ゲットしたい", "手に入れたい", "集め", "集めたい", "コンプ",
        "全種類", "推し", "沼", "気が狂う", "狂う", "どうしても",
    ],
    "喜び・満足": [
        "嬉しい", "うれしい", "幸せ", "しあわせ", "最高", "サイコー", "激アツ",
        "素敵", "かわいい", "可愛い", "好き", "満足", "よかった", "良かった",
        "楽しい", "楽しみ", "当たった", "買えた", "ゲット", "GET", "届いた",
        "見つけた", "ありがとう", "神",
    ],
    "情報共有": [
        "入荷", "再入荷", "発売", "販売", "予約", "抽選販売", "在庫", "売り場",
        "店舗", "セリア", "ダイソー", "DAISO", "キャンドゥ", "ロフト", "場所",
        "どこ", "いつ", "本日", "今日", "明日", "お知らせ", "情報", "リンク",
        "URL", "http",
    ],
    "中立": [],
}


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: Pattern[str]
    weight: float
    negation_sensitive: bool = False


def rule(
    name: str,
    pattern: str,
    weight: float,
    *,
    negation_sensitive: bool = False,
) -> Rule:
    return Rule(name, re.compile(pattern, re.IGNORECASE), weight, negation_sensitive)


RULES: dict[str, list[Rule]] = {
    "不満・怒り": [
        rule("anger", r"腹(?:が)?立|ムカつ|むかつ|ブチギレ|イライラ|うざ|ウザ|ふざけ|許せない|暴れそう|ちくしょ", 2.8, negation_sensitive=True),
        rule("strong_dislike", r"最悪|最低|地獄|不快|嫌い|嫌すぎ|無理(?:すぎ|だ|です|。|!|！|$)", 2.5, negation_sensitive=True),
        rule("distress", r"しんど|だる|疲れ|怖い|悲し|泣きそう|落ち込|後悔|絶望|鬱|つらい|辛い", 2.1, negation_sensitive=True),
        rule("counterfeit_resale", r"転売(?:ヤー)?|買い占め|偽物|にせもん|偽造|パチモン", 2.4),
        rule("cannot_obtain", r"買え(?:ない|なかった)|買える気がしない|手に入らない|見つからない|出会えない|どこにも(?:ない|無い)|売って(?:い)?ない|在庫(?:が)?ない|品切れ|全滅|落選|外れた|当たらない|諦め(?:た|て|る)", 2.2),
        rule("failed_search", r"見つけられない|残ってなかった|空振り|途方に暮れ|心(?:が)?折れ", 2.5),
        rule("limited_disappointment", r"限定(?:なん|なの|かよ).{0,12}[😭😢😞💔]", 2.0),
        rule("scarcity", r"売り切れ|完売|もぬけの殻|影も形も(?:ない|無い)", 1.7),
        rule("price_complaint", r"高すぎ|高過ぎ|ぼったくり|値段.{0,8}(?:無理|異常)", 2.1),
        rule("negative_emoji", r"[😡🤬💢]", 1.6),
        rule("sad_emoji", r"[😭😢😞💔]", 0.7),
    ],
    "焦り・競争": [
        rule("urgency", r"焦(?:る|り|って)|急げ|急いで|今すぐ|早く(?:買|行|押|並|取|欲)|はやく(?:買|行|押|並|取|欲)", 2.1),
        rule("queue_competition", r"待機|並んで|並ぶ|行列|開店ダッシュ|争奪戦|瞬殺|殺到|先着|倍率|当落|競争|情報戦|入荷待ち|再入荷待ち", 2.3),
        rule("battle_context", r"(?:買|入手|シール|ボンドロ).{0,15}(?:戦争|戦い)|(?:戦争|戦い).{0,15}(?:買|入手|シール|ボンドロ)", 1.9),
        rule("limited_remaining", r"残り(?:わずか|僅か|\d)|あと\d+(?:個|点|枚)", 2.0),
        rule("difficulty", r"難易度(?:が)?高|激戦", 1.8),
    ],
    "交換・取引": [
        rule("exchange_header", r"【\s*交換\s*】|\b交換\b|シール交換|交換希望|交換募集", 3.0),
        rule("offer_field", r"(?:譲|提供)\s*[)】\]：:▶▷]|【\s*譲\s*】", 2.7),
        rule("want_field", r"(?:求|希望)\s*[)】\]：:▶▷]|【\s*求\s*】", 2.7),
        rule("exchange_request", r"交換(?:できますか|可能でしょうか|お願い|してもらえ)|との交換|交換して(?:ください|下さい)", 2.8),
        rule("trade_terms", r"譲渡|お譲り|買取|買い取り|郵送取引|郵送交換|手渡し|取引希望", 2.0),
        rule("trade_platform", r"メルカリ|ラクマ|paypay|フリマ", 1.1),
        rule("trade_support", r"検索(?:から|より)失礼|条件(?:が)?合う方|お声(?:掛|が)け|送料|局留め", 0.8),
    ],
    "欲望・執着": [
        rule("want", r"欲しい|ほしい|欲しすぎ|ほしすぎ|欲し過ぎ|欲しがる|欲しくなった|欲しかった", 2.5, negation_sensitive=True),
        rule("acquisition_intent", r"買いたい|買わなきゃ|手に入れたい|ゲットしたい|探して(?:る|いる)|探しに行|出会いたい", 2.3, negation_sensitive=True),
        rule("collection_drive", r"集めたい|集めてる|集めている|コンプしたい|コンプリート|全種類|沼|中毒|気が狂う", 2.1, negation_sensitive=True),
        rule("planned_purchase", r"買いに.{0,12}(?:行く|行きたい|出かけ|予定)|購入予定|予約したい", 1.9, negation_sensitive=True),
        rule("strong_desire", r"どうしても|何としても", 1.4),
    ],
    "喜び・満足": [
        rule("joy", r"嬉しい|うれしい|幸せ|しあわせ|最高|サイコー|激アツ|テンション(?:が)?上が|大歓喜", 2.3, negation_sensitive=True),
        rule("appreciation", r"素敵|かわいい|可愛い|かっこいい|満足|楽しい|楽しみ|綺麗|きれい", 1.9, negation_sensitive=True),
        rule("good_outcome", r"(?:買|見つ|届|手に入|あって|出会えて|作って).{0,12}(?:よかった|良かった)|(?:よかった|良かった)(?:[!！。]|$)", 1.9, negation_sensitive=True),
        rule("topic_love", r"(?:ボンドロ|ボンボンドロップ|シール|これ|この子|実物)(?:が|は|も)?(?:大好き|好き(?:すぎ|です|だ|!|！|。|$))|(?:シール|文房具)好き(?:として|です|だ|!|！|。|$)", 2.2, negation_sensitive=True),
        rule("successful_acquisition", r"買えた|買えて|ゲット(?:できた|した)?|get(?:できた|した)?|届いた|見つけた|お迎え(?:した|できた)|当たった|購入できた|買っちゃった", 2.5, negation_sensitive=True),
        rule("thanks", r"ありがとう|ありがとうございます|感謝", 1.5, negation_sensitive=True),
        rule("positive_emoji", r"[🥰😍😊☺💗💕❤🫶✨]", 0.45),
    ],
    "情報共有": [
        rule("stock_update", r"再入荷|入荷(?:して|した|あり|中|予定)|在庫(?:あり|有り|戻|復活)|販売(?:開始|再開|中)|発売(?:日|開始)|取り扱い|取扱い|予約(?:開始|受付)|抽選(?:受付|販売)", 2.4),
        rule("formal_notice", r"完売いたしました|販売終了しました|入荷がありましたら|(?:こちら|この)アカウントでポスト|情報を訂正|訂正・補足|要注意", 2.7),
        rule("store_availability", r"(?:ロフト|loft|イオン|ドンキ|セリア|seria|ダイソー|daiso|キャンドゥ|ハンズ|しまむら|バースデイ|コンビニ).{0,24}(?:あり|なし|無い|入荷|在庫|販売|売り切れ|完売|見かけ|置いて)|(?:あり|なし|無い|入荷|在庫|販売|売り切れ|完売|見かけ|置いて).{0,24}(?:ロフト|loft|イオン|ドンキ|セリア|seria|ダイソー|daiso|キャンドゥ|ハンズ|しまむら|バースデイ|コンビニ)", 2.1),
        rule("where_when", r"(?:どこ|いつ).{0,18}(?:売|買|入荷|発売|在庫)|(?:売|買|入荷|発売|在庫).{0,18}(?:どこ|いつ)", 1.5),
        rule("information_terms", r"入荷情報|在庫情報|販売情報|目撃情報|情報共有|お知らせ", 1.8),
    ],
}


TEXT_COLUMN_CANDIDATES = [
    "投稿本文",
    "内容",
    "本文",
    "テキスト",
    "text",
    "tweet",
    "body",
]

OUTPUT_COLUMNS = [
    "sentiment_category",
    "sentiment_secondary",
    "sentiment_polarity",
    "sentiment_score",
    "sentiment_confidence",
    "matched_keywords",
    "category_scores",
    "classification_version",
]

URL_RE = re.compile(r"(?:https?://|www\.)\S+|\[\[(?:https?://)?[^\]]+\]\]|(?:pic\.)?x\.com/\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"(?<!\w)@[A-Za-z0-9_]+")
WHITESPACE_RE = re.compile(r"\s+")
NEGATION_RE = re.compile(r"^(?:く|じゃ|では|でも)?(?:ない|無い|ねえ|なく|なかった|ありません|ません)")


@dataclass
class Classification:
    primary: str
    secondary: str
    polarity: str
    score: float
    confidence: str
    evidence: list[str]
    scores: dict[str, float]

    @property
    def matched_keywords(self) -> str:
        return "|".join(self.evidence)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    normalized = URL_RE.sub(" ", normalized)
    normalized = MENTION_RE.sub(" ", normalized)
    return WHITESPACE_RE.sub(" ", normalized).strip()


def find_text_column(headers: list[str], requested: str | None) -> int:
    if requested:
        if requested not in headers:
            raise ValueError(f"Text column '{requested}' was not found. Headers: {headers}")
        return headers.index(requested)

    for candidate in TEXT_COLUMN_CANDIDATES:
        if candidate in headers:
            return headers.index(candidate)

    raise ValueError(
        "Text column was not found. "
        f"Use --text-column to specify it. Headers: {headers}"
    )


def keyword_matches(text: str, keywords: Iterable[str]) -> list[str]:
    """Compatibility helper used by the legacy comparison."""
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    matches: list[str] = []
    for keyword in keywords:
        normalized_keyword = unicodedata.normalize("NFKC", keyword).casefold()
        if normalized_keyword and normalized_keyword in normalized:
            matches.append(keyword)
    return matches


def classify_legacy(text: str) -> tuple[str, str]:
    """Reproduce the v1 first-match classifier for QA comparisons."""
    for category in PRIORITY:
        matches = keyword_matches(text, LEGACY_KEYWORDS[category])
        if matches:
            return category, "|".join(matches)
    return "中立", ""


def _is_negated(text: str, end: int) -> bool:
    suffix = text[end : end + 10].lstrip(" 　、,。.!！?？")
    return bool(NEGATION_RE.match(suffix))


def _score_rules(text: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    scores = {category: 0.0 for category in ACTIVE_CATEGORIES}
    evidence = {category: [] for category in ACTIVE_CATEGORIES}

    for category, category_rules in RULES.items():
        for item in category_rules:
            matches = list(item.pattern.finditer(text))
            accepted = [
                match
                for match in matches
                if not (item.negation_sensitive and _is_negated(text, match.end()))
            ]
            if not accepted:
                continue

            # Repetition adds some evidence, but is capped to avoid keyword spam.
            multiplier = 1.0 + min(len(accepted) - 1, 2) * 0.2
            scores[category] += item.weight * multiplier
            snippets = []
            for match in accepted[:2]:
                snippet = match.group(0).strip()
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
            evidence[category].append(f"{item.name}:{'/'.join(snippets)}")

    # Structured trade posts become much more reliable when both fields occur.
    has_offer = bool(re.search(r"(?:譲|提供)\s*[)】\]：:▶▷]|【\s*譲\s*】", text))
    has_want = bool(re.search(r"(?:求|希望)\s*[)】\]：:▶▷]|【\s*求\s*】", text))
    if has_offer and has_want:
        scores["交換・取引"] += 2.2
        evidence["交換・取引"].append("structured_pair:譲+求")

    # Generic trade-support wording should not classify unrelated conversations.
    trade_strong = any(
        token in "|".join(evidence["交換・取引"])
        for token in ("exchange_header", "offer_field", "want_field", "exchange_request", "trade_terms", "structured_pair")
    )
    if not trade_strong and scores["交換・取引"]:
        scores["交換・取引"] = min(scores["交換・取引"], 1.2)

    # Emoji are supporting signals. Without lexical joy, cap them below threshold.
    positive_non_emoji = [x for x in evidence["喜び・満足"] if not x.startswith("positive_emoji:")]
    if not positive_non_emoji:
        scores["喜び・満足"] = min(scores["喜び・満足"], 0.9)

    negative_non_emoji = [
        x for x in evidence["不満・怒り"]
        if not x.startswith(("negative_emoji:", "sad_emoji:"))
    ]
    if not negative_non_emoji:
        scores["不満・怒り"] = min(scores["不満・怒り"], 1.0)

    return scores, evidence


def classify_detailed(text: str) -> Classification:
    normalized = normalize_text(text)
    scores, evidence_by_category = _score_rules(normalized)
    ranked = sorted(
        ACTIVE_CATEGORIES,
        key=lambda category: (-scores[category], PRIORITY.index(category)),
    )
    top, second = ranked[0], ranked[1]
    top_score = scores[top]
    second_score = scores[second]

    if top_score < MIN_PRIMARY_SCORE:
        primary = "中立"
        secondary = ""
        selected_evidence: list[str] = []
        confidence = "中" if top_score < 0.8 else "低"
    else:
        primary = top
        secondary = second if second_score >= MIN_PRIMARY_SCORE else ""
        selected_evidence = [f"{top}:{item}" for item in evidence_by_category[top]]
        if secondary:
            selected_evidence.extend(
                f"{secondary}:{item}" for item in evidence_by_category[second]
            )
        margin = top_score - second_score
        if top_score >= 4.0 and margin >= 1.4:
            confidence = "高"
        elif top_score >= 1.9 and margin >= 0.5:
            confidence = "中"
        else:
            confidence = "低"

    positive = scores["喜び・満足"] >= MIN_PRIMARY_SCORE
    negative = scores["不満・怒り"] >= MIN_PRIMARY_SCORE
    if positive and negative:
        polarity = "混合"
    elif positive:
        polarity = "ポジティブ"
    elif negative:
        polarity = "ネガティブ"
    else:
        polarity = "中立・行動"

    rounded_scores = {category: round(scores[category], 2) for category in ACTIVE_CATEGORIES}
    return Classification(
        primary=primary,
        secondary=secondary,
        polarity=polarity,
        score=round(top_score, 2),
        confidence=confidence,
        evidence=selected_evidence,
        scores=rounded_scores,
    )


def classify(text: str) -> tuple[str, str]:
    """Backward-compatible two-field interface used by older scripts."""
    result = classify_detailed(text)
    return result.primary, result.matched_keywords


def unique_output_headers(headers: list[str]) -> list[str]:
    return [header for header in headers if header not in OUTPUT_COLUMNS] + OUTPUT_COLUMNS


def classify_csv(input_path: Path, output_path: Path, text_column: str | None) -> int:
    with input_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.reader(src)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"Input CSV is empty: {input_path}") from None

        text_index = find_text_column(headers, text_column)
        old_indexes = {index for index, header in enumerate(headers) if header in OUTPUT_COLUMNS}
        output_headers = unique_output_headers(headers)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8-sig", newline="") as dst:
            writer = csv.writer(dst)
            writer.writerow(output_headers)

            count = 0
            for row in reader:
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                text = row[text_index] if text_index < len(row) else ""
                result = classify_detailed(text)
                base = [
                    value
                    for index, value in enumerate(row[: len(headers)])
                    if index not in old_indexes
                ]
                writer.writerow(
                    base
                    + [
                        result.primary,
                        result.secondary,
                        result.polarity,
                        f"{result.score:.2f}",
                        result.confidence,
                        result.matched_keywords,
                        json.dumps(result.scores, ensure_ascii=False, separators=(",", ":")),
                        VERSION,
                    ]
                )
                count += 1

    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify Japanese SNS posts with explainable context-aware rules."
    )
    parser.add_argument("--input", default="INPUT_new.csv", type=Path)
    parser.add_argument(
        "--output",
        default=Path("data/output/rule_based_classified.csv"),
        type=Path,
    )
    parser.add_argument("--text-column", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = classify_csv(args.input, args.output, args.text_column)
    print(f"Classified {count:,} rows with v{VERSION} -> {args.output}")


if __name__ == "__main__":
    main()
