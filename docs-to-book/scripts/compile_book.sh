#!/usr/bin/env bash
# compile_book.sh — Assembla i capitoli e compila il libro in PDF con Typst.
#
# Usage:
#   bash compile_book.sh /tmp/docs-to-book/<job-id>
#
# Si aspetta questa struttura nella work-dir:
#   <work-dir>/
#     ├── config.json        # {"title": "...", "subtitle": "...", "source": "...", "language": "it"}
#     ├── toc.json           # indice con chapters[].included
#     ├── chapters/cap-01.typ, cap-02.typ, ...
#     └── book/              # output: book/main.typ + book/book.pdf
#
# Copia styles.typ, cover.typ e i capitoli inclusi in <work-dir>/book/,
# genera main.typ dal template, e compila con typst.

set -euo pipefail

WORK_DIR="${1:?Usage: compile_book.sh <work-dir>}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$SKILL_DIR/assets"

if ! command -v typst >/dev/null 2>&1; then
  echo "ERROR: typst non installato. Su macOS: brew install typst" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq non installato. Su macOS: brew install jq" >&2
  exit 2
fi

CONFIG="$WORK_DIR/config.json"
TOC="$WORK_DIR/toc.json"
CHAPTERS_DIR="$WORK_DIR/chapters"
BOOK_DIR="$WORK_DIR/book"

[[ -f "$CONFIG" ]] || { echo "ERROR: $CONFIG mancante" >&2; exit 1; }
[[ -f "$TOC" ]] || { echo "ERROR: $TOC mancante" >&2; exit 1; }
[[ -d "$CHAPTERS_DIR" ]] || { echo "ERROR: $CHAPTERS_DIR mancante" >&2; exit 1; }

mkdir -p "$BOOK_DIR"

cp "$ASSETS_DIR/styles.typ" "$BOOK_DIR/styles.typ"
cp "$ASSETS_DIR/cover.typ" "$BOOK_DIR/cover.typ"

# Brand palette override: if brand.json exists in work-dir, swap the 3 brand
# colors (primary/secondary/accent) in the copied styles.typ. The semantic
# callout colors (info/danger/success/warning) are kept as-is.
BRAND_JSON="$WORK_DIR/brand.json"
DISCLAIMER=""
if [[ -f "$BRAND_JSON" ]]; then
  BRAND_PRIMARY=$(jq -r '.primary' "$BRAND_JSON")
  BRAND_SECONDARY=$(jq -r '.secondary' "$BRAND_JSON")
  BRAND_ACCENT=$(jq -r '.accent' "$BRAND_JSON")
  BRAND_SOURCE=$(jq -r '.source // ""' "$BRAND_JSON")

  # Replace the default hex values in styles.typ with the brand ones.
  # The default hex values are well-known constants in the template.
  sed -i.bak \
    -e "s|primary:    rgb(\"#5B4FE9\")|primary:    rgb(\"$BRAND_PRIMARY\")|" \
    -e "s|secondary:  rgb(\"#FF6B6B\")|secondary:  rgb(\"$BRAND_SECONDARY\")|" \
    -e "s|accent:     rgb(\"#FFD93D\")|accent:     rgb(\"$BRAND_ACCENT\")|" \
    "$BOOK_DIR/styles.typ"
  rm -f "$BOOK_DIR/styles.typ.bak"

  echo "[compile] applied brand palette ($BRAND_SOURCE): primary=$BRAND_PRIMARY"

  # If the palette comes from real extraction (not the default), include a
  # disclaimer on the cover. The brand owner's name is best-effort: derive
  # from the source URL host.
  if [[ "$BRAND_SOURCE" != "default" ]]; then
    BRAND_NAME=$(jq -r '.source // ""' "$CONFIG" | sed -E 's|https?://(www\.)?||; s|/.*||; s|\.[a-z]+$||' | tr '[:lower:]' '[:upper:]' | head -c 40)
    [[ -z "$BRAND_NAME" ]] && BRAND_NAME="THE ORIGINAL AUTHORS"
    DISCLAIMER="Unofficial guide based on public documentation. All trademarks and brand assets belong to ${BRAND_NAME}."
  fi
fi

TITLE="$(jq -r '.title // "Untitled"' "$TOC")"
SUBTITLE="$(jq -r '.subtitle // ""' "$TOC")"
SOURCE="$(jq -r '.source // ""' "$CONFIG")"
LANG="$(jq -r '.language // "it"' "$TOC")"

INCLUDED_NUMBERS=$(jq -r '.chapters[] | select(.included == true) | .number' "$TOC")
[[ -n "$INCLUDED_NUMBERS" ]] || { echo "ERROR: nessun capitolo incluso in toc.json" >&2; exit 1; }

CHAPTERS_INCLUDES=""
MISSING=()
for N in $INCLUDED_NUMBERS; do
  CAP_FILE=$(printf "cap-%02d.typ" "$N")
  SRC_PATH="$CHAPTERS_DIR/$CAP_FILE"
  if [[ ! -f "$SRC_PATH" ]]; then
    MISSING+=("$CAP_FILE")
    continue
  fi
  cp "$SRC_PATH" "$BOOK_DIR/$CAP_FILE"
  CHAPTERS_INCLUDES+="#include \"$CAP_FILE\""$'\n'
done

if (( ${#MISSING[@]} > 0 )); then
  echo "WARNING: capitoli mancanti, saranno saltati: ${MISSING[*]}" >&2
fi

MAIN_OUT="$BOOK_DIR/main.typ"

# Escape doppi apici e backslash per sicurezza nel contesto string Typst
typst_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

TITLE_ESC="$(typst_escape "$TITLE")"
SUBTITLE_ESC="$(typst_escape "$SUBTITLE")"
SOURCE_ESC="$(typst_escape "$SOURCE")"
LANG_ESC="$(typst_escape "$LANG")"
DISCLAIMER_ESC="$(typst_escape "$DISCLAIMER")"

{
  echo '#import "styles.typ": *'
  echo '#import "cover.typ": cover, toc-page'
  echo ''
  echo "#cover("
  echo "  title: \"$TITLE_ESC\","
  echo "  subtitle: \"$SUBTITLE_ESC\","
  echo "  source: \"$SOURCE_ESC\","
  echo "  language: \"$LANG_ESC\","
  echo "  disclaimer: \"$DISCLAIMER_ESC\","
  echo ")"
  echo ''
  echo "#show: book-setup.with(title: \"$TITLE_ESC\", language: \"$LANG_ESC\")"
  echo ''
  echo "#toc-page(title: \"Indice\")"
  echo ''
  printf '%s' "$CHAPTERS_INCLUDES"
} > "$MAIN_OUT"

echo "[compile] generated $MAIN_OUT"
echo "[compile] running: typst compile $MAIN_OUT $BOOK_DIR/book.pdf"

cd "$BOOK_DIR"
typst compile main.typ book.pdf 2>&1 | tee compile.log

if [[ -f "$BOOK_DIR/book.pdf" ]]; then
  PAGES=$(typst query main.typ 'page' --field count 2>/dev/null || echo "?")
  echo "[compile] ✅ PDF generato: $BOOK_DIR/book.pdf"
  echo "[compile] dimensione: $(du -h "$BOOK_DIR/book.pdf" | cut -f1)"
else
  echo "[compile] ❌ compilazione fallita — vedi $BOOK_DIR/compile.log" >&2
  exit 1
fi
