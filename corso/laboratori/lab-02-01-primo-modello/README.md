# Il primo modello

> Modulo: [02: Primi passi: `llama cli`](../../moduli/02-primi-passi/README.md) · <span class="stato stato-verificato">verificato su b11046</span> · Durata stimata: 40 minuti

## Obiettivo

Scaricare il modello di prova del corso da Hugging Face, trovarlo nella cache, chattare con `llama cli`
usando i comandi interni, dare un prompt di sistema, fare una domanda "usa e getta" da script, leggere il
banner e la riga dei tempi, e trovare nel log verbose le righe che descrivono memoria, template e sampler.

## Prerequisiti

- `llama` installato e `llama version` funzionante ([modulo 01](../../moduli/01-installazione/README.md)).
- Connessione internet per il primo download (785 MiB) e ~1,5 GB di RAM libera.
- Ubuntu con binario dell'installer: `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF`, file `Qwen3.5-0.8B-Q8_0.gguf`, licenza Apache 2.0 | Hugging Face, via `-hf` | 785 MiB |
| Un file di testo qualsiasi (una pagina di appunti, un README) per `/read` | tuo | pochi KB |

## Procedura

1. **Scarica e avvia**. La prima volta vedrai la barra di download, poi `Loading model...` e il banner:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF
    ```

    ```text
    build      : b11046-60081bb2b
    model      : ggml-org/Qwen3.5-0.8B-GGUF
    ftype      : Q8_0
    modalities : text
    ```

    Annota build, ftype e modalità. Chiedi «Chi sei?» e osserva: il modello prima **pensa** (`[Start thinking]`),
    poi risponde. Esci con `/exit`.

2. **Trova il file nella cache** e verifica che `-cl` lo elenchi:

    ```bash
    llama cli -cl
    ls -la ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/
    du -sh ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF
    ```

    Atteso: `1. ggml-org/Qwen3.5-0.8B-GGUF:Q8_0`; nello snapshot un link simbolico `Qwen3.5-0.8B-Q8_0.gguf -> ../../blobs/37ae48…`;
    785 MiB in totale. Da ora in poi `-hf` non scarica più nulla (`--offline` per esserne certi).

3. **Chat senza ragionamento, con i comandi interni**:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -rea off -c 4096 -t 4     # -t: i tuoi core fisici
    ```

    - Chiedi «Spiega in una frase cos'è un token» e annota la riga `[ Prompt: … | Generation: … ]`.
      Verificato: il modello risponde parlando di token *crittografici*, non linguistici. È normale per 0,8 B di
      parametri senza contesto: lo sistemiamo al punto 5.
    - `/regen`: la risposta cambia? (Il seed è casuale: sì, quasi sempre.)
    - `/read appunti.txt` seguito da «Riassumi il file in tre punti»: il contenuto entra nel messaggio.
    - `/clear` poi «Di cosa stavamo parlando?»: la cronologia è sparita.
    - `/exit`.

4. **Domanda usa e getta da script** (`-st -p`), salvando l'output:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Quanto fa 17 per 3? Solo il numero." -n 30 -rea off -t 4
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Quanto fa 17 per 3?" -n 40 -t 4      # thinking acceso
    ```

    Atteso: il primo comando stampa la risposta ed esce (`Exiting...`); il secondo consuma i 40 token dentro
    `[Start thinking]` e non risponde (verificato). Riprova con `--reasoning-budget 25`: il pensiero viene
    troncato con `[End thinking]` e arriva una risposta.

5. **Prompt di sistema**. Ripeti la domanda sul token con un contesto:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 60 \
      -sys "Sei un esperto di modelli linguistici (LLM). Rispondi in italiano, in una frase." \
      -p "Cos'è un token?"
    ```

    Verificato: «Un token è una parte dell'input dell'LLM, che rappresenta una parte della sequenza dei caratteri.»
    Stesso modello, stessa domanda, risposta giusta: il prompt di sistema conta più di quanto sembri.

6. **Log verbose**. Lancia una domanda brevissima con `-v` e salva il log:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao" -n 5 -rea off -t 4 -c 4096 -v 2> log.txt
    grep -E "system_info|file type|n_ctx_train|model params|llama_kv_cache: size|memory breakdown|Host|chat template, thinking|sampler chain" log.txt
    ```

    Atteso (valori della macchina di prova):

    ```text
    system_info: n_threads = 4 (n_threads_batch = 4) / 6 | CPU : … AVX2 = 1 …
    print_info: file type   = Q8_0
    print_info: n_ctx_train           = 262144
    print_info: model params          = 772.85 M
    llama_kv_cache: size =   48.00 MiB (  4096 cells,   6 layers, …)
    common_memory_breakdown_print: |   - Host  |  877 =   763 +      67 +      46   |
    init: chat template, thinking = 0
    sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
    ```

    Confronta i 48 MiB di KV cache con la formula del [modulo 00](../../moduli/00-introduzione/README.md#5-stimare-la-memoria-pesi-kv-cache-overhead)
    e gli 877 MiB totali con la RAM libera (`free -m`).

7. **Thread e velocità**. Ripeti il punto 4 (prima variante) con `-t 1`, `-t 2`, `-t` = core fisici, `-t` = core
   logici, e annota `Generation` per ciascuno. Di solito il massimo è ai core fisici; oltre, peggiora.

## Verifica del risultato

- [ ] `llama cli -cl` elenca `ggml-org/Qwen3.5-0.8B-GGUF:Q8_0` e sai indicare il percorso del blob.
- [ ] Hai usato `/regen`, `/read`, `/clear` e sai cosa cambia nel contesto con ognuno.
- [ ] Con `-n 40` e thinking acceso non hai avuto risposta; con `-rea off` o `--reasoning-budget` sì.
- [ ] Nel log verbose hai trovato memoria totale (`Host`), KV cache, `thinking = 0` e la catena dei sampler.
- [ ] Hai una tabella thread → token/s.

## Domande e varianti

- Perché il download di `-hf ggml-org/Qwen3.5-0.8B-GGUF` prende il `Q8_0` e non un `Q4_K_M`? (Guarda l'elenco file del repo.)
- Cosa cambia in `memory breakdown` con `-c 16384`? Calcola prima, poi verifica.
- Variante: `llama cli -hf LiquidAI/LFM2.5-230M-GGUF:Q4_K_M` (146 MiB): confronta banner, velocità e qualità
  delle risposte con Qwen3.5-0.8B.
- Variante multimodale (se hai ≥ 6 GB liberi): `llama cli -hf ggml-org/gemma-3-4b-it-qat-GGUF`, poi `/image foto.jpg`
  e «Descrivi l'immagine»: il banner mostra `modalities: text, vision`.
- Da script: `llama cli … -st -p "$(cat domanda.txt)" -o risposta.txt` e poi `cat risposta.txt`.

## Consegna

Un file `lab-02-01.md` con: il banner; l'output di `llama cli -cl` e il percorso del blob; le due risposte
alla domanda sul token (senza e con prompt di sistema) con le rispettive righe dei tempi; le otto righe di log
del punto 6 commentate in una frase ciascuna; la tabella thread → token/s con una riga di conclusione.
