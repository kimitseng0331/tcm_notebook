#!/usr/bin/env python3
# Re-render existing J23 HTML files into the new v2 template.
# Usage: python3 tools/rerender_html_v2.py

from __future__ import annotations

import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "html"

V2_STYLE = r"""
:root{
  --bg:#0b1220;
  --paper:#0f172a;
  --card:#111c33;
  --text:#e5e7eb;
  --muted:#9ca3af;
  --link:#60a5fa;
  --border:rgba(255,255,255,.10);
  --shadow:0 10px 30px rgba(0,0,0,.35);
  --accent:#22c55e;
  --accent2:#38bdf8;
  --codebg:#070b16;
  --quote:#0b2a2f;
  --quoteBorder:#2dd4bf;
}
@media (prefers-color-scheme: light){
  :root{
    --bg:#f6f7fb;
    --paper:#ffffff;
    --card:#ffffff;
    --text:#111827;
    --muted:#6b7280;
    --link:#0b66c3;
    --border:rgba(17,24,39,.12);
    --shadow:0 10px 30px rgba(0,0,0,.08);
    --accent:#16a34a;
    --accent2:#0284c7;
    --codebg:#0b1020;
    --quote:#e8f4fd;
    --quoteBorder:#0284c7;
  }
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
  background: radial-gradient(1200px 500px at 20% -10%, rgba(56,189,248,.25), transparent 60%),
              radial-gradient(900px 500px at 85% 0%, rgba(34,197,94,.20), transparent 55%),
              var(--bg);
  color:var(--text);
  line-height:1.8;
}
a{color:var(--link); text-decoration:none}
a:hover{text-decoration:underline}
.container{max-width:1000px; margin:0 auto; padding:28px 18px 60px}
.header{
  background: linear-gradient(180deg, rgba(56,189,248,.15), rgba(34,197,94,.10));
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:var(--shadow);
  padding:22px 20px;
}
.kicker{color:var(--muted); font-size:.95rem; margin:0 0 8px 0}
.h1{font-size:2.05rem; line-height:1.25; margin:0}
.meta{margin-top:10px; color:var(--muted); font-size:.95rem}
.badge{display:inline-block; margin-left:.5rem; padding:2px 10px; border-radius:999px; border:1px solid var(--border); color:var(--muted); font-size:.85rem}
.grid{display:grid; grid-template-columns: 1fr; gap:14px; margin-top:14px}
@media (min-width: 860px){
  .grid{grid-template-columns: 320px 1fr}
}
.toc, .card{
  background:var(--paper);
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:var(--shadow);
}
.toc{padding:16px 16px}
.toc h2{font-size:1.05rem; margin:0 0 10px 0; color:var(--muted); letter-spacing:.02em}
.toc ul{margin:0; padding-left:18px}
.toc li{margin:.35rem 0}
.toc li ul{margin-top:.25rem}
.main{padding:18px 18px}
section{margin:0 0 14px 0}
section:last-child{margin-bottom:0}
hr.sep{border:none; border-top:1px solid var(--border); margin:18px 0}
h2{margin:22px 0 10px 0; font-size:1.35rem}
h3{margin:16px 0 8px 0; font-size:1.12rem; color:var(--muted)}
p{margin:10px 0}
ul,ol{margin:8px 0 14px 1.2rem}
li{margin:6px 0}
blockquote{
  margin:12px 0;
  padding:12px 14px;
  background:var(--quote);
  border-left:4px solid var(--quoteBorder);
  border-radius:10px;
}
pre{white-space:pre-wrap; word-break:break-word; background:var(--codebg); color:#f8fafc; padding:14px; border-radius:12px; overflow:auto}
code{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size:.95em}
.footer{margin-top:18px; color:var(--muted); font-size:.85rem; text-align:center}
.anchor{opacity:.55; margin-left:.35rem; font-size:.9em}
.anchor:hover{opacity:1}
""".strip()

BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")


def slug_id(prefix: str, n: int, m: int | None = None) -> str:
    return f"{prefix}-{n}" if m is None else f"{prefix}-{n}-{m}"


def replace_inline_md(soup: BeautifulSoup) -> None:
    # Convert **bold** and `code` inside text nodes to <strong>/<code>.
    # Skip nodes already inside <code>, <pre>, <script>, <style>.
    for text_node in list(soup.find_all(string=True)):
        if not isinstance(text_node, NavigableString):
            continue
        parent = text_node.parent
        if parent is None:
            continue
        if parent.name in {"code", "pre", "script", "style"}:
            continue
        if parent.find_parent(["code", "pre", "script", "style"]) is not None:
            continue

        s = str(text_node)
        if "**" not in s and "`" not in s:
            continue

        # Escape only by letting BeautifulSoup parse the fragment; content is trusted (local files).
        def sub_all(src: str) -> str:
            src = CODE_RE.sub(r"<code>\1</code>", src)
            src = BOLD_RE.sub(r"<strong>\1</strong>", src)
            return src

        new_html = sub_all(s)
        if new_html == s:
            continue

        frag = BeautifulSoup(new_html, "html.parser")
        text_node.replace_with(*frag.contents)


def p_gt_to_blockquote(doc: BeautifulSoup, wrapper: Tag) -> None:
    # Convert paragraphs starting with '>' or '&gt;' into blockquote.
    for p in list(wrapper.find_all("p")):
        txt = p.get_text(strip=True)
        if txt.startswith(">"):
            # remove leading '>' (first occurrence) from the HTML string
            inner = "".join(str(x) for x in p.contents)
            inner = re.sub(r"^\s*&gt;\s*", "", inner)
            inner = re.sub(r"^\s*>\s*", "", inner)
            bq = doc.new_tag("blockquote")
            frag = BeautifulSoup(inner, "html.parser")
            bq.extend(frag.contents)
            p.replace_with(bq)


