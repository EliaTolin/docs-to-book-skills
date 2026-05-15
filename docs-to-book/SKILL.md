---
name: docs-to-book
description: Trasforma una documentazione tecnica online in un libro PDF colorato, leggibile e tradotto nella lingua scelta dall'utente. Usa questa skill ogni volta che l'utente vuole "trasformare una documentazione in libro", "generare un PDF da una documentazione", "creare un manuale", "creare un ebook da docs", oppure fornisce un URL di documentazione (docs.*, *.dev, *.io/docs) e chiede di "ricreare", "riscrivere", "spiegare" o "raccogliere" il contenuto in formato libro/PDF/manuale. Triggera anche quando l'utente menziona "libro tecnico", "manuale tecnico", "ebook tecnico", o chiede di "studiare" una doc in formato leggibile offline.
---

# Docs → Book

Trasforma una documentazione online in un libro PDF curato, esaustivo e piacevole da leggere.

## Cosa fa questa skill

Prende in input un URL di documentazione tecnica e produce un libro PDF:

1. **Crawla** ricorsivamente tutto il dominio della documentazione
2. **Analizza** il contenuto e propone un **indice** all'utente
3. L'utente può **modificare, escludere o aggiungere** capitoli
4. **Genera** ogni capitolo in parallelo con sub-agent (Italiano/Inglese/altro)
5. **Compila** il tutto in un PDF colorato con Typst

Il libro è esaustivo sui contenuti della documentazione, ma può integrare conoscenza generale (es. "cos'è un'API REST", "cos'è OAuth") quando aiuta la comprensione — segnalandolo sempre con un box dedicato.

## Quando usarla

Triggera quando l'utente:
- Fornisce un URL di documentazione e chiede un libro/PDF/manuale
- Dice frasi tipo "voglio un libro su X dalla loro doc", "crea un manuale di Y", "trasforma queste docs in un ebook"
- Vuole studiare una tecnologia in formato leggibile offline

Non triggera per: traduzioni semplici di una pagina singola (usa direttamente WebFetch), riassunti brevi, o documentazione fornita come file locale (in quel caso adatta il flusso saltando il crawling).

---

## Flusso completo

### Step 1 — Raccogli i parametri

Chiedi all'utente in un singolo messaggio (usa `AskUserQuestion` per l'esperienza migliore):

1. **URL** della documentazione (root, es. `https://hono.dev/docs`)
2. **Lingua** del libro (Italiano, Inglese, Spagnolo, ecc.)
3. **Tono**:
   - **Tecnico/Asciutto** — formale, conciso, riferimenti puntuali. Per chi vuole una reference seria.
   - **Bilanciato** — chiaro ma con qualche esempio pratico. Default per developer.
   - **Caloroso/Didattico** — esempi, metafore, analogie quotidiane. Per chi sta imparando da zero.
4. **Profondità** (opzionale): "introduttivo" / "completo" / "deep dive". Default: completo.

Se l'utente ha già fornito alcuni di questi nel messaggio iniziale, non richiederli.

### Step 2 — Inizializza la cartella di lavoro

Crea una cartella di lavoro per questo job. Usa il nome del dominio per identificarla:

```bash
JOB_ID="$(date +%Y%m%d-%H%M%S)-$(echo "$URL" | sed 's|https\?://||' | sed 's|/.*||' | tr '.' '-')"
WORK_DIR="/tmp/docs-to-book/$JOB_ID"
mkdir -p "$WORK_DIR"/{raw,clean,chapters,book}
```

Salva i parametri (URL, lingua, tono, profondità) in `$WORK_DIR/config.json` per riferimento futuro.

### Step 3 — Crawl della documentazione

Lancia lo script di crawling. Mostra all'utente che stai crawlando con un breve messaggio.

```bash
python3 <skill-path>/scripts/crawl.py \
  --url "$URL" \
  --output "$WORK_DIR/raw" \
  --max-pages 500
```

