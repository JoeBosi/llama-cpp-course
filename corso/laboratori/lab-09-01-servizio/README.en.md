# Lab 09-01: The server as a service

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/09-deploy-produzione/README.md">09: Going to production</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60-90 minutes</span>
</div>

## Objective

Install `llama serve` as a systemd service that starts at boot, restarts on its own if it crashes, runs as an
unprivileged user inside a sandbox, reads the API key from a file, writes logs to journald and exposes `/metrics`.
At the end you simulate an update and a rollback.

## Prerequisites

- A Linux machine with systemd where you have `sudo` (VM, VPS, Raspberry Pi OS, WSL2 with systemd enabled).
- [Lab 04-01](../lab-04-01-server-e-webui/README.md): you know how to start the server by hand and query it with `curl`.
- `curl`, `python3` and `jq` (optional) installed.

## Materials

| What | Where | Size |
|---|---|---|
| Model | `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, Apache-2.0) | 785 MiB |
| systemd unit | [`llama-serve.service`](llama-serve.service) (in this folder) | |
| Check script | [`verifica-servizio.sh`](verifica-servizio.sh) (in this folder) | |

If you have 16 GB of RAM: replace the model with `ggml-org/gemma-3-4b-it-qat-GGUF` (2.4 GiB) and raise
`MemoryMax` to `8G`.

## Steps

### 1. Dedicated user and installation

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin llama
sudo -u llama bash -c 'cd && curl -LsSf https://llama.app/install.sh | sh'
sudo -u llama /home/llama/.local/bin/llama version
```

Expected output (the build may be newer):

```
version: 0.4.1-dev (build 11046, commit 60081bb2b)
built with Clang 22.1.8 for Linux x86_64
```

The service must not download anything at startup (it will run with `--offline`): download the model now **as the
`llama` user**, so it lands in that user's cache (`/home/llama/.cache/huggingface/hub`):

```bash
sudo -u llama env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
  /home/llama/.local/bin/llama download -hf ggml-org/Qwen3.5-0.8B-GGUF
sudo -u llama /home/llama/.local/bin/llama serve -cl      # lists the cache: the model must appear
```

### 2. The API key file

```bash
sudo mkdir -p /etc/llama
printf '# una chiave per riga; le righe con # sono commenti\n%s\n' "$(openssl rand -hex 24)" | sudo tee /etc/llama/api-keys.txt >/dev/null
sudo chown root:llama /etc/llama/api-keys.txt
sudo chmod 640 /etc/llama/api-keys.txt
sudo cat /etc/llama/api-keys.txt
```

Write down the key: you will use it in the clients. The service reads it (group `llama`), no other user can.

### 3. Installing the unit

Copy [`llama-serve.service`](llama-serve.service) to `/etc/systemd/system/` and read it line by line: the
`LLAMA_ARG_*` variables are the server configuration, the final part is the sandbox.

```bash
sudo cp llama-serve.service /etc/systemd/system/llama-serve.service
sudo nano /etc/systemd/system/llama-serve.service      # set LLAMA_ARG_THREADS to the number of physical cores
sudo systemd-analyze verify /etc/systemd/system/llama-serve.service
```

`systemd-analyze verify` prints nothing if the unit is correct. If it prints `Command /home/llama/.local/bin/llama
is not executable`, check step 1.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now llama-serve
sleep 5; systemctl status llama-serve --no-pager
```

Expected output (shortened):

```
● llama-serve.service - llama.cpp - server di inferenza (llama serve)
     Loaded: loaded (/etc/systemd/system/llama-serve.service; enabled; preset: enabled)
     Active: active (running) since ...
   Main PID: 12345 (llama)
     Memory: 1.1G (max: 6.0G)
   …
   llama[12345]: srv  load_model: initializing, n_slots = 2, n_ctx_slot = 4096
   llama[12345]: llama_server: listening on http://127.0.0.1:8080