def build_toc(doc: BeautifulSoup, main: Tag) -> Tag:
    toc = doc.new_tag("div", **{"class": "toc"})
    h = doc.new_tag("h2")
    h.string = "目錄"
    toc.append(h)

    ul = doc.new_tag("ul")
    toc.append(ul)

    h2s = main.find_all("h2")
    h2_index = 0
    for h2 in h2s:
        h2_index += 1
        # collect h3 until next h2
        li = doc.new_tag("li")
        a = doc.new_tag("a", href=f"#{h2.get('id')}")
        a.string = h2.get_text(strip=True)
        li.append(a)

        # nested h3s
        nested = []
        for sib in h2.next_siblings:
            if isinstance(sib, Tag) and sib.name == "h2":
                break
            if isinstance(sib, Tag) and sib.name == "h3":
                nested.append(sib)

        if nested:
            ul2 = doc.new_tag("ul")
            for h3 in nested:
                li2 = doc.new_tag("li")
                a2 = doc.new_tag("a", href=f"#{h3.get('id')}")
                a2.string = h3.get_text(strip=True)
                li2.append(a2)
                ul2.append(li2)
            li.append(ul2)

        ul.append(li)

    return toc


def add_heading_ids_and_anchors(doc: BeautifulSoup, main: Tag) -> None:
    h2_count = 0
    for el in main.find_all(["h2", "h3"]):
        if el.name == "h2":
            h2_count += 1
            el["id"] = slug_id("s", h2_count)
            h3_count = 0
        else:
            h3_count += 1
            el["id"] = slug_id("s", h2_count, h3_count)

        # add a small anchor link
        a = doc.new_tag("a", href=f"#{el['id']}", **{"class": "anchor"})
        a.string = "#"
        el.append(a)


def extract_content(old: BeautifulSoup) -> tuple[str, str, list[Tag]]:
    wrapper = old.select_one("div.wrapper") or old.select_one("div.container") or old.body
    title = (old.title.string.strip() if old.title and old.title.string else None)

    h1 = wrapper.find("h1") if wrapper else None
    h1_text = h1.get_text(strip=True) if h1 else (title or "")

    meta = ""
    meta_el = wrapper.select_one(".meta") if wrapper else None
    if meta_el:
        meta = meta_el.get_text(" ", strip=True)

    # collect sections; if none, wrap everything except h1/meta
    sections = list(wrapper.find_all("section", recursive=False)) if wrapper else []
    if not sections and wrapper:
        # create a single section with remaining content
        sec = old.new_tag("section")
        for child in list(wrapper.children):
            if isinstance(child, Tag) and child.name in {"h1"}:
                continue
            if isinstance(child, Tag) and ("meta" in (child.get("class") or [])):
                continue
            if isinstance(child, NavigableString) and not child.strip():
                continue
            sec.append(child.extract() if isinstance(child, Tag) else child)
        sections = [sec]

    return (title or h1_text), (meta or "（新版排版 v2）"), sections


def render_v2(src_path: Path) -> str:
    old = BeautifulSoup(src_path.read_text(encoding="utf-8"), "html.parser")
    doc_title, meta, sections = extract_content(old)

    # Build new document
    soup = BeautifulSoup("<!doctype html><html lang=\"zh-TW\"></html>", "html.parser")
    html = soup.html

    head = soup.new_tag("head")
    html.append(head)

    head.append(soup.new_tag("meta", charset="UTF-8"))
    head.append(soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1"}))
    title = soup.new_tag("title")
    title.string = doc_title
    head.append(title)

    style = soup.new_tag("style")
    style.string = V2_STYLE
    head.append(style)

    body = soup.new_tag("body", **{"data-template": "tcm-notebook-v2"})
    html.append(body)

    container = soup.new_tag("div", **{"class": "container"})
    body.append(container)

    header = soup.new_tag("div", **{"class": "header"})
    container.append(header)

    kicker = soup.new_tag("div", **{"class": "kicker"})
    kicker.string = "TCM Notebook · HTML"
    header.append(kicker)

    h1 = soup.new_tag("h1", **{"class": "h1"})
    h1.string = doc_title
    header.append(h1)

    meta_div = soup.new_tag("div", **{"class": "meta"})
    meta_div.string = meta
    badge = soup.new_tag("span", **{"class": "badge"})
    badge.string = "新版排版"
    meta_div.append(badge)
    header.append(meta_div)

    grid = soup.new_tag("div", **{"class": "grid"})
    container.append(grid)

    main = soup.new_tag("div", **{"class": "card main"})
    # add content sections into main
    for sec in sections:
        main.append(sec)

    # Transformations
    p_gt_to_blockquote(soup, main)
    replace_inline_md(main)

    # Headings ids + anchors and TOC
    add_heading_ids_and_anchors(soup, main)
    toc = build_toc(soup, main)

    grid.append(toc)
    grid.append(main)

    footer = soup.new_tag("div", **{"class": "footer"})
    footer.string = "Rendered with tcm_notebook HTML template v2"
    container.append(footer)

    return str(soup)


def main() -> None:
    if not HTML_DIR.exists():
        raise SystemExit(f"Missing html dir: {HTML_DIR}")

    paths = sorted(HTML_DIR.glob("*.html"))
    if not paths:
        raise SystemExit("No html files found.")

    changed = 0
    for p in paths:
        new_html = render_v2(p)
        old_html = p.read_text(encoding="utf-8")
        if new_html != old_html:
            p.write_text(new_html, encoding="utf-8")
            changed += 1

    print(f"Re-rendered {changed}/{len(paths)} files into v2 template.")


if __name__ == "__main__":
    main()