Lo script:
- Segue solo i link interni allo stesso dominio E sotto lo stesso path della doc
- Salta asset binari (img, pdf, zip)
- Salva ogni pagina come HTML + URL d'origine in `raw/<slug>.html`
- Genera `raw/sitemap.json` con tutti gli URL scoperti

Vedi `references/crawling_strategy.md` per dettagli e troubleshooting.

### Step 4 — Estrai contenuto pulito

```bash
python3 <skill-path>/scripts/extract.py \
  --input "$WORK_DIR/raw" \
  --output "$WORK_DIR/clean"
```

Produce un file Markdown per ogni pagina HTML, rimuovendo nav/footer/sidebar e mantenendo testo, code block, tabelle e immagini. Genera anche `clean/manifest.json` con titolo e prime 200 parole di ogni pagina.

### Step 4.5 — Estrai la palette brand (opzionale ma consigliato)

Prima di proporre l'indice, estrai la palette colori del brand dalla doc. Questo dà al libro un look "ufficiale" senza sforzo.

```bash
python3 <skill-path>/scripts/extract_brand.py \
  --input "$WORK_DIR/raw" \
  --output "$WORK_DIR/brand.json"
```

Lo script tenta in ordine:
1. `<meta name="theme-color">` (più affidabile)
2. CSS custom properties tipo `--brand`, `--color-primary`
3. Heuristic sui colori più frequenti nelle prime 5 pagine

Se trova un colore primario, deriva automaticamente secondary (più scuro) e accent (più chiaro). Se non trova nulla, scrive comunque un `brand.json` con la palette default — `compile_book.sh` gestisce entrambi i casi.

**Override manuale:** se l'utente ha specificato un colore (o se vedi un brand color "ovvio" ma mal estratto), puoi forzarlo:

```bash
python3 <skill-path>/scripts/extract_brand.py \
  --input "$WORK_DIR/raw" \
  --output "$WORK_DIR/brand.json" \
  --override-primary "#3ECF8E"
```

**Trademark guardrail:** quando `compile_book.sh` rileva un `brand.json` con `source != "default"`, aggiunge automaticamente alla copertina un disclaimer tipo "Unofficial guide based on public documentation. All trademarks belong to <BRAND>". Non rimuoverlo: protegge sia te sia il brand owner.

### Step 5 — Analizza e proponi l'indice

Leggi `clean/manifest.json` per avere la mappa di tutti i contenuti. Se sono molti file (>30), leggi i contenuti completi in batch (puoi usare un sub-agent Explore se serve).

Costruisci un indice strutturato. Linee guida:

- **Capitolo 1** è sempre un'introduzione che spiega cosa imparerà il lettore e a chi è rivolto (basata sulla landing/intro della doc)
- **Capitoli centrali** seguono un ordine logico di apprendimento, non l'ordine dei file della doc
- **Ultimo capitolo** è una "guida di riferimento" con tabelle compatte di tutto ciò che non è entrato altrove
- Ogni capitolo deve avere: titolo, descrizione (1-2 frasi), e lista di file `clean/*.md` da cui attinge

Salva l'indice proposto in `$WORK_DIR/toc.json` con questa struttura:

```json
{
  "title": "Hono — Il framework web minimalista",
  "subtitle": "Guida completa al framework che gira ovunque",
  "language": "it",
  "tone": "balanced",
  "chapters": [
    {
      "number": 1,
      "title": "Benvenuto in Hono",
      "description": "Cos'è Hono, perché esiste, a chi è rivolto",
      "sources": ["clean/index.md", "clean/concepts.md"],
      "included": true
    }
  ]
}
```

### Step 6 — Validazione dell'indice con l'utente

Mostra l'indice all'utente in formato leggibile (titolo + descrizione di ogni capitolo, numerati). Spiega che può:

