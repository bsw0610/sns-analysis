#!/usr/bin/env python3
"""Build a standalone HTML report from the latest clean3 sentiment outputs."""

from __future__ import annotations

import csv
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path


SUMMARY = Path("data/output/sentiment_summary.csv")
CLASSIFIED = Path("data/output/rule_based_classified_clean3.csv")
SAMPLES = Path("data/output/manual_check_by_category_30_clean3.csv")
OUTPUT = Path("data/output/sentiment_analysis_report.html")

CATEGORY_ORDER = [
    "不満・怒り",
    "焦り・競争",
    "交換・取引",
    "欲望・執着",
    "喜び・満足",
    "情報共有",
    "中立",
]

COLORS = {
    "不満・怒り": "#d9544d",
    "焦り・競争": "#e69b32",
    "交換・取引": "#4c78a8",
    "欲望・執着": "#8f63a8",
    "喜び・満足": "#2f9e72",
    "情報共有": "#33a6b8",
    "中立": "#7b8490",
}


def read_summary() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with SUMMARY.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if row["集計種別"] != "カテゴリ別":
                continue
            rows.append(
                {
                    "category": row["カテゴリ"],
                    "count": int(row["件数"]),
                    "percentage": float(row["割合"]),
                }
            )
    by_category = {row["category"]: row for row in rows}
    return [by_category[category] for category in CATEGORY_ORDER]


def read_keyword_counts() -> dict[str, Counter[str]]:
    counts = {category: Counter() for category in CATEGORY_ORDER}
    with CLASSIFIED.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            category = row.get("sentiment_category", "中立")
            matched = row.get("matched_keywords", "")
            if category not in counts or not matched:
                continue
            counts[category].update(
                keyword.strip() for keyword in matched.split("|") if keyword.strip()
            )
    return counts


def read_samples() -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    with SAMPLES.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            samples.append(
                {
                    "id": row["確認用ID"],
                    "category": row["分類カテゴリ"],
                    "keywords": row["matched_keywords"],
                    "text": row["投稿本文"],
                }
            )
    return samples


def fmt_count(value: int) -> str:
    return f"{value:,}"


def donut_gradient(summary: list[dict[str, object]]) -> str:
    stops: list[str] = []
    start = 0.0
    for index, row in enumerate(summary):
        end = 100.0 if index == len(summary) - 1 else start + float(row["percentage"])
        color = COLORS[str(row["category"])]
        stops.append(f"{color} {start:.2f}% {end:.2f}%")
        start = end
    if start < 100:
        stops.append(f"#e5e8ec {start:.2f}% 100%")
    return ", ".join(stops)


