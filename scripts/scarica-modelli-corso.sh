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
