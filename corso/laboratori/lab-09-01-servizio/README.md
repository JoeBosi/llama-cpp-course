# Lab 09-01: Il server come servizio

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/09-deploy-produzione/README.md">09: Messa in produzione</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60-90 minuti</span>
</div>

## Obiettivo

Installare `llama serve` come servizio systemd che parte al boot, riparte da solo se cade, gira con un utente
senza privilegi e in un sandbox, legge la chiave API da un file, scrive i log in journald ed espone `/metrics`.
Alla fine simuli un aggiornamento e un rollback.

## Prerequisiti

- Una macchina Linux con systemd su cui hai `sudo` (VM, VPS, Raspberry Pi OS, WSL2 con systemd abilitato).
- [Lab 04-01](../lab-04-01-server-e-webui/README.md): sai avviare il server a mano e interrogarlo con `curl`.
- `curl`, `python3` e `jq` (opzionale) installati.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| Modello | `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, Apache-2.0) | 785 MiB |
| Unità systemd | [`llama-serve.service`](llama-serve.service) (in questa cartella) | |
| Script di verifica | [`verifica-servizio.sh`](verifica-servizio.sh) (in questa cartella) | |

Per chi ha 16 GB di RAM: sostituisci il modello con `ggml-org/gemma-3-4b-it-qat-GGUF` (2,4 GiB) e alza
`MemoryMax` a `8G`.

## Procedura

### 1. Utente dedicato e installazione

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin llama
sudo -u llama bash -c 'cd && curl -LsSf https://llama.app/install.sh | sh'
sudo -u llama /home/llama/.local/bin/llama version
```

Output atteso (la build può essere più recente):

```
version: 0.4.1-dev (build 11046, commit 60081bb2b)
built with Clang 22.1.8 for Linux x86_64
```

Il servizio non deve scaricare nulla all'avvio (partirà con `--offline`): scarica ora il modello **come utente
`llama`**, così finisce nella sua cache (`/home/llama/.cache/huggingface/hub`):

```bash
sudo -u llama env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
  /home/llama/.local/bin/llama download -hf ggml-org/Qwen3.5-0.8B-GGUF
sudo -u llama /home/llama/.local/bin/llama serve -cl      # elenca la cache: deve comparire il modello
```

### 2. Il file delle chiavi API

```bash
sudo mkdir -p /etc/llama
printf '# una chiave per riga; le righe con # sono commenti\n%s\n' "$(openssl rand -hex 24)" | sudo tee /etc/llama/api-keys.txt >/dev/null
sudo chown root:llama /etc/llama/api-keys.txt
sudo chmod 640 /etc/llama/api-keys.txt
sudo cat /etc/llama/api-keys.txt
```

Segnati la chiave: la userai nei client. Il servizio la legge (gruppo `llama`), nessun altro utente può.

### 3. Installare l'unità

Copia [`llama-serve.service`](llama-serve.service) in `/etc/systemd/system/` e leggilo riga per riga: le
variabili `LLAMA_ARG_*` sono la configurazione del server, la parte finale è il sandbox.

```bash
sudo cp llama-serve.service /etc/systemd/system/llama-serve.service
sudo nano /etc/systemd/system/llama-serve.service      # adatta LLAMA_ARG_THREADS al numero di core fisici
sudo systemd-analyze verify /etc/systemd/system/llama-serve.service
```

`systemd-analyze verify` non stampa nulla se l'unità è corretta. Se stampa `Command /home/llama/.local/bin/llama
is not executable`, controlla il passo 1.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now llama-serve
sleep 5; systemctl status llama-serve --no-pager
```

Output atteso (accorciato):

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

Nota `n_ctx_slot = 4096`: `LLAMA_ARG_CTX_SIZE=8192` diviso per `LLAMA_ARG_N_PARALLEL=2`.

### 4. Verificare che risponda

```bash
curl -s http://127.0.0.1:8080/health; echo
KEY=$(sudo grep -v '^#' /etc/llama/api-keys.txt | head -1)
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Ciao! Rispondi in 5 parole."}],"max_tokens":32,"chat_template_kwargs":{"enable_thinking":false}}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["choices"][0]["message"]["content"]); print(d["timings"]["predicted_per_second"], "t/s")'
```

Atteso: `{"status":"ok"}`, poi una risposta breve e la velocità. Ora prova **senza** chiave:

```bash
curl -s http://127.0.0.1:8080/v1/models; echo
```

Atteso: `{"error":{"code":401,"message":"Invalid API Key","type":"authentication_error"}}`. Mentre `/health`
risponde anche senza chiave: è pubblico per costruzione.

Lo script [`verifica-servizio.sh`](verifica-servizio.sh) fa tutto questo in un colpo e torna 0/1: usalo dopo
ogni modifica.

```bash
chmod +x verifica-servizio.sh
sudo ./verifica-servizio.sh                 # legge la chiave da /etc/llama/api-keys.txt
```

