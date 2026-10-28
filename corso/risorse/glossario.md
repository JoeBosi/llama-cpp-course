# Glossario

I termini che incontri nei log, nella documentazione e in questo corso, in ordine alfabetico. Le voci in
inglese restano in inglese perché è così che le troverai in `--help` e nei messaggi del programma.

| Termine | Significato |
|---|---|
| **Alias (`-a`)** | Nome con cui il server presenta il modello nell'API (`/v1/models`, campo `model`), indipendente dal nome del file. |
| **API key** | Chiave segreta che il client manda come `Authorization: Bearer …`; il server la verifica se avviato con `--api-key` o `--api-key-file`. `/health` è escluso dal controllo. |
| **Backend** | Implementazione dei calcoli di ggml per un tipo di hardware: CPU, CUDA (NVIDIA), Metal (Apple), Vulkan, HIP/ROCm (AMD), SYCL (Intel), RPC (remoto)… Il binario sceglie quello disponibile. |
| **Batch (`-b`, `-ub`)** | Numero massimo di token elaborati in un colpo durante il prompt processing: `-b` logico, `-ub` fisico. Più grande = prompt più veloce ma più memoria. |
| **Batching continuo** | Il server elabora nello stesso `llama_decode` i token di più richieste (slot) contemporaneamente; una richiesta nuova entra senza aspettare che le altre finiscano. |
| **Build (`bNNNNN`)** | Numero progressivo della build notturna di llama.cpp (es. `b11046`). Le release `vX.Y.Z` puntano a una build. `llama version` li stampa entrambi. |
| **Chat template** | Modello Jinja, salvato nei metadati del GGUF, che trasforma la lista di messaggi (system/user/assistant/tool) nel testo che il modello si aspetta. `--jinja` (default) lo usa; `--chat-template` lo sovrascrive. |
| **Contesto (`-c`, `n_ctx`)** | Numero massimo di token (prompt + risposta) che il modello tiene "in mente". `-c 0` usa quello nativo del modello. Nel server è **totale** e si divide tra gli slot. |
| **Context shift** | Quando il contesto è pieno, il server scarta i token più vecchi per continuare (`--context-shift`, disabilitato di default). |
| **Decodifica speculativa** | Un modello bozza (draft) piccolo propone più token, il modello grande li verifica in un solo passaggio: stessa qualità, meno tempo per token. `-md`, `--spec-type draft-simple`, o varianti senza draft (`ngram-*`). |
| **Draft model** | Il modello bozza della decodifica speculativa: stessa famiglia e stesso tokenizer del modello principale, molto più piccolo. |
| **Embedding** | Vettore di numeri che rappresenta il significato di un testo; testi simili hanno vettori vicini. `llama serve --embedding`, endpoint `/v1/embeddings`. Base del RAG. |
| **Flash Attention (`-fa`)** | Implementazione dell'attenzione che usa meno memoria e, su GPU, è più veloce; necessaria per la KV cache quantizzata. `auto` di default. |
| **fit (`--fit`)** | Adattamento automatico dei parametri non impostati (contesto, offload) alla memoria disponibile. Comodo, ma in produzione fissa i valori esplicitamente. |
| **ftype** | Tipo di quantizzazione prevalente di un GGUF, mostrato nel banner (es. `Q8_0`, `Q4_K_M`, `F16`). |
| **GBNF** | Grammatica in formato BNF di llama.cpp che vincola i token generabili: garantisce output in un formato (JSON, lista, SQL). Il JSON Schema viene convertito in GBNF. |
| **GGUF** | Formato di file di llama.cpp: pesi del modello (eventualmente quantizzati) + metadati (architettura, tokenizer, chat template). Un solo file, mappabile in memoria. |
| **ggml** | Libreria tensoriale in C su cui è costruito llama.cpp: definisce i tensori, il grafo di calcolo e i backend. |
| **gguf-split** | Strumento per dividere un GGUF grande in più file (`-00001-of-00006.gguf`) o riunirli; llama.cpp li carica dal primo pezzo. |
| **Grammatica** | Vedi GBNF. |
| **Health check** | `GET /health`: 200 `{"status":"ok"}` quando il modello è pronto, 503 mentre carica. Usato da Compose, Kubernetes, uptime monitor. |
| **HF (`-hf`)** | Hugging Face, il sito da cui si scaricano i modelli. `-hf utente/repo[:quant]` scarica e mette in cache; `HF_TOKEN` per i repo con accesso limitato. |
| **imatrix** | Matrice di importanza: statistiche raccolte su un testo di calibrazione che dicono al quantizzatore quali pesi contano di più. Migliora molto le quantizzazioni a pochi bit. |
| **Infill (FIM)** | Completamento "nel mezzo" di un testo dato prefisso e suffisso; usato dagli assistenti di codice. Endpoint `/infill`. |
| **JSON Schema** | Descrizione formale della forma di un JSON (campi, tipi, obbligatori). Con `response_format: {"type":"json_schema", …}` il server lo converte in grammatica e garantisce output conforme. |
| **KL divergence (KLD)** | Misura di quanto la distribuzione dei token di un modello quantizzato si discosta da quella del modello di riferimento: più precisa della perplexity per confrontare quantizzazioni. |
| **KV cache** | Memoria che conserva chiavi e valori dell'attenzione per i token già elaborati, così non vanno ricalcolati. Cresce linearmente con il contesto; quantizzabile con `-ctk`/`-ctv`. |
| **KV unified (`--kv-unified`)** | Un'unica KV cache condivisa tra gli slot invece di N fette fisse: gli slot possono usare contesti diversi. |
| **Latenza al primo token (TTFT)** | Tempo tra l'invio della richiesta e il primo token ricevuto; dipende dal prompt processing e dall'attesa in coda. |
| **LoRA** | Adattatore a basso rango che modifica un modello base senza riscriverne i pesi; llama.cpp lo carica con `--lora` e lo può attivare per richiesta. |
| **Load mode (`--load-mode`)** | Come leggere il file: `mmap` (mappato in memoria, default), `mlock` (bloccato in RAM), `dio` (I/O diretto). Sostituisce i vecchi `--mmap`/`--mlock`. |
| **Metrics** | `GET /metrics` in formato Prometheus (attivo con `--metrics`): contatori e gauge `llamacpp:*` su token, tempi, richieste in corso e in coda. |
| **mmproj** | Proiettore multimodale: file GGUF separato che collega un encoder di immagini/audio al modello linguistico. Con `-hf` viene scaricato in automatico. |
| **MoE (Mixture of Experts)** | Architettura in cui ogni token attiva solo alcuni "esperti" (sottoreti): molti parametri su disco, pochi attivi per token. `-cmoe` tiene gli esperti su CPU. |
| **MTP** | Multi-Token Prediction: testa aggiuntiva del modello (es. gemma-4) usata come draft nella decodifica speculativa (`--spec-type draft-mtp`). |
| **Offload (`-ngl`)** | Numero di layer del modello spostati sulla GPU (`all`, `auto` o un numero); il resto resta su CPU (inferenza ibrida). |
| **Perplexity (PPL)** | Misura di quanto il modello è "sorpreso" da un testo: più bassa è meglio. `llama perplexity` la calcola; utile per confrontare quantizzazioni dello stesso modello sullo stesso testo. |
| **pp / tg** | Prompt processing / token generation: le due velocità (token/s) misurate da `llama bench` (`pp512`, `tg128`). pp è limitata dal calcolo, tg dalla banda di memoria. |
| **Prompt caching** | Il server riusa la KV cache di un prefisso già visto (system prompt, conversazione precedente): quei token non vengono rielaborati. `--cache-reuse N` permette il riuso anche con spostamenti. |
| **Prompt injection** | Testo ostile dentro un documento o una pagina che il modello legge e scambia per istruzioni; pericoloso quando il modello può chiamare strumenti. |
| **Quantizzazione** | Rappresentare i pesi con meno bit (8, 5, 4, 3, 2) per ridurre memoria e aumentare la velocità, perdendo un po' di qualità. Tipi: `Q8_0`, `Q4_K_M`, `IQ4_XS`… |
| **RAG** | Retrieval-Augmented Generation: cercare i passaggi pertinenti in un archivio (con gli embedding) e passarli nel prompt, così il modello risponde su dati tuoi e cita le fonti. |
| **Reasoning / thinking** | Modelli che "pensano" prima di rispondere, producendo un blocco di ragionamento. `-rea on|off|auto`, `--reasoning-budget N`, `--reasoning-format`; per richiesta `chat_template_kwargs: {"enable_thinking": false}`. |
| **Reranker** | Modello che dà un punteggio di pertinenza a coppie (domanda, documento); usato dopo la ricerca vettoriale per riordinare i risultati. `--rerank --pooling rank`, `/v1/rerank`. |
| **Reverse proxy** | Server (Caddy, Nginx) che sta davanti a `llama serve`: termina HTTPS, autentica, limita, logga; il server resta su `127.0.0.1`. |
| **Router mode** | `llama serve` senza modello: carica e scarica modelli su richiesta (dalla cache, da `--models-dir` o da un preset `.ini`) e inoltra ogni richiesta all'istanza giusta in base al campo `model`. |
| **RPC** | Backend che esegue parte del modello su un'altra macchina (`ggml-rpc-server`); senza autenticazione: solo in rete privata. |
| **Sampling (campionamento)** | Come si sceglie il prossimo token tra i candidati: `--temp`, `--top-k`, `--top-p`, `--min-p`, penalità di ripetizione, `--seed`. |
| **Slot** | Unità di lavoro del server: ogni slot serve una richiesta alla volta con la sua fetta di contesto. `-np N` = N slot; `/slots` ne mostra lo stato. |
| **SSE (Server-Sent Events)** | Formato dello streaming HTTP usato con `"stream": true`: righe `data: {...}` fino a `data: [DONE]`. Il proxy non deve bufferizzarlo. |
| **systemd unit** | File `.service` che descrive come avviare, riavviare e confinare un processo su Linux; `Environment=LLAMA_ARG_*` per configurare il server. |
| **Thread (`-t`)** | Thread CPU usati per la generazione: di norma = core fisici. `-tb` per il prompt processing, `--threads-http` per le connessioni HTTP. |
| **Token** | Unità di testo del modello (pezzo di parola, parola, simbolo): ~0,7 parole in italiano. Tutto si misura in token: contesto, velocità, costi. `/tokenize` mostra la suddivisione. |
| **Tool calling** | Il modello, dato l'elenco degli strumenti (`tools` nell'API), risponde con una chiamata strutturata (`tool_calls`) che il tuo codice esegue; il risultato torna al modello con `role: tool`. |
| **VRAM** | Memoria della GPU: ci devono stare i layer offloadati e la relativa KV cache. |
| **Web UI** | Interfaccia web integrata in `llama serve` (su `/`): chat, allegati, impostazioni; `--no-webui` la disattiva. |
