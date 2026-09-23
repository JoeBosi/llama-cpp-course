# Fatti verificati (settembre 2026)

Tutto ciò che segue è stato **provato davvero** su questo VPS il 22/09/2026 o letto dalla documentazione
ufficiale di quel giorno. Chi scrive i moduli parte da qui e **non inventa flag, nomi o numeri**.
Se un comando non è in questa lista e non è nella documentazione scaricata in `redazione/upstream/`,
va provato prima di scriverlo (o marcato esplicitamente "da verificare").

## Versioni

| Cosa | Valore |
|---|---|
| Release stabile più recente | `v0.4.1` (14/09/2026). Le release `vX.Y.Z` puntano a una build `bNNNNN` (v0.4.1 → `b10964`). |
| Build installata dall'installer ufficiale | `b11046` → `llama version` stampa `version: 0.4.1-dev (build 11046, commit 60081bb2b)` |
| Build notturne | escono più volte al giorno (`b11095` il 22/09/2026); ogni build ha binari per tutte le piattaforme |
| ggml | v0.24.0 (`libggml.so.0.24.0`) |
| Licenza | MIT |
| Stelle GitHub | ~129k |

## Il binario unico `llama` (novità 2026)

Da inizio 2026 c'è un **eseguibile unico `llama` con sottocomandi**. I vecchi nomi `llama-cli`, `llama-server`,
`llama-bench`, `llama-quantize` ecc. **esistono ancora** nei tarball delle release e nelle immagini Docker
(verificato: `llama-cli --version` funziona), e la documentazione nel repo li usa ancora spesso.
Nel corso usiamo la forma nuova `llama <comando>` e segnaliamo l'equivalenza una volta per modulo.

`llama help all` (build 11046) elenca:

```
serve           HTTP API server
cli             Command-line interactive interface
update          Update llama to the latest release
download        Download a model
completion      Text completion
bench           Benchmark prompt processing and text generation
batched-bench   Benchmark batched decoding performance
fit-params      Compute parameters to fit a model in device memory
quantize        Quantize a model
perplexity      Compute model perplexity and KL divergence
version         Show version
licenses        Show third-party licenses
help            Show available commands
```

