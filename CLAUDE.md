# Corso pratico di llama.cpp

Sito MkDocs Material in **italiano** su https://github.com/ggml-org/llama.cpp (installazione, uso, produzione,
laboratori, progetti finali). Pubblicato su https://corso-llamacpp.giuseppebosi.com/ (Caddy con basic auth, blocco `corso-llamacpp.giuseppebosi.com` in
`/etc/caddy/Caddyfile`, root `/srv/llamacorso`). Solo Markdown + script: llama.cpp non è nel repo.

## Da leggere prima di scrivere contenuti
- `redazione/fatti-verificati.md`: versioni, comandi e output **provati** sul VPS (22/09/2026). Non inventare flag:
  cercarli in `redazione/upstream/help_*.txt` (output reale di `llama <cmd> --help`) o nei README ufficiali lì salvati.
- `redazione/convenzioni.md`: lingua, kit MkDocs (ammonizioni, schede, Mermaid, SVG, badge di stato), nomi file.
- `redazione/brief-scrittori.md`: struttura richiesta per moduli e lab.
- `corso/versione.md`: build di riferimento (b11046). Cambiarla = rieseguire i lab e aggiornare la pagina.

## Struttura e navigazione
- `corso/` è la docs_dir. Nav automatica (awesome-nav): titolo = H1, ordine = nome file; `.nav.yml` solo se serve.
- Pagine indice = `README.md`. Link interni relativi ai file `.md`. `mkdocs build --strict` deve passare.
- Pubblicare: `./scripts/pubblica.sh` (build strict → `/srv/llamacorso`). Anteprima: `.venv/bin/mkdocs serve`.

## Ambiente di prova (questo VPS)
- Ubuntu 24.04 x86_64, 6 vCPU AMD EPYC (AVX2), 11 GB RAM ma ~4 liberi, **nessuna GPU**, Docker, cmake/ninja/ccache.
- `llama` (build b11046) in `~/.local/bin`; serve `SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt` per scaricare da HF.
- Tarball release completo in `~/llama-lab/rel/llama-b11046/`; modello di prova `ggml-org/Qwen3.5-0.8B-GGUF` (785 MB) in cache HF.
- Usare modelli ≤ 1 GB, `-t 3`, un processo llama alla volta; niente build dai sorgenti sul VPS.
- GPU/macOS/Windows/Android non verificabili qui: badge `stato-bozza` e `redazione/piattaforme.md`.
