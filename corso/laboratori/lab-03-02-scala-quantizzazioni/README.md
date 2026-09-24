# Lab 03-02: La scala delle quantizzazioni

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/03-modelli-gguf-quantizzazione/README.md">03: Modelli, GGUF e quantizzazione</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti (di cui 5-10 di calcolo)</span>
<span class="stato stato-verificato">verificato su b11046</span>
</div>

## Obiettivo

Produrre con `llama quantize` tre quantizzazioni dello stesso modello (`Q4_K_M`, `Q4_0`, `Q2_K`) partendo dal `Q8_0`
già in cache, e misurare per ciascuna **dimensione**, **bit per peso**, **velocità** (`llama bench`) e **perplexity**
su un breve testo italiano. Il risultato è una tabella che mostra dal vivo il compromesso qualità / memoria /
velocità del [modulo 00](../../moduli/00-introduzione/README.md).

## Prerequisiti

- Modello di prova in cache ([lab 02-01](../lab-02-01-primo-modello/README.md)); `llama quantize`, `llama bench`,
  `llama perplexity` funzionanti (`llama help all` li elenca).
- ~2 GB liberi su disco per i tre file (ognuno 400-550 MB) e ~2 GB di RAM libera.
- Aver letto le sezioni [3](../../moduli/03-modelli-gguf-quantizzazione/README.md#3-le-famiglie-di-quantizzazione) e
  [5](../../moduli/03-modelli-gguf-quantizzazione/README.md#5-misurare-la-qualità-perplexity-e-kl-divergence) del modulo.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF`, `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0): il **sorgente** | cache HF | 785 MiB |
| [`testo-it.txt`](testo-it.txt): 384 parole di italiano generico (caffè, storia, preparazione) | in questa cartella | 2,5 KB |
| [`quantizza-e-misura.sh`](quantizza-e-misura.sh): quantizza, misura e scrive `risultati.md` | in questa cartella | – |

Partiamo da un `Q8_0` e non da un F16 per non scaricare 1,5 GB: `Q8_0` è quasi lossless (+0,003 di perplexity su un
8 B), quindi l'esperimento resta valido. `llama quantize` però lo rifiuta di default: serve `--allow-requantize`.

## Procedura

1. **Trova il sorgente e prova `--dry-run`**:

    ```bash
    SRC=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    mkdir -p ~/llama-lab/quant
    llama quantize --dry-run $SRC Q4_K_M 2>&1 | tail -4
    ```

    Verificato (0,6 s):

    ```text
    llama_model_quantize_impl: model size  =   784.52 MiB (8.52 BPW)
    llama_model_quantize_impl: quant size  =   506.34 MiB (5.50 BPW)
    ```

    Il dry-run calcola la dimensione finale senza scrivere nulla: comodo per decidere prima di aspettare.

2. **Prima quantizzazione a mano**, per leggere il log:

    ```bash
    llama quantize $SRC ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf Q4_K_M 4 2>&1 | tee ~/llama-lab/quant/quant-Q4_K_M.log | tail -5
    ```

    Verificato: senza `--allow-requantize` si ferma subito con
    `llama_model_quantize: failed to quantize: requantizing from type q8_0 is disabled`. Aggiungilo:

    ```bash
    llama quantize --allow-requantize $SRC ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf Q4_K_M 4 2>&1 | tee ~/llama-lab/quant/quant-Q4_K_M.log | tail -5
    ```

    Ora scorrono 335 righe, una per tensore. Cerca nel log (`grep -E "token_embd|blk.0\." …`) e osserva il **mix**:
    `token_embd.weight … converting to q6_K`, `blk.0.attn_qkv.weight → q6_K`, `blk.0.ffn_down.weight → q6_K`,
    `blk.0.ffn_gate.weight → q4_K`, le `*_norm.weight` restano `f32`. In coda: `model size = 784.52 MiB (8.52 BPW)`,
    `quant size = 506.34 MiB (5.50 BPW)`, tempo 20-60 s.

3. **Tutto il resto con lo script**, che quantizza ogni tipo, poi misura con `llama bench -p 32 -n 16 -t 3 -r 1` e
   `llama perplexity -c 128` sul testo italiano (un processo alla volta):

    ```bash
    bash quantizza-e-misura.sh $SRC Q4_K_M Q4_0 Q2_K          # T=4 bash … per usare 4 thread
    cat ~/llama-lab/quant/risultati.md
    ```

    Risultato verificato sulla macchina del corso (6 vCPU condivise, 3 thread, quindi velocità **indicative**):

    | Tipo | MiB | bpw | pp32 t/s | tg16 t/s | PPL (`-c 128`, 4 blocchi) |
    |---|---|---|---|---|---|
    | `Q8_0` (sorgente) | 795 | 8,52 | 39,7 | 10,6 | 11,50 ± 1,81 |
    | `Q4_K_M` | 517 | 5,50 | 53,8 | 7,2 | 12,50 ± 1,97 |
    | `Q4_0` | 490 | 5,20 | 38,9 | 13,5 | 14,66 ± 2,34 |
    | `Q2_K` | 410 | 4,34 | 41,0 | 8,3 | **154,9** ± 30,4 |

    (Il totale dura circa 4 minuti; i MiB sono di `du`, quindi leggermente diversi dai MiB "del modello" nel log.)

4. **Leggi la tabella**:

    - **Dimensione**: da 795 a 410 MiB, ma non "8 bit → 2 bit = un quarto": l'embedding da 248 320 × 1 024 resta a
      6 bit e da solo pesa 200 MiB. Su un 8 B (vocabolario proporzionalmente piccolo) `Q2_K` sarebbe 2,96 GB contro
      7,96 di `Q8_0`.
    - **Perplexity**: `Q4_K_M` +9 % (accettabile), `Q4_0` +28 % (si sente), `Q2_K` ×13 (inutilizzabile). Con 4 blocchi
      di 128 token le barre d'errore sono grandi, ma l'ordine è lo stesso che vedresti su Wikitext. Un modello da 0,8 B
      soffre i pochi bit molto più di un 8 B (tabella del modulo: `Q2_K` su Llama-3-8B è +3,5, cioè +60 %).
    - **Velocità**: su questa macchina condivisa i numeri ballano (ripetendo il bench il `Q4_0` è andato da 13 a 16 t/s
      e il `Q8_0` da 1,7 a 10,6). Su una macchina tranquilla ti aspetti: generazione più veloce quanto più il file è
      piccolo (banda di memoria) e `Q4_0` particolarmente rapido grazie al *repacking* dei kernel CPU; prompt processing
      meno sensibile al tipo. Ripeti con `-r 5` e `-t` = core fisici per numeri stabili ([modulo 05](../../moduli/05-prestazioni/README.md#2-misurare-llama-bench)).

5. **Prova con le mani**. Stessa domanda a `--temp 0` ai quattro file:

    ```bash
    for f in $SRC ~/llama-lab/quant/*.gguf; do echo "== $f"; llama cli -m $f -st -rea off --temp 0 -n 40 -t 4 -p "Elenca tre città italiane sul mare." 2>&1 | sed -n '/^> /,/Prompt:/p'; done
    ```

    Il `Q2_K` di solito produce testo sconnesso o ripetitivo; `Q4_0` e `Q4_K_M` risposte plausibili; confronta con il `Q8_0`.

6. **Pulisci**. Tieni solo ciò che serve al [lab 03-03](../lab-03-03-imatrix/README.md) (il `Q2_K`), cancella il resto:

    ```bash
    rm ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf ~/llama-lab/quant/Qwen3.5-0.8B-Q4_0.gguf
    ```

## Verifica del risultato

- [ ] `--dry-run` ha previsto 506,34 MiB e il file `Q4_K_M` reale li conferma (`5.50 BPW` nel log).
- [ ] Sai spiegare, dal log, perché `Q4_K_M` non è "tutto a 4 bit".
- [ ] `risultati.md` ha quattro righe con MiB, bpw, pp, tg e PPL.
- [ ] Le perplexity crescono nell'ordine `Q8_0 < Q4_K_M < Q4_0 << Q2_K`.
- [ ] Hai visto con i tuoi occhi la differenza di qualità del `Q2_K`.

## Domande e varianti

- Perché il primo tentativo senza `--allow-requantize` è stato rifiutato, e perché la documentazione sconsiglia
  comunque di requantizzare?
- Quantizza con `--pure` (`Q4_K_M --pure`) e confronta bpw e perplexity: quanto vale il mix?
- Aggiungi `Q6_K`, `Q5_K_M`, `Q3_K_M`, `IQ4_XS` alla lista dello script (attenzione allo spazio su disco: ~500 MB ciascuno).
- `--token-embedding-type q4_0 --output-tensor-type q4_0` su `Q4_K_M`: quanti MiB risparmi e quanto costa in PPL?
  Su questo modello l'embedding è metà del file: è il caso in cui la scelta pesa di più.
- Variante lunga: scarica Wikitext-2 (`scripts/get-wikitext-2.sh` dei sorgenti) e misura la PPL "vera" con `-c 512`
  su un modello che ti interessa (ore su CPU: fallo di notte, o con GPU).

## Consegna

`risultati.md` prodotto dallo script, più: le 6 righe di log del punto 2 che mostrano il mix; le quattro risposte del
punto 5; un paragrafo che dica quale dei quattro file useresti su un telefono con 2 GB liberi, quale su un portatile,
e perché.
