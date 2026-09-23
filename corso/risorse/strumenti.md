# Strumenti del corso

<span class="stato stato-verificato">script provati su Ubuntu 24.04 · settembre 2026</span>

Due script bash nella cartella `scripts/` del repository del corso: uno per controllare che la macchina sia
pronta, uno per scaricare in anticipo i modelli dei laboratori. Entrambi sono corti e leggibili: prima di
lanciarli, leggili.

## `verifica-ambiente.sh`

Percorso nel repository: `scripts/verifica-ambiente.sh`. Solo lettura: non installa nulla, non modifica
nulla. Stampa sistema, CPU (con le estensioni AVX2/AVX-512/AMX che il backend CPU sfrutta), RAM, disco, GPU
rilevate, strumenti di sviluppo presenti e se `llama` (o il vecchio `llama-cli`) è nel PATH.

```bash
bash scripts/verifica-ambiente.sh
```

Output sul VPS del corso (6 vCPU AMD EPYC, nessuna GPU):

```
== Sistema
  Linux x86_64
  CPU: AMD EPYC ... (6 core)
  RAM: 11 GB totali, 3 GB disponibili
  ✔ CPU supporta avx2
  ✘ CPU senza avx512f
  ✘ CPU senza amx_tile
  Disco libero qui: 23G
== GPU
  ✘ nessuna GPU NVIDIA (nvidia-smi assente)
  ✘ ROCm assente
  ✘ vulkaninfo assente
== Strumenti
  ✔ git
  ✔ cmake
  ✔ ninja
  ✔ ccache
  ✔ gcc
  ✘ clang non trovato
  ✔ python3
  ✔ docker
  ✔ curl
== llama.cpp
  ✔ llama: version: 0.4.1-dev (build 11046, commit 60081bb2b)
```

Come leggerlo: `avx2` basta per tutti i laboratori; `avx512f`/`amx_tile` accelerano il prompt processing
su CPU Intel recenti. "RAM disponibili" è quella che conta per il modello (vedi
[lab 00-01](../laboratori/lab-00-01-stima-memoria/README.md)). Se `llama` manca, vai al
[modulo 01](../moduli/01-installazione/README.md). Su Windows lancialo da WSL o Git Bash.

Il testo completo:

```bash title="scripts/verifica-ambiente.sh"
#!/usr/bin/env bash
# Verifica rapida dell'ambiente per il corso llama.cpp (Linux/macOS; su Windows usare WSL o Git Bash).
# Solo lettura: non installa nulla.

ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
no()   { printf '  \033[33m✘\033[0m %s\n' "$1"; }
cmd()  { command -v "$1" >/dev/null 2>&1; }

echo "== Sistema"
echo "  $(uname -s) $(uname -m)"
if [ "$(uname -s)" = "Darwin" ]; then
  echo "  CPU: $(sysctl -n machdep.cpu.brand_string 2>/dev/null) ($(sysctl -n hw.ncpu) core)"
  echo "  RAM: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 )) GB"
else
  echo "  CPU: $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs) ($(nproc) core)"
  echo "  RAM: $(free -g | awk '/Mem:/{print $2}') GB totali, $(free -g | awk '/Mem:/{print $7}') GB disponibili"
  flags=$(grep -m1 '^flags' /proc/cpuinfo 2>/dev/null)
  for f in avx2 avx512f amx_tile; do [[ $flags == *" $f"* ]] && ok "CPU supporta $f" || no "CPU senza $f"; done
fi
echo "  Disco libero qui: $(df -h . | awk 'NR==2{print $4}')"

echo "== GPU"
cmd nvidia-smi && ok "NVIDIA: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)" || no "nessuna GPU NVIDIA (nvidia-smi assente)"
cmd rocminfo   && ok "AMD ROCm presente" || no "ROCm assente"
cmd vulkaninfo && ok "Vulkan presente" || no "vulkaninfo assente"
[ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ] && ok "Apple Silicon: backend Metal disponibile"

echo "== Strumenti"
for t in git cmake ninja ccache gcc clang python3 docker curl; do
  cmd "$t" && ok "$t" || no "$t non trovato"
done

echo "== llama.cpp"
if cmd llama; then ok "llama: $(llama --version 2>&1 | head -1)"
elif cmd llama-cli; then ok "llama-cli (nomi vecchi): $(llama-cli --version 2>&1 | head -1)"
else no "llama.cpp non installato (vedi modulo 01)"; fi
```

