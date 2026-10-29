# Lab 02-01: The first model

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/02-primi-passi/README.md">02: First steps: `llama cli`</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 40 minutes</span>
</div>

## Objective

Download the course test model from Hugging Face, find it in the cache, chat with `llama cli`
using the built-in commands, give a system prompt, ask a "one-shot" question from a script, read the
banner and the timing line, and find in the verbose log the lines that describe memory, template and samplers.

## Prerequisites

- `llama` installed and `llama version` working ([module 01](../../moduli/01-installazione/README.md)).
- An Internet connection for the first download (785 MiB) and ~1.5 GB of free RAM.
- Ubuntu with the installer's binary: `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF`, file `Qwen3.5-0.8B-Q8_0.gguf`, Apache 2.0 license | Hugging Face, via `-hf` | 785 MiB |
| Any text file (a page of notes, a README) for `/read` | yours | a few KB |

## Steps

1. **Download and start**. The first time you see the download bar, then `Loading model...` and the banner:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF
    ```

    ```text
    build      : b11046-60081bb2b
    model      : ggml-org/Qwen3.5-0.8B-GGUF
    ftype      : Q8_0
    modalities : text
    ```

    Write down build, ftype and modalities. Ask «Chi sei?» ("Who are you?") and observe: the model first **thinks** (`[Start thinking]`),
    then answers. Exit with `/exit`.

2. **Find the file in the cache** and check that `-cl` lists it:

    ```bash
    llama cli -cl
    ls -la ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/
    du -sh ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF
    ```

    Expected: `1. ggml-org/Qwen3.5-0.8B-GGUF:Q8_0`; in the snapshot a symbolic link `Qwen3.5-0.8B-Q8_0.gguf -> ../../blobs/37ae48…`;
    785 MiB in total. From now on `-hf` downloads nothing more (`--offline` to be sure).

3. **Chat without reasoning, with the built-in commands**:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -rea off -c 4096 -t 4     # -t: your physical cores
    ```

    - Ask «Spiega in una frase cos'è un token» ("Explain in one sentence what a token is") and write down the `[ Prompt: … | Generation: … ]` line.
      The model answers talking about *cryptographic* tokens, not linguistic ones. This is normal for 0.8 B
      parameters without context: you fix it in step 5.
    - `/regen`: does the answer change? (The seed is random: yes, almost always.)
    - `/read appunti.txt` followed by «Riassumi il file in tre punti» ("Summarize the file in three points"): the content enters the message.
    - `/clear` then «Di cosa stavamo parlando?» ("What were we talking about?"): the history is gone.
    - `/exit`.

4. **One-shot question from a script** (`-st -p`), saving the output:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Quanto fa 17 per 3? Solo il numero." -n 30 -rea off -t 4
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Quanto fa 17 per 3?" -n 40 -t 4      # thinking on
    ```

    Expected: the first command prints the answer and exits (`Exiting...`); the second uses up the 40 tokens inside
    `[Start thinking]` and does not answer. Try again with `--reasoning-budget 25`: the thinking is
    cut off with `[End thinking]` and an answer arrives.

5. **System prompt**. Repeat the token question with a context:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 60 \
      -sys "Sei un esperto di modelli linguistici (LLM). Rispondi in italiano, in una frase." \
      -p "Cos'è un token?"
    ```

    Answer: «Un token è una parte dell'input dell'LLM, che rappresenta una parte della sequenza dei caratteri.»
    ("A token is a part of the LLM's input that represents a part of the character sequence.")
    Same model, same question, right answer: the system prompt matters more than it seems.

6. **Verbose log**. Run a very short question with `-v` and save the log:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao" -n 5 -rea off -t 4 -c 4096 -v 2> log.txt
    grep -E "system_info|file type|n_ctx_train|model params|llama_kv_cache: size|memory breakdown|Host|chat template, thinking|sampler chain" log.txt
    ```

    Expected (values on a 6-vCPU machine without GPU):

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

    Compare the 48 MiB of KV cache with the formula in [module 00](../../moduli/00-introduzione/README.md#5-estimating-memory-weights-kv-cache-overhead)
    and the 877 MiB total with the free RAM (`free -m`).

7. **Threads and speed**. Repeat step 4 (first variant) with `-t 1`, `-t 2`, `-t` = physical cores, `-t` = logical
   cores, and write down `Generation` for each. Usually the maximum is at the physical cores; beyond that, it gets worse.

## Check

- [ ] `llama cli -cl` lists `ggml-org/Qwen3.5-0.8B-GGUF:Q8_0` and you can point to the path of the blob.
- [ ] You used `/regen`, `/read`, `/clear` and you know what each one changes in the context.
- [ ] With `-n 40` and thinking on you got no answer; with `-rea off` or `--reasoning-budget` you did.
- [ ] In the verbose log you found the total memory (`Host`), KV cache, `thinking = 0` and the sampler chain.
- [ ] You have a threads → tokens/s table.

## Questions and variations

- Why does the download of `-hf ggml-org/Qwen3.5-0.8B-GGUF` take the `Q8_0` and not a `Q4_K_M`? (Look at the repo's file list.)
- What changes in `memory breakdown` with `-c 16384`? Calculate first, then check.
- Variation: `llama cli -hf LiquidAI/LFM2.5-230M-GGUF:Q4_K_M` (146 MiB): compare banner, speed and quality
  of the answers with Qwen3.5-0.8B.
- Multimodal variation (if you have ≥ 6 GB free): `llama cli -hf ggml-org/gemma-3-4b-it-qat-GGUF`, then `/image foto.jpg`
  and «Descrivi l'immagine» ("Describe the image"): the banner shows `modalities: text, vision`.
- From a script: `llama cli … -st -p "$(cat domanda.txt)" -o risposta.txt` and then `cat risposta.txt`.

## Deliverable

A `lab-02-01.md` file with: the banner; the output of `llama cli -cl` and the path of the blob; the two answers
to the token question (without and with system prompt) with their timing lines; the eight log lines
from step 6, each commented in one sentence; the threads → tokens/s table with a concluding line.
