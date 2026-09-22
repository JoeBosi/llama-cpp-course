# Modulo 05: Prestazioni e ottimizzazione

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Metriche: prompt processing (pp) vs token generation (tg), perché la tg è limitata dalla banda di memoria
2. `llama-bench` e `batched-bench`
3. Thread, affinità CPU, NUMA
4. Offload su GPU (`-ngl`), inferenza ibrida CPU+GPU, modelli MoE con esperti su CPU
5. Flash attention, quantizzazione della KV cache
6. Decodifica speculativa (modello bozza)
7. Multi-GPU e inferenza distribuita via RPC
8. Adattare automaticamente i parametri alla memoria disponibile (`fit-params`)

## Laboratori
- [Benchmark riproducibili](../../laboratori/lab-05-01-benchmark/README.md): Misurare pp/tg con `llama-bench` su diverse quantizzazioni e numeri di thread; produrre un grafico.
- [Offload ibrido CPU+GPU](../../laboratori/lab-05-02-offload-ibrido/README.md): Trovare il valore di `-ngl` ottimale per un modello più grande della VRAM.
- [Decodifica speculativa](../../laboratori/lab-05-03-speculativa/README.md): Misurare l'accelerazione con un modello bozza su testo e su codice.
- [Cluster RPC](../../laboratori/lab-05-04-rpc/README.md): Distribuire un modello su due macchine (o due container) tramite il backend RPC.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
