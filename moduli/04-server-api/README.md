# Modulo 04: `llama serve`: server e API

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Avviare il server, web UI integrata
2. API compatibile OpenAI: `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`
3. Endpoint nativi: `/completion`, `/tokenize`, `/health`, `/metrics`, `/slots`
4. Richieste in parallelo (`-np`), batching continuo, riuso della cache del prompt
5. Embedding e reranking
6. Tool/function calling
7. Chiavi API, CORS e cosa NON esporre su internet
8. Gestire più modelli con un solo server

## Laboratori
- [Server e web UI](../../laboratori/lab-04-01-server-e-webui/README.md): Avviare il server, usare la web UI, interrogarlo con curl.
- [Client compatibili OpenAI](../../laboratori/lab-04-02-client-openai/README.md): Usare l'SDK `openai` (Python e JS) puntato al server locale, streaming incluso.
- [Carico e parallelismo](../../laboratori/lab-04-03-parallelismo/README.md): Misurare throughput e latenza al variare di `-np` con un piccolo script di carico.
- [Tool calling](../../laboratori/lab-04-04-tool-calling/README.md): Far chiamare al modello una funzione Python (meteo finto → poi reale) tramite l'API.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
