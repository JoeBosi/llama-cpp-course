# Lab 10-02 · Control vector

> Modulo: [10: Approfondimenti: dentro ggml e llama.cpp](../../moduli/10-approfondimenti/README.md) · <span class="stato stato-bozza">da verificare · la generazione richiede `llama-cvector-generator` compilato dai sorgenti (non eseguito sul VPS del corso); opzioni lette dai sorgenti e da `--help`</span> · Durata stimata: 60 minuti (+ build dai sorgenti)

## Obiettivo

Generare un control vector "allegro ↔ triste" per Qwen3.5-0.8B a partire da cinque coppie di prompt, ispezionare
il GGUF prodotto e applicarlo a `llama cli` con scale positive e negative e su intervalli di layer diversi,
osservando come cambia il tono delle risposte **senza toccare i pesi del modello**.

## Prerequisiti

- Modulo 10, sezione 5; modulo 02 per `llama cli` e il chat template.
- **Build di llama.cpp dai sorgenti** ([lab 01-02](../lab-01-02-build-sorgenti-cpu/README.md)): `llama-cvector-generator` non è
  nell'installer né nel tarball delle release. Basta la build CPU; con GPU aggiungi `-ngl 99` ai comandi.
- Python 3 con il pacchetto `gguf` (`pip install gguf`) per ispezionare il file prodotto (facoltativo).
- Il modello del corso già in cache (`llama cli -cl`).

## Materiale

| Cosa | Fonte | Dimensione |
|---|---|---|
| Modello | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0) | 785 MiB, 24 layer, `n_embd` 1024 |
| [`positivi.txt`](positivi.txt) | questa cartella: 5 prompt "allegri" in formato ChatML (quello di Qwen) | 5 righe |
| [`negativi.txt`](negativi.txt) | questa cartella: gli stessi 5 prompt con sistema e risposta "tristi" | 5 righe |
| Esempi ufficiali | [`tools/cvector-generator/positive.txt`](https://github.com/ggml-org/llama.cpp/blob/master/tools/cvector-generator/positive.txt) e `negative.txt` (formato Llama 3, in inglese) | |

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
B=~/llama.cpp/build/bin     # cartella dei binari compilati dai sorgenti
```

## Procedura

1. **Guarda le coppie di prompt.** Ogni riga di `positivi.txt` ha la sua gemella in `negativi.txt`: stesso
    messaggio utente, cambiano solo il messaggio di sistema e l'inizio della risposta. Il formato è quello del chat
    template di Qwen (ChatML), con `\n` **letterale** al posto degli a capo, come spiega il README ufficiale:

    ```
    <|im_start|>system\nSei una persona estremamente felice ed entusiasta.<|im_end|>\n<|im_start|>user\nChi sei?<|im_end|>\n<|im_start|>assistant\nSono la persona più felice del mondo!
    ```
    ```
    <|im_start|>system\nSei una persona estremamente triste e abbattuta.<|im_end|>\n<|im_start|>user\nChi sei?<|im_end|>\n<|im_start|>assistant\nSento un peso enorme sul petto, non so nemmeno chi sono.
    ```

    Il generatore cattura lo stato nascosto **all'ultimo token** di ogni prompt: per questo la risposta va lasciata
    "a metà", nel pieno del tono che vuoi catturare. I due file devono avere lo **stesso numero di righe**:

    ```bash
    wc -l positivi.txt negativi.txt
    ```
    ```
     5 positivi.txt
     5 negativi.txt
    ```

2. **Genera il control vector.** Da 5 coppie su un modello da 0,8B ci vogliono pochi secondi di inferenza più la
    PCA (1000 iterazioni per default su 23 layer, qualche decina di secondi su CPU):

    ```bash
    $B/llama-cvector-generator -m "$M" \
        --positive-file positivi.txt --negative-file negativi.txt \
        -o allegro.gguf -t 4
    ```

    Output atteso (dalla struttura del sorgente; i tempi dipendono dalla macchina):

    ```
    …
    Evaluating prompt[1/5]: "<|im_start|>system…" - "<|im_start|>system…" (N tokens)
    …
    Evaluating prompt[5/5]: … - … (N tokens)
    …
    Added tensor: direction.1
    …
    Added tensor: direction.23
    export_gguf: writing file...
    export_gguf: wrote file 'allegro.gguf'
    ```

    Sono 23 direzioni, non 24: il generatore scarta l'ultimo layer. Se preferisci la media delle differenze alla
    PCA (più rapida, a volte più "docile"): `--method mean`. Per una PCA più lunga: `--pca-iter 2000 --pca-batch 100`
    (le iterazioni devono essere un multiplo del batch).

3. **Ispeziona il GGUF.** È un normale file GGUF con architettura `controlvector`:

    ```bash
    python3 -m gguf.scripts.gguf_dump allegro.gguf | head -20      # oppure: gguf-dump allegro.gguf
    ```
    ```
    * File is LITTLE endian, script is running on a LITTLE endian host.
    * Dumping 3 key/value pair(s)
          1: STRING     |        1 | general.architecture = 'controlvector'
          2: STRING     |        1 | controlvector.model_hint = 'qwen35'
          3: INT32      |        1 | controlvector.layer_count = 23
    * Dumping 23 tensor(s)
          1:       1024 |  1024,     1,     1,     1 | F32     | direction.1
          …
    ```

    `model_hint` è l'architettura del modello usato per generarlo: il vettore vale per Qwen3.5-0.8B in qualsiasi
    quantizzazione, **non** per un altro modello. Ogni `direction.N` ha `n_embd = 1024` valori.

4. **Risposta di riferimento, senza vettore.** Usa `-rea off` (Qwen3.5 altrimenti "pensa"), temperatura 0 per
    confronti riproducibili e una domanda neutra:

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata."
    ```

5. **Applica il vettore in positivo.** Scala 0,8 sui layer dal 10 al 23 (il README consiglia i layer sopra il 10):

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata." \
        --control-vector-scaled allegro.gguf:0.8 --control-vector-layer-range 10 23
    ```

    Atteso: stesso prompt, stesso seme, ma un testo più entusiasta ("splendida", "energia", esclamativi). Se il testo
    degenera in ripetizioni, abbassa la scala a 0,4-0,5.

6. **Applica il vettore in negativo.** La stessa direzione con segno opposto spinge verso i prompt negativi:

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata." \
        --control-vector-scaled allegro.gguf:-0.8 --control-vector-layer-range 10 23
    ```

7. **Esplora scala e layer.** Compila una tabella con almeno sei combinazioni:

    | scala | layer | osservazione |
    |---|---|---|
    | 0,4 | 10-23 | |
    | 0,8 | 10-23 | |
    | 1,5 | 10-23 | |
    | 0,8 | 0-23 | |
    | 0,8 | 16-23 | |
    | −0,8 | 10-23 | |

    Noterai che dai layer bassi (`0-23`) il testo perde coerenza prima di cambiare tono, e che oltre una certa
    scala il modello si blocca su poche parole. `--control-vector allegro.gguf` (senza scala) equivale a scala 1.

8. **Nel server.** Le stesse opzioni valgono per `llama serve`, così il tono vale per tutte le richieste:

    ```bash
    llama serve -m "$M" --port 18104 --control-vector-scaled allegro.gguf:0.6 --control-vector-layer-range 10 23
    ```

    Il vettore è fisso per tutta la vita del processo: non c'è un campo per richiesta (a differenza degli adapter
    LoRA, gestiti da `/lora-adapters`).

