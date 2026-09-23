#!/usr/bin/env bash
# scan-ngl.sh: misura pp/tg per una serie di valori di -ngl e salva tutto in un CSV.
#
# Uso:
#   ./scan-ngl.sh modello.gguf "0,8,16,24,32,40,48" [contesto]
#
# Esempio:
#   ./scan-ngl.sh ~/modelli/gemma-3-12b-it-Q4_K_M.gguf "0,16,24,32,40,44,48" 4096
#
# Ogni valore di -ngl è una riga del CSV (risultati.csv); le colonne utili sono
# n_gpu_layers, n_prompt, n_gen, avg_ts, stddev_ts. Con --fit-target si lascia
# a llama bench il compito di scartare i valori che non entrano in VRAM.
set -euo pipefail

MODELLO="${1:?indica il file GGUF}"
LISTA_NGL="${2:-0,8,16,24,32}"
CTX="${3:-4096}"
OUT="risultati.csv"

# --fit off: vogliamo misurare esattamente il valore di -ngl chiesto, senza aggiustamenti automatici.
# -r 3: tre ripetizioni per ogni test, la tabella riporta media ± deviazione standard.
# --progress: stampa su stderr l'avanzamento (utile con modelli grandi).
llama bench -m "$MODELLO" \
    -ngl "$LISTA_NGL" \
    -p 512 -n 128 -r 3 \
    -fa on \
    --progress \
    -o csv > "$OUT"

echo "risultati in $OUT"
# Estrae le colonne che interessano (n_gpu_layers, test, t/s) con python per non dipendere da csvkit.
python3 - "$OUT" <<'EOF'
import csv, sys
with open(sys.argv[1], newline="") as f:
    righe = list(csv.DictReader(f))
print(f"{'ngl':>5} {'test':>8} {'t/s':>10} {'± dev':>8}")
for r in righe:
    test = f"pp{r['n_prompt']}" if int(r['n_gen']) == 0 else f"tg{r['n_gen']}"
    print(f"{r['n_gpu_layers']:>5} {test:>8} {float(r['avg_ts']):>10.2f} {float(r['stddev_ts']):>8.2f}")
EOF
