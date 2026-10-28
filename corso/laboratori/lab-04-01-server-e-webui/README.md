# Lab 04-01: Server e web UI

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/04-server-api/README.md">04: `llama serve`: server e API</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
</div>

## Obiettivo

Avviare `llama serve` con un modello piccolo, leggere i log di avvio, usare la web UI dal browser
(allegati, branching, schema JSON) e interrogare con `curl` gli endpoint principali: `/health`, `/props`,
`/v1/models`, `/v1/chat/completions` (normale e streaming), `/tokenize`, `/apply-template`, `/slots`, `/metrics`.

## Prerequisiti

- `llama` installato e funzionante (modulo 01), `curl` e `python3` (per `python3 -m json.tool`) o `jq`.
- Il modello del modulo 02 già in cache (altrimenti il primo avvio lo scarica: 785 MB).
- Ubuntu con binario dell'installer: `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, licenza Apache 2.0) | Hugging Face, via `-hf` | 785 MiB |
| Una foto o un PDF (solo se usi un modello multimodale, variante finale) | tua | – |

## Procedura

1. **Avvia il server** in un terminale che lascerai aperto. Usiamo `-c 2048 -np 2` apposta per vedere la
   divisione del contesto, `--metrics` per l'endpoint Prometheus e un alias:

    ```bash
    llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF --host 127.0.0.1 --port 8080 -c 2048 -np 2 --metrics -a qwen-0.8b
    ```

    Output atteso (le righe importanti):

    ```
    srv    load_model: initializing, n_slots = 2, n_ctx_slot = 1024, kv_unified = 'false'
    srv  llama_server: model loaded
    srv  llama_server: listening on http://127.0.0.1:8080
    ```

    Annota `n_ctx_slot`: hai chiesto 2048 di contesto e 2 slot, ogni richiesta ne avrà 1024.

