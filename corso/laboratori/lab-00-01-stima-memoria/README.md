# Lab 00-01: Stimare la memoria di un modello

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/00-introduzione/README.md">00: Introduzione a llama.cpp</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
</div>

## Obiettivo

Calcolare, prima a mano e poi con lo script [`stima_memoria.py`](stima_memoria.py), la memoria necessaria a
tre modelli in tre quantizzazioni e con contesti diversi; poi confrontare la stima con il valore reale che
llama.cpp scrive nel log. Alla fine sai rispondere a "ci sta sul mio computer?" senza scaricare nulla.

## Prerequisiti

- Aver letto la sezione 5 del modulo 00 (formula pesi + KV cache + overhead).
- Python 3.8 o più recente (solo libreria standard, nessun `pip install`).
- Per il passo 5 (facoltativo): llama.cpp installato (modulo 01) e il modello di prova in cache.

## Materiale

| Cosa | Dove | Note |
|---|---|---|
| `stima_memoria.py` | in questa cartella | script con formule, preset e nomi delle quantizzazioni |
| Metadati dei modelli | pagina Hugging Face del GGUF o `gguf-dump` (lab 00-02) | servono `block_count`, `head_count_kv`, `key_length` |
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf`, 785 MiB, Apache-2.0 | solo per il confronto finale |

I preset già dentro lo script (parametri letti dai metadati GGUF):

| Preset | Parametri | Layer con KV | Teste KV | head_dim |
|---|---|---|---|---|
| `qwen3.5-0.8b` | 0,77 B | 6 (ibrido: 25 blocchi, 1 su 4 con attenzione) | 2 | 256 |
| `qwen3-8b` | 8,19 B | 36 | 8 | 128 |
| `llama-3.1-8b` | 8,03 B | 32 | 8 | 128 |
| `qwen3-32b` | 32,8 B | 64 | 8 | 128 |
| `llama-3.3-70b` | 70,6 B | 80 | 8 | 128 |

## Procedura

### 1. A mano: i pesi

Per ciascuno dei tre modelli `qwen3-8b`, `qwen3-32b`, `llama-3.3-70b` calcola i pesi in Q8_0 (8,5 bit),
Q4_K_M (4,85 bit) e Q2_K (2,63 bit) con `parametri × bit / 8`, e converti in GiB (÷ 1024³). Compila la
tabella:

| Modello | Q8_0 | Q4_K_M | Q2_K |
|---|---|---|---|
| Qwen3-8B (8,19 B) | | | |
| Qwen3-32B (32,8 B) | | | |
| Llama 3.3 70B (70,6 B) | | | |

### 2. A mano: la KV cache

Per Qwen3-8B calcola la KV cache in F16 (2 byte) a 4 096, 8 192 e 32 768 token:

```text
KV = 2 × 36 × 8 × 128 × ctx × 2 byte
```

Poi rifai il calcolo a 32 768 token con la cache quantizzata `q8_0` (8,5 bit = 1,0625 byte per elemento).

### 3. Con lo script

```bash
cd corso/laboratori/lab-00-01-stima-memoria
python3 stima_memoria.py --lista-preset
python3 stima_memoria.py --preset qwen3-8b --quant q4_k_m --ctx 8192
```

Output atteso:

```text
Modello: qwen3-8b  attention piena su tutti i layer, GQA 8 teste KV
  parametri = 8.19 B, 4.85 bit/peso; layer con KV = 36, kv_heads = 8, head_dim = 128
  contesto  = 8192 token x 1 slot = 8192 token, KV cache f16 (16.0 bit/elemento)

  pesi             4.62 GiB   = 8.19e+09 x 4.85 / 8
  KV cache         1.12 GiB   = 2 x 36 x 8 x 128 x 8192 x 2
  overhead          474 MiB   (stima: max(10 % dei pesi, 300 MiB))
  -------------------------
  TOTALE stimato   6.21 GiB

  KV cache per token: 144.0 KiB  ->  1 GiB di KV basta per circa 7.281 token
