# Recommended models for the labs

To understand **which** of these to choose for your machine (RAM, GPU, Mac, Raspberry Pi): [Module 02b](../moduli/02b-scegliere-modello/README.md).

Criteria: **small** models that run on CPU with 8-16 GB of RAM, with a permissive or clearly stated license,
official GGUFs (`ggml-org` is the llama.cpp organization) or from reliable quantizers (`unsloth`,
`LiquidAI`). Sizes are those of the listed GGUF file (MiB, from `…/api/models/<repo>/tree/main`);
for multimodal models the `mmproj` is listed too, which `-hf` downloads on its own.

To download them all at once: [`scripts/scarica-modelli-corso.sh`](strumenti.md#scarica-modelli-corsosh).

!!! note "How to read the license"
    "Card" = stated in the GGUF repo's model card. For some `ggml-org` repos the card does not state the
    license: the original model's license applies, shown in parentheses. The Gemma and LFM licenses are permissive
    but come with usage terms: read them before commercial use.

## Chat: small (8 GB of RAM, Raspberry Pi 5 too)

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf` (`:Q8_0`, default with `-hf`) | 795 | Apache-2.0 (card) | **the course model**: example from the official README; thinking by default (`-rea off`); `Q4_0` 537 MiB |
| `LiquidAI/LFM2.5-230M-GGUF` | `LFM2.5-230M-Q4_K_M.gguf` | 146 | LFM Open License (card: other) | the fastest; `Q8_0` 235 MiB |
| `ggml-org/gemma-3-270m-it-GGUF` | `gemma-3-270m-it-Q8_0.gguf` | 278 | (Gemma) | classification, rephrasing |
| `ggml-org/gemma-3-1b-it-GGUF` | `gemma-3-1b-it-Q4_K_M.gguf` | 769 | Gemma (card) | `Q8_0` 1020 MiB |
| `LiquidAI/LFM2.5-1.2B-Instruct-GGUF` | `LFM2.5-1.2B-Instruct-Q4_K_M.gguf` | 697 | LFM Open License (card: other) | good Italian for its size |

## Chat: medium (16 GB of RAM)

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/gemma-3-4b-it-qat-GGUF` | `gemma-3-4b-it-qat-Q4_0.gguf` + `mmproj-model-f16-4B.gguf` | 2409 + 812 | (Gemma) | quantization-aware: a high-quality Q4_0; vision too |
| `unsloth/Qwen3.5-4B-GGUF` | `Qwen3.5-4B-Q4_K_M.gguf` + `mmproj-F16.gguf` | 2614 + 641 | Apache-2.0 (card) | thinking, tool calling, vision; `UD-Q4_K_XL` 2777 MiB |
| `unsloth/Qwen3.5-2B-GGUF` | `Qwen3.5-2B-Q4_K_M.gguf` | 1222 | Apache-2.0 (card) | middle ground |
| `ggml-org/SmolLM3-3B-GGUF` | `SmolLM3-Q4_K_M.gguf` | 1827 | Apache-2.0 (card) | |
| `ggml-org/gemma-4-E2B-it-GGUF` | `gemma-4-E2B-it-Q4_0.gguf` + `mmproj-…-Q8_0.gguf` | 2710 + 532 | Apache-2.0 (card) | text, images, audio; MTP draft in the repo |
| **With GPU** `ggml-org/gemma-4-E4B-it-GGUF` | `gemma-4-E4B-it-Q4_0.gguf` + mmproj Q8_0 + `mtp-…-Q4_0.gguf` | 4378 + 534 + 57 | Apache-2.0 (card) | the model in the llama.app examples; ~6 GB with 16k context |
| **With GPU** `ggml-org/gpt-oss-20b-GGUF` | `gpt-oss-20b-MXFP4.gguf` + `eagle3-gpt-oss-20b-Q8_0.gguf` | 11549 + 879 | Apache-2.0 (card) | reasoning and tools; EAGLE3 draft in the repo |

## Thinking (explicit reasoning)

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Q8_0` | 795 | Apache-2.0 | `--reasoning-budget N` to limit the thinking |
| `unsloth/Qwen3.5-4B-GGUF` | `Q4_K_M` | 2614 | Apache-2.0 | the best on a 16 GB CPU machine |
| **With GPU** `ggml-org/gpt-oss-20b-GGUF` | `MXFP4` | 11549 | Apache-2.0 | `--reasoning-effort low|medium|high` |

## Embedding

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/embeddinggemma-300M-GGUF` | `embeddinggemma-300M-Q8_0.gguf` | 318 | (Gemma) | 768 dimensions, multilingual; `unsloth/embeddinggemma-300m-GGUF` (Q8_0 313 MiB, card: gemma) is the one in the llama.app examples |
| `ggml-org/bge-m3-Q8_0-GGUF` | `bge-m3-q8_0.gguf` | 605 | MIT (card) | 1024 dim, 8k context, excellent in Italian |
| `ggml-org/Nomic-Embed-Text-V2-GGUF` | `nomic-embed-text-v2-moe-q8_0.gguf` | 488 | Apache-2.0 (card) | multilingual, MoE |
| `ggml-org/bge-small-en-v1.5-Q8_0-GGUF` | `bge-small-en-v1.5-q8_0.gguf` | 35 | MIT (card) | English only; for very quick tests |

Start it with: `llama serve -hf <repo> --embedding` → `/v1/embeddings`.

## Reranker

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF` | `qwen3-reranker-0.6b-q8_0.gguf` | 610 | Apache-2.0 (card) | official example: `--embedding --rerank --pooling rank` |
| `ggml-org/jina-reranker-v1-turbo-en-GGUF` | `Jina-Bert-Implementation-38M-F16.gguf` | 73 | Apache-2.0 (card) | English only, tiny |

## Vision (images, documents)

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/SmolVLM-500M-Instruct-GGUF` | `SmolVLM-500M-Instruct-Q8_0.gguf` + `mmproj-…-Q8_0.gguf` | 417 + 104 | Apache-2.0 (card) | lab 07-01; `SmolVLM-256M` for tiny devices |
| `ggml-org/LFM2-VL-450M-GGUF` | `LFM2-VL-450M-Q8_0.gguf` + mmproj | 362 + 99 | (LFM Open License) | |
| `ggml-org/granite-docling-258M-GGUF` | `granite-docling-258M-Q8_0.gguf` + mmproj | 170 + 99 | Apache-2.0 (card) | documents: layout, tables, formulas (project P6) |
| `ggml-org/SmolVLM2-2.2B-Instruct-GGUF` | `SmolVLM2-2.2B-Instruct-Q4_K_M.gguf` + mmproj Q8_0 | 1061 + 565 | Apache-2.0 (card) | video too |
| `ggml-org/gemma-3-4b-it-qat-GGUF` | see medium chat | 2409 + 812 | (Gemma) | the best on a 16 GB CPU machine for receipts and forms |
| `unsloth/Qwen3.5-4B-GGUF` | see medium chat | 2614 + 641 | Apache-2.0 | excellent OCR |

## Audio (speech → text, questions about audio)

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF` | `Llama-3.2-1B-Instruct-Q4_K_M.gguf` + `mmproj-…-f16.gguf` | 770 + 1308 | MIT (card) | lab 07-02 |
| `ggml-org/LFM2-Audio-1.5B-GGUF` | `LFM2-Audio-1.5B-Q8_0.gguf` + mmproj | 1189 + 317 | (LFM Open License) | |
| `ggml-org/Voxtral-Mini-3B-2507-GGUF` | `Voxtral-Mini-3B-2507-Q4_K_M.gguf` + mmproj Q8_0 | 2358 + 683 | (Apache-2.0, Mistral model) | 16 GB |
| `ggml-org/gemma-4-E2B-it-GGUF` / `E4B` | see medium chat | | Apache-2.0 | text + images + audio in a single model |

## Drafts for speculative decoding

| Pair (main + draft) | File | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/Qwen2.5-Coder-7B-Q8_0-GGUF` + `ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF` | q8_0 | 7723 + 506 | Apache-2.0 (card) | the pair in the official `--fim-qwen-7b-spec` presets; on CPU use the 1.5B as the main model for lab 05-03 |
| `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` + `…-0.5B-Q8_0-GGUF` | q8_0 | 1570 + 506 | Apache-2.0 | lab 05-03 on 8 GB |
| `ggml-org/gemma-4-E4B-it-GGUF` (same repo, `--hf-repo-draft` + `--spec-type draft-mtp`) | Q4_0 + mtp Q4_0 | 4378 + 57 | Apache-2.0 | built-in MTP draft |
| `ggml-org/gpt-oss-20b-GGUF` (same repo, EAGLE3) | MXFP4 + eagle3 Q8_0 | 11549 + 879 | Apache-2.0 | with GPU |

Without a draft model: `--spec-type ngram-simple` (n-gram, no extra file).

## Code

| Repository | File / quant | MiB | License | Notes |
|---|---|---|---|---|
| `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` | `qwen2.5-coder-1.5b-q8_0.gguf` | 1570 | Apache-2.0 (card) | base for infill (`--fim-qwen-1.5b-default`) |
| `ggml-org/Qwen2.5-Coder-3B-Instruct-Q8_0-GGUF` | `qwen2.5-coder-3b-instruct-q8_0.gguf` | 3133 | Qwen Research (card: other) | chat about code, 16 GB |
| `ggml-org/functiongemma-270m-it-GGUF` | `functiongemma-270m-it-q8_0.gguf` | 278 | Gemma (card) | tiny function calling (project P3) |
| **With GPU** `ggml-org/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF` | `qwen3-coder-30b-a3b-instruct-q8_0.gguf` | 30979 | Apache-2.0 (card) | MoE: 3B active; with 32 GB of RAM on CPU too (`-cmoe`) |

## To convert (safetensors, lab 03-01 and project P5)

| Repository | Source size | License | Notes |
|---|---|---|---|
| `HuggingFaceTB/SmolLM2-135M-Instruct` | 257 MiB | Apache-2.0 | converts in a minute; compare with `ggml-org/SmolLM2-135M-GGUF` |
| `Qwen/Qwen2.5-0.5B-Instruct` | 942 MiB | Apache-2.0 | |
| `Qwen/Qwen3.5-0.8B` | 1666 MiB | Apache-2.0 | compare with the official `ggml-org` GGUFs |

## How to find more

On Hugging Face filter by `apps=llama.cpp` (declared compatibility):
[chat](https://huggingface.co/models?apps=llama.cpp&sort=trending),
[embedding](https://huggingface.co/models?pipeline_tag=sentence-similarity&apps=llama.cpp&sort=trending),
[reranker](https://huggingface.co/models?pipeline_tag=text-ranking&apps=llama.cpp&sort=trending).
With the API you can check a repo before downloading it:

```bash
curl -s https://huggingface.co/api/models/ggml-org/Qwen3.5-0.8B-GGUF | python3 -c 'import sys,json; m=json.load(sys.stdin); print(m["id"], m.get("cardData",{}).get("license"))'
curl -s https://huggingface.co/api/models/ggml-org/Qwen3.5-0.8B-GGUF/tree/main | python3 -c 'import sys,json; [print(f["path"], f["size"]//2**20, "MiB") for f in json.load(sys.stdin) if f["path"].endswith(".gguf")]'
```
