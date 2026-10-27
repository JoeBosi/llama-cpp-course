# Revisione per l'apertura al pubblico — corso llama.cpp

Richiesta del Controller (Giuseppe, 27/10/2026). Revisione in sola lettura: **nessuna modifica al sito** è stata fatta.
Sito: https://corso-llamacpp.giuseppebosi.com/ · repo privato https://github.com/JoeBosi/corso-llamacpp (tag v1.2.0).

## 1. Il corso come opera di divulgazione

### Com'è
Fatto bene per essere mostrato: 55 pagine (11 moduli, 30 laboratori, 6 progetti finali, glossario, modelli consigliati),
schemi (39 diagrammi + 16 SVG, tutti validati), navigazione uniforme, funziona su telefono e tablet, ricerca interna.
Ogni pagina dichiara con un badge se i comandi sono stati **eseguiti davvero** (Linux/CPU) o scritti dalla
documentazione ("bozza"): questa onestà è un punto di forza, va solo resa più visibile (vedi B).
Link: 191 esterni controllati oggi, **nessuno rotto** (restano solo indirizzi d'esempio tipo localhost/example.com;
openai.com e reddit rifiutano i robot, per le persone funzionano).

### Problemi trovati
- **A. Versione vecchia (il più importante).** Il corso è fermo a llama.cpp **v0.4.1 / build b11046** (22/09/2026).
  Oggi: **v0.7.0** (15/10/2026), build b11936 (27/10). Un cambio concreto rompe i comandi: **dalla v0.7.0 `llama serve`
  ascolta sulla porta 9931, non più 8080**. Tutte le pagine che dicono "apri http://127.0.0.1:8080" (moduli 04 e 09,
  laboratori 04-xx e 09-xx, quickstart) sono sbagliate per chi installa oggi. Non coperte anche le novità v0.5-v0.7
  (`--moe-cache-mib`, decodifica speculativa LiliCorr, ggml 0.27).
- **B. 20 pagine su 55 con parti "bozza / da verificare"**: GPU, macOS, Windows, Android, audio/TTS, compilazione C
  fuori da Linux. Dichiarato pagina per pagina, ma manca una frase in home che dica cosa è stato provato e cosa no.
- **C. 4 link interni da sistemare** (ancore cambiate dopo la riscrittura): lab 02-02 → modulo 02 §4; lab 03-02 →
  modulo 03 §5; modulo 02 → modulo 05 §3; lab 08-02 punta alla cartella `documenti/` invece che ai file.
- **D. Refuso tecnico**: lab 02-03, script con percorso `/root/.cache/...` fisso (va `~/.cache`).
- **E. Nessuna dicitura di legge/attribuzione** (oggi nel sito non compaiono né "Giuseppe", né "autore", né una licenza,
  né contatti): senza il nome dell'autore l'opera citata nel CV **non è attribuibile**.

### Proposte, in ordine di importanza
1. **Pagina "Informazioni" + piè di pagina** (mezza giornata): autore (Giuseppe Bosi) e data di ultimo aggiornamento;
   **licenza dei contenuti** (proposta: testi e schemi CC BY-SA 4.0, codice dei laboratori MIT; llama.cpp resta MIT di
   ggml-org, già nel piè di pagina); **marchi**: "llama.cpp, ggml, Hugging Face, NVIDIA, CUDA, Apple, Metal, AMD, Intel,
   Qwen, Gemma, Llama, Docker, Raspberry Pi sono marchi dei rispettivi proprietari; corso indipendente, non affiliato né
   approvato"; **IA**: "contenuti prodotti con l'aiuto di un assistente IA e rivisti dall'autore; i comandi con badge
   'verificato' sono stati eseguiti, le parti 'bozza' no"; **contatti**: info@giuseppebosi.com (casella dei progetti)
   e come segnalare errori. Piè di pagina: "© 2026 Giuseppe Bosi · CC BY-SA 4.0 · Informazioni".
2. **Avviso di versione** (10 minuti): in home e in `versione.md`: "verificato su v0.4.1; dalla v0.7.0 la porta del
   server è 9931: aggiungi `--port 8080` oppure cambia l'indirizzo nei comandi". Poi, con calma, aggiornare a v0.7 e
   rieseguire i laboratori 01-02-04-05-09 (1-2 giorni).
