# Modelli consigliati per i laboratori

<div class="meta" markdown>
<span class="stato stato-verificato">repository, file, dimensioni e licenze verificati sull'API di Hugging Face il 23/09/2026</span>
</div>

Per capire **quale** di questi scegliere in base alla tua macchina (RAM, GPU, Mac, Raspberry Pi): [Modulo 02b](../moduli/02b-scegliere-modello/README.md).

Criteri: modelli **piccoli** che girano su CPU con 8-16 GB di RAM, licenza permissiva o chiaramente indicata,
GGUF ufficiali (`ggml-org` è l'organizzazione di llama.cpp) o di quantizzatori affidabili (`unsloth`,
`LiquidAI`). Le dimensioni sono quelle del file GGUF indicato (MiB, da `…/api/models/<repo>/tree/main`);
per i modelli multimodali è indicato anche l'`mmproj`, che `-hf` scarica da solo.

Per scaricarli tutti in una volta: [`scripts/scarica-modelli-corso.sh`](strumenti.md#scarica-modelli-corsosh).

!!! note "Come leggere la licenza"
    "Scheda" = indicata nella scheda del repo GGUF. Per alcuni repo di `ggml-org` la scheda non riporta la
    licenza: vale quella del modello originale, indicata tra parentesi. Le licenze Gemma e LFM sono permissive
    ma con condizioni d'uso: leggile prima di un uso commerciale.

## Chat: piccoli (8 GB di RAM, anche Raspberry Pi 5)

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf` (`:Q8_0`, default con `-hf`) | 795 | Apache-2.0 (scheda) | **il modello del corso**: esempio del README ufficiale; thinking di default (`-rea off`); `Q4_0` 537 MiB |
| `LiquidAI/LFM2.5-230M-GGUF` | `LFM2.5-230M-Q4_K_M.gguf` | 146 | LFM Open License (scheda: other) | il più veloce; `Q8_0` 235 MiB |
| `ggml-org/gemma-3-270m-it-GGUF` | `gemma-3-270m-it-Q8_0.gguf` | 278 | (Gemma) | classificazione, riformulazione |
| `ggml-org/gemma-3-1b-it-GGUF` | `gemma-3-1b-it-Q4_K_M.gguf` | 769 | Gemma (scheda) | `Q8_0` 1020 MiB |
| `LiquidAI/LFM2.5-1.2B-Instruct-GGUF` | `LFM2.5-1.2B-Instruct-Q4_K_M.gguf` | 697 | LFM Open License (scheda: other) | buon italiano per la taglia |

## Chat: medi (16 GB di RAM)

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/gemma-3-4b-it-qat-GGUF` | `gemma-3-4b-it-qat-Q4_0.gguf` + `mmproj-model-f16-4B.gguf` | 2409 + 812 | (Gemma) | quantization-aware: Q4_0 di qualità; anche visione |
| `unsloth/Qwen3.5-4B-GGUF` | `Qwen3.5-4B-Q4_K_M.gguf` + `mmproj-F16.gguf` | 2614 + 641 | Apache-2.0 (scheda) | thinking, tool calling, visione; `UD-Q4_K_XL` 2777 MiB |
| `unsloth/Qwen3.5-2B-GGUF` | `Qwen3.5-2B-Q4_K_M.gguf` | 1222 | Apache-2.0 (scheda) | via di mezzo |
| `ggml-org/SmolLM3-3B-GGUF` | `SmolLM3-Q4_K_M.gguf` | 1827 | Apache-2.0 (scheda) | |
| `ggml-org/gemma-4-E2B-it-GGUF` | `gemma-4-E2B-it-Q4_0.gguf` + `mmproj-…-Q8_0.gguf` | 2710 + 532 | Apache-2.0 (scheda) | testo, immagini, audio; draft MTP nel repo |
| **Con GPU** `ggml-org/gemma-4-E4B-it-GGUF` | `gemma-4-E4B-it-Q4_0.gguf` + mmproj Q8_0 + `mtp-…-Q4_0.gguf` | 4378 + 534 + 57 | Apache-2.0 (scheda) | il modello degli esempi di llama.app; ~6 GB con 16k di contesto |
| **Con GPU** `ggml-org/gpt-oss-20b-GGUF` | `gpt-oss-20b-MXFP4.gguf` + `eagle3-gpt-oss-20b-Q8_0.gguf` | 11549 + 879 | Apache-2.0 (scheda) | ragionamento e strumenti; draft EAGLE3 nel repo |

## Thinking (ragionamento esplicito)

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` | `Q8_0` | 795 | Apache-2.0 | `--reasoning-budget N` per limitare il pensiero |
| `unsloth/Qwen3.5-4B-GGUF` | `Q4_K_M` | 2614 | Apache-2.0 | il migliore su CPU 16 GB |
| **Con GPU** `ggml-org/gpt-oss-20b-GGUF` | `MXFP4` | 11549 | Apache-2.0 | `--reasoning-effort low|medium|high` |

## Embedding

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/embeddinggemma-300M-GGUF` | `embeddinggemma-300M-Q8_0.gguf` | 318 | (Gemma) | 768 dimensioni, multilingue; `unsloth/embeddinggemma-300m-GGUF` (Q8_0 313 MiB, scheda: gemma) è quello degli esempi di llama.app |
| `ggml-org/bge-m3-Q8_0-GGUF` | `bge-m3-q8_0.gguf` | 605 | MIT (scheda) | 1024 dim, contesto 8k, ottimo in italiano |
| `ggml-org/Nomic-Embed-Text-V2-GGUF` | `nomic-embed-text-v2-moe-q8_0.gguf` | 488 | Apache-2.0 (scheda) | multilingue, MoE |
| `ggml-org/bge-small-en-v1.5-Q8_0-GGUF` | `bge-small-en-v1.5-q8_0.gguf` | 35 | MIT (scheda) | solo inglese; per prove velocissime |

Avvio: `llama serve -hf <repo> --embedding` → `/v1/embeddings`.

## Reranker

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF` | `qwen3-reranker-0.6b-q8_0.gguf` | 610 | Apache-2.0 (scheda) | esempio ufficiale: `--embedding --rerank --pooling rank` |
| `ggml-org/jina-reranker-v1-turbo-en-GGUF` | `Jina-Bert-Implementation-38M-F16.gguf` | 73 | Apache-2.0 (scheda) | solo inglese, minuscolo |

## Visione (immagini, documenti)

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/SmolVLM-500M-Instruct-GGUF` | `SmolVLM-500M-Instruct-Q8_0.gguf` + `mmproj-…-Q8_0.gguf` | 417 + 104 | Apache-2.0 (scheda) | lab 07-01; `SmolVLM-256M` per dispositivi minuscoli |
| `ggml-org/LFM2-VL-450M-GGUF` | `LFM2-VL-450M-Q8_0.gguf` + mmproj | 362 + 99 | (LFM Open License) | |
| `ggml-org/granite-docling-258M-GGUF` | `granite-docling-258M-Q8_0.gguf` + mmproj | 170 + 99 | Apache-2.0 (scheda) | documenti: layout, tabelle, formule (progetto P6) |
| `ggml-org/SmolVLM2-2.2B-Instruct-GGUF` | `SmolVLM2-2.2B-Instruct-Q4_K_M.gguf` + mmproj Q8_0 | 1061 + 565 | Apache-2.0 (scheda) | anche video |
| `ggml-org/gemma-3-4b-it-qat-GGUF` | vedi chat medi | 2409 + 812 | (Gemma) | il migliore su CPU 16 GB per scontrini e moduli |
| `unsloth/Qwen3.5-4B-GGUF` | vedi chat medi | 2614 + 641 | Apache-2.0 | ottimo OCR |

## Audio (parlato → testo, domande sull'audio)

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF` | `Llama-3.2-1B-Instruct-Q4_K_M.gguf` + `mmproj-…-f16.gguf` | 770 + 1308 | MIT (scheda) | lab 07-02 |
| `ggml-org/LFM2-Audio-1.5B-GGUF` | `LFM2-Audio-1.5B-Q8_0.gguf` + mmproj | 1189 + 317 | (LFM Open License) | |
| `ggml-org/Voxtral-Mini-3B-2507-GGUF` | `Voxtral-Mini-3B-2507-Q4_K_M.gguf` + mmproj Q8_0 | 2358 + 683 | (Apache-2.0, modello Mistral) | 16 GB |
| `ggml-org/gemma-4-E2B-it-GGUF` / `E4B` | vedi chat medi | | Apache-2.0 | testo + immagini + audio in un solo modello |

## Draft per la decodifica speculativa

| Coppia (principale + draft) | File | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/Qwen2.5-Coder-7B-Q8_0-GGUF` + `ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF` | q8_0 | 7723 + 506 | Apache-2.0 (scheda) | la coppia dei preset ufficiali `--fim-qwen-7b-spec`; su CPU usa il 1.5B come principale per il lab 05-03 |
| `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` + `…-0.5B-Q8_0-GGUF` | q8_0 | 1570 + 506 | Apache-2.0 | lab 05-03 su 8 GB |
| `ggml-org/gemma-4-E4B-it-GGUF` (stesso repo, `--hf-repo-draft` + `--spec-type draft-mtp`) | Q4_0 + mtp Q4_0 | 4378 + 57 | Apache-2.0 | draft MTP integrato |
| `ggml-org/gpt-oss-20b-GGUF` (stesso repo, EAGLE3) | MXFP4 + eagle3 Q8_0 | 11549 + 879 | Apache-2.0 | con GPU |

Senza modello draft: `--spec-type ngram-simple` (n-gram, nessun file in più).

## Codice

| Repository | File / quant | MiB | Licenza | Note |
|---|---|---|---|---|
| `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` | `qwen2.5-coder-1.5b-q8_0.gguf` | 1570 | Apache-2.0 (scheda) | base per infill (`--fim-qwen-1.5b-default`) |
| `ggml-org/Qwen2.5-Coder-3B-Instruct-Q8_0-GGUF` | `qwen2.5-coder-3b-instruct-q8_0.gguf` | 3133 | Qwen Research (scheda: other) | chat sul codice, 16 GB |
| `ggml-org/functiongemma-270m-it-GGUF` | `functiongemma-270m-it-q8_0.gguf` | 278 | Gemma (scheda) | function calling minuscolo (progetto P3) |
| **Con GPU** `ggml-org/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF` | `qwen3-coder-30b-a3b-instruct-q8_0.gguf` | 30979 | Apache-2.0 (scheda) | MoE: 3B attivi; con 32 GB di RAM anche su CPU (`-cmoe`) |

## Da convertire (safetensors, lab 03-01 e progetto P5)

| Repository | Dimensione sorgente | Licenza | Note |
|---|---|---|---|
| `HuggingFaceTB/SmolLM2-135M-Instruct` | 257 MiB | Apache-2.0 | conversione in un minuto; confronta con `ggml-org/SmolLM2-135M-GGUF` |
| `Qwen/Qwen2.5-0.5B-Instruct` | 942 MiB | Apache-2.0 | |
| `Qwen/Qwen3.5-0.8B` | 1666 MiB | Apache-2.0 | confronta con i GGUF ufficiali di `ggml-org` |

## Come cercarne altri

Su Hugging Face filtra per `apps=llama.cpp` (compatibilità dichiarata):
[chat](https://huggingface.co/models?apps=llama.cpp&sort=trending),
[embedding](https://huggingface.co/models?pipeline_tag=sentence-similarity&apps=llama.cpp&sort=trending),
[reranker](https://huggingface.co/models?pipeline_tag=text-ranking&apps=llama.cpp&sort=trending).
Con l'API puoi verificare un repo prima di scaricarlo:

```bash
curl -s https://huggingface.co/api/models/ggml-org/Qwen3.5-0.8B-GGUF | python3 -c 'import sys,json; m=json.load(sys.stdin); print(m["id"], m.get("cardData",{}).get("license"))'
curl -s https://huggingface.co/api/models/ggml-org/Qwen3.5-0.8B-GGUF/tree/main | python3 -c 'import sys,json; [print(f["path"], f["size"]//2**20, "MiB") for f in json.load(sys.stdin) if f["path"].endswith(".gguf")]'
```