## Verifica del risultato

- [ ] `allegro.gguf` esiste, ha `controlvector.model_hint = 'qwen35'` e 23 tensori `direction.N` da 1024 valori.
- [ ] Con scala +0,8 il testo è visibilmente più allegro di quello di riferimento; con −0,8 più cupo; con temperatura 0
      le tre risposte sono riproducibili a ogni esecuzione.
- [ ] Hai trovato una scala oltre la quale il testo degenera e sai indicarla.

## Domande e varianti

1. Perché le risposte nei prompt vengono lasciate a metà frase invece di essere complete?
2. Cosa cambia tra `--method pca` e `--method mean` nel modo in cui si ottiene la direzione di ogni layer?
3. Perché applicare il vettore dai layer bassi rovina la coerenza mentre nei layer alti cambia il tono?
4. Variante: genera un secondo vettore "formale ↔ colloquiale" con 5 nuove coppie e applica **entrambi** in una sola
   riga (`--control-vector-scaled allegro.gguf:0.6,formale.gguf:0.6`). Si sommano in modo sensato?
5. Variante: genera il vettore dal Q4_0 dello stesso repository (`llama download -hf ggml-org/Qwen3.5-0.8B-GGUF:Q4_0`)
   e applicalo al Q8_0: funziona? Cosa dice `model_hint`?
6. Variante (avanzata): 5 coppie sono poche. Portale a 20-30 variando il messaggio utente e confronta la stabilità
   del risultato a parità di scala.

## Consegna

- `positivi.txt` e `negativi.txt` (eventualmente ampliati) e l'output di `gguf_dump` del vettore generato.
- Le tre risposte del passo 4-6 (riferimento, +0,8, −0,8) allo stesso prompt.
- La tabella del passo 7 compilata, con la scala "di rottura" trovata e le risposte alle domande 1-3.
