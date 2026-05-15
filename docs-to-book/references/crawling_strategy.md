# Strategie di crawling per documentazione tecnica

Le doc tecniche moderne sono spesso SPA (React/Vue/Next) che renderizzano contenuto via JavaScript. Lo script base `crawl.py` usa `requests` + `BeautifulSoup`, che funzionano solo su HTML server-rendered. Ecco come gestire i casi limite.

---

## Casi normali (server-rendered) ✅

Funzionano con lo script default:
- MkDocs, Docusaurus (con SSR/SSG abilitato), Read The Docs, GitBook static
- La maggior parte delle doc su `*.github.io`
- Siti con sitemap.xml o sezione `/docs/` ben strutturata

Se `crawl.py` ritorna >5 pagine con contenuto sensato, sei a posto.

---

## Caso SPA (client-side rendering) ⚠️

**Sintomi:** `crawl.py` salva pagine quasi vuote, oppure tutte uguali (solo il guscio HTML senza contenuto).

**Diagnosi rapida:**
```bash
curl -s https://docs.esempio.com/page | grep -c '<p>'
# Se ritorna 0 o 1, è probabile SPA
```

**Strategie:**

### Strategia A — Sitemap.xml o llms.txt

Molte doc moderne espongono un file `sitemap.xml` o `llms.txt` con tutti gli URL:

```bash
curl https://docs.esempio.com/sitemap.xml
curl https://docs.esempio.com/llms-full.txt   # standard llms.txt
```

Se esistono, usa quegli URL come seed list. Per `llms-full.txt`, il contenuto è già in Markdown — saltare extraction.

### Strategia B — Endpoint API JSON

Alcune doc (Algolia DocSearch, ecc.) hanno un endpoint che restituisce tutto in JSON. Cerca nel sorgente HTML stringhe come:
- `__NEXT_DATA__` (Next.js)
- `window.docsData`
- `/api/docs/` o `/api/search`

### Strategia C — Playwright (fallback robusto)

Se le altre fallback non funzionano, usa Playwright per renderizzare le pagine:

```python
# scripts/crawl_spa.py (esempio di estensione)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    html = page.content()
```

Costo: ~2-5 secondi per pagina (vs 0.3s con requests). Per >100 pagine, considera di farlo notturno.

### Strategia D — Repo GitHub della doc

Molte doc open-source hanno il sorgente Markdown su GitHub:

```
https://github.com/honojs/website/tree/main/docs
```

Clona il repo e usa direttamente i `.md`. Salta crawling e extraction.

---

## Rate limiting e gentilezza

Anche se la doc è permissiva:
- Mantieni `--delay 0.3` o più alto
- Aggiungi `User-Agent` identificabile (lo fa già `crawl.py`)
- Se ricevi 429, aumenta il delay a 2s e ripeti

---

## Filtraggio dei link

`crawl.py` segue solo link sotto lo stesso path-prefix del seed. Esempi:

| Seed                              | Crawla                          | Salta                          |
|-----------------------------------|---------------------------------|--------------------------------|
| `https://hono.dev/docs`           | `https://hono.dev/docs/...`     | `https://hono.dev/blog/...`    |
| `https://supabase.com/docs/guides/functions` | `/docs/guides/functions/...` | `/docs/guides/auth/...`        |

Se serve allargare lo scope, usa un seed più "in alto" (es. `/docs` invece di `/docs/guides/functions`).

---

## Verifica post-crawl

Prima di passare allo step di indicizzazione, controlla:

```bash
WORK_DIR=/tmp/docs-to-book/<job-id>
ls "$WORK_DIR/raw" | wc -l           # numero file salvati
du -sh "$WORK_DIR/raw"               # dimensione totale
jq '.pages_count' "$WORK_DIR/raw/sitemap.json"
```

Se:
- 0-2 file: probabile SPA, retry con strategia A/C
- 3-10 file: doc piccola, ok
- 10-100 file: standard
- 100+ file: doc enterprise, valuta di filtrare ulteriormente prima dell'indice
