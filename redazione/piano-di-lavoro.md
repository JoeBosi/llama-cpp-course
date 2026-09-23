# Piano di lavoro

## Fatto (22/09/2026)
- [x] Struttura del repository, programma, scalette
- [x] Framework: MkDocs Material + awesome-nav + glightbox (tema chiaro default, switch scuro, Mermaid, schede, SVG)
- [x] Pubblicazione: Caddy `corso-llamacpp.giuseppebosi.com` (HTTPS + basic auth) → `/srv/llamacorso`, `scripts/pubblica.sh`
- [x] llama.cpp b11046 installato sul VPS, comandi base verificati (cli, serve, bench, API) → `fatti-verificati.md`
- [x] Prima stesura completa di moduli, laboratori, progetti e risorse (scrittori A1–A6)

## Da fare
- [ ] Rilettura incrociata: coerenza fra moduli (stessi nomi di modelli, stessi flag), link, badge di stato
- [ ] Verificare i laboratori GPU/macOS/Windows/Android su hardware reale (vedi `piattaforme.md`)
- [ ] Soluzioni di riferimento dei progetti finali (repo separato, non pubblico)
- [ ] Quiz interattivi (oggi: domande + soluzioni ripiegabili)
- [ ] Dominio e HTTPS quando Giuseppe deciderà il sottodominio (`*.giuseppebosi.com`)

## Decisioni prese (senza chiedere, su mandato di Giuseppe)
- Formato: sito statico MkDocs Material; contenuti in `corso/`, Markdown puro.
- Versione di riferimento: build b11046 (quella distribuita dall'installer il 22/09/2026), non `master`.
- Modello didattico principale: `ggml-org/Qwen3.5-0.8B-GGUF` (piccolo, ufficiale, gira su CPU).
- Pubblicazione: prima per IP in HTTP; il 23/09 Giuseppe ha chiesto dominio + HTTPS + basic auth (fatto).
