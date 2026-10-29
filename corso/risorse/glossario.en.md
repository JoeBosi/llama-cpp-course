# Glossary

The terms you meet in the logs, in the documentation and in this course, in alphabetical order. They match the
names you find in `--help` and in the program's messages.

| Term | Meaning |
|---|---|
| **Alias (`-a`)** | Name under which the server presents the model in the API (`/v1/models`, `model` field), independent of the file name. |
| **API key** | Secret key the client sends as `Authorization: Bearer …`; the server checks it if started with `--api-key` or `--api-key-file`. `/health` is exempt from the check. |
| **Backend** | Implementation of ggml's computations for one kind of hardware: CPU, CUDA (NVIDIA), Metal (Apple), Vulkan, HIP/ROCm (AMD), SYCL (Intel), RPC (remote)… The binary picks the one available. |
| **Batch (`-b`, `-ub`)** | Maximum number of tokens processed in one go during prompt processing: `-b` logical, `-ub` physical. Larger = faster prompt but more memory. |
| **Build (`bNNNNN`)** | Sequential number of the llama.cpp nightly build (e.g. `b11046`). The `vX.Y.Z` releases point to a build. `llama version` prints both. |
| **Chat template** | Jinja template, stored in the GGUF metadata, that turns the list of messages (system/user/assistant/tool) into the text the model expects. `--jinja` (default) uses it; `--chat-template` overrides it. |
| **Context (`-c`, `n_ctx`)** | Maximum number of tokens (prompt + answer) the model keeps "in mind". `-c 0` uses the model's native value. In the server it is the **total**, split across the slots. |
| **Context shift** | When the context is full, the server discards the oldest tokens to keep going (`--context-shift`, disabled by default). |
| **Continuous batching** | The server processes tokens from several requests (slots) in the same `llama_decode` at once; a new request joins without waiting for the others to finish. |
| **Draft model** | The draft model for speculative decoding: same family and same tokenizer as the main model, much smaller. |
| **Embedding** | Vector of numbers that represents the meaning of a text; similar texts have nearby vectors. `llama serve --embedding`, endpoint `/v1/embeddings`. The basis of RAG. |
| **fit (`--fit`)** | Automatic fitting of unset parameters (context, offload) to the available memory. Handy, but in production set the values explicitly. |
| **Flash Attention (`-fa`)** | Attention implementation that uses less memory and, on GPU, is faster; required for a quantized KV cache. `auto` by default. |
| **ftype** | Predominant quantization type of a GGUF, shown in the banner (e.g. `Q8_0`, `Q4_K_M`, `F16`). |
| **GBNF** | llama.cpp's BNF-style grammar that constrains which tokens can be generated: it guarantees output in a format (JSON, list, SQL). JSON Schema is converted to GBNF. |
| **GGUF** | llama.cpp's file format: model weights (possibly quantized) + metadata (architecture, tokenizer, chat template). A single file, memory-mappable. |
| **ggml** | C tensor library llama.cpp is built on: it defines tensors, the compute graph and the backends. |
| **gguf-split** | Tool to split a large GGUF into several files (`-00001-of-00006.gguf`) or merge them; llama.cpp loads them from the first piece. |
| **Grammar** | See GBNF. |
| **Health check** | `GET /health`: 200 `{"status":"ok"}` when the model is ready, 503 while it loads. Used by Compose, Kubernetes, uptime monitors. |
| **HF (`-hf`)** | Hugging Face, the site you download models from. `-hf user/repo[:quant]` downloads and caches; `HF_TOKEN` for gated repos. |
| **imatrix** | Importance matrix: statistics collected on a calibration text that tell the quantizer which weights matter most. It greatly improves low-bit quantizations. |
| **Infill (FIM)** | "Fill in the middle" completion of a text given a prefix and a suffix; used by code assistants. Endpoint `/infill`. |
| **JSON Schema** | Formal description of the shape of a JSON document (fields, types, required). With `response_format: {"type":"json_schema", …}` the server converts it into a grammar and guarantees conforming output. |
| **KL divergence (KLD)** | Measure of how far the token distribution of a quantized model departs from that of the reference model: more precise than perplexity for comparing quantizations. |
| **KV cache** | Memory that stores the attention keys and values for tokens already processed, so they need not be recomputed. It grows linearly with the context; quantizable with `-ctk`/`-ctv`. |
| **KV unified (`--kv-unified`)** | A single KV cache shared by the slots instead of N fixed slices: slots can use different context sizes. |
| **Load mode (`--load-mode`)** | How the file is read: `mmap` (memory-mapped, default), `mlock` (locked in RAM), `dio` (direct I/O). Replaces the old `--mmap`/`--mlock`. |
| **LoRA** | Low-rank adapter that modifies a base model without rewriting its weights; llama.cpp loads it with `--lora` and can enable it per request. |
| **Metrics** | `GET /metrics` in Prometheus format (enabled with `--metrics`): `llamacpp:*` counters and gauges on tokens, timings, requests in progress and queued. |
| **mmproj** | Multimodal projector: a separate GGUF file that connects an image/audio encoder to the language model. With `-hf` it is downloaded automatically. |
| **MoE (Mixture of Experts)** | Architecture in which each token activates only some "experts" (subnetworks): many parameters on disk, few active per token. `-cmoe` keeps the experts on CPU. |
| **MTP** | Multi-Token Prediction: an extra head of the model (e.g. gemma-4) used as the draft in speculative decoding (`--spec-type draft-mtp`). |
| **Offload (`-ngl`)** | Number of model layers moved to the GPU (`all`, `auto` or a number); the rest stays on CPU (hybrid inference). |
| **Perplexity (PPL)** | Measure of how "surprised" the model is by a text: lower is better. `llama perplexity` computes it; useful for comparing quantizations of the same model on the same text. |
| **pp / tg** | Prompt processing / token generation: the two speeds (tokens/s) measured by `llama bench` (`pp512`, `tg128`). pp is compute-bound, tg is bound by memory bandwidth. |
| **Prompt caching** | The server reuses the KV cache of a prefix it has already seen (system prompt, previous conversation): those tokens are not processed again. `--cache-reuse N` allows reuse even with shifts. |
| **Prompt injection** | Hostile text inside a document or page that the model reads and mistakes for instructions; dangerous when the model can call tools. |
| **Quantization** | Representing weights with fewer bits (8, 5, 4, 3, 2) to reduce memory and increase speed, at the cost of some quality. Types: `Q8_0`, `Q4_K_M`, `IQ4_XS`… |
| **RAG** | Retrieval-Augmented Generation: find the relevant passages in a store (with embeddings) and pass them in the prompt, so the model answers from your data and cites the sources. |
| **Reasoning / thinking** | Models that "think" before answering, producing a reasoning block. `-rea on|off|auto`, `--reasoning-budget N`, `--reasoning-format`; per request `chat_template_kwargs: {"enable_thinking": false}`. |
| **Reranker** | Model that scores the relevance of (question, document) pairs; used after vector search to reorder the results. `--rerank --pooling rank`, `/v1/rerank`. |
| **Reverse proxy** | Server (Caddy, Nginx) that sits in front of `llama serve`: it terminates HTTPS, authenticates, rate-limits, logs; the server stays on `127.0.0.1`. |
| **Router mode** | `llama serve` without a model: it loads and unloads models on demand (from the cache, from `--models-dir` or from an `.ini` preset) and forwards each request to the right instance based on the `model` field. |
| **RPC** | Backend that runs part of the model on another machine (`ggml-rpc-server`); no authentication: private networks only. |
| **Sampling** | How the next token is chosen among the candidates: `--temp`, `--top-k`, `--top-p`, `--min-p`, repetition penalties, `--seed`. |
| **Slot** | The server's unit of work: each slot serves one request at a time with its own slice of context. `-np N` = N slots; `/slots` shows their state. |
| **Speculative decoding** | A small draft model proposes several tokens, the large model verifies them in a single pass: same quality, less time per token. `-md`, `--spec-type draft-simple`, or draft-free variants (`ngram-*`). |
| **SSE (Server-Sent Events)** | HTTP streaming format used with `"stream": true`: `data: {...}` lines until `data: [DONE]`. The proxy must not buffer it. |
| **systemd unit** | `.service` file that describes how to start, restart and confine a process on Linux; `Environment=LLAMA_ARG_*` to configure the server. |
| **Thread (`-t`)** | CPU threads used for generation: normally = physical cores. `-tb` for prompt processing, `--threads-http` for HTTP connections. |
| **Time to first token (TTFT)** | Time between sending the request and receiving the first token; it depends on prompt processing and on queue wait. |
| **Token** | The model's unit of text (piece of a word, word, symbol): about 0.7 words of Italian text. Everything is measured in tokens: context, speed, costs. `/tokenize` shows the split. |
| **Tool calling** | Given the list of tools (`tools` in the API), the model answers with a structured call (`tool_calls`) that your code runs; the result goes back to the model with `role: tool`. |
| **VRAM** | GPU memory: it must hold the offloaded layers and their KV cache. |
| **Web UI** | Web interface built into `llama serve` (at `/`): chat, attachments, settings; `--no-webui` disables it. |
