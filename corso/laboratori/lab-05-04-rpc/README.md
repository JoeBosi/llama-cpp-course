# Lab 05-04 · Cluster RPC

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/05-prestazioni/README.md">05: Prestazioni e ottimizzazione</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
<span class="stato stato-verificato">verificato su b11046 (server e client sulla stessa macchina, CPU)</span> <span class="stato stato-bozza">due macchine con GPU: dalla documentazione</span>
</div>

## Obiettivo

Far girare un modello usando la memoria (e, se c'è, la GPU) di **un'altra macchina** attraverso il backend RPC di ggml:
avviare `ggml-rpc-server` sull'host remoto, collegarlo con `--rpc`, verificare la distribuzione dei pesi e misurare il
prezzo che si paga in velocità. Lo stesso esercizio funziona su una sola macchina con due terminali (o due container),
che è il modo con cui è stato verificato per il corso.

## Prerequisiti

- Due macchine sulla stessa rete locale fidata (A = principale, B = remota), **oppure** una macchina sola con due terminali.
- Su entrambe i **binari del tarball della release** (es. `llama-b11046-bin-ubuntu-x64.tar.gz`, modulo 01) o una build
  con `-DGGML_RPC=ON`. Il binario dell'installer `llama` **non** ha il backend RPC: il suo `--help` non mostra `--rpc`.
- Il modello scaricato **sulla macchina A** (B riceve i tensori dalla rete, non legge il file).

## Materiale

| Cosa | Fonte | Dimensione |
|---|---|---|
| Modello di prova | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0) | 795 MB |
| Modello "che non entra" (variante) | `ggml-org/gemma-3-12b-it-GGUF:Q4_K_M` | 6,96 GB |
| Binari | tarball della release in `~/llama-lab/rel/llama-b11046/` (contiene `ggml-rpc-server`, `llama-cli`, `llama-server`, `llama-bench` e `libggml-rpc.so`) | 16 MB |

```bash
R=~/llama-lab/rel/llama-b11046
$R/ggml-rpc-server --help
```

Output atteso:

```
load_backend: loaded RPC backend from …/libggml-rpc.so
load_backend: loaded CPU backend from …/libggml-cpu-haswell.so
Usage: ggml-rpc-server [options]
  -t, --threads N                  number of threads for the CPU device (default: 3)
  -d, --device <dev1,dev2,...>     comma-separated list of devices
  -H, --host HOST                  host to bind to (default: 127.0.0.1)
  -p, --port PORT                  port to bind to (default: 50052)
  -c, --cache                      enable local file cache
```

## Procedura

1. **Sulla macchina B (o nel terminale 1): avvia il server.** In locale usa `127.0.0.1`; su due macchine usa
    l'indirizzo LAN di B (`-H 192.168.1.20`) e **solo** su una rete fidata:

    ```bash
    $R/ggml-rpc-server -H 127.0.0.1 -p 50052 -t 3
    ```

    Output verificato:

    ```
    Starting RPC server v7.0.0
      endpoint       : 127.0.0.1:50052
      local cache    : n/a
    Devices:
      CPU: AMD EPYC Processor (with IBPB) (11960 MiB, 11960 MiB free)
      transport      : TCP
    ```

    Su una macchina con GPU compare invece `CUDA0: NVIDIA … (32109 MiB, 31588 MiB free)`; con `-d CUDA0` o
    `CUDA_VISIBLE_DEVICES` scegli quali dispositivi esporre.

2. **Sulla macchina A (terminale 2): il dispositivo remoto è visibile?**

    ```bash
    $R/llama-cli --rpc 127.0.0.1:50052 --list-devices
    ```

    ```
    Available devices:
      RPC0: 127.0.0.1:50052 (11960 MiB, 11960 MiB free)
    ```

    Il dispositivo si chiama `RPC0` (poi `RPC1`… per altri server, in ordine di elenco). Sul server compare
    `Accepted client connection` / `Client connection closed`.

3. **Genera attraverso la rete.**

    ```bash
    M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    $R/llama-cli --rpc 127.0.0.1:50052 -m "$M" -st -p "ciao" -n 20 -t 3 -rea off
    ```

    Output verificato sul VPS (macchina condivisa e carica):

    ```
    > ciao
    Ciao! Come posso aiutarti oggi?

    [ Prompt: 1.4 t/s | Generation: 0.6 t/s ]
    ```

    Il caricamento è più lento del normale: i pesi vengono **inviati** al server RPC (785 MB su loopback in pochi
    secondi; su una LAN a 1 Gbit/s circa 8 secondi, per un modello da 7 GB oltre un minuto).