def build_report() -> str:
    summary = read_summary()
    keyword_counts = read_keyword_counts()
    samples = read_samples()
    total = sum(int(row["count"]) for row in summary)
    percentages = {str(row["category"]): float(row["percentage"]) for row in summary}
    counts = {str(row["category"]): int(row["count"]) for row in summary}

    exchange_neutral = (counts["交換・取引"] + counts["中立"]) / total * 100
    tension = (counts["不満・怒り"] + counts["焦り・競争"]) / total * 100
    positive_desire = (counts["喜び・満足"] + counts["欲望・執着"]) / total * 100
    classified_share = (total - counts["中立"]) / total * 100

    bar_rows = []
    legend_rows = []
    for row in sorted(summary, key=lambda item: int(item["count"]), reverse=True):
        category = str(row["category"])
        count = int(row["count"])
        percentage = float(row["percentage"])
        color = COLORS[category]
        bar_rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label"><strong>{html.escape(category)}</strong><span>{fmt_count(count)}件</span></div>
              <div class="bar-track" aria-label="{html.escape(category)} {percentage:.2f}%">
                <span class="bar-fill" style="width:{percentage:.2f}%;background:{color}"></span>
              </div>
              <span class="bar-value">{percentage:.2f}%</span>
            </div>"""
        )
        legend_rows.append(
            f"<li><span style=\"background:{color}\"></span><b>{html.escape(category)}</b><em>{percentage:.2f}%</em></li>"
        )

    keyword_rows = []
    for category in CATEGORY_ORDER:
        if category == "中立":
            keyword_html = "<span class=\"muted\">一致キーワードなし</span>"
        else:
            keywords = keyword_counts[category].most_common(8)
            keyword_html = "".join(
                f"<span class=\"keyword\">{html.escape(keyword)} <small>{count:,}</small></span>"
                for keyword, count in keywords
            )
        keyword_rows.append(
            f"""
            <tr>
              <th><span class="category-dot" style="background:{COLORS[category]}"></span>{html.escape(category)}</th>
              <td>{keyword_html}</td>
            </tr>"""
        )

    category_buttons = [
        '<button class="filter active" data-category="all" type="button">すべて <span>210</span></button>'
    ]
    category_buttons.extend(
        f'<button class="filter" data-category="{html.escape(category)}" type="button">{html.escape(category)} <span>30</span></button>'
        for category in CATEGORY_ORDER
    )

    sample_json = json.dumps(samples, ensure_ascii=False).replace("</", "<\\/")
    report_date = date.today().isoformat()
    gradient = donut_gradient(summary)

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="clean3.csvに基づくSNS感情分析結果レポート">
  <title>SNS感情分析結果レポート</title>
  <style>
    :root {{
      --bg: #f3f5f7;
      --paper: #ffffff;
      --ink: #20252b;
      --muted: #66707a;
      --line: #dce1e6;
      --deep: #17212b;
      --accent: #287e78;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Noto Sans KR", "Noto Sans JP", "Apple SD Gothic Neo", sans-serif;
      line-height: 1.65;
      letter-spacing: 0;
    }}
    a {{ color: inherit; }}
    .topbar {{
      position: sticky;
      z-index: 20;
      top: 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 58px;
      padding: 0 5vw;
      border-bottom: 1px solid rgba(255,255,255,.14);
      background: rgba(23,33,43,.96);
      color: white;
    }}
    .brand {{ font-size: 15px; font-weight: 800; }}
    .topbar nav {{ display: flex; gap: 22px; }}
    .topbar nav a {{ color: #d9e0e6; text-decoration: none; font-size: 13px; }}
    .hero {{
      min-height: 370px;
      padding: 76px 5vw 56px;
      color: white;
      background: var(--deep);
    }}
    .hero-inner {{ max-width: 1180px; margin: 0 auto; }}
    .eyebrow {{ margin: 0 0 14px; color: #77d0c8; font-size: 13px; font-weight: 800; text-transform: uppercase; }}
    h1 {{ max-width: 820px; margin: 0; font-size: 48px; line-height: 1.18; }}
    .hero-copy {{ max-width: 760px; margin: 20px 0 0; color: #cfd7de; font-size: 17px; }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: 10px 22px; margin-top: 30px; color: #aeb9c3; font-size: 13px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 34px 24px 80px; }}
    section {{ padding: 36px 0; border-bottom: 1px solid var(--line); }}
    section:last-child {{ border-bottom: 0; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }}
    h2 {{ margin: 0; font-size: 28px; line-height: 1.3; }}
    .section-head p {{ max-width: 620px; margin: 0; color: var(--muted); font-size: 14px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .kpi {{ min-height: 132px; padding: 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }}
    .kpi span {{ display: block; color: var(--muted); font-size: 13px; }}
    .kpi strong {{ display: block; margin: 8px 0 5px; font-size: 29px; line-height: 1.2; }}
    .kpi small {{ color: var(--muted); font-size: 12px; }}
    .overview {{ display: grid; grid-template-columns: 360px minmax(0,1fr); gap: 42px; align-items: center; }}
    .donut-wrap {{ display: grid; place-items: center; }}
    .donut {{
      display: grid;
      width: 270px;
      height: 270px;
      place-items: center;
      border-radius: 50%;
      background: conic-gradient({gradient});
    }}
    .donut::after {{ content: ""; width: 164px; height: 164px; border-radius: 50%; background: var(--paper); }}
    .donut-label {{ position: absolute; text-align: center; pointer-events: none; }}
    .donut-label strong {{ display: block; font-size: 28px; }}
    .donut-label span {{ color: var(--muted); font-size: 12px; }}
    .legend {{ display: grid; grid-template-columns: repeat(2,1fr); gap: 8px 18px; margin: 22px 0 0; padding: 0; list-style: none; }}
    .legend li {{ display: grid; grid-template-columns: 10px 1fr auto; align-items: center; gap: 7px; font-size: 12px; }}
    .legend li > span {{ width: 9px; height: 9px; border-radius: 2px; }}
    .legend b {{ font-weight: 700; }}
    .legend em {{ color: var(--muted); font-style: normal; }}
    .bars {{ padding: 24px; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }}
    .bar-row {{ display: grid; grid-template-columns: 150px minmax(120px,1fr) 65px; align-items: center; gap: 12px; min-height: 47px; }}
    .bar-label {{ display: flex; justify-content: space-between; gap: 8px; font-size: 13px; }}
    .bar-label span {{ color: var(--muted); font-size: 11px; white-space: nowrap; }}
    .bar-track {{ height: 11px; overflow: hidden; border-radius: 3px; background: #e9edf0; }}
    .bar-fill {{ display: block; height: 100%; min-width: 2px; border-radius: 3px; }}
    .bar-value {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 800; font-size: 13px; }}
    .findings {{ display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; }}
    .finding {{ padding: 22px; border-left: 4px solid var(--accent); background: var(--paper); }}
    .finding .number {{ margin: 0 0 7px; color: var(--accent); font-size: 25px; font-weight: 850; }}
    .finding h3 {{ margin: 0 0 8px; font-size: 17px; }}
    .finding p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 15px 17px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; font-size: 13px; }}
    tr:last-child th, tr:last-child td {{ border-bottom: 0; }}
    th {{ width: 160px; white-space: nowrap; background: #f8f9fa; }}
    .category-dot {{ display: inline-block; width: 9px; height: 9px; margin-right: 8px; border-radius: 2px; }}
    .keyword {{ display: inline-flex; align-items: baseline; gap: 5px; margin: 2px 5px 2px 0; padding: 5px 8px; border: 1px solid var(--line); border-radius: 5px; background: #fafbfc; }}
    .keyword small {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
    .muted {{ color: var(--muted); }}
    .notice {{ margin-top: 16px; padding: 16px 18px; border-left: 4px solid #e69b32; background: #fff9ee; color: #6a5129; font-size: 13px; }}
    .sample-tools {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
    .filter {{ min-height: 36px; padding: 7px 10px; border: 1px solid var(--line); border-radius: 6px; background: var(--paper); color: var(--ink); cursor: pointer; }}
    .filter:hover, .filter:focus-visible, .filter.active {{ border-color: var(--deep); background: var(--deep); color: white; outline: none; }}
    .filter span {{ margin-left: 4px; opacity: .66; font-size: 11px; }}
    .search-row {{ display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px; margin-bottom: 14px; }}
    .search-row input {{ width: 100%; min-height: 42px; padding: 9px 12px; border: 1px solid var(--line); border-radius: 6px; background: var(--paper); font: inherit; }}
    .result-count {{ align-self: center; color: var(--muted); font-size: 13px; white-space: nowrap; }}
    .sample-table th:nth-child(1), .sample-table td:nth-child(1) {{ width: 64px; }}
    .sample-table th:nth-child(2), .sample-table td:nth-child(2) {{ width: 130px; }}
    .sample-table th:nth-child(3), .sample-table td:nth-child(3) {{ width: 180px; }}
    .sample-table td:last-child {{ min-width: 420px; line-height: 1.55; }}
    .empty {{ padding: 34px; text-align: center; color: var(--muted); }}
    .method {{ display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 18px 32px; }}
    .method article {{ padding-top: 15px; border-top: 3px solid var(--line); }}
    .method h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .method p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    footer {{ padding: 30px 24px 50px; text-align: center; color: var(--muted); font-size: 12px; }}
    @media (max-width: 900px) {{
      h1 {{ font-size: 38px; }}
      .kpis {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
      .overview {{ grid-template-columns: 1fr; }}
      .donut-panel {{ max-width: 420px; margin: 0 auto; }}
      .findings {{ grid-template-columns: 1fr; }}
      .section-head {{ align-items: start; flex-direction: column; gap: 8px; }}
    }}
    @media (max-width: 620px) {{
      .topbar {{ padding: 0 18px; }}
      .topbar nav {{ display: none; }}
      .hero {{ min-height: 330px; padding: 58px 20px 40px; }}
      h1 {{ font-size: 32px; }}
      .hero-copy {{ font-size: 15px; }}
      main {{ padding: 20px 16px 60px; }}
      section {{ padding: 30px 0; }}
      .kpis {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 112px minmax(80px,1fr) 56px; gap: 8px; }}
      .bar-label {{ display: block; }}
      .bar-label span {{ display: block; }}
      .bars {{ padding: 15px 12px; }}
      .legend {{ grid-template-columns: 1fr; }}
      .method {{ grid-template-columns: 1fr; }}
      th, td {{ padding: 12px; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">SNS SENTIMENT REPORT</div>
    <nav aria-label="レポート目次">
      <a href="#overview">分布</a>
      <a href="#findings">解釈</a>
      <a href="#keywords">キーワード</a>
      <a href="#samples">検証サンプル</a>
      <a href="#method">方法論</a>
    </nav>
  </header>

  <div class="hero">
    <div class="hero-inner">
      <p class="eyebrow">Rule-based classification / clean3.csv</p>
      <h1>SNS感情分析結果レポート</h1>
      <p class="hero-copy">ボンボンドロップシール関連投稿{fmt_count(total)}件を7カテゴリに分類した結果です。全体傾向、分類根拠、人手で確認すべき誤分類リスクをまとめました。</p>
      <div class="hero-meta">
        <span>分析基準日 {report_date}</span>
        <span>入力データ clean3.csv</span>
        <span>分析方式 キーワードルールベース</span>
        <span>日付列なし</span>
      </div>
    </div>
  </div>

  <main>
    <section aria-labelledby="kpi-title">
      <div class="section-head">
        <h2 id="kpi-title">結果サマリー</h2>
        <p>最大の2カテゴリは交換・取引と中立で、両者が全体の半数を超えています。</p>
      </div>
      <div class="kpis">
        <article class="kpi"><span>全投稿</span><strong>{fmt_count(total)}</strong><small>分析対象の総件数</small></article>
        <article class="kpi"><span>最大カテゴリ</span><strong>{percentages['交換・取引']:.2f}%</strong><small>交換・取引 · {fmt_count(counts['交換・取引'])}件</small></article>
        <article class="kpi"><span>不満・焦り合計</span><strong>{tension:.2f}%</strong><small>不満・怒り + 焦り・競争</small></article>
        <article class="kpi"><span>キーワード分類割合</span><strong>{classified_share:.2f}%</strong><small>中立を除く投稿</small></article>
      </div>
    </section>

    <section id="overview" aria-labelledby="overview-title">
      <div class="section-head">
        <h2 id="overview-title">カテゴリ分布</h2>
        <p>割合は1投稿につき最終カテゴリ1件として計算しました。複数ルールに一致した場合は、事前に定めた優先順位を適用しています。</p>
      </div>
      <div class="overview">
        <div class="donut-panel">
          <div class="donut-wrap">
            <div class="donut" role="img" aria-label="7感情カテゴリの構成比"></div>
            <div class="donut-label"><strong>{fmt_count(total)}</strong><span>全投稿</span></div>
          </div>
          <ul class="legend">{''.join(legend_rows)}</ul>
        </div>
        <div class="bars">{''.join(bar_rows)}</div>
      </div>
    </section>

    <section id="findings" aria-labelledby="findings-title">
      <div class="section-head">
        <h2 id="findings-title">主要な解釈</h2>
        <p>数値そのものより、投稿がどのような行動や状況を示しているかに焦点を当てた解釈です。</p>
      </div>
      <div class="findings">
        <article class="finding">
          <p class="number">{exchange_neutral:.2f}%</p>
          <h3>交換・中立投稿が半数以上</h3>
          <p>交換・取引と中立で全体の{exchange_neutral:.2f}%を占めます。感情表現だけでなく、購入・交換・販売・単純言及も会話の大きな軸です。</p>
        </article>
        <article class="finding">
          <p class="number">{tension:.2f}%</p>
          <h3>不満と競争緊張が明確</h3>
          <p>不満・怒りと焦り・競争は{fmt_count(counts['不満・怒り'] + counts['焦り・競争'])}件です。品切れ、落選、確保競争に関連する反応を優先確認する必要があります。</p>
        </article>
        <article class="finding">
          <p class="number">{positive_desire:.2f}%</p>
          <h3>好感と所有欲求も強い</h3>
          <p>喜び・満足と欲望・執着の合計は{positive_desire:.2f}%です。商品への好感が購入欲求や収集行動につながる投稿も少なくありません。</p>
        </article>
      </div>
    </section>

    <section id="keywords" aria-labelledby="keywords-title">
      <div class="section-head">
        <h2 id="keywords-title">分類で多く使用されたキーワード</h2>
        <p>各カテゴリのmatched_keywordsを投稿単位で集計した上位8件です。数値はそのキーワードが最終分類根拠として記録された回数です。</p>
      </div>
      <div class="table-wrap">
        <table>
          <tbody>{''.join(keyword_rows)}</tbody>
        </table>
      </div>
      <div class="notice"><strong>検証ポイント：</strong>「泣」は嬉し泣きにも使われ、「売り切れ」は情報共有文にも現れます。キーワード頻度が高いほど代表性が高いとは限らないため、以下のサンプルで文脈も確認する必要があります。</div>
    </section>

    <section id="samples" aria-labelledby="samples-title">
      <div class="section-head">
        <h2 id="samples-title">人手確認用サンプル</h2>
        <p>各カテゴリから無作為抽出した30件、合計210件です。カテゴリ選択または本文・キーワード検索ができます。</p>
      </div>
      <div class="sample-tools" role="group" aria-label="カテゴリフィルター">{''.join(category_buttons)}</div>
      <div class="search-row">
        <input id="sample-search" type="search" placeholder="投稿本文または一致キーワードを検索" aria-label="サンプル検索">
        <span class="result-count" id="result-count">210件表示</span>
      </div>
      <div class="table-wrap">
        <table class="sample-table">
          <thead><tr><th>ID</th><th>分類</th><th>一致キーワード</th><th>投稿本文</th></tr></thead>
          <tbody id="sample-body"></tbody>
        </table>
        <div class="empty" id="empty-state" hidden>条件に一致するサンプルがありません。</div>
      </div>
    </section>

    <section id="method" aria-labelledby="method-title">
      <div class="section-head">
        <h2 id="method-title">分析基準と注意事項</h2>
        <p>この結果は統計的な感情モデルではなく、明示的なキーワードルールによる一次分類です。</p>
      </div>
      <div class="method">
        <article><h3>分類優先順位</h3><p>不満・怒り &gt; 焦り・競争 &gt; 交換・取引 &gt; 欲望・執着 &gt; 喜び・満足 &gt; 情報共有 &gt; 中立の順です。複数カテゴリに一致した場合は、先のカテゴリのみが最終結果になります。</p></article>
        <article><h3>「抽選」の扱い</h3><p>ユーザー指定により、「抽選」単独キーワードは焦り・競争から除外しました。他の競争関連キーワードが併存する場合のみ該当カテゴリになり得ます。</p></article>
        <article><h3>月別分析の制限</h3><p>clean3.csvには日付列がないため、月別変化は計算していません。時系列解釈には投稿日または投稿時間を含むデータが必要です。</p></article>
        <article><h3>推奨検証方法</h3><p>210件のサンプルに人手で正解カテゴリを記録し、カテゴリ別適合率を比較する必要があります。特に嬉し泣き、品切れ案内、交換に言及した不満文を優先確認することを推奨します。</p></article>
      </div>
    </section>
  </main>
  <footer>Source: rule_based_classified_clean3.csv · sentiment_summary.csv · manual_check_by_category_30_clean3.csv</footer>

  <script>
    const samples = {sample_json};
    const tbody = document.getElementById('sample-body');
    const search = document.getElementById('sample-search');
    const count = document.getElementById('result-count');
    const empty = document.getElementById('empty-state');
    const filters = [...document.querySelectorAll('.filter')];
    let activeCategory = 'all';

    function escapeHTML(value) {{
      return String(value).replace(/[&<>\"']/g, char => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#039;'
      }})[char]);
    }}

    function renderSamples() {{
      const query = search.value.trim().toLocaleLowerCase();
      const visible = samples.filter(item => {{
        const categoryMatch = activeCategory === 'all' || item.category === activeCategory;
        const haystack = `${{item.text}} ${{item.keywords}}`.toLocaleLowerCase();
        return categoryMatch && (!query || haystack.includes(query));
      }});
      tbody.innerHTML = visible.map(item => `
        <tr>
          <td>${{escapeHTML(item.id)}}</td>
          <td><span class="category-dot" style="background:${{({json.dumps(COLORS, ensure_ascii=False)})[item.category]}}"></span>${{escapeHTML(item.category)}}</td>
          <td>${{item.keywords ? escapeHTML(item.keywords) : '<span class="muted">なし</span>'}}</td>
          <td>${{escapeHTML(item.text)}}</td>
        </tr>`).join('');
      count.textContent = `${{visible.length}}件表示`;
      empty.hidden = visible.length !== 0;
      tbody.closest('table').hidden = visible.length === 0;
    }}

    filters.forEach(button => button.addEventListener('click', () => {{
      activeCategory = button.dataset.category;
      filters.forEach(item => item.classList.toggle('active', item === button));
      renderSamples();
    }}));
    search.addEventListener('input', renderSamples);
    renderSamples();
  </script>
</body>
</html>
"""


def main() -> None:
    if not SUMMARY.exists() or not CLASSIFIED.exists() or not SAMPLES.exists():
        missing = [str(path) for path in (SUMMARY, CLASSIFIED, SAMPLES) if not path.exists()]
        raise SystemExit(f"missing input files: {', '.join(missing)}")
    OUTPUT.write_text(build_report(), encoding="utf-8")
    print(f"created {OUTPUT}")


if __name__ == "__main__":
    main()
