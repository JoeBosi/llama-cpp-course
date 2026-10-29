# Corso pratico di llama.cpp

🇬🇧 [English](README.md) · 🇮🇹 Italiano

Guida e corso pratico, in italiano, su [llama.cpp](https://github.com/ggml-org/llama.cpp): installazione su tutte le
piattaforme, uso, modelli e quantizzazione, server e API, prestazioni, output strutturato, multimodale, integrazione,
produzione, con laboratori e progetti finali. Aggiornato a settembre 2026.

**Sito pubblicato:** https://corso-llamacpp.giuseppebosi.com/ (aperto a tutti)

## Come è fatto

- `corso/` — **tutto il contenuto**, in Markdown. È la `docs_dir` di MkDocs.
  - `corso/moduli/NN-nome/README.md` — le lezioni
  - `corso/laboratori/lab-NN-MM-nome/README.md` (+ script) — le esperienze pratiche
  - `corso/progetti-finali/` — le tracce dei progetti
  - `corso/risorse/` — glossario, modelli, link, strumenti
  - `corso/assets/img/` — schemi SVG
- `redazione/` — materiale per chi scrive: convenzioni, fatti verificati, brief, piano di lavoro
  (`redazione/upstream/` = documentazione ufficiale scaricata, non in git)
- `scripts/` — `verifica-ambiente.sh` per gli studenti, `pubblica.sh` per pubblicare
- `mkdocs.yml` — configurazione del sito (MkDocs Material: tema chiaro di default con interruttore scuro, Mermaid, schede, ammonizioni)

## Aggiungere, togliere, modificare

La navigazione è **automatica** (plugin `awesome-nav`): titolo = primo `#` della pagina, ordine = nome del file.

- **Aggiungere una pagina**: crea `corso/<sezione>/<nome>.md` (o `<cartella>/README.md`) e scrivi. Fine.
- **Togliere una pagina**: cancella il file (e i link che la citavano: `mkdocs build --strict` te li segnala).
- **Cambiare ordine**: rinomina i file (prefissi `00-`, `01-`…) oppure elenca i file in un `.nav.yml` nella cartella.
- **Nuovo laboratorio**: copia `templates/laboratorio.md` in `corso/laboratori/lab-NN-MM-nome/README.md`.

## Anteprima e pubblicazione

```bash
PYTHONPATH=$PWD .venv/bin/mkdocs serve -a 127.0.0.1:8000   # anteprima con ricarica automatica
./scripts/pubblica.sh                     # build --strict → /srv/llamacorso (servito da Caddy su https://corso-llamacpp.giuseppebosi.com/)
```

Ambiente: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

## Licenza

Testi e schemi [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.it), codice dei laboratori MIT.

## Autore

Prof. Giuseppe Bosi, Dottore in Ingegneria Elettronica (V.O.), Professore di Scienze e Tecnologie Informatiche ·
[www.giuseppebosi.com](https://www.giuseppebosi.com) · [LinkedIn](https://www.linkedin.com/in/giuseppebosi)

