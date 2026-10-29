# Useful links

## Official documentation

- Repository: https://github.com/ggml-org/llama.cpp (README with the list of supported backends and models)
- Site and installer: https://llama.app · quickstart https://llama.app/docs/quickstart · installation https://llama.app/docs/installation
- `llama cli`: https://llama.app/docs/cli · `llama serve`: https://llama.app/docs/serve · API: https://llama.app/docs/api · web UI: https://llama.app/docs/webui
- Server (all flags, endpoints, metrics, router mode): https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- Building from source: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md · installation with package managers: https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md
- Docker: https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md · images: https://github.com/ggml-org/llama.cpp/pkgs/container/llama.cpp
- Releases and nightly builds: https://github.com/ggml-org/llama.cpp/releases · release process: https://github.com/ggml-org/llama.cpp/blob/master/docs/release.md
- Multimodal (mtmd): https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md · https://github.com/ggml-org/llama.cpp/tree/master/tools/mtmd
- Function calling: https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md
- GBNF grammars: https://github.com/ggml-org/llama.cpp/tree/master/grammars
- Quantization: https://github.com/ggml-org/llama.cpp/tree/master/tools/quantize · imatrix: https://github.com/ggml-org/llama.cpp/tree/master/tools/imatrix · perplexity/KLD: https://github.com/ggml-org/llama.cpp/tree/master/tools/perplexity
- Benchmark: https://github.com/ggml-org/llama.cpp/tree/master/tools/llama-bench · performance tips: https://github.com/ggml-org/llama.cpp/blob/master/docs/development/token_generation_performance_tips.md
- Multi-GPU: https://github.com/ggml-org/llama.cpp/blob/master/docs/multi-gpu.md · RPC: https://github.com/ggml-org/llama.cpp/tree/master/tools/rpc
- Android: https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md · iOS/macOS (xcframework): https://github.com/ggml-org/llama.cpp/blob/master/docs/xcframework.md
- Backends: SYCL https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md · OpenCL https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENCL.md
- C API (`llama.h`): https://github.com/ggml-org/llama.cpp/blob/master/include/llama.h · examples: https://github.com/ggml-org/llama.cpp/tree/master/examples
- ggml: https://github.com/ggml-org/ggml · GGUF format: https://github.com/ggml-org/ggml/blob/master/docs/gguf.md
- Server changelog: https://github.com/ggml-org/llama.cpp/issues/9291 · `libllama` changelog: https://github.com/ggml-org/llama.cpp/issues/9289

## Models

- Official ggml-org GGUFs: https://huggingface.co/ggml-org
- Search with the llama.cpp filter: https://huggingface.co/models?apps=llama.cpp&sort=trending
- Reliable quantizers: https://huggingface.co/unsloth · https://huggingface.co/bartowski · https://huggingface.co/LiquidAI
- Convert and quantize in the browser: GGUF-my-repo https://huggingface.co/spaces/ggml-org/gguf-my-repo · GGUF-my-LoRA https://huggingface.co/spaces/ggml-org/gguf-my-lora · metadata editor https://huggingface.co/spaces/CISCai/gguf-editor
- [Recommended models for the course](modelli-consigliati.md) (repositories, files, sizes and licenses)

## Community and discussions

- GitHub Discussions: https://github.com/ggml-org/llama.cpp/discussions (announcements, "show and tell", questions)
- Issues and roadmap: https://github.com/ggml-org/llama.cpp/issues · https://github.com/ggml-org/llama.cpp/discussions/categories/announcements
- ggml.ai blog: https://ggml.ai · Hugging Face blog on llama.cpp: https://huggingface.co/blog?tag=llama.cpp
- Subreddit r/LocalLLaMA: https://www.reddit.com/r/LocalLLaMA/ (quantization comparisons, hardware, news)
- ggml Discord (link in the repository README)

## Compatible tools (they use llama.cpp or its API)

| Tool | What it is | Link |
|---|---|---|
| Open WebUI | full web UI (users, RAG, documents) that connects to the OpenAI-compatible API of `llama serve` | https://github.com/open-webui/open-webui |
| LM Studio | desktop app (Windows/macOS/Linux) with a built-in llama.cpp engine and a GGUF catalog | https://lmstudio.ai |
| Ollama | model manager with CLI and API, based on llama.cpp/ggml; GGUF models importable with a `Modelfile` | https://ollama.com |
| Jan | open source desktop app, llama.cpp engine, local API | https://jan.ai |
| KoboldCpp | llama.cpp fork aimed at storytelling, with a built-in UI | https://github.com/LostRuins/koboldcpp |
| llama-cpp-python | Python bindings for `libllama` with an OpenAI-compatible server | https://github.com/abetlen/llama-cpp-python |
| node-llama-cpp | Node.js bindings | https://github.com/withcatai/node-llama-cpp |
| llama.vim / llama.vscode | local code completion (infill) with `llama serve` | https://github.com/ggml-org/llama.vim · https://github.com/ggml-org/llama.vscode |
| Continue / Cline | code assistants in IDEs, configurable to point at `http://localhost:8080/v1` | https://continue.dev · https://cline.bot |
| whisper.cpp | speech transcription with the same ggml engine | https://github.com/ggml-org/whisper.cpp |
| OpenAI SDK (Python/JS) | official clients: just set `base_url="http://localhost:8080/v1"` | https://github.com/openai/openai-python · https://github.com/openai/openai-node |

## Production and monitoring (module 09)

- Caddy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy · `basic_auth` https://caddyserver.com/docs/caddyfile/directives/basic_auth · rate limit (plugin) https://github.com/mholt/caddy-ratelimit
- Nginx: `ngx_http_proxy_module` https://nginx.org/en/docs/http/ngx_http_proxy_module.html · `limit_req` https://nginx.org/en/docs/http/ngx_http_limit_req_module.html · certbot https://certbot.eff.org
- systemd: `systemd.exec` (sandboxing) https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html · `systemd.service` https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- Prometheus: https://prometheus.io/docs/prometheus/latest/configuration/configuration/ · Grafana: https://grafana.com/docs/grafana/latest/
- Docker Compose (healthcheck, secrets): https://docs.docker.com/compose/compose-file/
- OWASP Top 10 for LLM applications (prompt injection and more): https://owasp.org/www-project-top-10-for-large-language-model-applications/
