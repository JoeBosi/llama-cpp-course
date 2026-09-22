# Corso pratico di llama.cpp

Guida e corso pratico su [llama.cpp](https://github.com/ggml-org/llama.cpp): dall'installazione sulle
varie piattaforme all'uso quotidiano, fino alla messa in produzione. Ogni modulo ha laboratori
guidati; il corso si chiude con un progetto finale.

> **Versione di riferimento:** vedi [`VERSIONE.md`](VERSIONE.md). llama.cpp cambia ogni giorno:
> tutti i comandi del corso sono verificati sulla versione indicata lì.

## Programma

| # | Modulo | Laboratori |
|---|---|---|
| 00 | [Introduzione a llama.cpp](moduli/00-introduzione/README.md) | 2 |
| 01 | [Installazione su varie piattaforme](moduli/01-installazione/README.md) | 4 |
| 02 | [Primi passi: `llama cli`](moduli/02-primi-passi/README.md) | 3 |
| 03 | [Modelli, GGUF e quantizzazione](moduli/03-modelli-gguf-quantizzazione/README.md) | 3 |
| 04 | [`llama serve`: server e API](moduli/04-server-api/README.md) | 4 |
| 05 | [Prestazioni e ottimizzazione](moduli/05-prestazioni/README.md) | 4 |
| 06 | [Output strutturato: GBNF e JSON Schema](moduli/06-output-strutturato/README.md) | 2 |
| 07 | [Multimodalità: visione, audio, voce](moduli/07-multimodale/README.md) | 2 |
| 08 | [Integrare llama.cpp nelle applicazioni](moduli/08-integrazione-sviluppo/README.md) | 2 |
| 09 | [Messa in produzione](moduli/09-deploy-produzione/README.md) | 2 |
| 10 | [Approfondimenti: dentro ggml e llama.cpp](moduli/10-approfondimenti/README.md) | 2 |
| — | [Progetti di fine corso](progetti-finali/README.md) | 6 tracce |

Percorsi consigliati:
- **Utente** (usare modelli in locale): 00 → 01 → 02 → 03 → 04 → 06
- **Sviluppatore** (integrare nelle app): utente + 05 → 07 → 08
- **DevOps / MLOps** (servire modelli): utente + 05 → 09
- **Avanzato**: tutto + 10

## Struttura del repository

```
moduli/            teoria, un modulo per cartella
laboratori/        esperienze pratiche (lab-MM-NN-nome), collegate ai moduli
progetti-finali/   tracce dei progetti di fine corso e griglia di valutazione
docs/              materiale per chi scrive il corso: convenzioni, piattaforme, piano di lavoro
risorse/           modelli consigliati, glossario, link
templates/         modelli di pagina per nuovi laboratori/moduli
scripts/           script di supporto (verifica ambiente, ecc.)
```

## Requisiti per seguire il corso
- Un computer con almeno 8 GB di RAM (16 GB consigliati); GPU facoltativa
- Linux, macOS o Windows; conoscenza base del terminale
- Per i moduli 08-10: basi di Python e/o C++

Verifica rapida dell'ambiente: `scripts/verifica-ambiente.sh`
