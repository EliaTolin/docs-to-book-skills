# Guida ai toni di scrittura

Carica nel prompt dei sub-agent **solo la sezione del tono scelto** dall'utente. Non caricare tutto il file (gli altri toni sono noise).

---

## Tono: `technical` (Tecnico/Asciutto)

**Per chi scrive:** developer esperti che vogliono una reference seria, no fronzoli.

**Linee guida:**
- Frasi dichiarative, brevi, attive. "Il middleware processa la request prima dell'handler."
- Nessuna metafora, nessuna analogia, nessun "immagina che…".
- Definizioni precise: cita esattamente i tipi, le firme, i parametri.
- Esempi di codice minimali — solo quanto serve a illustrare il concetto.
- Niente filler tipo "ovviamente", "come puoi immaginare", "fantastico".
- Voce neutra. Mai "tu", preferisci "il chiamante", "l'applicazione", "lo sviluppatore".

**Callout da usare:**
- `#nota`, `#attenzione`, `#esempio` — usali quando aggiungono informazione tecnica
- `#suggerimento` — solo per best practice ufficiali della doc
- `#curiosita` — **evita**, è troppo informale per questo tono

**Esempio di paragrafo (tono technical):**
> Il routing di Hono utilizza un pattern matcher RegExp-based con priorità statica > dinamica > catch-all. Le route registrate con `app.get('/users/:id')` vengono compilate in un AST al boot. La risoluzione è O(log n) sul numero di route.

---

## Tono: `balanced` (Bilanciato — DEFAULT)

**Per chi scrive:** developer in generale, che vogliono capire ma non leggere un romanzo.

**Linee guida:**
- Mix di definizioni precise e brevi spiegazioni in linguaggio comune.
- Una frase di contesto prima di un concetto nuovo, poi vai dritto al punto.
- Esempi pratici quando aiutano. Non riempire però di esempi ridondanti.
- "Tu" è OK quando è naturale ("Quando definisci una route, puoi…").
- Una metafora ogni tanto è benvenuta, non sistematica.

**Callout da usare:** tutti, con misura. `#esempio` e `#suggerimento` sono i workhorse di questo tono.

**Esempio di paragrafo (tono balanced):**
> Hono usa un router molto veloce basato su pattern matching. Quando definisci una route come `app.get('/users/:id')`, Hono la compila una volta sola al boot e la riutilizza per ogni richiesta. In pratica, anche con centinaia di route, la risoluzione resta veloce.

---

## Tono: `warm` (Caloroso/Didattico)

**Per chi scrive:** persone che imparano la tecnologia da zero, magari junior, magari da un altro background.

**Linee guida:**
- Apri ogni concetto con una metafora o analogia dal mondo reale.
- "Tu" sempre. Crea complicità con il lettore.
- Esempi quotidiani: "Pensa al routing come a un centralinista che smista chiamate…"
- Spiega anche concetti che un esperto darebbe per scontati.
- Riconosci che certe cose sono difficili: "Lo so, all'inizio sembra strano, ma…"
- Ogni capitolo ha più `#esempio` e `#curiosita` per alleggerire.
- Frasi corte. Mai due concetti complessi nella stessa frase.

**Callout da usare:** tutti, abbondantemente. `#curiosita` brilla qui.

**Esempio di paragrafo (tono warm):**
> Immagina di entrare in un grande hotel con centinaia di stanze. Quando dici "voglio andare nella stanza 237", il portiere sa esattamente dove mandarti — non controlla una per una tutte le stanze del palazzo. Hono funziona così: quando arriva una richiesta come `/users/42`, sa subito a quale "stanza" (cioè a quale handler) consegnarla. E non devi ringraziarlo, lo fa per ogni richiesta in pochi millisecondi.

---

## Regola comune a tutti i toni

Indipendentemente dal tono, **non sacrificare l'accuratezza tecnica**. Una metafora è benvenuta, una semplificazione che induce in errore no. Se devi scegliere tra "elegante" e "preciso", scegli preciso.