2. **Controlla che sia pronto** da un secondo terminale:

    ```bash
    curl -s http://127.0.0.1:8080/health ; echo
    curl -s http://127.0.0.1:8080/v1/models | python3 -m json.tool | head -30
    ```

    Atteso: `{"status":"ok"}` e un elenco `data` con un solo modello, `"id": "qwen-0.8b"` (l'alias), `owned_by: llamacpp`
    e in `meta` i dati del modello (`n_ctx_train`, `n_params`, `size`).

3. **Leggi le proprietà del server**:

    ```bash
    curl -s http://127.0.0.1:8080/props | python3 -c "
    import json,sys; d=json.load(sys.stdin)
    print('slot:', d['total_slots'], '| n_ctx per slot:', d['default_generation_settings']['n_ctx'])
    print('modalità:', d['modalities'], '| build:', d['build_info'])
    print('template supporta tool:', d['chat_template_caps']['supports_tools'])
    p=d['default_generation_settings']['params']; print({k:p[k] for k in ['temperature','top_k','top_p','min_p','repeat_penalty']})"
    ```

    Atteso: `slot: 2 | n_ctx per slot: 1024`, `modalities {'vision': False, 'video': False, 'audio': False}`,
    `build: b11046-60081bb2b`, i sampler di default (`temperature 0.8, top_k 40, top_p 0.95, min_p 0.05, repeat_penalty 1.0`).

4. **Prima chat via API**. Spegniamo il thinking del modello con `chat_template_kwargs`:

    ```bash
    curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
      "messages": [{"role": "user", "content": "Qual è la capitale d'\''Italia? Rispondi in una frase."}],
      "max_tokens": 40, "temperature": 0,
      "chat_template_kwargs": {"enable_thinking": false}}' | python3 -m json.tool
    ```

    Atteso: `"content": "Roma è la capitale d'Italia."`, `finish_reason: stop`, `usage` con 27 token di prompt e ~9 di
    completamento, e il blocco `timings` con `prompt_per_second`, `predicted_per_second`, `cache_n: 0`.

5. **Ripeti la stessa richiesta** e guarda `timings.cache_n` e `prompt_n`: ora il prompt è già in cache
   (`cache_n` vicino al totale, `prompt_n` piccolo, `prompt_ms` molto più basso): ad esempio `cache_n 0 → 33`,
   `prompt_ms 1259 → 227`.

6. **Streaming**. Aggiungi `"stream": true` e usa `curl -N`:

    ```bash
    curl -sN http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
      "messages": [{"role": "user", "content": "Conta da 1 a 5."}],
      "max_tokens": 30, "temperature": 0, "stream": true,
      "chat_template_kwargs": {"enable_thinking": false}}'
    ```

    Atteso: righe `data: {"choices":[{"delta":{"content":"…"}}],…,"object":"chat.completion.chunk"}`, una per token,
    un ultimo chunk con `"finish_reason":"stop"` e `timings`, poi `data: [DONE]`.

7. **Token e template**:

    ```bash
    curl -s http://127.0.0.1:8080/tokenize -H "Content-Type: application/json" -d '{"content":"Ciao mondo!","with_pieces":true}'; echo
    curl -s http://127.0.0.1:8080/apply-template -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"system","content":"Sei un assistente."},{"role":"user","content":"Ciao"}]}'; echo
    ```

    Atteso: 4 token (`C`, `iao`, ` mondo`, `!`) e il prompt ChatML `<|im_start|>system\n…<|im_start|>assistant\n<think>\n`.
    Quel `<think>` finale è il motivo per cui il modello ragiona se non glielo vieti.

8. **Slot e metriche**:

    ```bash
    curl -s http://127.0.0.1:8080/slots | python3 -m json.tool | grep -E '"id"|n_ctx|is_processing'
    curl -s http://127.0.0.1:8080/metrics | grep -E "^llamacpp:(prompt_tokens_total|tokens_predicted_total|requests_processing)"
    ```

    Atteso: due slot con `n_ctx: 1024` e `is_processing: false`; i contatori Prometheus con i token delle richieste fatte finora.

9. **Web UI**. Apri `http://127.0.0.1:8080` nel browser e:
    - fai una domanda e osserva lo streaming e il blocco "reasoning" ripiegabile (qui il thinking è attivo: la UI
      ha la sua impostazione per mostrarlo/nasconderlo e per i parametri di campionamento);
    - modifica un messaggio precedente: la conversazione si **biforca**, con le frecce passi da un ramo all'altro;
    - `Settings → Developer → Custom JSON` e incolla:

        ```json
        {"json_schema": {"type": "object",
          "properties": {"sentimento": {"type": "string", "enum": ["positivo", "neutro", "negativo"]},
                         "riassunto": {"type": "string", "maxLength": 120}},
          "required": ["sentimento", "riassunto"]}}
        ```

        poi scrivi «Il servizio era lento ma il personale gentilissimo»: la risposta è un JSON che rispetta lo schema;
    - esporta la conversazione in JSON dal menu, poi rimuovi lo schema per non condizionare le prove successive.

10. **Ferma il server** con ++ctrl+c++ nel primo terminale (o `pkill -f "llama serve"`).

## Verifica del risultato

- [ ] Nel log hai letto `n_slots = 2, n_ctx_slot = 1024` e sai spiegare perché non 2048.
- [ ] `/health` → `{"status":"ok"}`; `/v1/models` riporta l'alias `qwen-0.8b`.
- [ ] La risposta di `/v1/chat/completions` contiene `timings` e alla seconda chiamata `cache_n > 0`.
- [ ] Hai visto lo stream SSE terminare con `data: [DONE]`.
- [ ] Nella web UI hai creato un ramo e ottenuto un JSON conforme allo schema.

## Domande e varianti

- Avvia con `-np 1` e `-c 2048`: quanto vale `n_ctx_slot`? E con `-np 2 --kv-unified`? (guarda il log e `/props`)
- Avvia con `--api-key segreta123`: cosa risponde `/v1/models` senza header? E `/health`? (`401 Invalid API Key`; `/health` resta `200`)
- Avvia con `--no-webui`: `GET /` risponde `404` ma l'API funziona. Quando ha senso?
- Manda una richiesta con `"max_tokens": 10` **senza** spegnere il thinking: cosa contiene `content`? Cosa vedi in `reasoning_content`?
- Variante multimodale (se hai ≥ 8 GB liberi): `llama serve -hf ggml-org/gemma-3-4b-it-qat-GGUF` e allega un'immagine nella UI;
  `/props` ora riporta `"vision": true`.
- Variante `--ui-config '{"theme":"dark"}'`: la UI parte in tema scuro.

## Consegna

Un file `lab-04-01.md` con: le tre righe di log dell'avvio; l'output di `/props` filtrato (punto 3); le due risposte
del punto 4-5 con `cache_n` evidenziato; uno screenshot (o l'export JSON) della conversazione con il ramo e la
risposta JSON conforme allo schema; le risposte alle prime tre domande.