```

Ripeti con `--quant q8_0`, `--quant q2_k`, con `--ctx 32768 --kv-type q8_0` e con `--slots 4` (simula
`llama serve -np 4`). Confronta con i tuoi calcoli a mano del passo 1 e 2: devono coincidere.

### 4. Un modello a tua scelta

Prendi un GGUF che ti interessa su Hugging Face, apri la scheda *Files* → clicca sul file `.gguf`: il viewer
mostra i metadati. Cerca `block_count`, `attention.head_count_kv`, `attention.key_length` e il numero di
parametri, poi lancia lo script senza preset:

```bash
python3 stima_memoria.py --params 7.6e9 --quant q4_k_m --ctx 8192 \
    --layers 28 --kv-heads 4 --head-dim 128
```

!!! note "Modelli ibridi e a finestra scorrevole"
    Se i metadati contengono `full_attention_interval` (Qwen3.5, Qwen3-Next) o `sliding_window` (Gemma 3),
    la formula sopravvaluta: i blocchi SSM non hanno KV cache e i blocchi a finestra la limitano a
    `sliding_window` token. Per Qwen3.5 usa `--layers block_count / full_attention_interval`.

### 5. Confronto con il valore reale (se hai già llama.cpp)

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt   # solo Linux + installer
llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -c 4096 -st -p "ciao" -n 1 -rea off -v 2>&1 \
  | grep -E "llama_kv_cache: size|memory_recurrent: size|compute buffer|memory breakdown|Host"
```

Output (build 11046, CPU):

```text
llama_kv_cache: size =   48.00 MiB (  4096 cells,   6 layers,  1/1 seqs), K (f16):   24.00 MiB, V (f16):   24.00 MiB
llama_memory_recurrent: size =   19.27 MiB (     1 cells,  24 layers,  1 seqs  0 rs_seq), R (f32): 1.27 MiB, S (f32): 18.00 MiB, P (f32): 0.00 MiB
sched_reserve:        CPU compute buffer size =    46.16 MiB
common_memory_breakdown_print: | memory breakdown [MiB] | total   free    self   model   context   compute    unaccounted |
common_memory_breakdown_print: |   - Host               |                  877 =   763 +      67 +      46                |
```

Confronta con `python3 stima_memoria.py --preset qwen3.5-0.8b --quant q8_0 --ctx 4096`: pesi 783 MiB (log:
763 di modello + una parte "unaccounted"), KV cache **48 MiB esatti**, overhead stimato 300 MiB contro 46 di
buffer di calcolo + 19 di stato ricorrente. La stima è prudente: è quello che vuoi.

## Verifica del risultato

- [ ] La tabella dei pesi è compilata: Qwen3-8B Q4_K_M ≈ 4,6 GiB, Qwen3-32B Q4_K_M ≈ 18,5 GiB, Llama 70B Q4_K_M ≈ 40 GiB.
- [ ] La KV cache di Qwen3-8B a 32 768 token in F16 è 4,5 GiB e in q8_0 circa 2,4 GiB.
- [ ] I numeri dello script coincidono con i calcoli a mano (differenze solo di arrotondamento).
- [ ] Il valore `llama_kv_cache: size` nel log coincide con la formula per il modello di prova.

## Domande e varianti

1. Con 16 GiB di RAM e senza GPU, qual è il modello più grande che puoi far girare in Q4_K_M con 8k di
   contesto, lasciando 4 GiB al sistema? E con la KV cache in q8_0?
2. Hai una GPU da 8 GiB di VRAM: Qwen3-8B Q4_K_M ci sta con 4k di contesto? E con 16k? Che cosa faresti
   (contesto, `-ctk/-ctv`, `-ngl` parziale)?
3. Un server con `-np 8` e `-c 65536`: quanta KV cache F16 per Llama 3.1 8B? Perché `--kv-unified`
   (visto nel modulo 04) può cambiare l'occupazione?
4. Variante: aggiungi allo script un preset per un modello MoE (es. 30 B totali, 3 B attivi). Nota che la
   memoria dipende dai parametri **totali**, non da quelli attivi: perché?
5. Variante: modifica `overhead_pct` e `overhead_min` in `stima()` e osserva quanto pesa l'ipotesi sui
   modelli piccoli rispetto a quelli da 70 B.

## Consegna

Un file `stima.md` (o un foglio di calcolo) con: la tabella 3 modelli × 3 quantizzazioni, la KV cache di
Qwen3-8B ai tre contesti, la stima per il modello che hai scelto tu con i metadati da cui hai preso i
numeri, e, se hai fatto il passo 5, le righe del log accanto alla stima con un commento sulle differenze.
