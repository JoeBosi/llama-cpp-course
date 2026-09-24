# Lab 03-03: Quantizzazione con imatrix

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/03-modelli-gguf-quantizzazione/README.md">03: Modelli, GGUF e quantizzazione</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
<span class="stato stato-verificato">verificato su b11046</span>
</div>

## Obiettivo

Calcolare una **matrice di importanza** con `llama-imatrix` su un testo italiano, usarla per produrre un `Q2_K` e
confrontarlo con il `Q2_K` "cieco" del [lab 03-02](../lab-03-02-scala-quantizzazioni/README.md) con perplexity e
**KL-divergence** rispetto al `Q8_0`. Capirai perché sotto i 4 bit l'imatrix non è un'opzione, e come si legge un
report di KL-divergence.

## Prerequisiti

- Lab 03-02 completato: `~/llama-lab/quant/Qwen3.5-0.8B-Q2_K.gguf` presente (o rifallo: 1 minuto).
- Il **tarball della release** scompattato (`llama-imatrix` non è nel binario `llama`), ad esempio
  `~/llama-lab/rel/llama-b11046/` ([lab 01-01](../lab-01-01-binari-precompilati/README.md)).
- ~1 GB di disco e ~2 GB di RAM libera.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `Qwen3.5-0.8B-Q8_0.gguf` (cache HF): sorgente e riferimento | `~/.cache/huggingface/hub/…` | 785 MiB |
| `Qwen3.5-0.8B-Q2_K.gguf` senza imatrix | `~/llama-lab/quant/` (lab 03-02) | 410 MiB |
| [`calibrazione-it.txt`](calibrazione-it.txt): 430 parole di italiano su argomenti vari (bicicletta, cucina, …) | in questa cartella | 2,6 KB |
| `testo-it.txt` del lab 03-02: il testo di **valutazione**, diverso da quello di calibrazione | [`../lab-03-02-scala-quantizzazioni/testo-it.txt`](../lab-03-02-scala-quantizzazioni/testo-it.txt) | 2,5 KB |

Calibrazione e valutazione devono essere testi **diversi**, altrimenti misuri quanto il modello ha "imparato" il
testo di calibrazione. Entrambi sono minuscoli per far durare il lab pochi minuti: i quantizzatori pubblici usano
centinaia di KB misti (Wikitext, codice, più lingue).

## Procedura

1. **Variabili e controllo degli strumenti**:

    ```bash
    SRC=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    REL=~/llama-lab/rel/llama-b11046
    Q=~/llama-lab/quant
    TESTO=../lab-03-02-scala-quantizzazioni/testo-it.txt
    $REL/llama-imatrix --help | head -3
    ```

2. **Calcola la imatrix** sul testo di calibrazione (in un caso reale: modello F16, `-c 512` o più, `-ngl 99`):

    ```bash
    $REL/llama-imatrix -m $SRC -f calibrazione-it.txt -o $Q/imatrix-it.gguf -c 128 -t 4
    ```

    Verificato (20 s, 3 thread):

    ```text
    compute_imatrix: tokenizing the input ..
    compute_imatrix: tokenization took 79.709 ms
    compute_imatrix: computing over 4 chunks, n_ctx=128, batch_size=2048, n_seq=16
    compute_imatrix: 17.34 seconds per pass - ETA 0.07 minutes
    [1]14.9594,[2]10.8089,[3]11.4033,[4]12.8878,
    Final estimate: PPL = 12.8878 +/- 1.90874
    ```

    Il programma stampa anche la perplexity del testo di calibrazione (è un sottoprodotto: `--no-ppl` per saltarla).
    Il file `imatrix-it.gguf` pesa 1,1 MB: contiene, per 186 tensori, un vettore di importanza per colonna.

3. **Guarda dentro** con `--show-statistics` (serve anche `-m`):

    ```bash
    $REL/llama-imatrix -m $SRC --in-file $Q/imatrix-it.gguf --show-statistics 2>&1 | grep -v " I \| W " | head -30
    ```

    Atteso: `Computing statistics for … (186 tensors)` e una tabella `Layer | Tensor | Σ(Act²) | Min | Max | μ | σ | % Active | N | Entropy | E (norm) | ZD | CosSim`.
    Cerca i tensori con `% Active` basso (colonne quasi mai usate dal testo: lì la quantizzazione può essere
    aggressiva) e confronta `Σ(Act²)` fra `attn_qkv`, `ffn_down`, `ffn_up` dello stesso strato.

4. **Quantizza `Q2_K` con l'imatrix**:

    ```bash
    llama quantize --allow-requantize --imatrix $Q/imatrix-it.gguf $SRC $Q/Qwen3.5-0.8B-Q2_K-imat.gguf Q2_K 4 2>&1 | tail -4
    ls -la $Q/*.gguf
    ```

    Verificato: stessa dimensione del `Q2_K` cieco a meno di 256 byte di metadati (429 768 736 contro 429 768 480:
    la imatrix cambia i **valori** quantizzati, non il formato) e, nel log:

    ```text
    load_imatrix: imatrix datasets=['…/calibrazione-it.txt']
    load_imatrix: loaded 186 importance matrix entries from …/imatrix-it.gguf computed on 4 chunks
    prepare_imatrix: have 186 importance matrix entries
    llama_model_quantize_impl: quant size  =   399.40 MiB (4.34 BPW)
    ```

