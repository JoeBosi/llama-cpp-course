# Modulo 03: Modelli, GGUF e quantizzazione

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Trovare modelli GGUF su Hugging Face e leggerne le schede
2. Tipi di quantizzazione: Q8_0, Q6_K, Q5_K_M, Q4_K_M, IQ* … e quando usarli
3. Convertire un modello Hugging Face in GGUF (`convert_hf_to_gguf.py`)
4. Quantizzare (`quantize`) e matrice di importanza (`imatrix`)
5. Misurare la qualità: perplexity e KL-divergence
6. Dividere/unire modelli grandi (`gguf-split`)
7. Adattatori LoRA: caricarli ed esportarli (`export-lora`)

## Laboratori
- [Da Hugging Face a GGUF](../../laboratori/lab-03-01-conversione/README.md): Convertire un modello piccolo in GGUF F16 e verificarne il funzionamento.
- [La scala delle quantizzazioni](../../laboratori/lab-03-02-scala-quantizzazioni/README.md): Produrre 5 quantizzazioni dello stesso modello e tabellare dimensione, velocità e perplexity.
- [Quantizzazione con imatrix](../../laboratori/lab-03-03-imatrix/README.md): Confrontare quantizzazioni a pochi bit con e senza matrice di importanza.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
