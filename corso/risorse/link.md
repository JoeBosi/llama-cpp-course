# Link utili

## Documentazione ufficiale

- Repository: https://github.com/ggml-org/llama.cpp (README con l'elenco dei backend e dei modelli supportati)
- Sito e installer: https://llama.app · guida rapida https://llama.app/docs/quickstart · installazione https://llama.app/docs/installation
- `llama cli`: https://llama.app/docs/cli · `llama serve`: https://llama.app/docs/serve · API: https://llama.app/docs/api · web UI: https://llama.app/docs/webui
- Server (tutti i flag, endpoint, metriche, router mode): https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- Build dai sorgenti: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md · installazione con gestori di pacchetti: https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md
- Docker: https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md · immagini: https://github.com/ggml-org/llama.cpp/pkgs/container/llama.cpp
- Release e build notturne: https://github.com/ggml-org/llama.cpp/releases · processo di release: https://github.com/ggml-org/llama.cpp/blob/master/docs/release.md
- Multimodale (mtmd): https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md · https://github.com/ggml-org/llama.cpp/tree/master/tools/mtmd
- Function calling: https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md
- Grammatiche GBNF: https://github.com/ggml-org/llama.cpp/tree/master/grammars
- Quantizzazione: https://github.com/ggml-org/llama.cpp/tree/master/tools/quantize · imatrix: https://github.com/ggml-org/llama.cpp/tree/master/tools/imatrix · perplexity/KLD: https://github.com/ggml-org/llama.cpp/tree/master/tools/perplexity
- Benchmark: https://github.com/ggml-org/llama.cpp/tree/master/tools/llama-bench · consigli sulle prestazioni: https://github.com/ggml-org/llama.cpp/blob/master/docs/development/token_generation_performance_tips.md
- Multi-GPU: https://github.com/ggml-org/llama.cpp/blob/master/docs/multi-gpu.md · RPC: https://github.com/ggml-org/llama.cpp/tree/master/tools/rpc
- Android: https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md · iOS/macOS (xcframework): https://github.com/ggml-org/llama.cpp/blob/master/docs/xcframework.md
- Backend: SYCL https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md · OpenCL https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENCL.md
- API C (`llama.h`): https://github.com/ggml-org/llama.cpp/blob/master/include/llama.h · esempi: https://github.com/ggml-org/llama.cpp/tree/master/examples
- ggml: https://github.com/ggml-org/ggml · formato GGUF: https://github.com/ggml-org/ggml/blob/master/docs/gguf.md
- Changelog del server: https://github.com/ggml-org/llama.cpp/issues/9291 · changelog di `libllama`: https://github.com/ggml-org/llama.cpp/issues/9289

## Modelli

- GGUF ufficiali di ggml-org: https://huggingface.co/ggml-org
- Ricerca con filtro llama.cpp: https://huggingface.co/models?apps=llama.cpp&sort=trending
- Quantizzatori affidabili: https://huggingface.co/unsloth · https://huggingface.co/bartowski · https://huggingface.co/LiquidAI
- Convertire e quantizzare nel browser: GGUF-my-repo https://huggingface.co/spaces/ggml-org/gguf-my-repo · GGUF-my-LoRA https://huggingface.co/spaces/ggml-org/gguf-my-lora · editor di metadati https://huggingface.co/spaces/CISCai/gguf-editor
- [Modelli consigliati per il corso](modelli-consigliati.md) (repository, file, dimensioni e licenze)

## Community e discussioni

- Discussioni GitHub: https://github.com/ggml-org/llama.cpp/discussions (annunci, "show and tell", domande)
- Issue e roadmap: https://github.com/ggml-org/llama.cpp/issues · https://github.com/ggml-org/llama.cpp/discussions/categories/announcements
- Blog di ggml.ai: https://ggml.ai · blog Hugging Face su llama.cpp: https://huggingface.co/blog?tag=llama.cpp
- Subreddit r/LocalLLaMA: https://www.reddit.com/r/LocalLLaMA/ (confronti di quantizzazioni, hardware, novità)
- Discord di ggml (link nel README del repository)

## Strumenti compatibili (usano llama.cpp o la sua API)

| Strumento | Cos'è | Link |
|---|---|---|
| Open WebUI | interfaccia web completa (utenti, RAG, documenti) che si collega all'API OpenAI-compatibile di `llama serve` | https://github.com/open-webui/open-webui |
| LM Studio | app desktop (Windows/macOS/Linux) con motore llama.cpp integrato e catalogo di GGUF | https://lmstudio.ai |
| Ollama | gestore di modelli con CLI e API, basato su llama.cpp/ggml; modelli GGUF importabili con un `Modelfile` | https://ollama.com |
| Jan | app desktop open source, motore llama.cpp, API locale | https://jan.ai |
| KoboldCpp | fork di llama.cpp orientato alla narrativa, con UI integrata | https://github.com/LostRuins/koboldcpp |
| llama-cpp-python | binding Python di `libllama` con server OpenAI-compatibile | https://github.com/abetlen/llama-cpp-python |
| node-llama-cpp | binding Node.js | https://github.com/withcatai/node-llama-cpp |
| llama.vim / llama.vscode | completamento di codice locale (infill) con `llama serve` | https://github.com/ggml-org/llama.vim · https://github.com/ggml-org/llama.vscode |
| Continue / Cline | assistenti di codice negli IDE, configurabili verso `http://localhost:8080/v1` | https://continue.dev · https://cline.bot |
| whisper.cpp | trascrizione vocale con lo stesso motore ggml | https://github.com/ggml-org/whisper.cpp |
| SDK OpenAI (Python/JS) | client ufficiali: basta `base_url="http://localhost:8080/v1"` | https://github.com/openai/openai-python · https://github.com/openai/openai-node |

## Produzione e monitoraggio (modulo 09)

- Caddy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy · `basic_auth` https://caddyserver.com/docs/caddyfile/directives/basic_auth · rate limit (plugin) https://github.com/mholt/caddy-ratelimit
- Nginx: `ngx_http_proxy_module` https://nginx.org/en/docs/http/ngx_http_proxy_module.html · `limit_req` https://nginx.org/en/docs/http/ngx_http_limit_req_module.html · certbot https://certbot.eff.org
- systemd: `systemd.exec` (sandboxing) https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html · `systemd.service` https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- Prometheus: https://prometheus.io/docs/prometheus/latest/configuration/configuration/ · Grafana: https://grafana.com/docs/grafana/latest/
- Docker Compose (healthcheck, secrets): https://docs.docker.com/compose/compose-file/
- OWASP Top 10 per applicazioni LLM (prompt injection e altro): https://owasp.org/www-project-top-10-for-large-language-model-applications/
