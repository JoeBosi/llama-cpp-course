# Course tools

Two bash scripts in the `scripts/` folder of the course repository: one to check that your machine is
ready, one to download the lab models in advance. Both are short and readable: read them before
you run them.

## `verifica-ambiente.sh`

Path in the repository: `scripts/verifica-ambiente.sh`. Read-only: it installs nothing and changes
nothing. It prints the system, CPU (with the AVX2/AVX-512/AMX extensions the CPU backend uses), RAM, disk, detected
GPUs, available development tools and whether `llama` (or the old `llama-cli`) is in the PATH.

```bash
bash scripts/verifica-ambiente.sh
```

Output on a Linux machine with 6 AMD EPYC vCPUs, no GPU:

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

How to read it: `avx2` is enough for all the labs; `avx512f`/`amx_tile` speed up prompt processing
on recent Intel CPUs. "RAM disponibili" (available RAM) is what counts for the model (see
[lab 00-01](../laboratori/lab-00-01-stima-memoria/README.md)). If `llama` is missing, go to
[module 01](../moduli/01-installazione/README.md). On Windows run it from WSL or Git Bash.

The full text:

```bash title="scripts/verifica-ambiente.sh"
#!/usr/bin/env bash
# Quick environment check for the llama.cpp course (Linux/macOS; on Windows use WSL or Git Bash).
# Read-only: installs nothing.

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

Path in the repository: `scripts/scarica-modelli-corso.sh`. It downloads with `llama download -hf` the models
used in the labs (list and sizes in [Recommended models](modelli-consigliati.md)), into the same
Hugging Face cache that `llama cli -hf` and `llama serve -hf` use (`~/.cache/huggingface/hub`). Before
downloading it prints the table with the total size and the free space, and asks for confirmation. Files already in
the cache are not downloaded again.

```bash
bash scripts/scarica-modelli-corso.sh --lista     # table only
bash scripts/scarica-modelli-corso.sh             # base set (~2.9 GB), for 8 GB of RAM
bash scripts/scarica-modelli-corso.sh --estesi    # + 16 GB models (~+10 GB)
```

Output of `--lista`:

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

!!! tip "On the classroom network"
    Downloading 3 GB for 20 students at once clogs any Wi-Fi. Do it at home the day before, or
    download them once and copy the `~/.cache/huggingface/hub` folder with a USB stick: `llama`
    recognizes it as is (`llama cli -cl` to check).

The full text:

```bash title="scripts/scarica-modelli-corso.sh"
#!/usr/bin/env bash
# Downloads in advance the models used in the course labs, with `llama download -hf`.
# It first prints the total size and asks for confirmation. Files land in the Hugging Face cache
# (~/.cache/huggingface/hub), the same one used by `llama cli -hf` and `llama serve -hf`.
#
# Usage:
#   scripts/scarica-modelli-corso.sh            # base set (~2.9 GB): modules 02-08 on 8 GB of RAM
#   scripts/scarica-modelli-corso.sh --estesi   # base + "16 GB" models (~+9 GB)
#   scripts/scarica-modelli-corso.sh --lista    # list without downloading
#   scripts/scarica-modelli-corso.sh --si       # do not ask for confirmation
# GGUF file sizes (Hugging Face API, September 2026) (MiB, mmproj included where needed).
set -euo pipefail

# format: "repo[:quant]|MiB|what it is for"
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
# The installer binary is static: on some distributions you must point it to the TLS certificates
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
  llama download -hf "$repo"          # also downloads the mmproj if the repo has one; skips it if already cached
done
echo "== Fatto. Modelli in cache:"
llama cli -cl
```

## Other tools used in the labs

| Script | Where | What it does |
|---|---|---|
| `verifica-servizio.sh` | [lab 09-01](../laboratori/lab-09-01-servizio/README.md) | checks `/health`, makes a test request with the API key, prints the speed; exits 0/1 |
| `carico.py` | [lab 09-02](../laboratori/lab-09-02-proxy-monitoraggio/README.md) | N parallel requests, time to first token, throughput, reading of `/metrics` |
| `compose.yaml` + `Caddyfile` + `prometheus.yml` | [lab 09-02](../laboratori/lab-09-02-proxy-monitoraggio/README.md) | full stack: server + HTTPS proxy + Prometheus + Grafana |
| `llama-serve.service` | [lab 09-01](../laboratori/lab-09-01-servizio/README.md) | hardened systemd unit, ready to copy |
