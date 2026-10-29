# Lab 00-01: Estimating the memory of a model

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/00-introduzione/README.md">00: Introduction to llama.cpp</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Calculate, first by hand and then with the [`stima_memoria.py`](stima_memoria.py) script, the memory needed by
three models in three quantizations and with different contexts; then compare the estimate with the real value
llama.cpp writes in its log. At the end you can answer "does it fit on my computer?" without downloading anything.

## Prerequisites

- You have read section 5 of module 00 (formula: weights + KV cache + overhead).
- Python 3.8 or newer (standard library only, no `pip install`).
- For step 5 (optional): llama.cpp installed (module 01) and the test model in the cache.

## Materials

| What | Where | Notes |
|---|---|---|
| `stima_memoria.py` | in this folder | script with formulas, presets and quantization names |
| Model metadata | Hugging Face page of the GGUF or `gguf-dump` (lab 00-02) | you need `block_count`, `head_count_kv`, `key_length` |
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf`, 785 MiB, Apache-2.0 | only for the final comparison |

The presets already in the script (parameters read from the GGUF metadata):

| Preset | Parameters | Layers with KV | KV heads | head_dim |
|---|---|---|---|---|
| `qwen3.5-0.8b` | 0.77 B | 6 (hybrid: 25 blocks, 1 in 4 with attention) | 2 | 256 |
| `qwen3-8b` | 8.19 B | 36 | 8 | 128 |
| `llama-3.1-8b` | 8.03 B | 32 | 8 | 128 |
| `qwen3-32b` | 32.8 B | 64 | 8 | 128 |
| `llama-3.3-70b` | 70.6 B | 80 | 8 | 128 |

## Steps

### 1. By hand: the weights

For each of the three models `qwen3-8b`, `qwen3-32b`, `llama-3.3-70b`, calculate the weights in Q8_0 (8.5 bits),
Q4_K_M (4.85 bits) and Q2_K (2.63 bits) with `parameters × bits / 8`, and convert to GiB (÷ 1024³). Fill in the
table:

| Model | Q8_0 | Q4_K_M | Q2_K |
|---|---|---|---|
| Qwen3-8B (8.19 B) | | | |
| Qwen3-32B (32.8 B) | | | |
| Llama 3.3 70B (70.6 B) | | | |

### 2. By hand: the KV cache

For Qwen3-8B, calculate the KV cache in F16 (2 bytes) at 4,096, 8,192 and 32,768 tokens:

```text
KV = 2 × 36 × 8 × 128 × ctx × 2 byte
```

Then redo the calculation at 32,768 tokens with the quantized `q8_0` cache (8.5 bits = 1.0625 bytes per element).

### 3. With the script

```bash
cd corso/laboratori/lab-00-01-stima-memoria
python3 stima_memoria.py --lista-preset
python3 stima_memoria.py --preset qwen3-8b --quant q4_k_m --ctx 8192
```

Expected output:

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

Repeat with `--quant q8_0`, `--quant q2_k`, with `--ctx 32768 --kv-type q8_0` and with `--slots 4` (simulates
`llama serve -np 4`). Compare with your hand calculations from steps 1 and 2: they must match.

### 4. A model of your choice

Pick a GGUF you are interested in on Hugging Face, open the *Files* tab → click the `.gguf` file: the viewer
shows the metadata. Look for `block_count`, `attention.head_count_kv`, `attention.key_length` and the number of
parameters, then run the script without a preset:

```bash
python3 stima_memoria.py --params 7.6e9 --quant q4_k_m --ctx 8192 \
    --layers 28 --kv-heads 4 --head-dim 128
```

!!! note "Hybrid and sliding-window models"
    If the metadata contain `full_attention_interval` (Qwen3.5, Qwen3-Next) or `sliding_window` (Gemma 3),
    the formula overestimates: SSM blocks have no KV cache, and window blocks limit it to
    `sliding_window` tokens. For Qwen3.5 use `--layers block_count / full_attention_interval`.

### 5. Comparison with the real value (if you already have llama.cpp)

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt   # Linux + installer only
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

Compare with `python3 stima_memoria.py --preset qwen3.5-0.8b --quant q8_0 --ctx 4096`: weights 783 MiB (log:
763 of model + an "unaccounted" part), KV cache **exactly 48 MiB**, estimated overhead 300 MiB versus 46 of
compute buffer + 19 of recurrent state. The estimate is conservative: that is what you want.

## Check

- [ ] The weights table is filled in: Qwen3-8B Q4_K_M ≈ 4.6 GiB, Qwen3-32B Q4_K_M ≈ 18.5 GiB, Llama 70B Q4_K_M ≈ 40 GiB.
- [ ] The Qwen3-8B KV cache at 32,768 tokens is 4.5 GiB in F16 and about 2.4 GiB in q8_0.
- [ ] The script's numbers match the hand calculations (differences only from rounding).
- [ ] The `llama_kv_cache: size` value in the log matches the formula for the test model.

## Questions and variations

1. With 16 GiB of RAM and no GPU, what is the largest model you can run in Q4_K_M with 8k of
   context, leaving 4 GiB to the system? And with the KV cache in q8_0?
2. You have a GPU with 8 GiB of VRAM: does Qwen3-8B Q4_K_M fit with 4k of context? And with 16k? What would you do
   (context, `-ctk/-ctv`, partial `-ngl`)?
3. A server with `-np 8` and `-c 65536`: how much F16 KV cache for Llama 3.1 8B? Why can `--kv-unified`
   (seen in module 04) change the usage?
4. Variation: add a preset to the script for a MoE model (e.g. 30 B total, 3 B active). Note that
   memory depends on the **total** parameters, not the active ones: why?
5. Variation: change `overhead_pct` and `overhead_min` in `stima()` and observe how much the assumption weighs on
   small models compared with 70 B ones.

## Deliverable

A `stima.md` file (or a spreadsheet) with: the 3 models × 3 quantizations table, the Qwen3-8B KV cache at the
three contexts, the estimate for the model you chose with the metadata you took the numbers from,
and, if you did step 5, the log lines next to the estimate with a comment on the differences.
