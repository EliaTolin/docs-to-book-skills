// cover.typ — Copertina del libro
// Importa con: #import "cover.typ": cover

#import "styles.typ": palette, font-heading, font-body

#let cover(
  title: "Untitled Book",
  subtitle: "",
  source: "",
  language: "it",
  generated-on: datetime.today().display(),
  disclaimer: "",
) = {
  set page(
    paper: "a4",
    margin: 0cm,
    fill: palette.primary,
    numbering: none,
  )

  // Banda diagonale decorativa di sfondo
  place(
    top + right,
    dx: 4cm, dy: -4cm,
    rotate(35deg, origin: center,
      rect(width: 20cm, height: 20cm, fill: palette.secondary.lighten(20%))
    )
  )
  place(
    bottom + left,
    dx: -3cm, dy: 3cm,
    rotate(-25deg, origin: center,
      rect(width: 16cm, height: 16cm, fill: palette.accent)
    )
  )

  // Box centrale con titolo
  place(
    center + horizon,
    block(
      width: 16cm,
      fill: palette.paper,
      inset: 2.4cm,
      radius: 12pt,
      stroke: 6pt + palette.accent,
      [
        #text(
          font: font-body,
          size: 10pt,
          weight: "bold",
          fill: palette.secondary,
          tracking: 4pt,
        )[GUIDA COMPLETA]

        #v(0.6cm)

        #text(
          font: font-heading,
          size: 36pt,
          weight: "black",
          fill: palette.primary,
        )[#title]

        #if subtitle != "" [
          #v(0.4cm)
          #text(
            font: font-heading,
            size: 16pt,
            weight: "regular",
            fill: palette.ink-soft,
            style: "italic",
          )[#subtitle]
        ]

        #v(1.2cm)
        #line(length: 60%, stroke: 2pt + palette.accent)
        #v(0.6cm)

        #if source != "" [
          #text(size: 9pt, fill: palette.ink-soft)[
            Generato da: #link(source)[#source]
          ]
          #linebreak()
        ]
        #text(size: 9pt, fill: palette.ink-soft)[
          #generated-on
        ]
      ]
    )
  )

  // Disclaimer in fondo, fuori dal box centrale
  if disclaimer != "" {
    place(
      bottom + center,
      dy: -1.4cm,
      block(
        width: 14cm,
        inset: (x: 12pt, y: 8pt),
        radius: 4pt,
        fill: palette.paper.transparentize(15%),
        text(
          size: 7.5pt,
          fill: palette.ink-soft,
          style: "italic",
        )[#align(center)[#disclaimer]]
      )
    )
  }

  pagebreak()
}

#let toc-page(title: "Indice") = {
  set page(numbering: none)
  v(2cm)
  text(font: font-heading, size: 32pt, weight: "bold", fill: palette.primary)[#title]
  v(8pt)
  line(length: 80pt, stroke: 4pt + palette.accent)
  v(20pt)

  outline(
    title: none,
    indent: auto,
    depth: 2,
  )

  pagebreak()
}
