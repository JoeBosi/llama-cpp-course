# Lab 03-01: From Hugging Face to GGUF

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/03-modelli-gguf-quantizzazione/README.md">03: Models, GGUF and quantization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes (20 of them for download and installation)</span>
</div>

## Objective

Take a model published in `safetensors`, convert it to GGUF F16 with `convert_hf_to_gguf.py`, check that the file is
complete (metadata, tokenizer, chat template), run it with `llama cli` and quantize it to `Q8_0` and `Q4_K_M`. By the
end you will have done by hand what `ggml-org` and `bartowski` do for every model that comes out.

## Prerequisites

- `llama` installed ([module 01](../../moduli/01-installazione/README.md)); `git`, `python3` ≥ 3.10 with `venv`.
- ~3 GB of disk (sources + CPU torch ≈ 2 GB, model ≈ 0.5 GB) and an internet connection.
- You have read [section 4 of the module](../../moduli/03-modelli-gguf-quantizzazione/README.md#4-the-pipeline-from-hugging-face-to-a-quantized-gguf).

## Materials

| What | Where | Size |
|---|---|---|
| `HuggingFaceTB/SmolLM2-135M-Instruct` (Apache 2.0, Llama architecture): `config.json`, `model.safetensors`, `tokenizer.json` | Hugging Face | ~270 MB (BF16) |
| llama.cpp sources (only for the Python scripts, we do **not** build them) | `git clone` | ~250 MB |
| Alternative with nothing to install: the [GGUF-my-repo](https://huggingface.co/spaces/ggml-org/gguf-my-repo) space | browser | – |

The model is small on purpose: conversion takes less than a minute and the F16 weighs ~270 MB. The steps are
identical for an 8 B model (only with 16 GB of F16 to write to disk).

## Steps

1. **Sources and Python environment**:

    ```bash
    git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/llama.cpp
    cd ~/llama.cpp
    python3 -m venv .venv && source .venv/bin/activate
    python3 -m pip install -r requirements.txt        # CPU torch, transformers, gguf, safetensors…
    python3 convert_hf_to_gguf.py --help | head -40
    ```

    Expected in the help: `--outtype {f32,f16,bf16,q8_0,tq1_0,tq2_0,auto}`, `--outfile`, `--remote`, `--mmproj`,
    `--vocab-only`, `--print-supported-models`. Also try `python3 convert_hf_to_gguf.py --print-supported-models | grep -i llama`.

2. **Download the model** (or use `--remote` in step 3):

    ```bash
    pip install -U "huggingface_hub[cli]"
    hf download HuggingFaceTB/SmolLM2-135M-Instruct --local-dir ~/modelli/smollm2-135m
    ls -la ~/modelli/smollm2-135m
    ```

    Expected: `config.json`, `generation_config.json`, `model.safetensors` (~270 MB), `tokenizer.json`,
    `tokenizer_config.json` (contains `chat_template`). Open `config.json`: `"architectures": ["LlamaForCausalLM"]`,
    `hidden_size 576`, `num_hidden_layers 30`, `torch_dtype bfloat16`.

3. **Convert to F16**:

    ```bash
    python3 convert_hf_to_gguf.py ~/modelli/smollm2-135m --outtype f16 --outfile ~/modelli/smollm2-135m-f16.gguf
    ```

    Expected in the log: the architecture detection (`Model architecture: LlamaForCausalLM`), one line per
    tensor (`token_embd.weight, torch.bfloat16 --> F16, shape = {576, 49152}`, `blk.0.attn_q.weight …`), the
    tokenizer (`gguf: … chat_template`) and at the end `Model successfully exported to …`. Size ≈ 270 MB.
    Variant without download: `python3 convert_hf_to_gguf.py --remote HuggingFaceTB/SmolLM2-135M-Instruct --outtype f16 --outfile ~/modelli/smollm2-135m-f16.gguf`.

4. **Inspect the GGUF** with the tools from [lab 00-02](../lab-00-02-anatomia-gguf/README.md):

    ```bash
    pip install gguf
    gguf-dump ~/modelli/smollm2-135m-f16.gguf | head -60
    ```

    Check: `general.architecture = llama`, `llama.block_count = 30`, `tokenizer.ggml.tokens` with 49,152 entries,
    `tokenizer.chat_template` present, `general.file_type = 1` (F16), and in the tensor index `F16` types for the weights
    and `F32` for the norms.

5. **Run it**:

    ```bash
    llama cli -m ~/modelli/smollm2-135m-f16.gguf -st -p "Ciao! Presentati in una frase." -n 40 -t 4
    ```

    Expected: a banner with `ftype : F16`, a sensible answer (it is a 135 M model: the answer is short and in English or
    in rough Italian) and the timing line. If the model rambles or does not stop, suspect number one is the chat
    template: `llama cli -v … | grep example_format`.

6. **Quantize** to two types and compare the sizes:

    ```bash
    llama quantize ~/modelli/smollm2-135m-f16.gguf ~/modelli/smollm2-135m-Q8_0.gguf Q8_0
    llama quantize ~/modelli/smollm2-135m-f16.gguf ~/modelli/smollm2-135m-Q4_K_M.gguf Q4_K_M
    ls -la ~/modelli/smollm2-135m-*.gguf
    ```

    Expected: `Q8_0` ≈ 145 MB, `Q4_K_M` ≈ 100 MB (the 49,152 × 576 embedding stays at `q6_K` and the vocabulary weighs
    a lot in such a small model: the ratio is not 16:4). The two final lines `model size` / `quant size`
    give the bpw.

7. **Perplexity of the three files** on the same text, to see what quantization costs on a tiny model:

    ```bash
    for q in f16 Q8_0 Q4_K_M; do llama perplexity -m ~/modelli/smollm2-135m-$q.gguf -f ../lab-03-02-scala-quantizzazioni/testo-it.txt -c 128 -t 4 2>&1 | grep Final; done
    ```

    Expected: F16 ≈ Q8_0 < Q4_K_M, with a proportionally larger gap than the one you see on the 0.8 B model
    in lab 03-02: the smaller the model, the more every bit counts.

## Check the result

- [ ] `convert_hf_to_gguf.py` produced a file with `general.architecture = llama` and the chat template.
- [ ] `llama cli -m` loads it and answers; the banner says `F16`.
- [ ] You have three files (F16, Q8_0, Q4_K_M) and can explain why Q4_K_M is not a quarter of F16.
- [ ] You have three perplexities in increasing order.

## Questions and variants

- Why does the documentation recommend `--outtype auto` (or `bf16`) instead of `f16` for models trained in BF16? (Think
  about the range of representable values.)
- What does `tokenizer_config.json` contain that ends up in the GGUF? And `generation_config.json`, which does **not**?
- Variant: convert a model with `--vocab-only` and look at its size: it is a GGUF with only the tokenizer.
- Docker variant: `docker run -v ~/modelli:/models ghcr.io/ggml-org/llama.cpp:full --all-in-one /models/ …` as in
  `docs/docker.md`, or enter the image (`--entrypoint bash`) and use `python3 /app/convert_hf_to_gguf.py`.
- Browser variant: load the same repo in GGUF-my-repo, pick `Q4_K_M`, and compare the produced file with yours
  (`gguf-dump`: same build? same type for the embedding?).
- If you have a multimodal model (Gemma 3 4B, Qwen3.5-VL): add the `--mmproj --outtype q8_0` step and try
  `llama cli -m … --mmproj … --image foto.jpg`.

## Deliverable

`lab-03-01.md` with: the first 20 lines of the conversion log; the `gguf-dump` output filtered on the keys
`general.*`, `llama.block_count`, `tokenizer.chat_template` (only the beginning); the `llama cli` answer; the table
file → size → bpw → perplexity; the answers to the first two questions.
