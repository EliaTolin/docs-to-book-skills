// styles.typ — Palette, tipografia e callout per "Docs → Book"
//
// Importa con: #import "styles.typ": *
//
// Filosofia: facilità di lettura sopra tutto.
// - Colori vivaci ma con contrasto alto sul testo
// - Generoso whitespace
// - Callout chiari per separare "documentazione" da "integrazione/contesto"

// ────────────────────────────────────────────────────────
// Palette
// ────────────────────────────────────────────────────────

#let palette = (
  primary:    rgb("#5B4FE9"),  // indigo vivace - copertina, heading principali
  secondary:  rgb("#FF6B6B"),  // corallo - accenti, link
  accent:     rgb("#FFD93D"),  // giallo sole - highlight
  success:    rgb("#06D6A0"),  // verde menta
  warning:    rgb("#FFA94D"),  // arancio
  danger:     rgb("#E63946"),  // rosso
  info:       rgb("#4DABF7"),  // azzurro
  ink:        rgb("#1A1A2E"),  // nero blu - testo principale
  ink-soft:   rgb("#4A4A68"),  // grigio - testo secondario
  paper:      rgb("#FDFCFB"),  // bianco caldo - sfondo
  paper-soft: rgb("#F4F1ED"),  // beige chiaro - box neutri
)

// ────────────────────────────────────────────────────────
// Tipografia
// ────────────────────────────────────────────────────────

// Font scelti per disponibilità su macOS + leggibilità.
// Fallback su font di sistema garantiti da Typst.
#let font-body = ("Inter", "Helvetica Neue", "Helvetica", "Arial", "New Computer Modern")
#let font-heading = ("Inter", "Helvetica Neue", "Helvetica", "Arial", "New Computer Modern")
#let font-mono = ("JetBrains Mono", "Menlo", "Monaco", "Courier New", "DejaVu Sans Mono")

// ────────────────────────────────────────────────────────
// Setup globale del documento
// ────────────────────────────────────────────────────────

#let book-setup(
  title: "Untitled",
  language: "it",
  body
) = {
  set document(title: title)
  set page(
    paper: "a4",
    margin: (x: 2.4cm, y: 2.6cm),
    fill: palette.paper,
    numbering: "1",
    number-align: center,
  )
  set text(
    font: font-body,
    size: 11pt,
    lang: language,
    fill: palette.ink,
    hyphenate: true,
  )
  set par(
    leading: 0.78em,
    spacing: 1.2em,
    justify: true,
    first-line-indent: 0pt,
  )
  set heading(numbering: "1")

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    let n = counter(heading).at(it.location()).first()
    block(
      width: 100%,
      inset: (top: 24pt, bottom: 16pt),
      [
        #text(size: 11pt, fill: palette.secondary, weight: "bold")[
          CAPITOLO #n
        ]
        #v(8pt)
        #text(font: font-heading, size: 28pt, weight: "bold", fill: palette.primary)[
          #it.body
        ]
        #v(4pt)
        #line(length: 60pt, stroke: 3pt + palette.accent)
      ]
    )
    v(8pt)
  }

  show heading.where(level: 2): it => {
    v(16pt)
    block[
      #text(font: font-heading, size: 18pt, weight: "bold", fill: palette.ink)[#it.body]
      #v(-6pt)
      #line(length: 100%, stroke: 0.5pt + palette.ink-soft.lighten(60%))
    ]
    v(4pt)
  }

  show heading.where(level: 3): it => {
    v(10pt)
    text(font: font-heading, size: 14pt, weight: "bold", fill: palette.primary)[#it.body]
    v(2pt)
  }

  show link: it => text(fill: palette.secondary, weight: "medium")[#it]

  show raw.where(block: false): it => box(
    fill: palette.paper-soft,
    inset: (x: 4pt, y: 1pt),
    outset: (y: 2pt),
    radius: 3pt,
    text(font: font-mono, size: 0.92em, fill: palette.danger)[#it]
  )

  show raw.where(block: true): it => block(
    width: 100%,
    fill: palette.ink,
    inset: 14pt,
    radius: 8pt,
    text(font: font-mono, size: 9.5pt, fill: rgb("#F8F8F2"))[#it]
  )

  show list: set list(indent: 1em, body-indent: 0.5em, marker: ([▸], [•], [◦]))
  show enum: set enum(indent: 1em, body-indent: 0.5em)

  body
}

// ────────────────────────────────────────────────────────
// Callout
//
// Filosofia: ogni callout ha un significato preciso.
// - #nota:       integrazione di conoscenza generale (non dalla doc)
// - #attenzione: warning, gotcha, breaking change
// - #esempio:    esempio pratico/snippet illustrativo
// - #suggerimento: best practice, pro-tip
// - #curiosita:  trivia, contesto storico, "lo sapevi che"
// - #riassunto:  blocco di chiusura capitolo
// ────────────────────────────────────────────────────────

#let _callout(color, icon, label, body) = block(
  width: 100%,
  fill: color.lighten(88%),
  stroke: (left: 4pt + color),
  inset: (x: 14pt, y: 12pt),
  radius: (right: 6pt),
  spacing: 1.4em,
  [
    #text(weight: "bold", fill: color, size: 10pt)[#icon  #label]
    #v(4pt)
    #body
  ]
)

#let nota(body) = _callout(
  palette.info, "ℹ", "NOTA — Integrazione di contesto", body
)

#let attenzione(body) = _callout(
  palette.danger, "⚠", "ATTENZIONE", body
)

#let esempio(body) = _callout(
  palette.success, "▶", "ESEMPIO", body
)

#let suggerimento(body) = _callout(
  palette.warning, "✦", "SUGGERIMENTO", body
)

#let curiosita(body) = _callout(
  palette.accent.darken(20%), "✱", "CURIOSITÀ", body
)

#let riassunto(body) = block(
  width: 100%,
  fill: palette.primary.lighten(92%),
  stroke: (paint: palette.primary, thickness: 1pt, dash: "loosely-dashed"),
  inset: 16pt,
  radius: 8pt,
  spacing: 1.6em,
  [
    #text(weight: "bold", fill: palette.primary, size: 12pt)[📖 Riassunto del capitolo]
    #v(6pt)
    #body
  ]
)

// "Cosa imparerai" — apertura capitolo
#let cosa-imparerai(items) = block(
  width: 100%,
  fill: palette.secondary.lighten(90%),
  inset: 14pt,
  radius: 8pt,
  spacing: 1.6em,
  [
    #text(weight: "bold", fill: palette.secondary, size: 11pt)[🎯 In questo capitolo imparerai]
    #v(4pt)
    #list(..items.map(it => [#it]))
  ]
)

// Definizione inline (termine + spiegazione breve)
#let definizione(termine, spiegazione) = box[
  #text(weight: "bold", fill: palette.primary)[#termine] —
  #text(fill: palette.ink-soft)[#spiegazione]
]
