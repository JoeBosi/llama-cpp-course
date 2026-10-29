# Lab 10-02 · Control vector

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/10-approfondimenti/README.md">10: Deep dives: inside ggml and llama.cpp</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes (+ build from source)</span>
</div>

## Objective

Generate a "cheerful ↔ sad" control vector for Qwen3.5-0.8B from five prompt pairs, inspect
the resulting GGUF and apply it to `llama cli` with positive and negative scales and over different layer ranges,
watching how the tone of the answers changes **without touching the model weights**.

## Prerequisites

- Module 10, section 5; module 02 for `llama cli` and the chat template.
- **llama.cpp built from source** ([lab 01-02](../lab-01-02-build-sorgenti-cpu/README.md)): `llama-cvector-generator` is not
  in the installer or in the release tarball. The CPU build is enough; with a GPU add `-ngl 99` to the commands.
- Python 3 with the `gguf` package (`pip install gguf`) to inspect the resulting file (optional).
- The course model already in cache (`llama cli -cl`).

## Materials

| What | Source | Size |
|---|---|---|
| Model | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0) | 785 MiB, 24 layers, `n_embd` 1024 |
| [`positivi.txt`](positivi.txt) | this folder: 5 "cheerful" prompts in ChatML format (Qwen's) | 5 lines |
| [`negativi.txt`](negativi.txt) | this folder: the same 5 prompts with a "sad" system message and answer | 5 lines |
| Official examples | [`tools/cvector-generator/positive.txt`](https://github.com/ggml-org/llama.cpp/blob/master/tools/cvector-generator/positive.txt) and `negative.txt` (Llama 3 format, in English) | |

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
B=~/llama.cpp/build/bin     # folder of the binaries built from source
```

## Steps

1. **Look at the prompt pairs.** Each line of `positivi.txt` has its twin in `negativi.txt`: same
    user message, only the system message and the start of the answer change. The format is Qwen's chat
    template (ChatML), with a **literal** `\n` in place of line breaks, as the official README explains:

    ```
    <|im_start|>system\nSei una persona estremamente felice ed entusiasta.<|im_end|>\n<|im_start|>user\nChi sei?<|im_end|>\n<|im_start|>assistant\nSono la persona più felice del mondo!
    ```
    ```
    <|im_start|>system\nSei una persona estremamente triste e abbattuta.<|im_end|>\n<|im_start|>user\nChi sei?<|im_end|>\n<|im_start|>assistant\nSento un peso enorme sul petto, non so nemmeno chi sono.
    ```

    The generator captures the hidden state **at the last token** of each prompt: that is why the answer is left
    "halfway", right in the middle of the tone you want to capture. The two files must have the **same number of lines**:

    ```bash
    wc -l positivi.txt negativi.txt
    ```
    ```
     5 positivi.txt
     5 negativi.txt
    ```

2. **Generate the control vector.** With 5 pairs on a 0.8B model it takes a few seconds of inference plus the
    PCA (1000 iterations by default over 23 layers, a few tens of seconds on CPU):

    ```bash
    $B/llama-cvector-generator -m "$M" \
        --positive-file positivi.txt --negative-file negativi.txt \
        -o allegro.gguf -t 4
    ```

    Expected output (timings depend on the machine):

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

    There are 23 directions, not 24: the generator drops the last layer. If you prefer the mean of the differences to
    PCA (faster, sometimes "gentler"): `--method mean`. For a longer PCA: `--pca-iter 2000 --pca-batch 100`
    (the iterations must be a multiple of the batch).

3. **Inspect the GGUF.** It is a normal GGUF file with the `controlvector` architecture:

    ```bash
    python3 -m gguf.scripts.gguf_dump allegro.gguf | head -20      # or: gguf-dump allegro.gguf
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

    `model_hint` is the architecture of the model used to generate it: the vector works for Qwen3.5-0.8B in any
    quantization, **not** for another model. Each `direction.N` has `n_embd = 1024` values.

4. **Reference answer, without the vector.** Use `-rea off` (otherwise Qwen3.5 "thinks"), temperature 0 for
    reproducible comparisons and a neutral question:

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata."
    ```

5. **Apply the vector positively.** Scale 0.8 on layers 10 to 23 (the README recommends layers above 10):

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata." \
        --control-vector-scaled allegro.gguf:0.8 --control-vector-layer-range 10 23
    ```

    Expected: same prompt, same seed, but a more enthusiastic text ("splendida", "energia", exclamation marks). If the text
    degenerates into repetition, lower the scale to 0.4-0.5.

6. **Apply the vector negatively.** The same direction with the opposite sign pushes toward the negative prompts:

    ```bash
    llama cli -m "$M" -st -rea off --temp 0 -n 60 -p "Descrivi in due frasi la tua giornata." \
        --control-vector-scaled allegro.gguf:-0.8 --control-vector-layer-range 10 23
    ```

7. **Explore scale and layers.** Fill in a table with at least six combinations:

    | scale | layers | observation |
    |---|---|---|
    | 0.4 | 10-23 | |
    | 0.8 | 10-23 | |
    | 1.5 | 10-23 | |
    | 0.8 | 0-23 | |
    | 0.8 | 16-23 | |
    | −0.8 | 10-23 | |

    You will notice that from the low layers (`0-23`) the text loses coherence before it changes tone, and that beyond a certain
    scale the model gets stuck on a few words. `--control-vector allegro.gguf` (without a scale) is the same as scale 1.

8. **In the server.** The same options work for `llama serve`, so the tone applies to every request:

    ```bash
    llama serve -m "$M" --port 18104 --control-vector-scaled allegro.gguf:0.6 --control-vector-layer-range 10 23
    ```

    The vector is fixed for the whole life of the process: there is no per-request field (unlike LoRA
    adapters, managed through `/lora-adapters`).

## Check the result

- [ ] `allegro.gguf` exists, has `controlvector.model_hint = 'qwen35'` and 23 `direction.N` tensors with 1024 values.
- [ ] With scale +0.8 the text is visibly more cheerful than the reference; with −0.8 gloomier; with temperature 0
      the three answers are reproducible on every run.
- [ ] You found a scale beyond which the text degenerates and can state it.

## Questions and variations

1. Why are the answers in the prompts left mid-sentence instead of complete?
2. What changes between `--method pca` and `--method mean` in how each layer's direction is obtained?
3. Why does applying the vector from the low layers ruin coherence while in the high layers it changes the tone?
4. Variation: generate a second "formal ↔ colloquial" vector with 5 new pairs and apply **both** on a single
   line (`--control-vector-scaled allegro.gguf:0.6,formale.gguf:0.6`). Do they add up sensibly?
5. Variation: generate the vector from the Q4_0 in the same repository (`llama download -hf ggml-org/Qwen3.5-0.8B-GGUF:Q4_0`)
   and apply it to the Q8_0: does it work? What does `model_hint` say?
6. Variation (advanced): 5 pairs are few. Raise them to 20-30 by varying the user message and compare the stability
   of the result at the same scale.

## Deliverable

- `positivi.txt` and `negativi.txt` (extended if you like) and the `gguf_dump` output of the generated vector.
- The three answers from steps 4-6 (reference, +0.8, −0.8) to the same prompt.
- The filled-in table from step 7, with the "breaking" scale you found and the answers to questions 1-3.
