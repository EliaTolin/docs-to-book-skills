#!/usr/bin/env python3
"""Recursive crawler for documentation sites.

Usage:
    python crawl.py --url https://hono.dev/docs --output ./raw --max-pages 500

Strategy:
- Stays within the same domain AND under the same path prefix as the seed URL
  (e.g. seed https://example.com/docs/ won't crawl https://example.com/blog/)
- Skips binary assets (images, pdfs, archives)
- Polite: 0.3s delay between requests, respects User-Agent
- Saves each page as <slug>.html plus sitemap.json with metadata

For SPA sites (React/Vue docs that render client-side), this crawler will
likely return mostly empty pages. See references/crawling_strategy.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: missing deps. Run: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(2)


SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".woff", ".woff2",
    ".ttf", ".eot", ".css", ".js", ".json", ".xml",
}

USER_AGENT = "docs-to-book-crawler/1.0 (+https://github.com/anthropics/claude-code)"


def slugify(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    if parsed.query:
        path += "_" + parsed.query.replace("=", "-").replace("&", "_")
    return path[:200]


def is_crawlable(url: str, base_netloc: str, base_path: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != base_netloc:
        return False
    if not parsed.path.startswith(base_path):
        return False
    suffix = Path(parsed.path).suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return False
    return True


def normalize(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def crawl(seed: str, output: Path, max_pages: int, delay: float) -> dict:
    parsed_seed = urlparse(seed)
    base_netloc = parsed_seed.netloc
    base_path = parsed_seed.path.rsplit("/", 1)[0] + "/" if "/" in parsed_seed.path else "/"

    output.mkdir(parents=True, exist_ok=True)

    visited: set[str] = set()
    queue: deque[str] = deque([normalize(seed)])
    pages: list[dict] = []

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})

    print(f"[crawl] seed={seed} base={base_netloc}{base_path}")

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
        except requests.RequestException as exc:
            print(f"[crawl] FAIL {url}: {exc}", file=sys.stderr)
            continue

        if resp.status_code != 200:
            print(f"[crawl] SKIP {url} ({resp.status_code})")
            continue

        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype.lower():
            continue

        slug = slugify(url)
        out_file = output / f"{slug}.html"
        out_file.write_text(resp.text, encoding="utf-8")

        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""

        pages.append({"url": url, "file": out_file.name, "title": title})
        print(f"[crawl] [{len(pages):3d}] {url}  →  {slug}.html")

        for link in soup.find_all("a", href=True):
            absolute = normalize(urljoin(url, link["href"]))
            if absolute in visited:
                continue
            if is_crawlable(absolute, base_netloc, base_path):
                queue.append(absolute)

        time.sleep(delay)

    sitemap = {
        "seed": seed,
        "base_netloc": base_netloc,
        "base_path": base_path,
        "pages_count": len(pages),
        "pages": pages,
    }
    (output / "sitemap.json").write_text(json.dumps(sitemap, indent=2), encoding="utf-8")
    print(f"[crawl] DONE. {len(pages)} pages saved to {output}")
    return sitemap


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", required=True, help="Seed URL to start crawling from")
    p.add_argument("--output", required=True, type=Path, help="Output directory for raw HTML")
    p.add_argument("--max-pages", type=int, default=500, help="Max pages to crawl (default: 500)")
    p.add_argument("--delay", type=float, default=0.3, help="Seconds between requests (default: 0.3)")
    args = p.parse_args()

    sitemap = crawl(args.url, args.output, args.max_pages, args.delay)
    if sitemap["pages_count"] == 0:
        print("[crawl] WARNING: 0 pages crawled. Site may be a SPA — see crawling_strategy.md", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
