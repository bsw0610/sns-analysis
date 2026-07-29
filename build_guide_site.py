#!/usr/bin/env python3
"""Build a static HTML guide site from sns_sentiment_analysis_guide.md."""

from __future__ import annotations

import html
import re
from pathlib import Path


SOURCE = Path("sns_sentiment_analysis_guide.md")
OUTPUT = Path("sns_sentiment_analysis_guide.html")


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "section"


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    table_lines: list[str] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        table_lines.append(lines[index].strip())
        index += 1

    if len(table_lines) < 2:
        return f"<p>{inline_markdown(lines[start])}</p>", start + 1

    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)

    if not rows:
        return "", index

    header, body = rows[0], rows[1:]
    out = ["<div class=\"table-wrap\"><table>"]
    out.append("<thead><tr>")
    for cell in header:
        out.append(f"<th>{inline_markdown(cell)}</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{inline_markdown(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out), index


def parse_markdown(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = markdown.splitlines()
    html_parts: list[str] = []
    headings: list[tuple[int, str, str]] = []
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_parts.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if stripped == "---":
            flush_paragraph()
            html_parts.append("<hr>")
            index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            lang = stripped.strip("`").strip()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            language_class = f" class=\"language-{html.escape(lang)}\"" if lang else ""
            html_parts.append(
                f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            section_id = slugify(title)
            headings.append((level, title, section_id))
            class_name = "guide-title" if level == 1 else ""
            html_parts.append(
                f"<h{level} id=\"{section_id}\" class=\"{class_name}\">{inline_markdown(title)}</h{level}>"
            )
            index += 1
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            table_html, next_index = parse_table(lines, index)
            html_parts.append(table_html)
            index = next_index
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().lstrip(">").strip())
                index += 1
            html_parts.append(f"<blockquote>{inline_markdown(' '.join(quote_lines))}</blockquote>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            items: list[str] = []
            while index < len(lines):
                item = re.match(r"^\d+\.\s+(.+)$", lines[index].strip())
                if not item:
                    break
                items.append(f"<li>{inline_markdown(item.group(1))}</li>")
                index += 1
            html_parts.append(f"<ol>{''.join(items)}</ol>")
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(f"<li>{inline_markdown(lines[index].strip()[2:])}</li>")
                index += 1
            html_parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return "\n".join(html_parts), headings


def toc_html(headings: list[tuple[int, str, str]]) -> str:
    links = []
    for level, title, section_id in headings:
        if level == 1:
            continue
        links.append(
            f"<a class=\"toc-link toc-level-{level}\" href=\"#{section_id}\">{html.escape(title)}</a>"
        )
    return "\n".join(links)


def build_page(content: str, headings: list[tuple[int, str, str]]) -> str:
    title = headings[0][1] if headings else "SNSデータ感情分析ガイド"
    toc = toc_html(headings)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --paper: #ffffff;
      --ink: #20242a;
      --muted: #626b76;
      --line: #d9dee5;
      --accent: #2f80c9;
      --accent-2: #39a96b;
      --warn: #d84a3a;
      --code: #1f2933;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", "Noto Sans JP", sans-serif;
      line-height: 1.75;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100vh;
    }}
    .sidebar {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 28px 22px;
      background: #eef2f6;
      border-right: 1px solid var(--line);
    }}
    .brand {{
      margin: 0 0 18px;
      font-size: 18px;
      line-height: 1.45;
      font-weight: 800;
    }}
    .summary-card {{
      padding: 14px;
      margin-bottom: 22px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      color: var(--muted);
      font-size: 13px;
    }}
    .toc-link {{
      display: block;
      padding: 7px 8px;
      border-radius: 6px;
      color: #2d3540;
      text-decoration: none;
      font-size: 14px;
      line-height: 1.45;
    }}
    .toc-link:hover, .toc-link:focus {{
      background: #dfe8f2;
      color: #0f4f86;
      outline: none;
    }}
    .toc-level-3 {{ padding-left: 22px; font-size: 13px; color: var(--muted); }}
    .main {{
      min-width: 0;
      padding: 44px 40px 80px;
    }}
    .hero {{
      margin: 0 auto 28px;
      max-width: 1120px;
      padding: 38px 42px;
      border-radius: 8px;
      color: white;
      background:
        linear-gradient(90deg, rgba(22, 29, 38, 0.92), rgba(22, 29, 38, 0.62)),
        url("data/output/sentiment_monthly_percentage_stacked.png") center / cover no-repeat;
    }}
    .hero h1 {{
      margin: 0;
      max-width: 760px;
      font-size: clamp(32px, 5vw, 54px);
      line-height: 1.18;
      letter-spacing: 0;
    }}
    .hero p {{
      max-width: 740px;
      margin: 18px 0 0;
      color: rgba(255, 255, 255, 0.88);
      font-size: 17px;
    }}
    .quick-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 24px;
    }}
    .quick-links a {{
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 7px 12px;
      border: 1px solid rgba(255,255,255,.35);
      border-radius: 6px;
      color: white;
      text-decoration: none;
      background: rgba(255,255,255,.12);
      font-size: 14px;
    }}
    .guide {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 34px 42px 56px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
    }}
    .graph-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      max-width: 1120px;
      margin: 0 auto 24px;
    }}
    .graph-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--paper);
    }}
    .graph-card img {{
      display: block;
      width: 100%;
      height: 170px;
      object-fit: cover;
      object-position: top left;
      border-bottom: 1px solid var(--line);
    }}
    .graph-card a {{
      display: block;
      padding: 11px 13px;
      color: var(--ink);
      text-decoration: none;
      font-weight: 700;
      font-size: 14px;
    }}
    h1.guide-title {{ display: none; }}
    h2 {{
      margin: 46px 0 14px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
      font-size: 28px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    h2:first-of-type {{ margin-top: 0; border-top: 0; }}
    h3 {{
      margin: 28px 0 10px;
      font-size: 20px;
      line-height: 1.45;
    }}
    p {{ margin: 0 0 15px; }}
    ul, ol {{ margin: 0 0 18px 24px; padding: 0; }}
    li {{ margin: 5px 0; }}
    hr {{
      border: 0;
      border-top: 1px solid var(--line);
      margin: 30px 0;
    }}
    .table-wrap {{
      width: 100%;
      overflow-x: auto;
      margin: 14px 0 24px;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 680px;
      background: white;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      background: #f0f4f8;
      font-weight: 800;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{
      padding: 2px 5px;
      border-radius: 5px;
      background: #eef2f6;
      color: #0f4f86;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: .92em;
    }}
    pre {{
      overflow: auto;
      margin: 16px 0 24px;
      padding: 18px;
      border-radius: 8px;
      background: var(--code);
      color: #f2f6fb;
      line-height: 1.6;
    }}
    pre code {{
      padding: 0;
      background: transparent;
      color: inherit;
      font-size: 14px;
    }}
    blockquote {{
      margin: 18px 0 24px;
      padding: 16px 18px;
      border-left: 5px solid var(--accent);
      border-radius: 6px;
      background: #f1f7fd;
      color: #26313d;
    }}
    .top-button {{
      position: fixed;
      right: 22px;
      bottom: 22px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 1px solid var(--line);
      background: var(--paper);
      color: var(--ink);
      text-decoration: none;
      box-shadow: 0 6px 18px rgba(20, 30, 40, .14);
      font-weight: 800;
    }}
    @media (max-width: 980px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{
        position: relative;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .toc {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 3px 10px;
      }}
      .main {{ padding: 24px 18px 64px; }}
      .hero, .guide {{ padding: 28px 22px; }}
      .graph-grid {{ grid-template-columns: 1fr; }}
      .graph-card img {{ height: 220px; }}
    }}
    @media (max-width: 560px) {{
      .toc {{ grid-template-columns: 1fr; }}
      .hero h1 {{ font-size: 32px; }}
      .hero p {{ font-size: 15px; }}
      .guide {{ padding: 24px 16px; }}
      h2 {{ font-size: 23px; }}
      .top-button {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <p class="brand">SNSデータ<br>感情分析ガイド</p>
      <div class="summary-card">
        目的設定からサンプリング、分類、集計、誤分類チェックまでを一つの流れで確認できます。
      </div>
      <nav class="toc" aria-label="目次">
        {toc}
      </nav>
    </aside>
    <main class="main">
      <section class="hero" id="top">
        <h1>{html.escape(title)}</h1>
        <p>ボンボンドロップシール関連投稿を題材に、SNS投稿を人間の判断とルールベース分類で分析するための実践ガイドです。</p>
        <div class="quick-links">
          <a href="#2-分類カテゴリを設定する">分類カテゴリ</a>
          <a href="#6-分類の優先順位を決める">優先順位</a>
          <a href="#8-pythonでルールベース分類を行う">Python分類</a>
          <a href="#10-分析結果の確認">結果確認</a>
        </div>
      </section>

      <section class="graph-grid" aria-label="分析グラフ">
        <article class="graph-card">
          <img src="data/output/sentiment_overall_bar.png" alt="カテゴリ別件数と割合">
          <a href="data/output/sentiment_overall_bar.png">カテゴリ別 件数と割合</a>
        </article>
        <article class="graph-card">
          <img src="data/output/sentiment_monthly_count_stacked.png" alt="月別カテゴリ件数">
          <a href="data/output/sentiment_monthly_count_stacked.png">月別カテゴリ件数</a>
        </article>
        <article class="graph-card">
          <img src="data/output/sentiment_monthly_percentage_stacked.png" alt="月別カテゴリ構成比">
          <a href="data/output/sentiment_monthly_percentage_stacked.png">月別カテゴリ構成比</a>
        </article>
      </section>

      <article class="guide">
        {content}
      </article>
    </main>
  </div>
  <a class="top-button" href="#top" aria-label="トップへ戻る">↑</a>
</body>
</html>
"""


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    content, headings = parse_markdown(markdown)
    OUTPUT.write_text(build_page(content, headings), encoding="utf-8")
    print(f"created {OUTPUT}")


if __name__ == "__main__":
    main()
