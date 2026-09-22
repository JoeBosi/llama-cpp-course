# Corso pratico di llama.cpp

Repository di una guida/corso in **italiano** su https://github.com/ggml-org/llama.cpp: installazione,
uso, prestazioni, integrazione, produzione, laboratori e progetti finali. Solo contenuti Markdown
(+ script dei laboratori): llama.cpp non è incluso nel repo.

## Da leggere prima di scrivere contenuti
- `VERSIONE.md`: versione di llama.cpp di riferimento. **Ogni comando va verificato su quella versione**
  prima di segnare una pagina 🟢. llama.cpp cambia ogni giorno: non scrivere flag o nomi a memoria.
- `docs/convenzioni.md`: lingua, formato dei comandi, modelli piccoli, nomi delle cartelle, stato delle pagine.
- `docs/piano-di-lavoro.md`: fasi, avanzamento e decisioni aperte (aggiornarlo quando si chiude un lavoro).

## Struttura
- `moduli/NN-nome/README.md`: teoria; `laboratori/lab-NN-MM-nome/`: pratica; `progetti-finali/`: tracce.
- Nuove pagine: partire da `templates/`. Se si aggiunge/rinomina un lab, aggiornare i link nel modulo
  e la tabella del `README.md` principale.

## Ambiente di prova (questo VPS)
- Linux x86_64, 6 vCPU AMD EPYC (AVX2, no AVX-512), 11 GB RAM ma spesso solo ~4 GB liberi
  (altri progetti girano qui), **nessuna GPU**. Docker disponibile; cmake/ninja/ccache non installati.
- Usare modelli ≤ 1-2 GB per le prove. Modelli e build fuori dal repo (es. `~/llama-lab/`), mai committati.
- Le parti GPU/macOS/Windows non si possono verificare qui: marcarle "da verificare" in `docs/piattaforme.md`.