- ✅ Confermare così com'è
- ✏️ Modificare titoli o descrizioni di singoli capitoli
- ❌ **Escludere** capitoli specifici (verranno saltati nella generazione)
- ➕ Aggiungere capitoli (specificando titolo e cosa devono coprire)
- 🔀 Riordinare i capitoli

Esempio di formato di presentazione:

```
📖 Indice proposto: "Hono — Il framework web minimalista"

  1. Benvenuto in Hono
     Cos'è Hono, perché esiste, a chi è rivolto

  2. Primi passi
     Installazione, primo "Hello World", struttura del progetto

  3. Routing e handler
     ...

Vuoi confermare, modificare, o escludere qualche capitolo?
```

Aggiorna `toc.json` in base al feedback. I capitoli esclusi restano nel file con `"included": false` (così rimane traccia di cosa è stato scartato).

**Loop**: ripeti questo step finché l'utente non conferma esplicitamente.

### Step 7 — File di progresso

Crea `$WORK_DIR/progress.json` per tracciare lo stato di ogni capitolo:

```json
{
  "started_at": "2026-05-15T14:30:00Z",
  "chapters": {
    "1": {"status": "pending", "file": null},
    "2": {"status": "pending", "file": null}
  }
}
```

Stati possibili: `pending` → `in_progress` → `done` | `failed`.

### Step 8 — Generazione capitoli in parallelo

Per ogni capitolo `included: true`, spawna un sub-agent in parallelo (tutti nello stesso messaggio).

**Importante**: lancia tutti i sub-agent insieme (multipli `Agent` tool call nello stesso turno) per massimizzare il parallelismo. Per libri con >10 capitoli, dividi in batch da 8-10 per non saturare.

Per ogni sub-agent usa **questo prompt template** (sostituendo i placeholder):

```
Sei uno scrittore tecnico esperto. Scrivi il Capitolo {N} di un libro tecnico.

CONTESTO DEL LIBRO:
- Titolo: {title}
- Lingua: {language} (scrivi TUTTO in questa lingua)
- Tono: {tone} — vedi guida sotto

CAPITOLO DA SCRIVERE:
- Titolo: {chapter_title}
- Descrizione: {chapter_description}
- Fonti documentazione: {sources_list}

GUIDA TONO ({tone}):
{tone_guide}  # carica da references/tone_guide.md

REGOLE FERREE DI INTEGRITÀ DEI CONTENUTI:
1. NON inventare API, parametri, comportamenti o esempi che non esistono nella documentazione fornita
2. Puoi e DEVI integrare conoscenza generale per chiarire concetti (es. "cos'è REST", "cosa sono i webhook")
   ma DEVI marcarla con il box `#nota[...]` (definito in styles.typ)
3. Se la documentazione è ambigua su qualcosa, scrivilo esplicitamente invece di colmare con assunzioni
4. Cita esempi di codice testualmente come appaiono nella doc (sintassi identica)

OUTPUT:
- Scrivi un file Typst (.typ) usando lo styling definito in {skill_path}/assets/styles.typ
- Inizia con `= {chapter_title}` (heading di capitolo)
- Usa i callout disponibili: #nota, #attenzione, #esempio, #suggerimento, #curiosita
- Code block: usa `​```linguaggio ... ```` di Typst (Typst li renderizza già stilizzati)
- Lunghezza target: 1500-4000 parole secondo la profondità "{depth}"

Salva il risultato in: {work_dir}/chapters/cap-{N:02d}.typ

