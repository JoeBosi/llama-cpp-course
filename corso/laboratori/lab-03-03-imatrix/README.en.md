# Lab 03-03: Quantization with imatrix

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/03-modelli-gguf-quantizzazione/README.md">03: Models, GGUF and quantization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Compute an **importance matrix** with `llama-imatrix` on an Italian text, use it to produce a `Q2_K` and
compare it with the "blind" `Q2_K` from [lab 03-02](../lab-03-02-scala-quantizzazioni/README.md) using perplexity and
**KL-divergence** against the `Q8_0`. You will understand why below 4 bits the imatrix is not optional, and how to read a
KL-divergence report.

## Prerequisites

- Lab 03-02 completed: `~/llama-lab/quant/Qwen3.5-0.8B-Q2_K.gguf` present (or redo it: 1 minute).
- The **release tarball** unpacked (`llama-imatrix` is not in the `llama` binary), for example
  `~/llama-lab/rel/llama-b11046/` ([lab 01-01](../lab-01-01-binari-precompilati/README.md)).
- ~1 GB of disk and ~2 GB of free RAM.

## Materials

| What | Where | Size |
|---|---|---|
| `Qwen3.5-0.8B-Q8_0.gguf` (HF cache): source and reference | `~/.cache/huggingface/hub/…` | 785 MiB |
| `Qwen3.5-0.8B-Q2_K.gguf` without imatrix | `~/llama-lab/quant/` (lab 03-02) | 410 MiB |
| [`calibrazione-it.txt`](calibrazione-it.txt): 430 words of Italian on various topics (bicycle, cooking, …) | in this folder | 2.6 KB |
| `testo-it.txt` from lab 03-02: the **evaluation** text, different from the calibration one | [`../lab-03-02-scala-quantizzazioni/testo-it.txt`](../lab-03-02-scala-quantizzazioni/testo-it.txt) | 2.5 KB |

Calibration and evaluation must be **different** texts, otherwise you measure how much the model has "learned" the
calibration text. Both are tiny so the lab lasts a few minutes: public quantizers use
hundreds of KB of mixed text (Wikitext, code, several languages).

## Steps

1. **Variables and tool check**:

    ```bash
    SRC=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    REL=~/llama-lab/rel/llama-b11046
    Q=~/llama-lab/quant
    TESTO=../lab-03-02-scala-quantizzazioni/testo-it.txt
    $REL/llama-imatrix --help | head -3
    ```

2. **Compute the imatrix** on the calibration text (in a real case: F16 model, `-c 512` or more, `-ngl 99`):

    ```bash
    $REL/llama-imatrix -m $SRC -f calibrazione-it.txt -o $Q/imatrix-it.gguf -c 128 -t 4
    ```

    Output (20 s with 3 threads on CPU):

    ```text
    compute_imatrix: tokenizing the input ..
    compute_imatrix: tokenization took 79.709 ms
    compute_imatrix: computing over 4 chunks, n_ctx=128, batch_size=2048, n_seq=16
    compute_imatrix: 17.34 seconds per pass - ETA 0.07 minutes
    [1]14.9594,[2]10.8089,[3]11.4033,[4]12.8878,
    Final estimate: PPL = 12.8878 +/- 1.90874
    ```

    The program also prints the perplexity of the calibration text (it is a by-product: `--no-ppl` skips it).
    The file `imatrix-it.gguf` weighs 1.1 MB: for 186 tensors it holds one importance vector per column.

3. **Look inside** with `--show-statistics` (it also needs `-m`):

    ```bash
    $REL/llama-imatrix -m $SRC --in-file $Q/imatrix-it.gguf --show-statistics 2>&1 | grep -v " I \| W " | head -30
    ```

    Expected: `Computing statistics for … (186 tensors)` and a table `Layer | Tensor | Σ(Act²) | Min | Max | μ | σ | % Active | N | Entropy | E (norm) | ZD | CosSim`.
    Look for tensors with low `% Active` (columns the text almost never uses: there quantization can be
    aggressive) and compare `Σ(Act²)` across `attn_qkv`, `ffn_down`, `ffn_up` of the same layer.

