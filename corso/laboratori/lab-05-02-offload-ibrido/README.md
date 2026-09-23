# Lab 05-02 · Offload ibrido CPU+GPU

> Modulo: [05: Prestazioni e ottimizzazione](../../moduli/05-prestazioni/README.md) · <span class="stato stato-bozza">bozza · richiede una GPU, non verificato sul VPS del corso (senza GPU)</span> · Durata stimata: 60 minuti

## Obiettivo

Prendere un modello **più grande della VRAM** disponibile, trovare sperimentalmente il valore di `-ngl` che dà la
generazione più veloce, e poi recuperare VRAM con la KV cache quantizzata e (per un MoE) con gli esperti su CPU.
Confronterai infine la tua scelta con quella automatica di `llama fit-params`.

## Prerequisiti

- Un binario con backend GPU (`llama cli --list-devices` deve elencare almeno un dispositivo: CUDA, Vulkan, Metal, HIP…).
- Almeno 16 GB di RAM di sistema e 6-8 GB di VRAM (con più VRAM scegli un modello più grande: l'esercizio ha senso solo se il modello **non** entra tutto).
- Lab 05-01 completato (sai leggere l'uscita di `llama bench`).

## Materiale

| Cosa | Fonte | Dimensione | Note |
|---|---|---|---|
| Modello denso | `ggml-org/gemma-3-12b-it-GGUF` → `gemma-3-12b-it-Q4_K_M.gguf` (licenza Gemma) | 6,96 GB | 48 layer; non entra in 8 GB con contesto e buffer |
| Modello MoE (variante) | `ggml-org/Qwen3-30B-A3B-GGUF` → `Qwen3-30B-A3B-Q4_K_M.gguf` (Apache 2.0) | 17,7 GB | 30 miliardi di parametri, 3 attivi per token: perfetto per `-ncmoe` |
| Script | [`scan-ngl.sh`](scan-ngl.sh) in questa cartella | | esegue `llama bench` su una lista di `-ngl` e stampa una tabella |

```bash
llama download -hf ggml-org/gemma-3-12b-it-GGUF:Q4_K_M --no-mmproj
G=$(ls ~/.cache/huggingface/hub/models--ggml-org--gemma-3-12b-it-GGUF/snapshots/*/gemma-3-12b-it-Q4_K_M.gguf)
```

## Procedura

1. **Quanti layer ha il modello e quanto pesa un layer?** Avvia con log a livello info e cerca `n_layer`:

    ```bash
    llama cli -m "$G" -st -p "ciao" -n 1 -lv 3 2>&1 | grep -E "n_layer|model size|offloaded"
    ```

    Con 48 layer e 6,96 GB, ogni layer pesa in media ~140 MB (l'embedding e l'output pesano di più). Annota anche la
    riga `load_tensors: offloaded N/49 layers to GPU`: con `-ngl auto` (default) è la funzione di fit a scegliere N.

2. **Che cosa ha deciso il fit?** Prima di misurare, chiedi la stima:

    ```bash
    llama fit-params -m "$G" -c 8192
    ```

    Stampa una riga tipo `-c 8192 -ngl 37`: annotala, è il valore da battere.

3. **Scansione di `-ngl`.** Lo script prende il modello, la lista di valori e il contesto; disattiva il fit (`--fit off`
    non esiste in `llama bench`, che usa `-ngl` esattamente come indicato) e usa `-fa on`:

    ```bash
    ./scan-ngl.sh "$G" "0,16,24,32,36,40,44,48" 8192
    ```

    Output atteso (valori indicativi per una GPU da 8 GB; i tuoi saranno diversi):

    ```
      ngl     test        t/s    ± dev
        0    pp512      45.10     0.80
        0    tg128       4.90     0.05
       16    pp512     120.30     1.10
       16    tg128       7.80     0.10
       …
       40    pp512     390.00     3.00
       40    tg128      19.50     0.30
       44    pp512   (errore: out of memory)
    ```

    Il valore di `-ngl` più alto che **non** va in out-of-memory è il tuo candidato. Se i test grandi vanno in OOM, la
    tabella si interrompe: rilancia con una lista più fitta intorno all'ultimo valore riuscito (es. `"38,39,40,41,42"`).

4. **Recupera VRAM con la KV cache quantizzata.** Ripeti i valori intorno al limite con `-ctk q8_0 -ctv q8_0`:

    ```bash
    llama bench -m "$G" -ngl 40,42,44,46,48 -p 512 -n 128 -r 3 -fa on -ctk q8_0 -ctv q8_0 --progress
    ```

    Con 8192 token di contesto la cache f16 di Gemma 3 12B occupa circa 1,5 GB; in q8_0 ne libera metà, spesso
    abbastanza per 2-4 layer in più. Se arrivi a `-ngl 48` (tutto in VRAM) vedrai il "salto" di tg descritto nel modulo.

5. **Confronto con la scelta automatica.** Avvia il server con i parametri migliori trovati e con quelli del fit e
    confronta `predicted_per_second` nel campo `timings` di una richiesta (modulo 04):

    ```bash
    llama serve -m "$G" -ngl 44 -c 8192 -fa on -ctk q8_0 -ctv q8_0 --port 18104
    curl -s localhost:18104/v1/chat/completions -H 'content-type: application/json' \
      -d '{"messages":[{"role":"user","content":"Descrivi Roma in 200 parole."}],"max_tokens":200}' | python3 -c "import json,sys; print(json.load(sys.stdin)['timings'])"
    ```

    Alla chiusura del server (++ctrl+c++) leggi `llama_memory_breakdown_print`: per il dispositivo GPU vedi `total`,
    `free`, `model`, `context`, `compute`. La colonna `free` dice quanto margine hai lasciato.

6. **Variante MoE.** Con Qwen3-30B-A3B (17,7 GB) nessun valore di `-ngl` entra in 8 GB con tutti i tensori. Prova
    invece tutti i layer in VRAM ma gli esperti su CPU:

    ```bash
    Q=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3-30B-A3B-GGUF/snapshots/*/Qwen3-30B-A3B-Q4_K_M.gguf)
    llama fit-params -m "$Q" -c 8192                       # (1)!
    llama bench -m "$Q" -ngl 99 -ncmoe 48,40,32,24 -p 512 -n 128 -r 2 --progress
    ```

    1. Stampa `-ngl 48 -ot blk\.NN\.ffn_(up|down|gate)_(ch|)exps=CPU,…`: è la forma "esplicita" di `-ncmoe`.

    `-ncmoe N` tiene su CPU gli esperti dei primi N layer: più basso è N, più esperti stanno in VRAM e più veloce è la
    generazione, finché non finisce la memoria. Cerca l'N minimo che non va in OOM.

## Verifica del risultato

- [ ] Hai una tabella t/s vs `-ngl` con almeno 6 punti e sai indicare il valore massimo che entra in VRAM.
- [ ] Con la KV cache q8_0 sei riuscito ad aumentare `-ngl` di almeno un layer (o hai capito perché no).
- [ ] Il valore di `-ngl` che hai trovato è ≥ di quello proposto da `llama fit-params` con margine di 1024 MiB (se è molto più alto, il fit sta lasciando margine: prova `--fit-target 512`).
- [ ] Per il MoE: hai trovato l'`-ncmoe` minimo e la tg corrispondente.

## Domande e varianti

- Perché tra `-ngl 44` e `-ngl 48` la tg può raddoppiare mentre tra 0 e 16 cresce solo del 60 %?
- Che succede a pp e tg se lasci `-ngl 48` ma disattivi l'offload della KV cache con `-nkvo`? In quali casi ha senso?
- Ripeti la scansione con `-c 32768`: quanto scende il massimo `-ngl` ammissibile? Calcola prima la dimensione della KV cache a mano (formula nel modulo).
- Con due GPU: `-ts 3,1` contro il default proporzionale alla memoria; e `-sm tensor -fa on -ctk f16 -ctv f16` (solo CUDA, modello denso).
- Senza GPU puoi comunque fare i passi 1, 2 e leggere `llama_memory_breakdown_print`: l'uscita di `fit-params` sarà `-c <contesto del modello> -ngl -1`.

## Consegna

La tabella del passo 3 (o il CSV `risultati.csv` prodotto dallo script), la riga di `llama fit-params`, il `timings`
del passo 5 e una relazione di 10 righe: valore di `-ngl` scelto, con quali opzioni di KV cache, quanto margine di VRAM
hai lasciato e perché.