Quando hai finito, aggiorna {work_dir}/progress.json marcando il capitolo come "done".
```

Mentre i sub-agent lavorano, NON poll-are: il sistema ti notifica quando ognuno completa.

Se un sub-agent fallisce (status `failed`), riprova una volta sola con feedback specifico sul fallimento, poi escludilo dal libro e avvisa l'utente.

### Step 9 — Compila il PDF

Una volta che tutti i capitoli sono pronti, compila il libro:

```bash
bash <skill-path>/scripts/compile_book.sh "$WORK_DIR"
```

Lo script:
1. Genera `book/main.typ` che importa cover, indice e tutti i capitoli in ordine
2. Esegue `typst compile book/main.typ book/book.pdf`
3. Mostra eventuali warning di compilazione

Se Typst non è installato, lo script avvisa con istruzioni: `brew install typst`.

### Step 10 — Consegna all'utente

Sposta il PDF finale in una location accessibile e mostra il path:

```bash
OUTPUT_DIR="$HOME/Desktop/docs-to-book-output"
mkdir -p "$OUTPUT_DIR"
BOOK_FILENAME="$(jq -r '.title' "$WORK_DIR/toc.json" | tr ' ' '_' | tr -cd '[:alnum:]_-').pdf"
cp "$WORK_DIR/book/book.pdf" "$OUTPUT_DIR/$BOOK_FILENAME"
echo "📚 Libro pronto: $OUTPUT_DIR/$BOOK_FILENAME"
```

Comunica all'utente:
- Path completo del PDF
- Numero di capitoli, pagine totali, tempo impiegato
- Path della cartella di lavoro (può servire per ri-generare singoli capitoli)

---

## Asset e risorse

### Template Typst (`assets/`)

- `assets/main.typ` — template principale del libro (importa tutto)
- `assets/styles.typ` — palette colori, callout, font, layout (carica sempre per primo)
- `assets/cover.typ` — copertina del libro

I sub-agent NON devono modificare questi file: scrivono solo i file di capitolo che importano `styles.typ`.

### Reference (`references/`)

Carica al bisogno:
- `references/tone_guide.md` — istruzioni dettagliate per i 3 toni (carica nel prompt dei sub-agent)
- `references/crawling_strategy.md` — come gestire siti SPA, paywall, rate limiting
- `references/integrity_rules.md` — esempi concreti di cosa è "integrazione legittima" vs "invenzione"
- `references/typst_callouts.md` — esempi visivi di tutti i callout disponibili

### Script (`scripts/`)

- `scripts/crawl.py` — crawler ricorsivo (requests + BeautifulSoup)
- `scripts/extract.py` — HTML → Markdown pulito (readability + markdownify)
- `scripts/extract_brand.py` — estrae palette brand (theme-color, CSS vars, heuristic)
- `scripts/compile_book.sh` — bash wrapper per Typst (applica brand.json se presente)

Tutti gli script accettano `--help` per documentare i flag.

---

## Errori comuni e come gestirli

- **Crawl restituisce 0 pagine**: la doc è probabilmente una SPA (Single Page App) che renderizza JS lato client. Vedi `references/crawling_strategy.md` per la strategia con Playwright.
- **Sub-agent allucina API non esistenti**: rinforza nel prompt l'elenco *specifico* dei file fonte e chiedigli di citare il path del file da cui proviene ogni affermazione.
- **PDF troppo lungo (>200 pagine)**: in fase di indice proponi all'utente di ridurre la profondità o di splittare in volumi.
- **Typst non trova un font**: lo script `compile_book.sh` usa solo font di sistema. Se manca, fallback su `New Computer Modern` (sempre disponibile con Typst).

---

## Principi di design del libro

Tieni questi principi in mente quando guidi i sub-agent e quando rivedi il PDF finale:

- **Facilità di lettura sopra tutto.** Frasi corte, paragrafi brevi, molti spazi bianchi.
- **Visual hierarchy chiara.** Ogni capitolo apre con un riquadro colorato che dice "cosa imparerai" e chiude con un riassunto a punti.
- **Callout come guide visive**, non come decorazione: usali quando aggiungono valore (warning reale, esempio concreto), non per riempire.
- **Codice leggibile.** Usa font monospaziato, syntax highlighting, e righe corte (max 80 char). Se un esempio è lungo, spezzalo o linka alla doc originale.
- **Coerenza narrativa.** Anche se i capitoli sono scritti in parallelo, devono sembrare scritti dalla stessa mano. La guida tono garantisce questa coerenza.
