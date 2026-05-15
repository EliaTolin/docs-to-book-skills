# Callout Typst disponibili — quick reference per i sub-agent

Tutti i callout sono definiti in `assets/styles.typ` e disponibili dopo `#import "styles.typ": *`.

## Quando usare ognuno

| Callout            | Quando usarlo                                                         | Tono ideale         |
|--------------------|----------------------------------------------------------------------|---------------------|
| `#nota[...]`       | Integrazione di conoscenza generale (NON dalla doc)                  | tutti               |
| `#attenzione[...]` | Warning, gotcha, breaking change, errore comune                      | tutti               |
| `#esempio[...]`    | Esempio pratico, snippet illustrativo                                | balanced, warm      |
| `#suggerimento[...]` | Best practice, pro-tip dalla doc                                   | tutti               |
| `#curiosita[...]`  | Trivia, contesto storico, "lo sapevi che"                            | warm (mai technical)|
| `#riassunto[...]`  | Blocco finale del capitolo con i takeaway                            | tutti               |
| `#cosa-imparerai((...,))` | Apertura del capitolo con bullet di obiettivi                 | tutti               |

## Esempi d'uso

### Apertura di capitolo
```typst
= Routing in Hono

#cosa-imparerai((
  [Come definire route statiche e dinamiche],
  [Come usare i parametri di path e query string],
  [Come organizzare route in sotto-applicazioni],
))

Hono fornisce un sistema di routing...
```

### Nota di integrazione (cosa è REST)
```typst
Le route Hono seguono le convenzioni REST.

#nota[
  *REST* (Representational State Transfer) è uno stile architetturale
  per API web introdotto da Roy Fielding nel 2000. Si basa sull'uso
  dei verbi HTTP (GET, POST, PUT, DELETE) per operare su risorse
  identificate da URL.
]
```

### Warning
```typst
#attenzione[
  Le middleware vengono eseguite nell'ordine in cui sono registrate.
  Un middleware che modifica `c.req` deve venire *prima* dell'handler
  che lo legge, altrimenti la modifica non sarà visibile.
]
```

### Esempio
```typst
#esempio[
  Definiamo una route che riceve un parametro `id` e ritorna un JSON:
  
  ```ts
  app.get('/users/:id', (c) => {
    const id = c.req.param('id')
    return c.json({ userId: id })
  })
  ```
]
```

### Suggerimento
```typst
#suggerimento[
  Per applicazioni di medie dimensioni, organizza le route in file
  separati e montale come sub-app con `app.route('/api', apiApp)`.
  Mantiene il file principale leggibile.
]
```

### Curiosità (solo tono warm)
```typst
#curiosita[
  Hono significa "fiamma" in giapponese. Il nome riflette la sua
  velocità — il framework punta a essere il più veloce della sua
  categoria nei benchmark TechEmpower.
]
```

### Definizione inline
```typst
Il routing in Hono usa un trie compresso.
#definizione("Trie", "struttura ad albero per ricerca efficiente di stringhe per prefisso")
Questo permette lookup O(k) dove k è la lunghezza del path.
```

### Chiusura di capitolo
```typst
#riassunto[
  - Hono usa un router pattern-based veloce e cache-friendly
  - Le route possono essere statiche, dinamiche con `:param`, o catch-all con `*`
  - Puoi montare sub-app con `app.route()` per organizzare progetti grandi
  - I middleware si eseguono in ordine di registrazione
]
```

## Code blocks

Per i blocchi di codice, usa la sintassi Typst standard:

````typst
```ts
const x: number = 42
```
````

Lo stile (font monospaziato, sfondo scuro, syntax highlight) è già configurato in `styles.typ`. **Non aggiungere** stili manuali ai code block.

## Heading

```typst
= Capitolo                  // h1 - automatico, fa pagebreak
== Sezione principale       // h2
=== Sotto-sezione           // h3
```

I capitoli (`=`) hanno styling automatico (banner colorato, numerazione, pagebreak). **Usa esattamente un `=` per file** — il file è UN capitolo.

## Link

```typst
#link("https://hono.dev")[Sito ufficiale Hono]
```

## Liste

```typst
- elemento 1
- elemento 2
  - annidato
- elemento 3

+ numerato 1
+ numerato 2
```

## Tabelle

Per tabelle compatte (utili nel capitolo "Reference"):

```typst
#table(
  columns: 3,
  align: (left, left, left),
  stroke: 0.5pt + palette.ink-soft.lighten(70%),
  fill: (_, row) => if row == 0 { palette.primary.lighten(85%) },
  table.header[*Metodo*][*Descrizione*][*Esempio*],
  [`c.text()`], [Risposta plain text], [`c.text("Hello")`],
  [`c.json()`], [Risposta JSON], [`c.json({ok: true})`],
  [`c.html()`], [Risposta HTML], [`c.html("<h1>Ciao</h1>")`],
)
```
