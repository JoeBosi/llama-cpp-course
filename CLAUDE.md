# Corso pratico di llama.cpp

Sito MkDocs Material in **italiano** su https://github.com/ggml-org/llama.cpp (installazione, uso, produzione,
laboratori, progetti finali). Pubblicato su https://corso-llamacpp.giuseppebosi.com/ (blocco `corso-llamacpp.giuseppebosi.com` in
`/etc/caddy/Caddyfile`, root `/srv/llamacorso`). Solo Markdown + script: llama.cpp non è nel repo.

## Sito APERTO, senza password (decisione di Giuseppe, 28/10/2026)
- Il corso è pubblico: i link stanno nel CV letto dalla commissione del Comune. Il Controller ha tolto `basic_auth`
  (backup `/etc/caddy/Caddyfile.bak-2026-10-28-082417`). **Non rimetterla mai** e **non toccare Caddy** nelle pubblicazioni.
- Dopo ogni `scripts/pubblica.sh` verificare che le pagine rispondano **200 senza password** (lo script lo fa da solo e
  fallisce se non è così). Il contenuto è pubblico: niente dati personali, IP, chiavi o note interne nelle pagine.

## Da leggere prima di scrivere contenuti
- `redazione/fatti-verificati.md`: versioni, comandi e output **provati** sul VPS (22/09/2026). Non inventare flag:
  cercarli in `redazione/upstream/help_*.txt` (output reale di `llama <cmd> --help`) o nei README ufficiali lì salvati.
- `redazione/convenzioni.md`: lingua, kit MkDocs (ammonizioni, schede, Mermaid, SVG, badge di stato), nomi file.
- `redazione/brief-scrittori.md`: struttura richiesta per moduli e lab.
- `corso/versione.md`: build di riferimento (b11046). Cambiarla = rieseguire i lab e aggiornare la pagina.

## Tono del corso (regola di Giuseppe, 28/10/2026)
- **Ogni frase deve insegnare qualcosa.** Niente avvertenze, scuse o giustificazioni: niente badge "verificato/bozza",
  niente "non testato", "da verificare", "scritto con l'aiuto dell'IA", note sull'autore o sulla macchina di prova
  dentro le lezioni. Le parti non provate si scrivono come contenuto normale, al presente, con rimando alla
  documentazione ufficiale. Regole complete: `redazione/regole-tono.md`. Lo stato di verifica resta solo nei file
  interni di `redazione/` (fatti-verificati, piattaforme), mai nelle pagine del sito.

## Diciture e privacy (revisione del 28/10/2026, approvata da Giuseppe)
- `corso/informazioni.md`: solo autore, licenza (testi CC BY 4.0, codice MIT) e crediti (marchi, strumenti,
  nessun tracciamento). Contatti: info@giuseppebosi.com. Piè di pagina in `mkdocs.yml` (`copyright`). Tenerli coerenti.
- Niente richieste a terzi dal browser: `font: false` (no Google Fonts) e Mermaid ospitato in
  `corso/assets/javascripts/mermaid.min.js` (11.17.2; per aggiornarlo: scaricare da unpkg e sostituire il file).
- Data "Ultimo aggiornamento" per pagina dal plugin `git-revision-date-localized`: le pagine vanno committate.
- Il corso è fermo a v0.4.1 mentre llama.cpp è alla v0.7.0 (porta server 8080 → 9931): avviso in home e in
  `versione.md`; quando si aggiorna il corso, togliere gli avvisi e aggiornare la tabella.

## Struttura e navigazione
- `corso/` è la docs_dir. Nav automatica (awesome-nav): titolo = H1, ordine = nome file; `.nav.yml` solo se serve.
- Pagine indice = `README.md`. Link interni relativi ai file `.md`. `mkdocs build --strict` deve passare.
- Pubblicare: `./scripts/pubblica.sh` (build strict → `/srv/llamacorso`). Anteprima: `PYTHONPATH=$PWD .venv/bin/mkdocs serve` (il PYTHONPATH serve a `scripts/mermaid_fence.py`).

## Ambiente di prova (questo VPS)
- Ubuntu 24.04 x86_64, 6 vCPU AMD EPYC (AVX2), 11 GB RAM ma ~4 liberi, **nessuna GPU**, Docker, cmake/ninja/ccache.
- `llama` (build b11046) in `~/.local/bin`; serve `SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt` per scaricare da HF.
- Tarball release completo in `~/llama-lab/rel/llama-b11046/`; modello di prova `ggml-org/Qwen3.5-0.8B-GGUF` (785 MB) in cache HF.
- Usare modelli ≤ 1 GB, `-t 3`, un processo llama alla volta; niente build dai sorgenti sul VPS.
- GPU/macOS/Windows/Android non verificabili qui: badge `stato-bozza` e `redazione/piattaforme.md`.