## `scarica-modelli-corso.sh`

Percorso nel repository: `scripts/scarica-modelli-corso.sh`. Scarica con `llama download -hf` i modelli
usati nei laboratori (elenco e dimensioni in [Modelli consigliati](modelli-consigliati.md)), nella stessa
cache Hugging Face che usano `llama cli -hf` e `llama serve -hf` (`~/.cache/huggingface/hub`). Prima di
scaricare stampa la tabella con la dimensione totale e lo spazio libero, e chiede conferma. I file già in
cache non vengono riscaricati.

```bash
bash scripts/scarica-modelli-corso.sh --lista     # solo la tabella
bash scripts/scarica-modelli-corso.sh             # set base (~2,9 GB), per 8 GB di RAM
bash scripts/scarica-modelli-corso.sh --estesi    # + modelli da 16 GB (~+10 GB)
```

Output di `--lista`:

```
Modello                                                         MiB  Uso
ggml-org/Qwen3.5-0.8B-GGUF:Q8_0                                 795  chat di base, moduli 02-09 (thinking)
LiquidAI/LFM2.5-230M-GGUF:Q4_K_M                                146  modello minuscolo per prove veloci e lab 05
ggml-org/embeddinggemma-300M-GGUF:Q8_0                          318  embedding, lab 08-02 (RAG)
ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF:Q8_0                     610  reranker, modulo 04
ggml-org/SmolVLM-500M-Instruct-GGUF:Q8_0                        521  visione, lab 07-01 (417 + mmproj 104)
ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF:Q8_0                      506  modello bozza per la decodifica speculativa, lab 05-03
Totale: 2896 MiB (~2.8 GB). Spazio libero nella cache: 23G
```

!!! tip "Sulla rete dell'aula"
    Scaricare 3 GB per 20 studenti insieme intasa qualsiasi Wi-Fi. Fallo a casa il giorno prima, oppure
    scaricali una volta e copia la cartella `~/.cache/huggingface/hub` con una chiavetta: `llama` la
    riconosce così com'è (`llama cli -cl` per controllare).

Il testo completo:

