#!/usr/bin/env bash
# campiona.sh: esegue lo stesso prompt con più combinazioni di parametri di campionamento
# e salva risposte + tempi in risultati.md. Un processo llama alla volta.
#
# Uso: bash campiona.sh [modello]   (default: -hf ggml-org/Qwen3.5-0.8B-GGUF)
set -euo pipefail

MODELLO="${1:--hf ggml-org/Qwen3.5-0.8B-GGUF}"   # oppure: "-m /percorso/modello.gguf"
PROMPT="Scrivi una frase su un gatto."
N=25            # token per risposta: pochi, così ogni prova dura secondi
T=4             # thread: metti i tuoi core fisici
SEED=1          # seed fisso per confrontare le prove
OUT=risultati.md

# nome | flag di campionamento
PROVE=(
  "default            |"
  "greedy (temp 0)    | --temp 0"
  "top-k 1            | --top-k 1 --temp 1.0"
  "temp 1.8 senza filtri | --temp 1.8 --top-k 0 --top-p 1 --min-p 0"
  "temp 1.8 + min-p 0.1  | --temp 1.8 --top-k 0 --top-p 1 --min-p 0.1"
  "temp 0.3           | --temp 0.3"
  "top-p 0.5          | --top-p 0.5 --min-p 0 --top-k 0"
  "repeat-penalty 1.3 | --repeat-penalty 1.3 --temp 0"
)

echo "# Risultati campionamento" > "$OUT"
echo "" >> "$OUT"
echo "Prompt: \`$PROMPT\` · -n $N · -s $SEED · -t $T" >> "$OUT"
echo "" >> "$OUT"
echo "| Prova | Flag | Risposta | Generation t/s |" >> "$OUT"
echo "|---|---|---|---|" >> "$OUT"

for riga in "${PROVE[@]}"; do
  nome="${riga%%|*}"; flag="${riga#*|}"
  nome="$(echo "$nome" | xargs)"     # toglie gli spazi
  # shellcheck disable=SC2086
  esito="$(llama cli $MODELLO -st -p "$PROMPT" -n "$N" -t "$T" -rea off -s "$SEED" $flag 2>&1 \
           | sed -n '/^> /,/Prompt:/p')"
  risposta="$(echo "$esito" | sed '1d;/^\[ Prompt/d;/^$/d' | tr '\n' ' ' | sed 's/|/\\|/g')"
  tps="$(echo "$esito" | grep -o 'Generation: [0-9.]* t/s' | grep -o '[0-9.]*' || true)"
  echo "| $nome | \`$flag\` | $risposta | $tps |" >> "$OUT"
  echo "fatto: $nome"
done

echo "Risultati in $OUT"
