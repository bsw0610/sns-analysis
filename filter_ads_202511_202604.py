#!/usr/bin/env python3
"""Merge monthly X exports and remove high-confidence promotional posts."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


SOURCE_NAMES = ["202511.csv", "202512.csv", "202601.csv", "202602.csv", "202603.csv", "202604.csv"]

USER_KEYWORDS = [
    "名様",
    "参加方法",
    "リポスト",
    "ころじいちゃん",
    "本日抽選開始ラインナップ",
    "準備資金",
    "お知らせ",
    "日間限定",
    "再入荷情報",
    "ご来店",
    "詳しくは",
    "会計につき",
    "プレオープン大還元祭",
    "大還元祭",
    "人達成企画",
    "第弾",
    "フォロワー様",
]


@dataclass(frozen=True)
class Rule:
    code: str
    reason: str
    pattern: re.Pattern[str]


def compile_rule(code: str, reason: str, pattern: str) -> Rule:
    return Rule(code, reason, re.compile(pattern, re.IGNORECASE | re.DOTALL))


AD_RULES = [
    compile_rule(
        "GIVEAWAY_CAMPAIGN",
        "경품·캠페인 응모를 유도하는 홍보 문구",
        r"(?:応募方法|応募条件|応募期間|応募受付|応募は|応募はこちら|"
        r"抽選で.{0,35}(?:プレゼント|当たる|進呈)|"
        r"(?:プレゼント|キャンペーン|記念企画).{0,55}(?:応募|抽選|当選|締切|〆切|フォロー|いいね|RT|リツイート)|"
        r"フォロー.{0,35}(?:いいね|RT|リツイート).{0,35}(?:応募|抽選|当選)|"
        r"(?:RT|リツイート).{0,35}(?:応募|抽選|当選)|"
        r"当選者(?:には|へ|の方)|当選発表|応募締切|締切[:：].{0,25}\d|"
        r"(?:抽選|先着)(?:販売)?(?:受付|申込|申し込み)(?:中|開始|スタート)|"
        r"抽選会(?:を)?(?:開催|実施)(?:します|いたします|中)?|"
        r"抽選販売.{0,45}(?:LivePocket|事前受付|対象商品|申込|申し込み|受付中|受付開始))",
    ),
    compile_rule(
        "DIRECT_SALES",
        "판매·예약·주문을 직접 권유하는 상업성 문구",
        r"(?:販売いたします|販売しております|好評販売中|販売中です|"
        r"発売いたします|好評発売中|発売中です|"
        r"予約受付(?:中|開始|は)|ご予約(?:受付|承り|は)|注文受付|ご注文(?:受付|は|はこちら)|"
        r"購入はこちら|ご購入はこちら|お買い求め(?:ください|いただけます)|お求めください|"
        r"商品ページ(?:はこちら|から)|オンラインショップ(?:はこちら|で販売|で購入)|"
        r"通販サイト(?:はこちら|で販売|で購入|でご購入)|"
        r"お取り置き(?:承り|受付)|店頭にて販売|数量限定販売|受注販売(?:開始|受付|いたします)|"
        r"(?:販売開始|発売開始|販売スタート|発売スタート|予約開始|先着販売)"
        r".{0,90}(?:税込|価格|詳細|リンク|リプ|ブックマーク|チェック|お早め|狙い目|必須|待機|ラインナップ|対象商品))",
    ),
    compile_rule(
        "SALES_INFORMATION",
        "판매 일정·구매 방법을 알리는 공식성 홍보 문구",
        r"(?:【[^】]{0,35}販売情報[^】]{0,15}】|【[^】]{0,45}販売について】|"
        r"📢[^\n]{0,25}販売情報|販売情報[:：]|購入券.{0,25}ご案内|販売を再開いたします|"
        r"本日.{0,30}(?:発売|販売).{0,40}(?:お見逃しなく|登場|開始)|"
        r"(?:発売|販売).{0,35}(?:気になる方|お見逃しなく|早い者勝ち))",
    ),
    compile_rule(
        "AFFILIATE_LINK_PROMO",
        "고정 투고·댓글 링크로 구매를 유도하는 홍보 문구",
        r"(?:(?:販売|発売|予約|再入荷|在庫復活|再販|商品).{0,100}"
        r"(?:詳細は固定|固定ポスト|固定ツイ|固ツイ|販売リンク|購入リンク|リンクはリプ|リンクはコメント|リプ欄|リプへ|"
        r"ブックマークで保存|チェックして|お早めに|狙い目|待機がおすすめ)|"
        r"(?:詳細は固定|固定ポスト|固定ツイ|固ツイ|販売リンク|購入リンク|リンクはリプ|リプ欄|リプへ)"
        r".{0,100}(?:販売|発売|予約|再入荷|在庫復活|再販|商品))",
    ),
    compile_rule(
        "PERSONAL_SALES_SOLICITATION",
        "개인 판매·구매대행을 공개적으로 모집하는 홍보 문구",
        r"(?:(?:定価で)?(?:譲れます|お譲りできます|お譲りします)|代行(?:も)?受付中|購入代行.{0,12}受付|"
        r"余って(?:いる|る).{0,18}(?:欲しい方|欲しい人))"
        r".{0,100}(?:希望者|欲しい方|欲しい人|メッセージ|DM|連絡|固定ポスト|固定ツイ|送料|手数料|代行費)|"
        r"(?:欲しい方|欲しい人|希望者).{0,70}(?:連絡(?:ください|下さい)|メッセージ(?:ください|お願いします)|DM(?:ください|お願いします))",
    ),
    compile_rule(
        "EC_AVAILABILITY_PROMO",
        "EC몰 재고·재판매 정보를 이용해 구매를 재촉하는 홍보 문구",
        r"(?:Amazon|アマゾン|楽天(?:市場)?|Yahoo!?ショッピング).{0,80}"
        r"(?:在庫がある今がチャンス|今がチャンス|在庫復活中|正規在庫復活中|先着販売スタート|"
        r"販売開始|販売リンク|購入リンク|お早めに|リンクはリプ|ブックマークで保存|早い者勝ち|"
        r"要チェック|チェックして|手に入れよう|再販速報)|"
        r"(?:在庫がある今がチャンス|今がチャンス|在庫復活中|先着販売スタート).{0,80}"
        r"(?:Amazon|アマゾン|楽天(?:市場)?|Yahoo!?ショッピング)",
    ),
    compile_rule(
        "MARKETPLACE_LISTING",
        "마켓·플리마에 상품을 출품·판매하는 홍보 문구",
        r"(?:メルカリ|ラクマ|ヤフーフリマ|Yahoo!?フリマ|PayPayフリマ|minne|BASE|BOOTH|Creema|フリマ)"
        r".{0,45}(?:出品しました|出品しています|出品中|販売しています|販売中)|"
        r"(?:出品しました|出品しています|出品中).{0,45}(?:メルカリ|ラクマ|ヤフーフリマ|Yahoo!?フリマ|PayPayフリマ|フリマ)",
    ),
    compile_rule(
        "RESTOCK_STORE_NOTICE",
        "매장 입고·재입고·재고를 알리는 상업성 안내",
        r"(?:(?:入荷しました|入荷いたしました|入荷しております|再入荷しました|再入荷いたしました)"
        r"(?=.{0,90}(?:#|販売|店頭|店舗|ショップ|商品|税込|円|ご用意|お求め|お待ち|ご容赦|少量|営業|数量|売り切れの際))|"
        r"(?:新入荷|入荷情報|入荷商品)(?=.{0,90}(?:#|販売|店頭|店舗|ショップ|商品|税込|円|ご用意|ご容赦|少量|営業|数量|売り切れの際|\d{1,2}月\d{1,2}日))|"
        r"(?:在庫ございます|在庫あります|在庫ありです)(?!か)(?=.{0,70}(?:販売|店頭|店舗|ショップ|商品|税込|円|お求め|ぜひ|営業))|"
        r"お取り扱い(?:中|開始)|取り扱い(?:開始|中です)|店頭在庫)",
    ),
    compile_rule(
        "STORE_POLICY_NOTICE",
        "매장의 구매 제한·정리권 등 판매 운영 안내",
        r"(?:(?:※|⚠️|🛒|購入制限[:：]?|販売制限[:：]?).{0,35}"
        r"お一人様.{0,18}(?:点|個|枚|セット|回)まで|"
        r"(?:購入制限|個数制限|販売制限)[:：]?.{0,45}(?:お一人様|各\d|最大\d|\d(?:点|個|枚|セット)まで)|"
        r"(?:\d{1,2}(?:時|[:：]\d{2}).{0,20})?整理券配布.{0,35}(?:抽選|販売|開始|予定|終了)|"
        r"購入整理券.{0,35}配布|店頭販売のみ|先着順で販売)",
    ),
    compile_rule(
        "PRODUCT_EVENT_PROMO",
        "신상품·팝업·행사·출점 홍보 문구",
        r"(?:新商品(?:情報|NEWS|入荷|発売|のお知らせ)|"
        r"新作.{0,35}(?:発売予定|予約販売決定|販売決定|予約受付|登場)|"
        r"(?:ポップアップ|POP\s*UP|期間限定ショップ).{0,45}(?:開催決定|開催します|開催いたします|全国で開催)|"
        r"(?:イベント出店|催事出店|出店します|オープンしました)|"
        r"(?:新発売|本日発売|先行販売).{0,45}(?:税込|円|店頭|店舗|ショップ|オンライン|予約|販売開始|お見逃しなく))",
    ),
    compile_rule(
        "DISCOUNT_COUPON_PROMO",
        "할인·쿠폰·특가로 구매를 유도하는 홍보 문구",
        r"(?:(?:セール開催|SALE開催|クーポン(?:配布|発行|コード)|\d{1,2}\s*[%％]\s*OFF|タイムセール)"
        r".{0,80}(?:販売|購入|注文|ショップ|ストア|店舗|商品|円|価格|こちら|実施|限定|詳細|固定|チェック|再入荷|リンク|紹介コード)|"
        r"(?:送料無料|特別価格|期間限定価格|お買い得).{0,60}(?:\d[\d,]*円|販売|購入|注文|こちら|詳細|固定|チェック|再入荷|ショップ|店舗|商品ページ))",
    ),
    compile_rule(
        "BUYBACK_PROMO",
        "매입·사정 서비스를 홍보하는 문구",
        r"(?:高価買取|買取強化|買取募集中|買取受付|査定無料|無料査定|"
        r"(?:郵送買取|宅配買取).{0,35}(?:受付|査定|申込|申し込み|サービス|実施))",
    ),
    compile_rule(
        "OFFICIAL_PR",
        "PR·협찬·광고임을 명시한 홍보 투고",
        r"(?:^|[\s#【［(（])(?:PR|広告|プロモーション|タイアップ)(?:$|[\s】］)）:：])",
    ),
    compile_rule(
        "COMMERCIAL_RECRUITMENT",
        "모니터·앰배서더 등 상업 목적 모집 홍보",
        r"(?:モニター募集|アンバサダー募集|代理店募集|販売店募集|出店者募集)",
    ),
]


def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def unique_headers(headers: list[str]) -> list[str]:
    result: list[str] = []
    seen: Counter[str] = Counter()
    preferred = {1: "投稿ID_文字列", 5: "ユーザーID_文字列"}
    for idx, header in enumerate(headers):
        if idx in preferred and header in result:
            candidate = preferred[idx]
        else:
            seen[header] += 1
            candidate = header if seen[header] == 1 else f"{header}_{seen[header]}"
        result.append(candidate)
    return result


def keyword_matches(text: str) -> list[str]:
    norm = normalized(text)
    matches: list[str] = []
    for term in USER_KEYWORDS:
        if term == "第弾":
            found = term in norm or re.search(r"第(?:\d+|[一二三四五六七八九十百〇零]+)弾", norm)
        elif term == "本日抽選開始ラインナップ":
            found = re.search(r"本日.{0,15}抽選開始.{0,15}ラインナップ", norm, re.DOTALL)
        elif term == "プレオープン大還元祭":
            found = re.search(r"プレオープン.{0,12}大還元祭", norm, re.DOTALL)
        else:
            found = term in norm
        if found:
            matches.append(term)
    return matches


def classify_additional_ad(text: str) -> tuple[str, str, str] | None:
    norm = normalized(text)
    for rule in AD_RULES:
        match = rule.pattern.search(norm)
        if match:
            if rule.code == "RESTOCK_STORE_NOTICE" and re.search(
                r"(?:在庫ございますか|入荷情報[、,].{0,30}(?:見る|見て|見かけ|聞い|羨ま|悔し)|"
                r"(?:貼り紙|張り紙).{0,35}(?:入荷|販売)|(?:入荷|販売).{0,35}(?:貼り紙|張り紙)|"
                r"と書いてあ|って書いてあ)",
                norm,
            ):
                continue
            if rule.code == "MARKETPLACE_LISTING" and re.search(
                r"(?:交換希望|交換募集|【交換】|\b交換\b.{0,20}(?:譲|求)|譲[】）)]|求[】）)])",
                norm,
            ):
                continue
            if rule.code == "STORE_POLICY_NOTICE" and not norm.startswith("RT @") and re.search(
                r"(?:夫|旦那|私|行った|来た|買った|だった|けど|のに|すぎる|離脱|思う|感じ|びっくり|なんで|何で|やっと)",
                norm,
            ):
                continue
            if rule.code == "PRODUCT_EVENT_PROMO" and re.search(
                r"オープンしました.{0,20}(?:って|と).{0,30}(?:行った|行ってみた|見た)",
                norm,
            ):
                continue
            if rule.code == "DISCOUNT_COUPON_PROMO" and re.search(
                r"クーポン.{0,25}(?:使って|使った|使いたい|使えた).{0,35}(?:買いたい|買った|購入したい|購入した)",
                norm,
            ):
                continue
            evidence = re.sub(r"\s+", " ", match.group(0)).strip()
            return rule.code, rule.reason, evidence[:240]
    return None


def load_sources(root: Path) -> tuple[list[str], list[tuple[str, list[str]]], dict[str, object]]:
    expected_header: list[str] | None = None
    rows: list[tuple[str, list[str]]] = []
    per_file: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    duplicate_ids = 0

    for name in SOURCE_NAMES:
        path = root / name
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source)
            header = next(reader)
            if expected_header is None:
                expected_header = header
            elif header != expected_header:
                raise ValueError(f"Schema mismatch: {name}")

            count = 0
            dates: list[str] = []
            for row in reader:
                if len(row) != len(header):
                    raise ValueError(f"Column count mismatch in {name}, row {count + 2}")
                count += 1
                dates.append(row[7])
                if row[0] in seen_ids:
                    duplicate_ids += 1
                else:
                    seen_ids.add(row[0])
                    rows.append((name, row))
            per_file.append({"file": name, "rows": count, "min_date": min(dates), "max_date": max(dates)})

    assert expected_header is not None
    return expected_header, rows, {"source_files": per_file, "duplicate_ids_skipped": duplicate_ids}


def analyze(root: Path, sample_size: int = 12) -> dict[str, object]:
    headers, rows, source_summary = load_sources(root)
    keyword_count = 0
    additional_count = 0
    reason_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    random.seed(20260716)

    reservoirs: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_by_reason: Counter[str] = Counter()
    for source_name, row in rows:
        text = row[8]
        if keyword_matches(text):
            keyword_count += 1
            continue
        classified = classify_additional_ad(text)
        if classified is None:
            continue
        code, reason, evidence = classified
        additional_count += 1
        reason_counts[code] += 1
        seen_by_reason[code] += 1
        item = {
            "source": source_name,
            "post_id": row[0],
            "account": row[3],
            "reason": reason,
            "evidence": evidence,
            "text": text[:500],
        }
        bucket = reservoirs[code]
        if len(bucket) < sample_size:
            bucket.append(item)
        else:
            j = random.randrange(seen_by_reason[code])
            if j < sample_size:
                bucket[j] = item

    samples.update(reservoirs)
    return {
        **source_summary,
        "input_rows": len(rows),
        "output_headers": unique_headers(headers),
        "keyword_deleted": keyword_count,
        "additional_ad_deleted": additional_count,
        "kept_rows": len(rows) - keyword_count - additional_count,
        "additional_reason_counts": dict(reason_counts),
        "samples": dict(samples),
    }


def write_outputs(root: Path, output_dir: Path) -> dict[str, object]:
    headers, rows, source_summary = load_sources(root)
    output_headers = unique_headers(headers)
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = output_dir / "combined_cleaned_202511_202604.csv"
    additional_path = output_dir / "removed_additional_ads_with_reasons_202511_202604.csv"
    summary_path = output_dir / "ad_filter_summary_202511_202604.json"

    keyword_count = 0
    additional_count = 0
    kept_count = 0
    reason_counts: Counter[str] = Counter()

    with cleaned_path.open("w", encoding="utf-8-sig", newline="") as cleaned_file, additional_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as additional_file:
        cleaned_writer = csv.writer(cleaned_file)
        additional_writer = csv.writer(additional_file)
        cleaned_writer.writerow(output_headers)
        additional_writer.writerow(
            output_headers + ["広告判定理由コード", "広告判定理由", "広告判定根拠"]
        )

        for _, row in rows:
            if keyword_matches(row[8]):
                keyword_count += 1
                continue
            classified = classify_additional_ad(row[8])
            if classified:
                code, reason, evidence = classified
                additional_count += 1
                reason_counts[code] += 1
                additional_writer.writerow(row + [code, reason, evidence])
            else:
                kept_count += 1
                cleaned_writer.writerow(row)

    summary = {
        **source_summary,
        "input_rows": len(rows),
        "keyword_deleted": keyword_count,
        "additional_ad_deleted": additional_count,
        "kept_rows": kept_count,
        "reconciled": len(rows) == keyword_count + additional_count + kept_count,
        "additional_reason_counts": dict(reason_counts),
        "specified_keywords": USER_KEYWORDS,
        "cleaned_csv": str(cleaned_path.resolve()),
        "additional_ads_csv": str(additional_path.resolve()),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--sample-size", type=int, default=12)
    args = parser.parse_args()

    result = (
        write_outputs(args.root, args.output_dir)
        if args.write
        else analyze(args.root, sample_size=args.sample_size)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