```bash title="scripts/scarica-modelli-corso.sh"
#!/usr/bin/env bash
# Scarica in anticipo i modelli usati nei laboratori del corso, con `llama download -hf`.
# Stampa prima la dimensione totale e chiede conferma. I file finiscono nella cache Hugging Face
# (~/.cache/huggingface/hub), la stessa che usano `llama cli -hf` e `llama serve -hf`.
#
# Uso:
#   scripts/scarica-modelli-corso.sh            # set base (~2,9 GB): moduli 02-08 su 8 GB di RAM
#   scripts/scarica-modelli-corso.sh --estesi   # base + modelli "16 GB" (~+9 GB)
#   scripts/scarica-modelli-corso.sh --lista    # elenca senza scaricare
#   scripts/scarica-modelli-corso.sh --si       # non chiedere conferma
# Dimensioni verificate sull'API di Hugging Face il 23/09/2026 (MiB, mmproj incluso dove serve).
set -euo pipefail

# formato: "repo[:quant]|MiB|a cosa serve"
BASE=(
  "ggml-org/Qwen3.5-0.8B-GGUF:Q8_0|795|chat di base, moduli 02-09 (thinking)"
  "LiquidAI/LFM2.5-230M-GGUF:Q4_K_M|146|modello minuscolo per prove veloci e lab 05"
  "ggml-org/embeddinggemma-300M-GGUF:Q8_0|318|embedding, lab 08-02 (RAG)"
  "ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF:Q8_0|610|reranker, modulo 04"
  "ggml-org/SmolVLM-500M-Instruct-GGUF:Q8_0|521|visione, lab 07-01 (417 + mmproj 104)"
  "ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF:Q8_0|506|modello bozza per la decodifica speculativa, lab 05-03"
)
ESTESI=(
  "ggml-org/gemma-3-4b-it-qat-GGUF:Q4_0|3221|chat di qualita' + visione (2409 + mmproj 812), 16 GB"
  "unsloth/Qwen3.5-4B-GGUF:Q4_K_M|3255|chat/thinking/visione 4B (2614 + mmproj 641), 16 GB"
  "ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF:Q8_0|1570|codice e infill, modulo 08"
  "ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF:Q4_K_M|2078|audio, lab 07-02 (770 + mmproj 1308)"
  "ggml-org/granite-docling-258M-GGUF:Q8_0|269|documenti e tabelle, progetto P6 (170 + mmproj 99)"
)

conferma=no; lista=no; set_scelto=("${BASE[@]}")
for a in "$@"; do
  case "$a" in
    --estesi) set_scelto=("${BASE[@]}" "${ESTESI[@]}");;
    --lista)  lista=yes;;
    --si)     conferma=yes;;
    -h|--help) sed -n '2,12p' "$0"; exit 0;;
    *) echo "opzione sconosciuta: $a" >&2; exit 2;;
  esac
done

command -v llama >/dev/null 2>&1 || { echo "llama non trovato nel PATH: installa prima llama.cpp (modulo 01)" >&2; exit 1; }
# Il binario dell'installer e' statico: su alcune distribuzioni serve indicare i certificati TLS
[ -z "${SSL_CERT_FILE:-}" ] && [ -f /etc/ssl/certs/ca-certificates.crt ] && export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

totale=0
printf '%-58s %8s  %s\n' "Modello" "MiB" "Uso"
for voce in "${set_scelto[@]}"; do
  IFS='|' read -r repo mib uso <<<"$voce"
  printf '%-58s %8s  %s\n' "$repo" "$mib" "$uso"
  totale=$((totale + mib))
done
printf 'Totale: %d MiB (~%.1f GB). Spazio libero nella cache: %s\n' "$totale" "$(echo "$totale/1024" | bc -l)" \
  "$(df -h "${HF_HOME:-$HOME/.cache/huggingface}" 2>/dev/null | awk 'NR==2{print $4}' || echo '?')"
[ "$lista" = yes ] && exit 0

if [ "$conferma" != yes ]; then
  read -r -p "Procedo con il download? [s/N] " r
  [[ "$r" =~ ^[sSyY]$ ]] || { echo "annullato"; exit 0; }
fi

for voce in "${set_scelto[@]}"; do
  IFS='|' read -r repo _ _ <<<"$voce"
  echo "== $repo"
  llama download -hf "$repo"          # scarica anche l'mmproj se il repo lo ha; salta se e' gia' in cache
done
echo "== Fatto. Modelli in cache:"
llama cli -cl
```

## Altri strumenti usati nei laboratori

| Script | Dove | Cosa fa |
|---|---|---|
| `verifica-servizio.sh` | [lab 09-01](../laboratori/lab-09-01-servizio/README.md) | controlla `/health`, fa una richiesta di prova con la chiave API, stampa la velocità; esce 0/1 |
| `carico.py` | [lab 09-02](../laboratori/lab-09-02-proxy-monitoraggio/README.md) | N richieste in parallelo, latenza al primo token, throughput, lettura di `/metrics` |
| `compose.yaml` + `Caddyfile` + `prometheus.yml` | [lab 09-02](../laboratori/lab-09-02-proxy-monitoraggio/README.md) | stack completo server + proxy HTTPS + Prometheus + Grafana |
| `llama-serve.service` | [lab 09-01](../laboratori/lab-09-01-servizio/README.md) | unità systemd con hardening, pronta da copiare |