3. **Privacy** (10 minuti di configurazione, zero costi): il sito non ha cookie, moduli né tracciamento, **ma** carica i
   font da Google (`fonts.googleapis.com`) e la libreria dei diagrammi da `unpkg.com`: l'IP di ogni visitatore arriva a
   quei due servizi. Soluzione pulita: ospitarli sul sito (Material: `font: false` + copia locale di `mermaid.min.js`);
   così basta una riga di informativa ("nessun cookie, nessun dato raccolto; i log del server conservano l'IP per N
   giorni per sicurezza") senza banner cookie.
4. **Frase in home su cosa è verificato** (Linux/CPU) e cosa è "bozza" (B).
5. **Link interni e refuso** (C, D): 15 minuti.
6. **Data di aggiornamento per pagina** automatica da git (plugin `git-revision-date-localized`, gratuito).

## 2. Rischi dell'apertura al pubblico

### Cosa c'è davvero dietro il sito
Solo **file statici** (HTML/CSS/JS, 7,9 MB) serviti da Caddy. **Nessuna API, nessun server llama esposto, nessuna
chiave, nessuna sandbox, nessun database, nessun modulo**: un estraneo non può far girare nulla sul VPS passando dal
sito. Costo variabile ≈ zero: 5 visitatori contemporanei su pagine da ~100 KB sono pochi GB al mese anche con migliaia
di visite.

### Controlli fatti sul contenuto pubblicato
- Nessun IP, hostname, email, password, token o chiave nel sito (cercati tutti). Il corso cita "il VPS del corso"
  solo con dati generici (Ubuntu, 6 vCPU, 11 GB, nessuna GPU): innocuo.
- File scaricabili dei laboratori (script, Caddyfile, compose, unit systemd): solo esempi; l'unico hash bcrypt è un
  esempio commentato ("studente"), la chiave API è `chiave-di-prova-cambiami`. Ok.
- Il repo GitHub è **privato** e deve restarlo così com'è: contiene `redazione/` (dettagli del VPS, note di lavoro),
  è in italiano e la cronologia non è ripulita. Se un giorno serve un repo pubblico ("contribuisci"), farne uno nuovo
  con la sola cartella `corso/`.

### Cosa sistemare prima di aprire (per chi tocca Caddy: il Controller)
1. **Utenti di prova nel basic_auth**: oggi ci sono `giuseppe` e **`pasquale`** (utente di prova, password debole
   decisa in chat). Togliere `pasquale`; se il sito diventa libero, togliere tutto il blocco `basic_auth`.
2. **Il limite "5 contemporanei"**: se è un contatore globale, 5 robot (Google, Bing, scanner) bastano a mostrare
   "troppe connessioni" alle persone vere. Meglio contare per IP (rate limit per indirizzo) o escludere gli
   user-agent dei motori; aggiungere un `robots.txt` che lascia indicizzare ma chiede un `Crawl-delay`.
3. **Header di sicurezza**: oggi solo `server: Caddy`. Aggiungere nel blocco: `Strict-Transport-Security`,
   `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options`, e una `Content-Security-Policy` (facile
   una volta ospitati font e mermaid in locale, punto 3 della parte 1).
4. **Codice di terzi**: oggi il browser dei visitatori esegue `mermaid.min.js` scaricato da unpkg.com; se quel CDN
   venisse compromesso, lo sarebbe anche il sito. Stessa soluzione: copia locale.
5. **File inutili**: `assets/javascripts/bundle.*.min.js.map` (1 MB, mappa di debug di Material): toglierlo in
   `scripts/pubblica.sh` (`rm` dopo la build). L'indice di ricerca (0,7 MB) è normale.
6. **Log di accesso**: se si attiva un log per contare i visitatori, dire nell'informativa che gli IP si conservano e
   per quanto (es. 7 giorni) e usare `logrotate`.

### Cosa non è un rischio
Nessun endpoint `/v1/...` raggiungibile, nessun cookie, nessun upload, niente commenti: spam e injection non sono
possibili. I laboratori insegnano a esporre un server llama **sulla macchina dello studente**, non su questo VPS.
