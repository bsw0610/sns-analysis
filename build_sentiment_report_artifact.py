#!/usr/bin/env python3
"""Build the canonical Data Analytics artifact for the 2511-2604 analysis."""

from __future__ import annotations

import json
from pathlib import Path


ANALYSIS = Path("data/output/sentiment_analysis_2511-2604.json")
ARTIFACT = Path("data/output/sentiment_report_artifact_2511-2604.json")
NOTES = Path("data/output/sentiment_report_notes_2511-2604.json")

CATEGORY_ORDER = [
    "不満・怒り",
    "焦り・競争",
    "交換・取引",
    "欲望・執着",
    "喜び・満足",
    "情報共有",
    "中立",
]


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    meta = analysis["metadata"]
    quality = analysis["quality"]
    category_rows = analysis["category_summary"]
    category_by_name = {row["category"]: row for row in category_rows}

    month_rows = analysis["monthly_summary"]
    month_lookup = {
        (row["month"], row["category"]): row for row in month_rows
    }
    nov = {cat: month_lookup[("2025-11", cat)] for cat in CATEGORY_ORDER}
    apr = {cat: month_lookup[("2026-04", cat)] for cat in CATEGORY_ORDER}

    confidence = {row["confidence"]: row for row in analysis["confidence_summary"]}
    non_low_confidence = 1.0 - confidence["低"]["share"]
    exchange = category_by_name["交換・取引"]

    headline = [{
        "total_posts": meta["source_rows"],
        "exchange_share": exchange["share"],
        "non_low_confidence_share": non_low_confidence,
        "changed_share": quality["classification_changed_share"],
    }]

    overall_mix = sorted(
        [
            {
                "category": row["category"],
                "count": row["count"],
                "share": row["share"],
                "unique_users": row["unique_users"],
                "repost_share": row["repost_share"],
            }
            for row in category_rows
        ],
        key=lambda row: row["share"],
        reverse=True,
    )

    key_categories = ["交換・取引", "不満・怒り", "欲望・執着", "喜び・満足"]
    lifecycle = [
        {
            "category": category,
            "nov_share": nov[category]["share"],
            "apr_share": apr[category]["share"],
            "change_pp": round((apr[category]["share"] - nov[category]["share"]) * 100, 2),
            "nov_count": nov[category]["count"],
            "apr_count": apr[category]["count"],
        }
        for category in key_categories
    ]

    months = sorted({row["month"] for row in month_rows})
    monthly_wide = []
    for month in months:
        monthly_wide.append(
            {
                "month": month,
                "total": month_lookup[(month, "中立")]["month_total"],
                "negative_share": month_lookup[(month, "不満・怒り")]["share"],
                "urgency_share": month_lookup[(month, "焦り・競争")]["share"],
                "exchange_share": month_lookup[(month, "交換・取引")]["share"],
                "desire_share": month_lookup[(month, "欲望・執着")]["share"],
                "positive_share": month_lookup[(month, "喜び・満足")]["share"],
                "information_share": month_lookup[(month, "情報共有")]["share"],
                "neutral_share": month_lookup[(month, "中立")]["share"],
            }
        )

    dedup = {row["category"]: row for row in analysis["deduplicated_text_summary"]}
    original = {row["category"]: row for row in analysis["original_only_summary"]}
    robustness = [
        {
            "category": row["category"],
            "all_posts_share": row["share"],
            "deduplicated_share": dedup[row["category"]]["share"],
            "original_only_share": original[row["category"]]["share"],
            "dedup_delta_pp": round((dedup[row["category"]]["share"] - row["share"]) * 100, 2),
            "original_delta_pp": round((original[row["category"]]["share"] - row["share"]) * 100, 2),
        }
        for row in category_rows
    ]

    changes = analysis["top_changed_pairs"][:10]
    change_rows = [
        {
            "legacy": row["legacy"],
            "improved": row["improved"],
            "count": row["count"],
            "share_of_all": row["count"] / meta["source_rows"],
        }
        for row in changes
    ]

    source = {
        "id": "sentiment_source",
        "label": "2511-2604.csvおよび改良版分類器v2.0",
        "path": "data/output/2511-2604.csv",
        "query": {
            "engine": "python",
            "language": "python",
            "description": "広告除去後に結合した2025年11月〜2026年4月のX投稿へ、説明可能なルールベース分類器を適用した。",
            "executed_at": meta["generated_at"],
            "tables_used": ["data/output/2511-2604.csv"],
            "filters": [
                "分析期間：2025-11-01〜2026-04-30",
                "広告除去後の結合ファイルに含まれる109,037件の投稿をすべて対象",
                "投稿IDの重複除去なし：元データの重複IDは0件",
            ],
            "metric_definitions": [
                "カテゴリ割合＝該当カテゴリに主分類された投稿数／同期間の全投稿数",
                "重複文面除去後の割合＝正規化本文が同一の場合、最初の1件のみを含めた割合",
                "オリジナル投稿割合＝リポスト以外の投稿のみを含めた割合",
                "旧コードとの差分率＝v1とv2で主分類が異なる投稿数／全投稿数",
                "非低信頼割合＝信頼度が「高」または「中」の投稿数／全投稿数",
            ],
        },
    }

    exchange_change_pp = (apr["交換・取引"]["share"] - nov["交換・取引"]["share"]) * 100
    negative_change_pp = (apr["不満・怒り"]["share"] - nov["不満・怒り"]["share"]) * 100
    desire_change_pp = (apr["欲望・執着"]["share"] - nov["欲望・執着"]["share"]) * 100

    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "2025年11月〜2026年4月 X投稿感情分析",
            "description": "従来のルールベースコードを改良し、109,037件の投稿について感情・行動カテゴリと月別変化を分析した技術レポート",
            "generatedAt": meta["generated_at"],
            "cards": [
                {
                    "id": "total_posts_card",
                    "description": "広告除去後に感情分析へ含めた投稿数",
                    "dataset": "headline",
                    "sourceId": "sentiment_source",
                    "metrics": [{"label": "分析対象投稿", "field": "total_posts", "format": "number"}],
                },
                {
                    "id": "exchange_share_card",
                    "description": "全投稿のうち交換・取引が主分類となった割合",
                    "dataset": "headline",
                    "sourceId": "sentiment_source",
                    "metrics": [{"label": "交換・取引割合", "field": "exchange_share", "format": "percent"}],
                },
                {
                    "id": "confidence_card",
                    "description": "自動分類の信頼度が中以上の投稿割合",
                    "dataset": "headline",
                    "sourceId": "sentiment_source",
                    "metrics": [{"label": "非低信頼分類", "field": "non_low_confidence_share", "format": "percent"}],
                },
                {
                    "id": "changed_card",
                    "description": "旧来の先着キーワード方式と主分類が変わった割合",
                    "dataset": "headline",
                    "sourceId": "sentiment_source",
                    "metrics": [{"label": "v1からの変更", "field": "changed_share", "format": "percent"}],
                },
            ],
            "charts": [
                {
                    "id": "lifecycle_chart",
                    "title": "2025年11月と2026年4月の主要カテゴリ割合",
                    "subtitle": "各月の全投稿を分母とした割合。6か月間の始点と終点を比較",
                    "type": "bar",
                    "dataset": "lifecycle",
                    "sourceId": "sentiment_source",
                    "xField": "category",
                    "series": [
                        {"field": "nov_share", "label": "2025-11", "color": "neutral", "role": "baseline"},
                        {"field": "apr_share", "label": "2026-04", "color": "blue", "role": "actual"},
                    ],
                    "settings": {"groupMode": "grouped", "orientation": "vertical", "showValues": True},
                    "valueFormat": "percent",
                    "intent": "comparison",
                    "question": "関心は獲得感情から交換行動へ移行したか？",
                    "comparisonContext": {"baseline": "2025-11", "denominator": "各月の全投稿", "grain": "月×主分類", "unit": "割合"},
                    "layout": "full",
                },
                {
                    "id": "overall_mix_chart",
                    "title": "全期間のカテゴリ構成",
                    "subtitle": "109,037件の投稿における主分類割合（降順）",
                    "type": "bar",
                    "dataset": "overall_mix",
                    "sourceId": "sentiment_source",
                    "xField": "category",
                    "series": [{"field": "share", "label": "割合", "color": "blue", "role": "actual"}],
                    "settings": {"orientation": "horizontal", "groupMode": "single", "sort": "descending", "showValues": True},
                    "valueFormat": "percent",
                    "intent": "composition",
                    "question": "全体の会話で最も多い感情・行動タイプは何か？",
                    "comparisonContext": {"denominator": "全109,037件の投稿", "grain": "投稿×主分類", "unit": "割合"},
                    "layout": "full",
                },
            ],
            "tables": [
                {
                    "id": "monthly_table",
                    "title": "月別カテゴリ割合",
                    "subtitle": "2025年11月〜2026年4月、各月の全投稿を分母として計算",
                    "dataset": "monthly_wide",
                    "sourceId": "sentiment_source",
                    "defaultSort": {"field": "month", "direction": "asc"},
                    "density": "spacious",
                    "columns": [
                        {"field": "month", "label": "月", "type": "text"},
                        {"field": "total", "label": "投稿数", "format": "number"},
                        {"field": "negative_share", "label": "不満・怒り", "format": "percent"},
                        {"field": "urgency_share", "label": "焦り・競争", "format": "percent"},
                        {"field": "exchange_share", "label": "交換・取引", "format": "percent"},
                        {"field": "desire_share", "label": "欲望・執着", "format": "percent"},
                        {"field": "positive_share", "label": "喜び・満足", "format": "percent"},
                        {"field": "information_share", "label": "情報共有", "format": "percent"},
                        {"field": "neutral_share", "label": "中立", "format": "percent"},
                    ],
                },
                {
                    "id": "robustness_table",
                    "title": "重複およびリポスト感度",
                    "subtitle": "全件・同一文面1件のみ・オリジナル投稿のみのカテゴリ割合を比較",
                    "dataset": "robustness",
                    "sourceId": "sentiment_source",
                    "defaultSort": {"field": "all_posts_share", "direction": "desc"},
                    "density": "spacious",
                    "columns": [
                        {"field": "category", "label": "カテゴリ", "type": "text"},
                        {"field": "all_posts_share", "label": "全件", "format": "percent"},
                        {"field": "deduplicated_share", "label": "同一文面除去", "format": "percent"},
                        {"field": "original_only_share", "label": "オリジナルのみ", "format": "percent"},
                        {"field": "dedup_delta_pp", "label": "同一文面除去差（pp）", "format": "number", "movement": True},
                        {"field": "original_delta_pp", "label": "オリジナルのみ差（pp）", "format": "number", "movement": True},
                    ],
                },
                {
                    "id": "changes_table",
                    "title": "旧コードから大きく変わった分類",
                    "subtitle": "v1とv2で主分類が異なる組み合わせの上位10件",
                    "dataset": "changes",
                    "sourceId": "sentiment_source",
                    "defaultSort": {"field": "count", "direction": "desc"},
                    "density": "spacious",
                    "columns": [
                        {"field": "legacy", "label": "旧分類", "type": "text"},
                        {"field": "improved", "label": "改良後分類", "type": "text"},
                        {"field": "count", "label": "変更件数", "format": "number"},
                        {"field": "share_of_all", "label": "全体比", "format": "percent"},
                    ],
                },
            ],
            "sources": [source],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# 2025年11月〜2026年4月 X投稿感情分析"},
                {
                    "id": "technical_summary",
                    "type": "markdown",
                    "sourceId": "sentiment_source",
                    "body": (
                        "## 技術概要\n\n"
                        f"- **全{meta['source_rows']:,}件では、交換・取引が21.2%で最大の非中立カテゴリでした。** 中立は41.4%でした。\n"
                        f"- **2025年11月から2026年4月にかけて、交換・取引の割合は{exchange_change_pp:+.1f}pp変化しました。** 同期間に不満・怒りは{negative_change_pp:+.1f}pp、欲望・執着は{desire_change_pp:+.1f}pp変化し、会話の中心が「獲得欲求・不満」から「交換行動」へ移るパターンが明確です。\n"
                        f"- **v1と主分類が異なる投稿は{quality['classification_changed_from_v1']:,}件（{pct(quality['classification_changed_share'])}）でした。** URL、短い単語、単一優先順位による過剰分類を抑えた影響が大きいと考えられます。\n"
                        f"- **同一文面の重複は{quality['duplicate_normalized_texts']:,}件（{pct(quality['duplicate_normalized_text_share'])}）ですが、重複除去後・オリジナル投稿限定でも主要順位と交換割合はほぼ維持されました。**"
                    ),
                },
                {"id": "headline_metrics", "type": "metric-strip", "cardIds": ["total_posts_card", "exchange_share_card", "confidence_card", "changed_card"]},
                {
                    "id": "lifecycle_section",
                    "type": "markdown",
                    "sourceId": "sentiment_source",
                    "body": (
                        "## 流行の中心は「購入競争」から「交換エコシステム」へ移行しました\n\n"
                        f"11月の交換・取引は{pct(nov['交換・取引']['share'])}でしたが、4月には{pct(apr['交換・取引']['share'])}まで上昇しました。一方、不満・怒りは{pct(nov['不満・怒り']['share'])}から{pct(apr['不満・怒り']['share'])}、欲望・執着は{pct(nov['欲望・執着']['share'])}から{pct(apr['欲望・執着']['share'])}へ低下しました。商品を探して購入する段階よりも、保有商品の交換・取引という後続行動が拡大したと解釈できます。"
                    ),
                },
                {"id": "lifecycle_chart_block", "type": "chart", "chartId": "lifecycle_chart"},
                {
                    "id": "lifecycle_note",
                    "type": "markdown",
                    "body": "月別観測点が6点のみのため、連続トレンド線ではなく始点と終点のグループ棒グラフを使用しました。この変化は、同一文面を月内で1件に限定した場合やリポストを除外した場合でも維持され、単純な複製拡散だけでは説明できません。ただし、因果関係や個々の利用者の態度変化を直接示すものではありません。",
                },
                {
                    "id": "mix_section",
                    "type": "markdown",
                    "sourceId": "sentiment_source",
                    "body": (
                        "## 全体では中立に次いで交換・取引が最大でした\n\n"
                        f"全体の主分類は、中立{pct(category_by_name['中立']['share'])}、交換・取引{pct(category_by_name['交換・取引']['share'])}、喜び・満足{pct(category_by_name['喜び・満足']['share'])}、不満・怒り{pct(category_by_name['不満・怒り']['share'])}の順でした。一般的な肯定・否定・中立の3分類だけでは、交換・取引や欲望・執着といった行動ベースのシグナルを見落とす可能性があります。"
                    ),
                },
                {"id": "overall_mix_chart_block", "type": "chart", "chartId": "overall_mix_chart"},
                {
                    "id": "monthly_detail_section",
                    "type": "markdown",
                    "body": "## 月別詳細では交換増加と緊張緩和が同時に見られます\n\n月別表は各月の投稿数をそれぞれ分母として使用します。2月は不満・怒りが13.3%と高く、3月以降は交換・取引が急速に拡大しました。月ごとの総量が異なるため、件数よりも割合の変化を中心に確認する必要があります。",
                    "sourceId": "sentiment_source",
                },
                {"id": "monthly_table_block", "type": "table", "tableId": "monthly_table"},
                {
                    "id": "scope_section",
                    "type": "markdown",
                    "body": (
                        "## 分析範囲と測定単位\n\n"
                        "分析単位は、広告除去後に結合した`2511-2604.csv`の投稿1件です。期間は2025年11月1日から2026年4月30日までで、元データのタイムゾーンはAsia/Tokyoと仮定しました。主分類は、不満・怒り、焦り・競争、交換・取引、欲望・執着、喜び・満足、情報共有、中立の7カテゴリです。1件の投稿に複数のシグナルがある場合は全カテゴリを採点し、最高得点を主分類、閾値を超えた次点を副分類として記録しました。"
                    ),
                },
                {
                    "id": "method_section",
                    "type": "markdown",
                    "body": (
                        "## v2では単一キーワード優先方式を文脈スコア方式へ変更しました\n\n"
                        "旧コードでは、優先順位上で最初に見つかったキーワードが最終分類を決めていました。v2ではURLとユーザーメンションを根拠から除外し、`欲`、`神`、`走`のように短く曖昧な単独ルールを削除しました。さらに、日本語の否定表現（`欲しくない`、`かわいくない`）、構造化された交換文脈（`譲`＋`求`、郵送・対面取引）、絵文字の補助シグナル、複合感情、分類信頼度を反映しました。観察に基づく28件の回帰ケースをすべて通過し、各結果にスコアと一致ルールを残しています。"
                    ),
                },
                {
                    "id": "robustness_section",
                    "type": "markdown",
                    "sourceId": "sentiment_source",
                    "body": (
                        "## 重複とリポストを除外しても結論の方向性は維持されました\n\n"
                        f"投稿IDは{quality['unique_post_ids']:,}件ですべて一意でしたが、正規化本文が同一の重複投稿は{quality['duplicate_normalized_texts']:,}件ありました。全件・同一文面除去後・オリジナル投稿限定のカテゴリ割合の差は小さく、交換・取引はそれぞれ{pct(category_by_name['交換・取引']['share'])}、{pct(dedup['交換・取引']['share'])}、{pct(original['交換・取引']['share'])}でした。したがって、全期間の交換中心パターンは重複やリポストに大きく依存していません。"
                    ),
                },
                {"id": "robustness_table_block", "type": "table", "tableId": "robustness_table"},
                {
                    "id": "code_change_section",
                    "type": "markdown",
                    "sourceId": "sentiment_source",
                    "body": (
                        "## 最大の修正効果はURL・短語による過剰分類の縮小でした\n\n"
                        f"主分類の変更率は{pct(quality['classification_changed_share'])}です。最大の移動は情報共有→中立の{changes[0]['count']:,}件で、v1で`http`、`今日`、`どこ`などを即座に情報共有とみなしていたルールを削除、または文脈条件付きに変更した影響です。交換・取引→中立、欲望・執着→中立も、`DM`、`定価`、`欲`、`推し`などの単独語による過剰分類を抑えた結果です。"
                    ),
                },
                {"id": "changes_table_block", "type": "table", "tableId": "changes_table"},
                {
                    "id": "limitations_section",
                    "type": "markdown",
                    "body": (
                        "## 自動分類は方向性分析用であり、手動正解を代替するものではありません\n\n"
                        f"信頼度が高または中の分類は{pct(non_low_confidence)}でしたが、この数値はモデル内部のルール根拠の強さであり、実際の正解率ではありません。皮肉、引用・リポストにおける話者の態度、画像内テキスト、商品と無関係な感情語は完全には解釈できません。同一本文の最大反復回数は{quality['max_duplicate_text_frequency']:,}回で、自動化・コピー投稿も一部含まれます。カテゴリ別30件、合計{quality['manual_validation_rows']}件の確認サンプルを作成しましたが、手動正解ラベルは未入力のため、適合率・再現率は提示していません。"
                    ),
                },
                {
                    "id": "next_steps_section",
                    "type": "markdown",
                    "body": (
                        "## 次の段階は210件の手動確認とルール再調整です\n\n"
                        "1. 確認サンプルの`手動正解ラベル`と`分類正誤`を人手で入力します。\n"
                        "2. カテゴリ別の適合率・再現率・混同行列を計算し、特に低信頼の10.2%を優先確認します。\n"
                        "3. 誤分類が繰り返される表現のみをルールへ追加し、同じ回帰テストへ固定して再発を防ぎます。\n"
                        "4. 研究上の解釈では、月別の交換割合・不満割合・欲望割合を主要指標としつつ、自動分類であることを明記します。"
                    ),
                },
                {
                    "id": "questions_section",
                    "type": "markdown",
                    "body": (
                        "## 追加で確認すべき問い\n\n"
                        "- 3〜4月の交換増加は、特定商品の発売やガチャ・ミニチュア商品の拡大と関連しているか？\n"
                        "- 同じ利用者が購入欲求から交換行動へ移行したのか、それとも参加利用者層が変化したのか？\n"
                        "- 手動確認後、リポストと引用文を別の発話行為として分離すると、肯定・否定割合はどの程度変わるか？"
                    ),
                },
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": meta["generated_at"],
            "status": "ready",
            "datasets": {
                "headline": headline,
                "overall_mix": overall_mix,
                "lifecycle": lifecycle,
                "monthly_wide": monthly_wide,
                "robustness": robustness,
                "changes": change_rows,
            },
        },
        "sources": [source],
    }

    notes = {
        "audience": "technical",
        "delivery_mode": "html",
        "required_structure_mapping": {
            "Title": "title",
            "Technical summary": "technical_summary + headline_metrics",
            "Key findings with visual evidence": "lifecycle_section + lifecycle_chart + mix_section + overall_mix_chart + monthly_table",
            "Scope, data, and metric definitions": "scope_section",
            "Methodology": "method_section + code_change_section",
            "Limitations, uncertainty, and robustness checks": "robustness_section + limitations_section",
            "Recommended next steps": "next_steps_section",
            "Further questions": "questions_section",
        },
        "chart_map": [
            {
                "section": "流行の中心の移行",
                "question": "獲得感情から交換行動へ移行したか？",
                "family": "Comparison",
                "type": "grouped bar",
                "fields": ["category", "nov_share", "apr_share"],
                "takeaway": "交換・取引の割合が8.1%から37.0%へ上昇",
                "palette": "neutral baseline + blue actual",
                "delivery": str(ARTIFACT),
            },
            {
                "section": "全体構成",
                "question": "全体の会話で最も多いタイプは何か？",
                "family": "Comparison & Ranking",
                "type": "horizontal bar",
                "fields": ["category", "share", "count", "unique_users"],
                "takeaway": "中立に次いで交換・取引が最大",
                "palette": "single-root blue",
                "delivery": str(ARTIFACT),
            },
        ],
        "omissions": [
            "6か月分は連続トレンド線の推奨観測点8〜12点より少ないため、折れ線ではなく始点・終点のグループ棒と月別表を使用",
            "感情語の頻度のみから因果関係を主張しない",
            "手動正解ラベルがないため、正解率・再現率・F1は未提示",
        ],
    }

    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(ARTIFACT)
    print(NOTES)


if __name__ == "__main__":
    main()
