# Lab 04-01: Server and web UI

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/04-server-api/README.md">04: `llama serve`: server and API</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Start `llama serve` with a small model, read the startup logs, use the web UI from the browser
(attachments, branching, JSON schema) and query the main endpoints with `curl`: `/health`, `/props`,
`/v1/models`, `/v1/chat/completions` (normal and streaming), `/tokenize`, `/apply-template`, `/slots`, `/metrics`.

## Prerequisites

- `llama` installed and working (module 01), `curl` and `python3` (for `python3 -m json.tool`) or `jq`.
- The module 02 model already in cache (otherwise the first start downloads it: 785 MB).
- Ubuntu with the installer binary: `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, Apache 2.0 license) | Hugging Face, via `-hf` | 785 MiB |
| A photo or a PDF (only if you use a multimodal model, final variant) | yours | – |

## Steps

1. **Start the server** in a terminal you leave open. We use `-c 2048 -np 2` on purpose to see the
   context split, `--metrics` for the Prometheus endpoint and an alias:

    ```bash
    llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF --host 127.0.0.1 --port 8080 -c 2048 -np 2 --metrics -a qwen-0.8b
    ```

    Expected output (the important lines):

    ```
    srv    load_model: initializing, n_slots = 2, n_ctx_slot = 1024, kv_unified = 'false'
    srv  llama_server: model loaded
    srv  llama_server: listening on http://127.0.0.1:8080
    ```

    Note `n_ctx_slot`: you asked for 2048 of context and 2 slots, each request gets 1024.

2. **Check that it is ready** from a second terminal:

    ```bash
    curl -s http://127.0.0.1:8080/health ; echo
    curl -s http://127.0.0.1:8080/v1/models | python3 -m json.tool | head -30
    ```

    Expected: `{"status":"ok"}` and a `data` list with a single model, `"id": "qwen-0.8b"` (the alias), `owned_by: llamacpp`
    and in `meta` the model data (`n_ctx_train`, `n_params`, `size`).

3. **Read the server properties**:

    ```bash
    curl -s http://127.0.0.1:8080/props | python3 -c "
    import json,sys; d=json.load(sys.stdin)
    print('slot:', d['total_slots'], '| n_ctx per slot:', d['default_generation_settings']['n_ctx'])
    print('modalità:', d['modalities'], '| build:', d['build_info'])
    print('template supporta tool:', d['chat_template_caps']['supports_tools'])
    p=d['default_generation_settings']['params']; print({k:p[k] for k in ['temperature','top_k','top_p','min_p','repeat_penalty']})"
    ```

    Expected: `slot: 2 | n_ctx per slot: 1024`, `modalities {'vision': False, 'video': False, 'audio': False}`,
    `build: b11046-60081bb2b`, the default samplers (`temperature 0.8, top_k 40, top_p 0.95, min_p 0.05, repeat_penalty 1.0`).

4. **First chat through the API**. Turn off the model's thinking with `chat_template_kwargs`:

    ```bash
    curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
      "messages": [{"role": "user", "content": "Qual è la capitale d'\''Italia? Rispondi in una frase."}],
      "max_tokens": 40, "temperature": 0,
      "chat_template_kwargs": {"enable_thinking": false}}' | python3 -m json.tool
    ```

    Expected: `"content": "Roma è la capitale d'Italia."`, `finish_reason: stop`, `usage` with 27 prompt tokens and ~9
    completion tokens, and the `timings` block with `prompt_per_second`, `predicted_per_second`, `cache_n: 0`.

5. **Repeat the same request** and look at `timings.cache_n` and `prompt_n`: now the prompt is already in cache
   (`cache_n` close to the total, `prompt_n` small, `prompt_ms` much lower): for example `cache_n 0 → 33`,
   `prompt_ms 1259 → 227`.

6. **Streaming**. Add `"stream": true` and use `curl -N`:

    ```bash
    curl -sN http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
      "messages": [{"role": "user", "content": "Conta da 1 a 5."}],
      "max_tokens": 30, "temperature": 0, "stream": true,
      "chat_template_kwargs": {"enable_thinking": false}}'
    ```

    Expected: lines `data: {"choices":[{"delta":{"content":"…"}}],…,"object":"chat.completion.chunk"}`, one per token,
    a last chunk with `"finish_reason":"stop"` and `timings`, then `data: [DONE]`.

7. **Tokens and template**:

    ```bash
    curl -s http://127.0.0.1:8080/tokenize -H "Content-Type: application/json" -d '{"content":"Ciao mondo!","with_pieces":true}'; echo
    curl -s http://127.0.0.1:8080/apply-template -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"system","content":"Sei un assistente."},{"role":"user","content":"Ciao"}]}'; echo
    ```

    Expected: 4 tokens (`C`, `iao`, ` mondo`, `!`) and the ChatML prompt `<|im_start|>system\n…<|im_start|>assistant\n<think>\n`.
    That final `<think>` is why the model reasons unless you forbid it.

8. **Slots and metrics**:

    ```bash
    curl -s http://127.0.0.1:8080/slots | python3 -m json.tool | grep -E '"id"|n_ctx|is_processing'
    curl -s http://127.0.0.1:8080/metrics | grep -E "^llamacpp:(prompt_tokens_total|tokens_predicted_total|requests_processing)"
    ```

    Expected: two slots with `n_ctx: 1024` and `is_processing: false`; the Prometheus counters with the tokens of the requests made so far.

9. **Web UI**. Open `http://127.0.0.1:8080` in the browser and:
    - ask a question and watch the streaming and the collapsible "reasoning" block (here thinking is on: the UI
      has its own setting to show/hide it and for the sampling parameters);
    - edit a previous message: the conversation **branches**, and the arrows move you from one branch to another;
    - `Settings → Developer → Custom JSON` and paste:

        ```json
        {"json_schema": {"type": "object",
          "properties": {"sentimento": {"type": "string", "enum": ["positivo", "neutro", "negativo"]},
                         "riassunto": {"type": "string", "maxLength": 120}},
          "required": ["sentimento", "riassunto"]}}
        ```

        then write «Il servizio era lento ma il personale gentilissimo»: the answer is a JSON that follows the schema;
    - export the conversation as JSON from the menu, then remove the schema so it does not affect later tests.

