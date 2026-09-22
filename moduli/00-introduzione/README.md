# Modulo 00: Introduzione a llama.cpp

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Cos'è l'inferenza locale e perché farla (privacy, costi, latenza, offline)
2. llama.cpp e ggml: storia, architettura a livelli (ggml → libllama → strumenti)
3. Il formato GGUF: metadati, tensori, tokenizer, chat template
4. Quantizzazione in concetto: bit per peso, qualità vs memoria
5. Stimare RAM/VRAM necessarie: pesi + KV cache + overhead
6. L'ecosistema: Hugging Face, Ollama, LM Studio, llama-cpp-python (cosa usa llama.cpp sotto)
7. Versioni: release `vX.Y.Z` stabili vs build notturne `bNNNNN`

## Laboratori
- [Stimare la memoria di un modello](../../laboratori/lab-00-01-stima-memoria/README.md): Calcolare a mano e con uno script la memoria per 3 modelli e 3 quantizzazioni, poi confrontare con l'uso reale (da verificare nel modulo 02).
- [Anatomia di un file GGUF](../../laboratori/lab-00-02-anatomia-gguf/README.md): Ispezionare metadati e tensori di un GGUF con `gguf-py` / viewer di Hugging Face.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
