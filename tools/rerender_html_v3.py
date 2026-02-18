#!/usr/bin/env python3
"""Render J23-01~07 report/summary markdown into the single HTML template (v3).

Inputs (workspace):  /Users/kimi/.openclaw/workspace/memory/tcm23_J23-XX_{research_report,summary}.md
Outputs (repo):      html/J23-XX_{report,summary}.html

Design goals:
- Card-like <section>
- <span class="highlight"> tags
- Table styling available
- Clean HTML (no markdown ** ` > remnants)

This is a deterministic renderer; it reorganizes summary into grouped sections
without adding new knowledge.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "html"
MEMORY_DIR = Path("/Users/kimi/.openclaw/workspace/memory")

STYLE = """
:root{
  --bg:#f3f4f6;
  --card:#ffffff;
  --text:#111827;
  --muted:#6b7280;
  --line:#e5e7eb;
  --shadow:0 8px 24px rgba(0,0,0,.08);
  --accent:#0b66c3;
  --hi-bg:#fff3bf;
  --hi-text:#7a2e00;
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
  background:var(--bg);
  color:var(--text);
  line-height:1.8;
}
a{color:var(--accent)}
.wrapper{max-width:980px; margin:0 auto; padding:28px 18px 52px}
h1{font-size:2.05rem; line-height:1.25; margin:0 0 8px 0}
.meta{color:var(--muted); font-size:.95rem; margin:0 0 18px 0}
section{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:14px;
  box-shadow:var(--shadow);
  padding:16px 18px;
  margin:14px 0;
}
h2{margin:0 0 10px 0; font-size:1.35rem}
h3{margin:14px 0 6px 0; font-size:1.05rem; color:var(--muted)}
p{margin:10px 0}
ul,ol{margin:8px 0 14px 1.25rem; padding:0}
li{margin:6px 0}
blockquote{
  margin:12px 0;
  padding:12px 14px;
  background:#f8fafc;
  border-left:4px solid var(--accent);
  border-radius:10px;
}
.highlight{
  display:inline-block;
  padding:1px 8px;
  border-radius:999px;
  background:var(--hi-bg);
  color:var(--hi-text);
  font-weight:700;
  letter-spacing:.02em;
}
.table{
  width:100%;
  border-collapse:collapse;
  margin:10px 0 4px 0;
  overflow:hidden;
  border-radius:12px;
  border:1px solid var(--line);
}
.table th,.table td{padding:10px 10px; border-bottom:1px solid var(--line); vertical-align:top}
.table th{background:#f9fafb; text-align:left}
.table tr:last-child td{border-bottom:none}
hr{border:none; border-top:1px solid var(--line); margin:14px 0}
""".strip()

BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")


def inline_md_to_html(text: str) -> str:
    # escape then restore inline constructs
    text = html.escape(text)
    text = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    return text


def strip_md_artifacts(s: str) -> str:
    # Safety net: remove stray markdown markers
    s = s.replace("**", "")
    s = s.replace("`", "")
    return s


def md_lines_to_sections(md: str) -> list[tuple[str, str]]:
    """Very small markdown subset -> list of (title, inner_html).

    Splits on '## ' headings; '### ' become in-section h3.
    Lists: '-', '*', '1)', '2)' become <ul>.
    Paragraphs become <p>.
    Blockquote: lines starting with '>' become <blockquote>.
    """

    lines = md.splitlines()
    title = None
    buf: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush():
        nonlocal title, buf
        if title is None:
            return
        inner = "\n".join(buf).strip()
        sections.append((title, inner))
        buf = []

    for line in lines:
        if line.startswith("## "):
            flush()
            title = line[3:].strip()
            continue
        if title is None:
            # ignore anything before first ##
            continue
        buf.append(line)
    flush()

    def render_block(block_lines: list[str]) -> str:
        out: list[str] = []
        i = 0
        while i < len(block_lines):
            ln = block_lines[i]
            if ln.strip() == "" or ln.strip() == "---":
                i += 1
                continue

            if ln.startswith("### "):
                out.append(f"<h3>{inline_md_to_html(ln[4:].strip())}</h3>")
                i += 1
                continue

            if ln.lstrip().startswith(">"):
                # gather contiguous quote lines
                q: list[str] = []
                while i < len(block_lines) and block_lines[i].lstrip().startswith(">"):
                    q.append(block_lines[i].lstrip()[1:].lstrip())
                    i += 1
                qtext = " ".join(x for x in q if x.strip())
                out.append(f"<blockquote>{inline_md_to_html(qtext)}</blockquote>")
                continue

            # list items
            m = re.match(r"^\s*([-*])\s+(.*)$", ln)
            m2 = re.match(r"^\s*(\d+)\)\s+(.*)$", ln)
            if m or m2:
                items: list[str] = []
                while i < len(block_lines):
                    ln2 = block_lines[i]
                    m = re.match(r"^\s*([-*])\s+(.*)$", ln2)
                    m2 = re.match(r"^\s*(\d+)\)\s+(.*)$", ln2)
                    if not (m or m2):
                        break
                    content = (m.group(2) if m else m2.group(2)).strip()
                    items.append(f"<li>{inline_md_to_html(content)}</li>")
                    i += 1
                out.append("<ul>" + "".join(items) + "</ul>")
                continue

            # numbered list like '1.'
            m3 = re.match(r"^\s*(\d+)\.\s+(.*)$", ln)
            if m3:
                items: list[str] = []
                while i < len(block_lines):
                    ln2 = block_lines[i]
                    m3 = re.match(r"^\s*(\d+)\.\s+(.*)$", ln2)
                    if not m3:
                        break
                    items.append(f"<li>{inline_md_to_html(m3.group(2).strip())}</li>")
                    i += 1
                out.append("<ol>" + "".join(items) + "</ol>")
                continue

            # plain paragraph (merge consecutive non-empty non-special lines)
            para: list[str] = [ln.strip()]
            i += 1
            while i < len(block_lines):
                nxt = block_lines[i]
                if nxt.strip() == "" or nxt.strip() == "---":
                    break
                if nxt.startswith("### ") or nxt.lstrip().startswith(">"):
                    break
                if re.match(r"^\s*([-*])\s+", nxt) or re.match(r"^\s*(\d+)[).]\s+", nxt):
                    break
                para.append(nxt.strip())
                i += 1
            out.append(f"<p>{inline_md_to_html(' '.join(para))}</p>")

        return "\n".join(out)

    rendered: list[tuple[str, str]] = []
    for sec_title, inner_md in sections:
        html_inner = render_block(inner_md.splitlines())
        rendered.append((sec_title, html_inner))
    return rendered


def build_page(title: str, meta: str, sections: list[tuple[str, str]]) -> str:
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-TW">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(title)}</title>",
        "<style>" + STYLE + "</style>",
        "</head>",
        "<body>",
        '<div class="wrapper">',
        f"<h1>{html.escape(title)}</h1>",
        f"<p class=\"meta\">{html.escape(meta)}</p>",
    ]

    for sec_title, sec_html in sections:
        sec_title_clean = strip_md_artifacts(sec_title)
        # Add highlight tags for the three pillars when appropriate
        if sec_title_clean.startswith("生理"):
            heading = f"<h2><span class=\"highlight\">生理（醫理）</span> {html.escape(sec_title_clean.replace('生理：','').replace('生理','').strip('： '))}</h2>"
        elif sec_title_clean.startswith("病理"):
            heading = f"<h2><span class=\"highlight\">病理（病機）</span> {html.escape(sec_title_clean.replace('病理：','').replace('病理','').strip('： '))}</h2>"
        elif sec_title_clean.startswith("方藥"):
            heading = f"<h2><span class=\"highlight\">方藥（方證）</span> {html.escape(sec_title_clean.replace('方藥：','').replace('方藥','').strip('： '))}</h2>"
        else:
            heading = f"<h2>{html.escape(sec_title_clean)}</h2>"

        parts.append("<section>")
        parts.append(heading)
        parts.append(sec_html)
        parts.append("</section>")

    parts += [
        "</div>",
        "</body>",
        "</html>",
    ]
    page = "\n".join(parts)
    # final cleanup: no stray markdown markers
    page = page.replace("**", "")
    page = page.replace("`", "")
    page = page.replace("&gt;", "")
    return page


def summary_to_sections(text: str) -> list[tuple[str, str]]:
    """Heuristic regrouping for J23 summaries.

    Expected anchors:
      在生理層面 / 在病理層面 / 在方藥層面 / 整體而言 / 若把 / 補充
    """
    t = text.strip()
    # Normalize whitespace
    t = re.sub(r"\n{3,}", "\n\n", t)

    anchors = [
        ("導讀", None),
        ("生理", r"在生理層面"),
        ("病理", r"在病理層面"),
        ("方藥", r"在方藥層面"),
        ("結語", r"整體而言"),
        ("流程化整理", r"若把"),
        ("補充", r"補充"),
    ]

    # Split by paragraphs
    paras = [p.strip() for p in re.split(r"\n\n+", t) if p.strip()]

    buckets: dict[str, list[str]] = {k: [] for k, _ in anchors}
    current = "導讀"

    for p in paras:
        switched = False
        for k, pat in anchors:
            if pat and re.search(pat, p):
                current = k
                switched = True
                break
        buckets[current].append(p)

    out: list[tuple[str, str]] = []
    order = [k for k, _ in anchors]
    for k in order:
        content = "\n\n".join(buckets[k]).strip()
        if not content:
            continue

        # turn each bucket into a short intro paragraph + bullets when possible
        # We keep wording, only formatting.
        # Try to convert long paragraphs into bullet points by sentence splitting when the bucket is one giant paragraph.
        if k in {"生理", "病理", "方藥", "流程化整理"}:
            # Keep first sentence as lead, rest as bullets (approx).
            sents = re.split(r"(?<=[。！？])\s*", content)
            sents = [s.strip() for s in sents if s.strip()]
            if len(sents) >= 4:
                lead = sents[0]
                bullets = sents[1:]
                html_parts = [f"<p>{inline_md_to_html(lead)}</p>", "<ul>"]
                for b in bullets:
                    html_parts.append(f"<li>{inline_md_to_html(b)}</li>")
                html_parts.append("</ul>")
                inner = "\n".join(html_parts)
            else:
                inner = "\n".join(f"<p>{inline_md_to_html(x)}</p>" for x in re.split(r"\n\n+", content))
        else:
            inner = "\n".join(f"<p>{inline_md_to_html(x)}</p>" for x in re.split(r"\n\n+", content))

        out.append((k, inner))

    # Rename section titles to match report style
    titled: list[tuple[str, str]] = []
    for k, inner in out:
        if k == "生理":
            titled.append(("生理：藥性—人體對應的理解框架", inner))
        elif k == "病理":
            titled.append(("病理：先候病機與對治規則", inner))
        elif k == "方藥":
            titled.append(("方藥：君臣佐使、七情與風險管理", inner))
        else:
            titled.append((k, inner))
    return titled


def render_report(j: str) -> None:
    src = MEMORY_DIR / f"tcm23_J23-{j}_research_report.md"
    md = src.read_text(encoding="utf-8")
    # title from first heading
    m = re.search(r"^#\s+(.+)$", md, flags=re.M)
    title = m.group(1).strip() if m else f"J23-{j} 研究報告"
    sections = md_lines_to_sections(md)

    page = build_page(
        title=title,
        meta="雙標：生理（醫理）／病理（病機）／方藥（方證）｜以原始 markdown 內容重新組織與排版（不新增新知）",
        sections=sections,
    )

    (HTML_DIR / f"J23-{j}_report.html").write_text(page, encoding="utf-8")


def render_summary(j: str) -> None:
    src = MEMORY_DIR / f"tcm23_J23-{j}_summary.md"
    text = src.read_text(encoding="utf-8")
    sections = summary_to_sections(text)
    page = build_page(
        title=f"J23-{j} 摘要",
        meta="雙標：生理（醫理）／病理（病機）／方藥（方證）｜重組段落（不新增新知）",
        sections=sections,
    )
    (HTML_DIR / f"J23-{j}_summary.html").write_text(page, encoding="utf-8")


def main() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    for j in ["01", "02", "03", "04", "05", "06", "07"]:
        render_report(j)
        render_summary(j)


if __name__ == "__main__":
    main()