4. **Dove sono finiti i pesi?** Ripeti con `-v` (log completo) e cerca i buffer:

    ```bash
    $R/llama-cli --rpc 127.0.0.1:50052 -m "$M" -st -p "ciao" -n 5 -rea off -v 2>&1 | grep -E "RPC0|CPU_Mapped|offloaded|buffer size"
    ```

    Di default llama.cpp distribuisce pesi e KV cache tra dispositivi locali e remoti **in proporzione alla memoria
    libera**; `-ngl` conta anche il dispositivo RPC come "GPU". Con `-ts` imponi le proporzioni: `-ts 1,0` (tutto sul
    primo dispositivo), `-ts 1,1` (metà e metà). Prova `-ngl all -ts 0,1` per mandare tutto al server remoto e confronta
    la riga `Generation:` con il passo 3.

5. **Il server HTTP con backend remoto.** Tutto ciò che vale per `llama-cli` vale per `llama-server`:

    ```bash
    $R/llama-server --rpc 127.0.0.1:50052 -m "$M" --port 18104 -c 4096
    curl -s localhost:18104/health
    ```

    Termina con ++ctrl+c++ e leggi `llama_memory_breakdown_print`: c'è una riga per `RPC0`.

6. **Cache locale (variante).** Su B riavvia con `-c`: alla seconda esecuzione i tensori grandi vengono letti da
    `~/.cache/llama.cpp/rpc` invece che ricevuti dalla rete. Cronometra il caricamento prima e dopo.

7. **Chiudi tutto.** ++ctrl+c++ sul server RPC, oppure:

    ```bash
    pkill -f "ggml-rpc-server"
    ```

    Un server RPC dimenticato acceso è un rischio (vedi sotto).

## Verifica del risultato

- [ ] `--list-devices` mostra `RPC0` con la memoria del server.
- [ ] Il modello ha risposto attraverso RPC e hai annotato pp/tg.
- [ ] Hai confrontato la velocità con lo stesso comando **senza** `--rpc`: la differenza è il costo della rete (in
      locale piccolo, su LAN grande).
- [ ] Hai spento il server RPC e verificato con `pgrep -af rpc-server` che non ci sia più.

!!! danger "Nessuna autenticazione: rete fidata soltanto"
    `ggml-rpc-server` non ha password, token né TLS; il README ufficiale lo definisce *proof of concept, fragile e
    insicuro* e dice di **non avviarlo mai su una rete aperta**. Chi raggiunge la porta può usare la tua GPU e la tua RAM
    a piacere. Regole: `-H 127.0.0.1` o indirizzo di LAN isolata, firewall che accetta solo la macchina A, oppure un
    tunnel SSH (`ssh -L 50052:localhost:50052 utente@B`) o una VPN; spegnere il server quando non serve.

## Domande e varianti

- Perché la generazione via RPC è più lenta anche quando il server ha una GPU veloce? Pensa a cosa attraversa la rete a ogni token (attivazioni tra i layer) e con quale latenza.
- Con due macchine: `-ts 3,1` (A tiene il 75 %) contro `-ts 1,3`. Quale ordine è meglio se A ha la GPU più veloce?
- Due server RPC: `--rpc B:50052,C:50052`. In quale ordine compaiono in `--list-devices`?
- `GGML_RPC_DEBUG=1 ggml-rpc-server …` mostra ogni comando ricevuto: conta quanti messaggi servono per generare 5 token.
- Due container sulla stessa macchina: crea una rete (`docker network create rpc`), avvia due container Ubuntu con il
  tarball montato in `/opt/llama` e usa i nomi dei container come host (`--rpc rpc-b:50052`). Stesse regole di sicurezza:
  la rete è interna a Docker, non pubblicare la porta con `-p`.
- Con una GPU su B e un modello che non entra nella VRAM di A (gemma-3-12b), confronta: tutto su A con `-ngl` parziale
  contro A+B via RPC. Chi vince dipende dalla rete: con 1 Gbit/s quasi sempre l'ibrido locale, con 10 Gbit/s o
  Thunderbolt/RDMA il cluster.

## Consegna

Il log di avvio del server (le righe `Devices:`), l'uscita di `--list-devices`, la riga `[ Prompt … | Generation … ]`
con e senza `--rpc`, e cinque righe di conclusioni: quando useresti RPC e quali misure di sicurezza adotteresti.