5. **Perplexity dei tre file** sul testo di valutazione:

    ```bash
    for f in $SRC $Q/Qwen3.5-0.8B-Q2_K.gguf $Q/Qwen3.5-0.8B-Q2_K-imat.gguf; do
      echo "== $(basename $f)"; llama perplexity -m $f -f $TESTO -c 128 -t 4 2>&1 | grep Final
    done
    ```

    Verificato:

    | File | PPL |
    |---|---|
    | `Q8_0` (riferimento) | 11,50 ± 1,81 |
    | `Q2_K` senza imatrix | 154,89 ± 30,39 |
    | `Q2_K` **con** imatrix | **34,09** ± 6,08 |

    Da ×13 a ×3 rispetto al riferimento: 430 parole di calibrazione bastano a cambiare la classe di qualità del file.
    (Resta un pessimo modello: 0,8 B a 2 bit non si salva. Su un 70 B lo stesso passaggio porta `IQ2_M` a un livello usabile.)

6. **KL-divergence**. Prima salva i logit del riferimento, poi confronta:

    ```bash
    llama perplexity -m $SRC -f $TESTO -c 128 -t 4 --kl-divergence-base $Q/base.kld 2>&1 | grep Final
    ls -la $Q/base.kld       # 125 MB: 512 token × 248 320 logit a 16 bit
    for f in Q2_K Q2_K-imat; do
      echo "== $f"; llama perplexity -m $Q/Qwen3.5-0.8B-$f.gguf -f $TESTO -c 128 -t 4 --kl-divergence-base $Q/base.kld --kl-divergence 2>&1 | grep -E "Mean|RMS|Same top"
    done
    ```

    Verificato:

    | Misura | `Q2_K` | `Q2_K` + imatrix | (`Q4_K_M`, per confronto) |
    |---|---|---|---|
    | Mean PPL(Q)/PPL(base) | 13,47 | 2,96 | 1,087 |
    | **Mean KLD** | 2,356 | 0,834 | 0,074 |
    | Mean Δp | −23,6 % | −13,4 % | −2,1 % |
    | Same top p | – | – | 85,3 % |

    Leggi il report completo: oltre alla media ci sono i percentili della KLD e di Δp. Se i percentili di Δp sono
    simmetrici (tanto positivi quanto negativi) la quantizzazione aggiunge rumore; se i negativi dominano, come qui,
    il modello sta peggiorando davvero.

7. **Pulisci**: `rm $Q/base.kld` (125 MB) e i GGUF che non ti servono più; tieni `imatrix-it.gguf` (1 MB) per le varianti.

## Verifica del risultato

- [ ] `imatrix-it.gguf` esiste, pesa ~1 MB e `--show-statistics` elenca 186 tensori.
- [ ] I due `Q2_K` hanno la stessa dimensione ma perplexity 155 contro 34.
- [ ] Hai un report di KL-divergence e sai dire cosa sono KLD, Δp e "Same top p".
- [ ] Sai spiegare perché calibrazione e valutazione devono essere testi diversi.

## Domande e varianti

- Ricalcola l'imatrix con un testo **inglese** (o di codice) e riquantizza: la PPL sul testo italiano migliora o peggiora?
  È la prova che il corpus di calibrazione deve somigliare all'uso.
- Unisci due imatrix (`--in-file a.gguf --in-file b.gguf -o c.gguf`) e confronta.
- `Q4_K_M` con e senza imatrix: qui il guadagno è piccolo (nella tabella del modulo, su Llama-3-8B, KLD 0,031 → 0,028).
  Misuralo: vale la pena?
- `IQ3_M` senza imatrix: in questa build viene prodotto senza errori (verificato: 431 MiB, 4,68 bpw), ma i tipi `IQ`
  sono progettati intorno all'imatrix. Misura la PPL con e senza: lo scarto è molto più grande che per `Q4_K_M`.
- `--include-weights ffn_down --include-weights attn_v`: imatrix solo su alcuni tensori. Cambia qualcosa?
- Variante lunga: `calibration_datav3.txt` di bartowski (pubblico su GitHub) con `-c 512` e il modello F16 del lab 03-01.

## Consegna

`lab-03-03.md` con: le sei righe di output di `llama-imatrix`; le prime 10 righe della tabella `--show-statistics`
con un commento su quale tensore è più "attivo"; la tabella delle tre perplexity; il report KLD dei due `Q2_K` con
una frase di interpretazione per KLD, Δp e percentili; la risposta alla prima domanda (con i numeri).