4. **Quantize `Q2_K` with the imatrix**:

    ```bash
    llama quantize --allow-requantize --imatrix $Q/imatrix-it.gguf $SRC $Q/Qwen3.5-0.8B-Q2_K-imat.gguf Q2_K 4 2>&1 | tail -4
    ls -la $Q/*.gguf
    ```

    The file has the same size as the blind `Q2_K` give or take 256 bytes of metadata (429,768,736 against 429,768,480:
    the imatrix changes the quantized **values**, not the format) and the log shows:

    ```text
    load_imatrix: imatrix datasets=['…/calibrazione-it.txt']
    load_imatrix: loaded 186 importance matrix entries from …/imatrix-it.gguf computed on 4 chunks
    prepare_imatrix: have 186 importance matrix entries
    llama_model_quantize_impl: quant size  =   399.40 MiB (4.34 BPW)
    ```

5. **Perplexity of the three files** on the evaluation text:

    ```bash
    for f in $SRC $Q/Qwen3.5-0.8B-Q2_K.gguf $Q/Qwen3.5-0.8B-Q2_K-imat.gguf; do
      echo "== $(basename $f)"; llama perplexity -m $f -f $TESTO -c 128 -t 4 2>&1 | grep Final
    done
    ```

    Result:

    | File | PPL |
    |---|---|
    | `Q8_0` (reference) | 11.50 ± 1.81 |
    | `Q2_K` without imatrix | 154.89 ± 30.39 |
    | `Q2_K` **with** imatrix | **34.09** ± 6.08 |

    From ×13 to ×3 against the reference: 430 words of calibration are enough to change the quality class of the file.
    (It is still a poor model: 0.8 B at 2 bits cannot be saved. On a 70 B model the same step brings `IQ2_M` to a usable level.)

6. **KL-divergence**. First save the reference logits, then compare:

    ```bash
    llama perplexity -m $SRC -f $TESTO -c 128 -t 4 --kl-divergence-base $Q/base.kld 2>&1 | grep Final
    ls -la $Q/base.kld       # 125 MB: 512 tokens × 248,320 logits at 16 bits
    for f in Q2_K Q2_K-imat; do
      echo "== $f"; llama perplexity -m $Q/Qwen3.5-0.8B-$f.gguf -f $TESTO -c 128 -t 4 --kl-divergence-base $Q/base.kld --kl-divergence 2>&1 | grep -E "Mean|RMS|Same top"
    done
    ```

    Result:

    | Measure | `Q2_K` | `Q2_K` + imatrix | (`Q4_K_M`, for comparison) |
    |---|---|---|---|
    | Mean PPL(Q)/PPL(base) | 13.47 | 2.96 | 1.087 |
    | **Mean KLD** | 2.356 | 0.834 | 0.074 |
    | Mean Δp | −23.6 % | −13.4 % | −2.1 % |
    | Same top p | – | – | 85.3 % |

    Read the full report: besides the mean there are the KLD and Δp percentiles. If the Δp percentiles are
    symmetric (as many positive as negative) the quantization adds noise; if the negatives dominate, as here,
    the model is really getting worse.

7. **Clean up**: `rm $Q/base.kld` (125 MB) and the GGUFs you no longer need; keep `imatrix-it.gguf` (1 MB) for the variants.

## Check the result

- [ ] `imatrix-it.gguf` exists, weighs ~1 MB and `--show-statistics` lists 186 tensors.
- [ ] The two `Q2_K` have the same size but perplexity 155 against 34.
- [ ] You have a KL-divergence report and can say what KLD, Δp and "Same top p" are.
- [ ] You can explain why calibration and evaluation must be different texts.

## Questions and variants

- Recompute the imatrix with an **English** text (or code) and requantize: does the PPL on the Italian text improve or get worse?
  It proves that the calibration corpus must resemble the intended use.
- Merge two imatrices (`--in-file a.gguf --in-file b.gguf -o c.gguf`) and compare.
- `Q4_K_M` with and without imatrix: here the gain is small (in the module table, on Llama-3-8B, KLD 0.031 → 0.028).
  Measure it: is it worth it?
- `IQ3_M` without imatrix: in this build it is produced without errors (431 MiB, 4.68 bpw), but `IQ` types
  are designed around the imatrix. Measure the PPL with and without: the gap is much larger than for `Q4_K_M`.
- `--include-weights ffn_down --include-weights attn_v`: imatrix on some tensors only. Does anything change?
- Long variant: bartowski's `calibration_datav3.txt` (public on GitHub) with `-c 512` and the F16 model from lab 03-01.

## Deliverable

`lab-03-03.md` with: the six output lines of `llama-imatrix`; the first 10 rows of the `--show-statistics` table
with a comment on which tensor is most "active"; the table of the three perplexities; the KLD report of the two `Q2_K` with
one sentence interpreting KLD, Δp and percentiles; the answer to the first question (with the numbers).
