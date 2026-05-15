# Regole di integrità dei contenuti

Il libro deve essere **affidabile**: un developer deve poter fidarsi di ciò che legge. Allo stesso tempo, può **integrare** conoscenza di contesto per aiutare la comprensione. La distinzione è cruciale.

---

## Cosa è ✅ integrazione legittima

Tutto ciò che è **conoscenza generale del settore**, non specifica del prodotto:

- Spiegare cos'è REST, HTTP, JSON, WebSocket, OAuth, JWT
- Spiegare cos'è un middleware, un decoratore, un closure
- Cenni storici ("Node.js è nato nel 2009 da Ryan Dahl…")
- Confronti con tecnologie analoghe ("simile a Express, ma…") **se confermati dalla doc**
- Definire termini di programmazione standard (idempotenza, race condition, ecc.)

**Regola:** ogni integrazione DEVE essere dentro un callout `#nota[...]`. Mai inline nel testo principale. Questo crea una distinzione visiva netta: testo normale = dalla doc, callout `#nota` = aggiunta esplicativa.

**Esempio buono:**
```
Hono fornisce un sistema di middleware basato sulla specifica WHATWG Fetch.

#nota[
  *La specifica Fetch* è uno standard web (originariamente per il browser) che
  definisce gli oggetti `Request` e `Response`. Hono la usa anche lato server
  perché funziona ovunque: Node.js, Deno, Bun, Cloudflare Workers.
]
```

---

## Cosa è ❌ invenzione (non fare MAI)

Qualunque informazione **specifica del prodotto** che non è nella documentazione fornita:

- Nomi di funzioni, parametri, flag, env var che non hai visto
- Numeri di versione, date di rilascio, prezzi
- Comportamenti precisi ("ritorna `null` quando…") non documentati
- Confronti con altre tecnologie inventati ("è 3x più veloce di X")
- Citazioni o quotes attribuite a maintainer
- Limiti di rate, di dimensione, di concorrenza non scritti

**Test mentale:** se grep-passi quella affermazione nei `.md` di `clean/`, la trovi? Se no, non scriverla.

---

## Quando la doc è ambigua

A volte la doc dice qualcosa di vago. Esempio: "Il rate limit dipende dal tier."

❌ **NON fare:** "Il rate limit è 1000 req/min nel tier free."  (numero inventato)

✅ **FAI:** Scrivi quello che dice la doc. Se rilevante, aggiungi un callout:
```
#nota[
  La documentazione non specifica i limiti esatti per tier. Per i numeri
  attuali consulta la sezione "Pricing" del sito o contatta il supporto.
]
```

---

## Esempi di codice

Gli esempi di codice devono essere **trascritti letteralmente** dalla documentazione, con la stessa sintassi e gli stessi nomi di variabile. È OK:

- Aggiungere commenti esplicativi sopra le righe
- Sostituire valori dummy con valori più chiari (`xxx` → `your-api-key`)
- Spezzare un esempio lungo in più snippet con spiegazione in mezzo

Non è OK:

- Cambiare i nomi delle funzioni o dei parametri
- "Migliorare" il codice usando feature non documentate
- Inventare esempi che non esistono nella doc per illustrare un concetto

Se vuoi un esempio non presente, scrivilo TU come autore in un callout `#esempio[...]`, esplicitando che è un esempio illustrativo:

```
#esempio[
  Un esempio illustrativo di come potresti combinare due middleware
  (basato sull'API descritta sopra):

  ​```ts
  app.use('*', logger())
  app.use('*', cors())
  ​```
]
```

---

## Citazione delle fonti

Ogni capitolo dovrebbe (alla fine) avere una nota a piè pagina o un blocco "Fonti" con i link alle pagine della doc da cui attinge. Esempio Typst:

```
== Fonti
- #link("https://hono.dev/docs/concepts/middleware")[Concepts → Middleware]
- #link("https://hono.dev/docs/api/hono")[API → Hono]
```

Questo dà credito alla fonte e permette al lettore di approfondire.
