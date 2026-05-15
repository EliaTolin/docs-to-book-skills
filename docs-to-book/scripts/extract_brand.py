#!/usr/bin/env python3
"""Extract a brand color palette from crawled HTML pages.

Usage:
    python extract_brand.py --input ./raw --output ./brand.json

Strategy (in order of preference):
1. <meta name="theme-color" content="#RRGGBB">
2. CSS custom properties (--brand, --color-brand, --color-primary, --primary)
   inside any <style> tag or inline style attributes
3. Heuristic: most-frequent saturated color found in inline styles or computed
   CSS in the first 5 pages (excluding pure white/black/grays)

Output (brand.json):
{
  "primary":   "#3ECF8E",
  "secondary": "#1F1F1F",
  "accent":    "#65D8A8",
  "source":    "theme-color | css-variable | heuristic | default"
}

If no brand can be extracted, the file is still written with the default
docs-to-book palette and source="default", so downstream tools always have
a valid file to read.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. pip install beautifulsoup4", file=sys.stderr)
    sys.exit(2)


DEFAULT_PALETTE = {
    "primary":   "#5B4FE9",
    "secondary": "#FF6B6B",
    "accent":    "#FFD93D",
}

HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
CSS_VAR_RE = re.compile(
    r"--(?:color-)?(?:brand|primary|accent|theme)[a-z0-9-]*\s*:\s*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\))",
    re.IGNORECASE,
)
RGB_RE = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")


def normalize_hex(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def parse_color(value: str) -> str | None:
    """Parse '#fff', '#3ECF8E', or 'rgb(62,207,142)' into a normalized hex."""
    value = value.strip()
    if value.startswith("#"):
        m = HEX_RE.match(value)
        if m:
            return normalize_hex(m.group(0))
    m = RGB_RE.search(value)
    if m:
        return rgb_to_hex(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def is_brand_worthy(hex_color: str) -> bool:
    """Reject pure black, white, and washed-out grays. Brand colors are saturated."""
    r, g, b = hex_to_rgb(hex_color)
    max_c, min_c = max(r, g, b), min(r, g, b)
    saturation = (max_c - min_c) / max_c if max_c > 0 else 0
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return saturation > 0.35 and 0.15 < luminance < 0.85


def find_theme_color(soup: BeautifulSoup) -> str | None:
    meta = soup.find("meta", attrs={"name": "theme-color"})
    if meta and meta.get("content"):
        return parse_color(meta["content"])
    return None


def find_css_variable(text: str) -> str | None:
    for m in CSS_VAR_RE.finditer(text):
        color = parse_color(m.group(1))
        if color and is_brand_worthy(color):
            return color
    return None


def collect_candidate_colors(text: str) -> list[str]:
    """Pull all hex/rgb colors from a chunk of HTML/CSS, filtered."""
    colors: list[str] = []
    for m in HEX_RE.finditer(text):
        c = normalize_hex(m.group(0))
        if is_brand_worthy(c):
            colors.append(c)
    for m in RGB_RE.finditer(text):
        c = rgb_to_hex(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if is_brand_worthy(c):
            colors.append(c)
    return colors


def darken(hex_color: str, amount: float = 0.6) -> str:
    """Multiply RGB by amount (0..1). Used to derive a secondary from primary."""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(int(r * amount), int(g * amount), int(b * amount))


def lighten(hex_color: str, amount: float = 0.4) -> str:
    """Mix with white. Used to derive an accent from primary."""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def derive_palette(primary: str) -> dict:
    """Given a primary brand color, derive a sensible secondary + accent."""
    return {
        "primary":   primary,
        "secondary": darken(primary, 0.35),
        "accent":    lighten(primary, 0.45),
    }


def extract_from_html(html_files: list[Path]) -> tuple[str | None, str]:
    """Try each strategy on each HTML file. Return (primary_hex, source_label)."""

    # Pass 1: theme-color meta
    for html_file in html_files:
        try:
            soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        except Exception:
            continue
        color = find_theme_color(soup)
        if color and is_brand_worthy(color):
            return color, "theme-color"

    # Pass 2: CSS variable
    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        color = find_css_variable(text)
        if color:
            return color, "css-variable"

    # Pass 3: heuristic — most-frequent saturated color in first 5 pages
    counter: Counter[str] = Counter()
    for html_file in html_files[:5]:
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        for color in collect_candidate_colors(text):
            counter[color] += 1
    if counter:
        most_common = counter.most_common(1)[0][0]
        return most_common, "heuristic"

    return None, "default"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, type=Path, help="Directory with raw HTML files")
    p.add_argument("--output", required=True, type=Path, help="Output path for brand.json")
    p.add_argument("--override-primary", default=None,
                   help="Skip extraction and use this hex color as primary")
    args = p.parse_args()

    if args.override_primary:
        primary = parse_color(args.override_primary)
        if not primary:
            print(f"ERROR: invalid color '{args.override_primary}'", file=sys.stderr)
            return 1
        palette = derive_palette(primary)
        palette["source"] = "user-override"
    elif not args.input.exists():
        print(f"WARNING: input dir does not exist, using default palette", file=sys.stderr)
        palette = {**DEFAULT_PALETTE, "source": "default"}
    else:
        html_files = sorted(args.input.glob("*.html"))
        if not html_files:
            print("WARNING: no HTML files to scan, using default palette", file=sys.stderr)
            palette = {**DEFAULT_PALETTE, "source": "default"}
        else:
            primary, source = extract_from_html(html_files)
            if primary:
                palette = derive_palette(primary)
                palette["source"] = source
                print(f"[brand] extracted primary={primary} via {source}")
            else:
                palette = {**DEFAULT_PALETTE, "source": "default"}
                print("[brand] no brand color found, using default palette")

    args.output.write_text(json.dumps(palette, indent=2), encoding="utf-8")
    print(f"[brand] wrote {args.output}: primary={palette['primary']} secondary={palette['secondary']} accent={palette['accent']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