```

Note `n_ctx_slot = 4096`: `LLAMA_ARG_CTX_SIZE=8192` divided by `LLAMA_ARG_N_PARALLEL=2`.

### 4. Checking that it answers

```bash
curl -s http://127.0.0.1:8080/health; echo
KEY=$(sudo grep -v '^#' /etc/llama/api-keys.txt | head -1)
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Ciao! Rispondi in 5 parole."}],"max_tokens":32,"chat_template_kwargs":{"enable_thinking":false}}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["choices"][0]["message"]["content"]); print(d["timings"]["predicted_per_second"], "t/s")'
```

Expected: `{"status":"ok"}`, then a short answer and the speed. Now try **without** the key:

```bash
curl -s http://127.0.0.1:8080/v1/models; echo
```

Expected: `{"error":{"code":401,"message":"Invalid API Key","type":"authentication_error"}}`. `/health`, on the other hand,
answers even without a key: it is public by design.

The script [`verifica-servizio.sh`](verifica-servizio.sh) does all of this in one go and returns 0/1: use it after
every change.

```bash
chmod +x verifica-servizio.sh
sudo ./verifica-servizio.sh                 # reads the key from /etc/llama/api-keys.txt
```

### 5. Making it crash on purpose

```bash
sudo kill -9 $(systemctl show -p MainPID --value llama-serve)
sleep 1; systemctl status llama-serve --no-pager | head -5     # activating (auto-restart)
sleep 10; curl -s http://127.0.0.1:8080/health; echo             # {"status":"ok"} again
journalctl -u llama-serve -n 20 --no-pager
```

In the journal you see `Main process exited, code=killed, status=9/KILL`, then `Scheduled restart job` and the
model loading from scratch. Also try `sudo systemctl stop llama-serve`: it does **not** restart (intentional
exit, `Restart=on-failure`).

### 6. Logs and metrics

```bash
journalctl -u llama-serve -f                # follow the logs; make a request in another terminal
journalctl -u llama-serve -p warning        # warnings and errors only
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8080/metrics | grep -E '^llamacpp:(tokens_predicted_total|requests_)'
```

In the log of each request you find lines such as `slot launch_slot_: id  0 | task 3 | processing task` and, at the end of
generation, the prompt and generation timings. If you prefer structured logs, add
`Environment=LLAMA_ARG_LOG_JSONL=1` and restart: every journald line becomes a JSON object.

### 7. How tight is the sandbox?

```bash
sudo systemd-analyze security llama-serve --no-pager | tail -3
```

With the lab's unit the score drops below 7 ("MEDIUM" or "EXPOSED", against "UNSAFE" ~9.6 for a unit
without directives). Try removing `ProtectSystem=strict` and check again: you see what carries weight. Also check
that the sandbox works: `sudo -u llama touch /etc/prova` always fails, but with `ProtectSystem=strict` it also fails
from the service process, which also runs as `llama`, should it ever be compromised.

### 8. Update and rollback

```bash
sudo -u llama cp /home/llama/.local/bin/llama /home/llama/.local/bin/llama-b11046   # backup copy
sudo -u llama env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt /home/llama/.local/bin/llama update
sudo -u llama /home/llama/.local/bin/llama version
sudo systemctl restart llama-serve && sleep 8 && sudo ./verifica-servizio.sh
```

If the script returns 1 (or the speed has collapsed), roll back:

```bash
sudo -u llama cp /home/llama/.local/bin/llama-b11046 /home/llama/.local/bin/llama
sudo systemctl restart llama-serve && sleep 8 && sudo ./verifica-servizio.sh
```

If you want to pin a specific build instead: `sudo -u llama env LLAMA_VERSION=b11046 bash -c 'curl -LsSf https://llama.app/install.sh | sh'`.

## Check the result

- [ ] `systemctl is-enabled llama-serve` prints `enabled`; after a machine reboot `/health` returns 200 without intervention.
- [ ] After `kill -9` the service is back to `active (running)` within ~15 s.
- [ ] Without a key: 401 on `/v1/models`; with a key: an answer. `/health` always answers.
- [ ] `ss -ltnp | grep 8080` shows `127.0.0.1:8080`, not `0.0.0.0` or `*`.
- [ ] `verifica-servizio.sh` returns 0 and prints the generation speed.

## Questions and variations

1. Move the configuration into `EnvironmentFile=/etc/llama/serve.env` instead of many `Environment=` lines. What do you gain for managing keys and secrets?
2. Add a second service `llama-embed.service` on port 8081 with `unsloth/embeddinggemma-300m-GGUF` and `LLAMA_ARG_EMBEDDINGS=1`. How much RAM does it take? Could you use a single process in *router mode* instead of two services?
3. Set `MemoryMax=512M` and restart: what do you see in `journalctl`? (Set it back to `6G` afterwards.)
4. With `Restart=always` and `systemctl stop`, does the service restart? Try it and explain.
5. On a Raspberry Pi or a machine with a GPU, which variables would you change? (`LLAMA_ARG_THREADS`, `LLAMA_ARG_N_GPU_LAYERS`, `MemoryMax`.)

## Deliverable

- The final `llama-serve.service` file (with your values) and `api-keys.txt` with the keys **redacted**.
- The output of `systemctl status`, of `journalctl` after the `kill -9` and of `systemd-analyze security`.
- The output of `verifica-servizio.sh` before and after the update (or after the rollback), with the speeds compared.
- Three lines: what you would do differently for an 8 GB model on a machine with 16 GB.
