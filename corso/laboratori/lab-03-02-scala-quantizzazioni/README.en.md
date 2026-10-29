# Lab 03-02: The quantization ladder

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/03-modelli-gguf-quantizzazione/README.md">03: Models, GGUF and quantization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes (5-10 of them computing)</span>
</div>

## Objective

Use `llama quantize` to produce three quantizations of the same model (`Q4_K_M`, `Q4_0`, `Q2_K`) starting from the `Q8_0`
already in cache, and measure for each one **size**, **bits per weight**, **speed** (`llama bench`) and **perplexity**
on a short Italian text. The result is a table that shows live the quality / memory / speed trade-off from
[module 00](../../moduli/00-introduzione/README.md).

## Prerequisites

- Test model in cache ([lab 02-01](../lab-02-01-primo-modello/README.md)); `llama quantize`, `llama bench`,
  `llama perplexity` working (`llama help all` lists them).
- ~2 GB free disk for the three files (400-550 MB each) and ~2 GB of free RAM.
- You have read sections [3](../../moduli/03-modelli-gguf-quantizzazione/README.md#3-the-quantization-families) and
  [5](../../moduli/03-modelli-gguf-quantizzazione/README.md#5-measuring-quality-perplexity-and-kl-divergence) of the module.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF`, `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0): the **source** | HF cache | 785 MiB |
| [`testo-it.txt`](testo-it.txt): 384 words of general Italian (coffee, history, preparation) | in this folder | 2.5 KB |
| [`quantizza-e-misura.sh`](quantizza-e-misura.sh): quantizes, measures and writes `risultati.md` | in this folder | – |

The source is the `Q8_0` already in cache: it is nearly lossless (+0.003 perplexity on an 8 B model) and a correct starting point for a teaching experiment; to publish a model you start from F16. `llama quantize` refuses it by default, though: you need `--allow-requantize`.

## Steps

1. **Find the source and try `--dry-run`**:

    ```bash
    SRC=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    mkdir -p ~/llama-lab/quant
    llama quantize --dry-run $SRC Q4_K_M 2>&1 | tail -4
    ```

    Output (0.6 s):

    ```text
    llama_model_quantize_impl: model size  =   784.52 MiB (8.52 BPW)
    llama_model_quantize_impl: quant size  =   506.34 MiB (5.50 BPW)
    ```

    The dry run computes the final size without writing anything: handy to decide before waiting.

2. **First quantization by hand**, to read the log:

    ```bash
    llama quantize $SRC ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf Q4_K_M 4 2>&1 | tee ~/llama-lab/quant/quant-Q4_K_M.log | tail -5
    ```

    Without `--allow-requantize` it stops right away with
    `llama_model_quantize: failed to quantize: requantizing from type q8_0 is disabled`. Add it:

    ```bash
    llama quantize --allow-requantize $SRC ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf Q4_K_M 4 2>&1 | tee ~/llama-lab/quant/quant-Q4_K_M.log | tail -5
    ```

    Now 335 lines scroll by, one per tensor. Search the log (`grep -E "token_embd|blk.0\." …`) and observe the **mix**:
    `token_embd.weight … converting to q6_K`, `blk.0.attn_qkv.weight → q6_K`, `blk.0.ffn_down.weight → q6_K`,
    `blk.0.ffn_gate.weight → q4_K`, the `*_norm.weight` stay `f32`. At the end: `model size = 784.52 MiB (8.52 BPW)`,
    `quant size = 506.34 MiB (5.50 BPW)`, time 20-60 s.

3. **Everything else with the script**, which quantizes each type, then measures with `llama bench -p 32 -n 16 -t 3 -r 1` and
   `llama perplexity -c 128` on the Italian text (one process at a time):

    ```bash
    bash quantizza-e-misura.sh $SRC Q4_K_M Q4_0 Q2_K          # T=4 bash … to use 4 threads
    cat ~/llama-lab/quant/risultati.md
    ```

    Result on a 6 vCPU machine without GPU, 3 threads (speeds are indicative and depend on the CPU):

    | Type | MiB | bpw | pp32 t/s | tg16 t/s | PPL (`-c 128`, 4 chunks) |
    |---|---|---|---|---|---|
    | `Q8_0` (source) | 795 | 8.52 | 39.7 | 10.6 | 11.50 ± 1.81 |
    | `Q4_K_M` | 517 | 5.50 | 53.8 | 7.2 | 12.50 ± 1.97 |
    | `Q4_0` | 490 | 5.20 | 38.9 | 13.5 | 14.66 ± 2.34 |
    | `Q2_K` | 410 | 4.34 | 41.0 | 8.3 | **154.9** ± 30.4 |

    (The whole run takes about 4 minutes; the MiB come from `du`, so they differ slightly from the "model" MiB in the log.)

4. **Read the table**:

    - **Size**: from 795 to 410 MiB, but not "8 bits → 2 bits = a quarter": the 248,320 × 1,024 embedding stays at
      6 bits and alone weighs 200 MiB. On an 8 B model (proportionally small vocabulary) `Q2_K` would be 2.96 GB against
      7.96 for `Q8_0`.
    - **Perplexity**: `Q4_K_M` +9 % (acceptable), `Q4_0` +28 % (noticeable), `Q2_K` ×13 (unusable). The error bars (± in the log) depend on the number of chunks: with more text they narrow, the order among types does not change. A 0.8 B model
      suffers from few bits much more than an 8 B one (module table: `Q2_K` on Llama-3-8B is +3.5, that is +60 %).
    - **Speed**: with `-r 1` each value is a single measurement: read the speeds in the table as orders of magnitude, do not compare them to the decimal. The trend to read: generation gets faster the
      smaller the file (memory bandwidth) and `Q4_0` is especially fast thanks to *repacking* in the CPU kernels; prompt processing
      is less sensitive to the type. Repeat with `-r 5` and `-t` = physical cores for stable numbers ([module 05](../../moduli/05-prestazioni/README.md#2-measuring-llama-bench)).

5. **Try it hands-on**. Same question at `--temp 0` to the four files:

    ```bash
    for f in $SRC ~/llama-lab/quant/*.gguf; do echo "== $f"; llama cli -m $f -st -rea off --temp 0 -n 40 -t 4 -p "Elenca tre città italiane sul mare." 2>&1 | sed -n '/^> /,/Prompt:/p'; done
    ```

    `Q2_K` usually produces disconnected or repetitive text; `Q4_0` and `Q4_K_M` plausible answers; compare with `Q8_0`.

6. **Clean up**. Keep only what [lab 03-03](../lab-03-03-imatrix/README.md) needs (the `Q2_K`), delete the rest:

    ```bash
    rm ~/llama-lab/quant/Qwen3.5-0.8B-Q4_K_M.gguf ~/llama-lab/quant/Qwen3.5-0.8B-Q4_0.gguf
    ```

## Check the result

- [ ] `--dry-run` predicted 506.34 MiB and the real `Q4_K_M` file confirms it (`5.50 BPW` in the log).
- [ ] You can explain, from the log, why `Q4_K_M` is not "all at 4 bits".
- [ ] `risultati.md` has four rows with MiB, bpw, pp, tg and PPL.
- [ ] Perplexities grow in the order `Q8_0 < Q4_K_M < Q4_0 << Q2_K`.
- [ ] You have seen with your own eyes the quality difference of `Q2_K`.

## Questions and variants

- Why was the first attempt without `--allow-requantize` refused, and why does the documentation advise against
  requantizing anyway?
- Quantize with `--pure` (`Q4_K_M --pure`) and compare bpw and perplexity: how much is the mix worth?
- Add `Q6_K`, `Q5_K_M`, `Q3_K_M`, `IQ4_XS` to the script's list (watch the disk space: ~500 MB each).
- `--token-embedding-type q4_0 --output-tensor-type q4_0` on `Q4_K_M`: how many MiB do you save and what does it cost in PPL?
  On this model the embedding is half the file: this is the case where the choice matters most.
- Long variant: download Wikitext-2 (`scripts/get-wikitext-2.sh` in the sources) and measure the "real" PPL with `-c 512`
  on a model you care about (hours on CPU: run it overnight, or with a GPU).

## Deliverable

`risultati.md` produced by the script, plus: the 6 log lines from step 2 that show the mix; the four answers from
step 5; a paragraph saying which of the four files you would use on a phone with 2 GB free, which on a laptop,
and why.
