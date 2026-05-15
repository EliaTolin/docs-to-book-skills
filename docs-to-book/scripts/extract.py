#!/usr/bin/env python3
"""Extract clean text content from crawled HTML pages.

Usage:
    python extract.py --input ./raw --output ./clean

Strategy:
- Uses readability-lxml when available (best quality), falls back to BeautifulSoup
- Strips nav, footer, sidebar, ads
- Preserves: headings, paragraphs, lists, code blocks, tables, inline links
- Outputs Markdown via markdownify
- Generates clean/manifest.json with title + first 200 words preview of each page
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify
except ImportError:
    print("ERROR: missing deps. Run: pip install beautifulsoup4 markdownify readability-lxml", file=sys.stderr)
    sys.exit(2)

try:
    from readability import Document
    HAS_READABILITY = True
except ImportError:
    HAS_READABILITY = False


JUNK_SELECTORS = [
    "nav", "footer", "aside", "header",
    "[role=navigation]", "[role=banner]", "[role=contentinfo]",
    ".sidebar", ".navbar", ".nav", ".footer", ".header",
    ".toc", ".table-of-contents",
    "script", "style", "noscript", "iframe",
    ".advertisement", ".ad", ".cookie-banner",
]


def extract_main(html: str) -> tuple[str, str]:
    """Return (title, clean_html_of_main_content)."""
    soup_full = BeautifulSoup(html, "html.parser")
    title = (soup_full.title.string or "").strip() if soup_full.title else ""

    if HAS_READABILITY:
        try:
            doc = Document(html)
            main_html = doc.summary(html_partial=True)
            if not title:
                title = doc.title()
            soup = BeautifulSoup(main_html, "html.parser")
        except Exception:
            soup = soup_full
    else:
        soup = soup_full

    for sel in JUNK_SELECTORS:
        for tag in soup.select(sel):
            tag.decompose()

    main = soup.find("main") or soup.find("article") or soup
    return title, str(main)


def html_to_markdown(html: str) -> str:
    md = markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        code_language="",
        strip=["script", "style"],
    )
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def first_words(text: str, n: int = 200) -> str:
    plain = re.sub(r"[#*`\[\]()_]", "", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    words = plain.split()
    return " ".join(words[:n])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, type=Path, help="Directory with raw HTML files")
    p.add_argument("--output", required=True, type=Path, help="Output directory for clean .md files")
    args = p.parse_args()

    if not args.input.exists():
        print(f"ERROR: input dir does not exist: {args.input}", file=sys.stderr)
        return 1

    args.output.mkdir(parents=True, exist_ok=True)

    sitemap_path = args.input / "sitemap.json"
    sitemap = json.loads(sitemap_path.read_text(encoding="utf-8")) if sitemap_path.exists() else {"pages": []}
    url_by_file = {p["file"]: p["url"] for p in sitemap.get("pages", [])}

    manifest: list[dict] = []

    html_files = sorted(args.input.glob("*.html"))
    print(f"[extract] processing {len(html_files)} files")

    for html_file in html_files:
        html = html_file.read_text(encoding="utf-8")
        title, main_html = extract_main(html)
        md = html_to_markdown(main_html)

        if not md or len(md) < 50:
            print(f"[extract] SKIP {html_file.name} (too short: {len(md)} chars)")
            continue

        md_path = args.output / (html_file.stem + ".md")
        source_url = url_by_file.get(html_file.name, "")
        header = f"<!-- source: {source_url} -->\n# {title}\n\n" if title else ""
        md_path.write_text(header + md, encoding="utf-8")

        manifest.append({
            "file": md_path.name,
            "title": title,
            "url": source_url,
            "word_count": len(md.split()),
            "preview": first_words(md, 200),
        })

    manifest.sort(key=lambda x: x["file"])
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total_words = sum(item["word_count"] for item in manifest)
    print(f"[extract] DONE. {len(manifest)} pages, {total_words:,} words total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
