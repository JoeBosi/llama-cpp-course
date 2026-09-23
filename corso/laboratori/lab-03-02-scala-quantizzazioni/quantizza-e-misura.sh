#!/usr/bin/env bash
# quantizza-e-misura.sh: quantizza un GGUF in più tipi e misura per ciascuno
# dimensione, bpw, velocità (llama bench) e perplexity su un testo breve.
# Un solo processo llama alla volta; ogni tipo richiede ~1 minuto e ~1,5 GB di RAM
# con il modello di prova (0,8 B).
#
# Uso: bash quantizza-e-misura.sh <modello-sorgente.gguf> [tipo ...]
#   es. bash quantizza-e-misura.sh ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf Q4_K_M Q4_0 Q2_K
set -euo pipefail

SRC="${1:?modello sorgente .gguf}"; shift
TIPI=("${@:-Q4_K_M}")          # default: solo Q4_K_M
OUTDIR="${OUTDIR:-$HOME/llama-lab/quant}"
TESTO="${TESTO:-$(dirname "$0")/testo-it.txt}"
T="${T:-3}"                    # thread
# Partiamo dal Q8_0 della cache, che è già quantizzato: llama quantize lo rifiuta
# ("requantizing from type q8_0 is disabled") senza --allow-requantize.
# Con un sorgente F16/BF16 metti EXTRA="" (o lascia: il flag non fa danni).
EXTRA="${EXTRA:---allow-requantize}"
OUT="$OUTDIR/risultati.md"
mkdir -p "$OUTDIR"

base="$(basename "$SRC" .gguf)"
base="${base%-Q8_0}"           # Qwen3.5-0.8B-Q8_0 -> Qwen3.5-0.8B

misura() {   # misura <file.gguf> <etichetta>
  local f="$1" et="$2"
  local mib bpw pp tg ppl
  mib="$(du -mL "$f" | cut -f1)"     # -L: segue il link simbolico della cache HF
  # bpw dal log di quantize se c'è, altrimenti dal file
  bpw="$(grep -ho 'quant size *= *[0-9.]* MiB ([0-9.]* BPW)' "$OUTDIR/quant-$et.log" 2>/dev/null | grep -o '[0-9.]* BPW' | cut -d' ' -f1 || true)"
  echo "-- bench $et"
  local b; b="$(llama bench -m "$f" -p 32 -n 16 -t "$T" -r 1 2>/dev/null)"
  pp="$(echo "$b" | grep 'pp32' | awk -F'|' '{print $8}' | xargs)"
  tg="$(echo "$b" | grep 'tg16' | awk -F'|' '{print $8}' | xargs)"
  echo "-- perplexity $et"
  ppl="$(llama perplexity -m "$f" -f "$TESTO" -c 128 -t "$T" 2>&1 | grep -o 'PPL = [0-9.]* +/- [0-9.]*' | sed 's/PPL = //')"
  echo "| $et | $mib | ${bpw:-?} | $pp | $tg | $ppl |" >> "$OUT"
}

{
  echo "# Scala delle quantizzazioni: $base"
  echo
  echo "Sorgente: \`$SRC\` · bench: -p 32 -n 16 -t $T -r 1 · perplexity: -c 128 su \`$(basename "$TESTO")\`"
  echo
  echo "| Tipo | MiB | bpw | pp32 t/s | tg16 t/s | PPL |"
  echo "|---|---|---|---|---|---|"
} > "$OUT"

misura "$SRC" "sorgente"

for tipo in "${TIPI[@]}"; do
  dst="$OUTDIR/$base-$tipo.gguf"
  echo "== quantizzo $tipo -> $dst"
  # shellcheck disable=SC2086
  llama quantize $EXTRA "$SRC" "$dst" "$tipo" "$T" > "$OUTDIR/quant-$tipo.log" 2>&1
  tail -3 "$OUTDIR/quant-$tipo.log"
  misura "$dst" "$tipo"
done

echo; cat "$OUT"
echo
echo "File prodotti in $OUTDIR (cancella quelli che non servono: rm $OUTDIR/*.gguf)"