### 5. Farlo cadere apposta

```bash
sudo kill -9 $(systemctl show -p MainPID --value llama-serve)
sleep 1; systemctl status llama-serve --no-pager | head -5     # activating (auto-restart)
sleep 10; curl -s http://127.0.0.1:8080/health; echo             # di nuovo {"status":"ok"}
journalctl -u llama-serve -n 20 --no-pager
```

Nel journal vedi `Main process exited, code=killed, status=9/KILL`, poi `Scheduled restart job` e il
caricamento del modello da capo. Prova anche `sudo systemctl stop llama-serve`: **non** riparte (uscita
voluta, `Restart=on-failure`).

### 6. Log e metriche

```bash
journalctl -u llama-serve -f                # segui i log; fai una richiesta in un altro terminale
journalctl -u llama-serve -p warning        # solo avvisi ed errori
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8080/metrics | grep -E '^llamacpp:(tokens_predicted_total|requests_)'
```

Nel log di ogni richiesta trovi righe come `slot launch_slot_: id  0 | task 3 | processing task` e, a fine
generazione, i tempi di prompt e generazione. Se preferisci log strutturati, aggiungi
`Environment=LLAMA_ARG_LOG_JSONL=1` e riavvia: ogni riga di journald diventa un oggetto JSON.

### 7. Quanto è chiuso il sandbox?

```bash
sudo systemd-analyze security llama-serve --no-pager | tail -3
```

Con l'unità del lab il punteggio scende sotto 7 ("MEDIUM" o "EXPOSED", contro "UNSAFE" ~9.6 di un'unità
senza direttive). Prova a togliere `ProtectSystem=strict` e ricontrolla: capisci cosa pesa. Verifica anche
che il sandbox funzioni: `sudo -u llama touch /etc/prova` fallisce sempre, ma con `ProtectSystem=strict` fallisce
anche dal processo del servizio, che pure gira come `llama`, se mai venisse compromesso.

### 8. Aggiornamento e rollback

```bash
sudo -u llama cp /home/llama/.local/bin/llama /home/llama/.local/bin/llama-b11046   # copia di sicurezza
sudo -u llama env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt /home/llama/.local/bin/llama update
sudo -u llama /home/llama/.local/bin/llama version
sudo systemctl restart llama-serve && sleep 8 && sudo ./verifica-servizio.sh
```

Se lo script torna 1 (o la velocità è crollata), rollback:

```bash
sudo -u llama cp /home/llama/.local/bin/llama-b11046 /home/llama/.local/bin/llama
sudo systemctl restart llama-serve && sleep 8 && sudo ./verifica-servizio.sh
```

Se invece vuoi fissare una build precisa: `sudo -u llama env LLAMA_VERSION=b11046 bash -c 'curl -LsSf https://llama.app/install.sh | sh'`.

## Verifica del risultato

- [ ] `systemctl is-enabled llama-serve` stampa `enabled`; dopo un riavvio della macchina `/health` risponde 200 senza intervento.
- [ ] Dopo `kill -9` il servizio è tornato `active (running)` entro ~15 s.
- [ ] Senza chiave: 401 su `/v1/models`; con chiave: risposta. `/health` risponde sempre.
- [ ] `ss -ltnp | grep 8080` mostra `127.0.0.1:8080`, non `0.0.0.0` o `*`.
- [ ] `verifica-servizio.sh` torna 0 e stampa la velocità di generazione.

## Domande e varianti

1. Sposta la configurazione in `EnvironmentFile=/etc/llama/serve.env` invece di tante righe `Environment=`. Che cosa guadagni per la gestione delle chiavi e dei segreti?
2. Aggiungi un secondo servizio `llama-embed.service` sulla porta 8081 con `unsloth/embeddinggemma-300m-GGUF` e `LLAMA_ARG_EMBEDDINGS=1`. Quanto pesa in RAM? Potresti usare un solo processo in *router mode* al posto di due servizi?
3. Imposta `MemoryMax=512M` e riavvia: cosa vedi in `journalctl`? (Rimettilo a `6G` dopo.)
4. Con `Restart=always` e `systemctl stop`, il servizio riparte? Prova e spiega.
5. Su Raspberry Pi o su una macchina con GPU, quali variabili cambieresti? (`LLAMA_ARG_THREADS`, `LLAMA_ARG_N_GPU_LAYERS`, `MemoryMax`.)

## Consegna

- Il file `llama-serve.service` finale (con i tuoi valori) e `api-keys.txt` con le chiavi **oscurate**.
- L'output di `systemctl status`, di `journalctl` dopo il `kill -9` e di `systemd-analyze security`.
- L'output di `verifica-servizio.sh` prima e dopo l'aggiornamento (o dopo il rollback), con le velocità a confronto.
- Tre righe: cosa faresti diversamente per un modello da 8 GB su una macchina con 16 GB.