**Attenzione:** il binario dell'installer **non** contiene `imatrix`, `gguf-split`, `tokenize`, `tts`,
`mtmd-cli`, `rpc-server`, `export-lora`, `cvector-generator`. Questi ci sono nel **tarball della release**
(es. `llama-b11046-bin-ubuntu-x64.tar.gz`, 16 MB, contiene sia `llama` sia `llama-cli`, `llama-server`,
`llama-imatrix`, `llama-gguf-split`, `llama-tokenize`, `llama-tts`, `llama-mtmd-cli`, `ggml-rpc-server`,
`llama-perplexity`, `llama-bench`, `llama-quantize`, `llama-fit-params`, `llama-batched-bench` + le `.so`)
oppure compilando dai sorgenti. `convert_hf_to_gguf.py` è solo nei sorgenti (e nell'immagine Docker `full`).

## Installazione

### Installer ufficiale (consigliato da llama.app)
```bash
curl -LsSf https://llama.app/install.sh | sh
```
Cosa fa (letto nello script): rileva OS/arch, su Linux prova in ordine CUDA → ROCm → Vulkan → CPU
(su macOS: Metal), scarica un binario da `https://huggingface.co/buckets/ggml-org/install.sh`, lo mette in
`~/.llama-app/llama` e lo copia in `~/.local/bin/llama`. Non serve root. Variabili utili:
`LLAMA_VERSION=bNNNNN` per fissare una build (solo le build presenti nel bucket), `SKIP_CUDA=1`,
`SKIP_ROCM=1`, `SKIP_VULKAN=1`, `SKIP_INSTALL=1`, `HF_TOKEN`. Poi `llama update` aggiorna.

**Gotcha verificato su Ubuntu 24.04:** il binario dell'installer è statico (Clang 22) e può non trovare i
certificati TLS: `llama cli -hf ...` fallisce con `E get_repo_commit: error: HTTPLIB failed: SSL connection failed`.
Soluzione: `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt` (metterlo in `~/.bashrc`).
I binari del tarball release (linkati a libcurl di sistema) non hanno il problema.

### Gestori di pacchetti (docs/install.md)
| Sistema | Comando |
|---|---|
| Windows | `winget install llama.cpp` |
| macOS / Linux | `brew install llama.cpp` |
| macOS | `sudo port install llama.cpp` |
| tutti | `conda install -c conda-forge llama.cpp` (varianti CUDA/Vulkan/Metal), `pixi global install llama.cpp` |
| Nix | `nix profile install nixpkgs#llama-cpp` |

### Binari precompilati (pagina release, build `bNNNNN`)
Nomi reali degli asset (build b10964, identici come schema per le altre):
`llama-bNNNNN-bin-ubuntu-x64.tar.gz` (16 MB, CPU), `-ubuntu-arm64`, `-ubuntu-vulkan-x64` (28 MB),
`-ubuntu-vulkan-arm64`, `-ubuntu-rocm-10.0-x64` (217 MB), `-ubuntu-sycl-fp16-x64`, `-ubuntu-openvino-2026.3.1-x64`,
`-ubuntu-s390x`, `-macos-arm64.tar.gz` (10 MB, Metal), `-macos-x64`, `-win-cpu-x64.zip` (17 MB), `-win-cpu-arm64`,
`-win-cuda-12.4-x64.zip` (242 MB) + `cudart-llama-bin-win-cuda-12.4-x64.zip` (373 MB, runtime CUDA da scompattare
nella stessa cartella), `-win-cuda-13.3-x64`, `-win-cuda-13.4-arm64`, `-win-vulkan-x64` (30 MB), `-win-rocm-10.0-x64`,
`-win-sycl-x64`, `-win-opencl-adreno-arm64`, `-win-openvino-2026.3.1-x64`, `-android-arm64.tar.gz` (67 MB),
`-xcframework.zip` (iOS/macOS), `-ui.tar.gz`. **Non ci sono binari Linux CUDA nelle release**: su Linux+NVIDIA
si usa l'installer, Docker `server-cuda`, conda-forge o la compilazione.
Il tarball Ubuntu contiene molte `libggml-cpu-<arch>.so` (sandybridge…zen4, sapphirerapids): il backend CPU
sceglie a runtime la variante migliore per la CPU.

### Docker (docs/docker.md)
Immagini `ghcr.io/ggml-org/llama.cpp:` + `full` | `light` | `server` (CPU, amd64/arm64/s390x) e varianti
`-cuda`, `-cuda13`, `-rocm`, `-musa`, `-intel` (SYCL), `-vulkan`, `-openvino`.
`light` = `llama-cli` + `llama-completion`; `server` = `llama-server`; `full` = tutto + script di conversione Python.
```bash
docker run -v /path/to/models:/models -p 8080:8080 ghcr.io/ggml-org/llama.cpp:server -m /models/x.gguf --port 8080 --host 0.0.0.0
docker run --gpus all ... ghcr.io/ggml-org/llama.cpp:server-cuda ... -ngl 99
```
Esempio Compose ufficiale (llama.app): servizio con `image: ghcr.io/ggml-org/llama.cpp:server`, `ports: 8080:8080`,
volume `./models:/models`, `environment: LLAMA_ARG_HOST=0.0.0.0, LLAMA_ARG_MODEL=/models/x.gguf, LLAMA_ARG_CTX_SIZE=4096, LLAMA_ARG_N_PARALLEL=2, LLAMA_ARG_PORT=8080`.
**Ogni flag ha una variabile d'ambiente `LLAMA_ARG_*`** (stampata da `--help`).

### Compilazione (docs/build.md)
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build            # CPU; + -DGGML_CUDA=ON | -DGGML_METAL=ON (default su mac) | -DGGML_VULKAN=ON | -DGGML_HIP=ON | -DGGML_SYCL=ON
cmake --build build --config Release -j 8
```
Binari in `build/bin/` (`llama`, `llama-cli`, …). `-DBUILD_SHARED_LIBS=OFF` per statici; `-DLLAMA_CURL=ON` è il default
(serve `libcurl4-openssl-dev` su Debian/Ubuntu); Ninja: `-G Ninja`; ccache rilevato automaticamente.
Windows: Visual Studio 2022 (workload "Desktop development with C++") o `winget install llama.cpp`; WoA:
`cmake --preset arm64-windows-llvm-release -D GGML_OPENMP_FETCH=ON`.
CUDA: `-DGGML_CUDA=ON`, opz. `-DCMAKE_CUDA_ARCHITECTURES="86;89"`. HIP: `-DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100`
con `HIPCXX="$(hipconfig -l)/clang"`. Vulkan Linux: pacchetti `libvulkan-dev glslc` (o SDK LunarG), `-DGGML_VULKAN=ON`.
Android: `docs/android.md` (Termux: `pkg install cmake clang git` poi build normale; o NDK con `-DANDROID_ABI=arm64-v8a`).
Su questo VPS sono installati cmake 3.28.3, ninja 1.11.1, ccache 4.9.1, gcc.

## Uso di `llama cli` (verificato)

```bash
llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF          # scarica (cache HF) ed entra in chat
llama cli -m modello.gguf                          # file locale
llama cli -hf ... -st -p "domanda" -n 120 -rea off # single-turn: risponde ed esce; -rea off spegne il "thinking"
llama cli -cl                                      # elenca i modelli in cache (~/.cache/huggingface/hub/)
llama download -hf ggml-org/gemma-3-4b-it-qat-GGUF:Q4_K_M
```
- `-hf <user>/<repo>[:quant]`: se non indichi la quant, cerca `Q4_K_M`, altrimenti prende il primo file. Scarica
  anche l'`mmproj` se c'è (`--no-mmproj` per evitarlo).
- La cache è quella standard Hugging Face: `~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/<hash>/Qwen3.5-0.8B-Q8_0.gguf`
  (link simbolico a `blobs/<sha256>`). `HF_TOKEN` per repo gated.
- Comandi interni della chat: `/exit`, `/regen`, `/clear`, `/read <file>`, `/glob <pattern>`, `/image <file>`, `/audio <file>`.
- Fine risposta: `[ Prompt: 5.3 t/s | Generation: 4.8 t/s ]`.
- Il banner mostra `build`, `model`, `ftype` (es. `Q8_0`), `modalities` (es. `text`).
- Flag chiave: `-c/--ctx-size` (0 = quello del modello), `-n/--predict`, `-t/--threads`, `-sys "..."`, `--temp`
  (default 0.8), `--top-k` 40, `--top-p` 0.95, `--min-p` 0.05, `--repeat-penalty` 1.0, `-s/--seed`, `-ngl N|auto|all`,
  `-fa on|off|auto`, `-ctk/-ctv q8_0` (KV cache quantizzata), `-cmoe` (esperti MoE su CPU), `--fit on|off` (default on:
  adatta i parametri alla memoria), `--list-devices`, `-dev`, `--reasoning-budget N`, `--image f.png`, `--audio f.mp3`,
  `-md draft.gguf --spec-type draft-simple` e `--hf-repo-draft` (speculativa), `--jinja` (default on), `--chat-template`,
  `--load-mode mmap|mlock|dio` (i vecchi `--mmap/--mlock` sono stati rimossi in 0.4.1), `--log-jsonl`, `--offline`.
- `llama completion` = completamento grezzo di testo (no chat template), erede di `-no-cnv`.

## `llama serve` (verificato)

```bash
llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF --host 127.0.0.1 --port 18080 -c 4096 -np 2
```
Log: `srv load_model: initializing, n_slots = 2, n_ctx_slot = 2048` ← **con `-np 2` il contesto 4096 si divide in 2 slot da 2048**
(a meno di `--kv-unified`). Poi `llama_server: listening on http://127.0.0.1:18080`.
Default: `127.0.0.1:8080`, web UI attiva su `/`, `-np -1` = auto.

Endpoint verificati: `GET /health` → `{"status":"ok"}` (503 durante il caricamento); `GET /v1/models`;
`POST /v1/chat/completions` (risposta OpenAI + campo extra `timings` con `prompt_per_second`, `predicted_per_second`,
`cache_n` e `system_fingerprint: b11046-60081bb2b`); `GET /props` (parametri di default: temperature 0.8, top_k 40,
top_p 0.95, min_p 0.05, repeat_penalty 1.0, dry_*, mirostat 0…); `GET /metrics` → 501 se non avvii con `--metrics`.
Altri (docs): `/v1/completions`, `/v1/embeddings` (`--embedding`), `/v1/rerank` (`--rerank --pooling rank`),
`/v1/responses`, `/v1/messages` (formato Anthropic!), `/v1/messages/count_tokens`, `/completion`, `/tokenize`,
`/detokenize`, `/apply-template`, `/infill`, `/slots`, `/lora-adapters`, `/models`, `/models/load`, `/models/unload`.
Per spegnere il thinking per richiesta: `"chat_template_kwargs": {"enable_thinking": false}` nel body (verificato).
`response_format: {"type":"json_schema","schema":{...}}` o `{"type":"json_object"}`; `tools`/`tool_choice` OpenAI.
Flag: `--api-key K1,K2` / `--api-key-file`, `--no-webui`, `-a/--alias nome`, `--metrics`, `--slots` (default on),
`--props`, `--ssl-key-file/--ssl-cert-file`, `--threads-http`, `--cache-reuse N`, `--slot-save-path`,
`--reasoning-format`, `-rea on|off|auto`, `--ui-config '{"theme":"dark"}'`, `--api-prefix`, `--path` (file statici),
`--lora`, `--mmproj`, `--chat-template-kwargs`, `--log-jsonl`.
**Router mode**: `llama serve` **senza modello** avvia un router che carica/scarica modelli su richiesta dalla
cache (`-cl`), da `--models-dir DIR` o da `--models-preset file.ini`; `--models-max N`, `--models-autoload`;
nelle richieste va indicato `"model"`. La web UI mostra allora un selettore di modelli.
Web UI: markdown, KaTeX, blocco "reasoning" ripiegabile, anteprima HTML/JS, allegati immagini/PDF/audio,
branching delle conversazioni, import/export JSON, `Settings → Developer → Custom JSON` per uno schema JSON.
SDK: `openai.OpenAI(base_url="http://localhost:8080/v1", api_key="no-key-required")`.

## Benchmark verificato sul VPS (CPU AMD EPYC 6 vCPU, macchina condivisa e carica)
```
llama bench -m Qwen3.5-0.8B-Q8_0.gguf -p 64 -n 32 -t 6 -r 2
| model             |       size |   params | backend | threads | test |          t/s |
| qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | pp64 | 56.90 ± 15.86 |
| qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | tg32 |  4.29 ± 0.80 |
```
(varianza alta perché il VPS è condiviso; la generazione da chat era 4.8 t/s, dal server 14 t/s con 2 token).

## Modello di prova
`ggml-org/Qwen3.5-0.8B-GGUF` → file `Qwen3.5-0.8B-Q8_0.gguf`, **785 MiB**, 772.85 M parametri, testo, modello
"thinking" (di default ragiona: usare `-rea off` o `enable_thinking:false`). È l'esempio del README ufficiale.
Altri citati nella doc ufficiale: `ggml-org/gemma-4-e4b-it-GGUF:Q4_0` (multimodale: testo+immagini+audio, ~6 GB
con 16k di contesto), `unsloth/gemma-4-E4B-it-GGUF:Q4_K_M`, `ggml-org/gemma-3-4b-it-qat-GGUF`,
`unsloth/embeddinggemma-300m-GGUF` (embedding), `ggml-org/Qwen3-reranker-0.6B-Q8_0-GGUF:Q8_0` (reranker),
`LiquidAI/LFM2.5-230M-GGUF:Q4_K_M`, `ggml-org/GLM-4.7-Flash-GGUF:Q4_K_M`. Ricerca su HF: filtro "apps=llama.cpp".

## Backend supportati (README)
BLAS, BLIS, CANN (Ascend), CUDA, HIP (AMD), Hexagon (Snapdragon), IBM zDNN, MUSA (Moore Threads), Metal,
OpenCL (Adreno), OpenVINO (in progress), RPC, SYCL (Intel), VirtGPU, Vulkan, WebGPU, ZenDNN (AMD CPU).
CPU: AVX/AVX2/AVX512/AMX su x86, NEON/Accelerate su Apple, RVV su RISC-V. Quantizzazioni da 1.5 a 8 bit.

## Novità 0.4.1 (release notes)
Maple 20B-A1B (MoE ternario), Tencent Hy 4, Spark2.5; `--fuse-qkv` in conversione; `--log-jsonl`; rimozione di
`--mmap/--mlock/--direct-io` (→ `--load-mode`); mmproj e draft seguono `--device`; refactor JSON schema
(`common_schema`); parser chat divisi in `common/parsers`; router con monitoraggio dei processi figli.

## Questo VPS
Linux x86_64 Ubuntu 24.04, 6 vCPU AMD EPYC (AVX2, no AVX-512), 11 GB RAM (spesso ~4 liberi), nessuna GPU,
Docker presente. `llama` in `~/.local/bin`, tarball release in `~/llama-lab/rel/llama-b11046/`, cache modelli HF.

## Aggiunte del 23/09/2026 (dagli scrittori)
- `llama cli -j/--json-schema` su b11046 fallisce con `Error: Failed to initialize samplers: std::exception` con qualsiasi
  schema (anche `llama-cli` del tarball); `llama completion -j` e `response_format` sul server funzionano.
- Con `-np N` il contesto si divide per N (`-c 2048 -np 4` → 512 per slot → `400 exceed_context_size_error`);
  `--kv-unified` lo evita. Throughput su 4 richieste parallele: -np 1/2/4 → 6,3 / 5,6 / 12,4 t/s (VPS, CPU).
- Tool calling con Qwen3.5-0.8B: un prompt di sistema troppo "direttivo" fa saltare la chiamata al tool; `tool_choice=required` ignorato.
- Modello embedding in cache: `ggml-org/embeddinggemma-300M-GGUF:Q8_0` (334 MB); router mode con `--models-preset modelli.ini` verificato.
- Qwen3.5-0.8B: arch `qwen35`, n_embd 1024, n_layer 24, n_vocab 248320, n_head 8 / n_head_kv 2, tokenizer gpt2/pre qwen35.
- `llama quantize` da un GGUF già quantizzato (es. Q8_0) richiede `--allow-requantize`. Misure reali: Q4_K_M 506 MiB PPL 12,5; Q2_K 399 MiB PPL 154,9 → con imatrix 34,1.