10. **Stop the server** with ++ctrl+c++ in the first terminal (or `pkill -f "llama serve"`).

## Check the result

- [ ] In the log you read `n_slots = 2, n_ctx_slot = 1024` and can explain why it is not 2048.
- [ ] `/health` → `{"status":"ok"}`; `/v1/models` reports the alias `qwen-0.8b`.
- [ ] The `/v1/chat/completions` response contains `timings` and on the second call `cache_n > 0`.
- [ ] You saw the SSE stream end with `data: [DONE]`.
- [ ] In the web UI you created a branch and got a JSON that matches the schema.

## Questions and variants

- Start with `-np 1` and `-c 2048`: what is `n_ctx_slot`? And with `-np 2 --kv-unified`? (look at the log and `/props`)
- Start with `--api-key segreta123`: what does `/v1/models` answer without a header? And `/health`? (`401 Invalid API Key`; `/health` stays `200`)
- Start with `--no-webui`: `GET /` answers `404` but the API works. When does it make sense?
- Send a request with `"max_tokens": 10` **without** turning off thinking: what does `content` contain? What do you see in `reasoning_content`?
- Multimodal variant (if you have ≥ 8 GB free): `llama serve -hf ggml-org/gemma-3-4b-it-qat-GGUF` and attach an image in the UI;
  `/props` now reports `"vision": true`.
- Variant `--ui-config '{"theme":"dark"}'`: the UI starts in dark theme.

## Deliverable

A file `lab-04-01.md` with: the three startup log lines; the filtered `/props` output (step 3); the two responses
from steps 4-5 with `cache_n` highlighted; a screenshot (or the JSON export) of the conversation with the branch and the
JSON answer that matches the schema; the answers to the first three questions.
