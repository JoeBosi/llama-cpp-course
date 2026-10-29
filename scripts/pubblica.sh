#!/usr/bin/env bash
# Ricostruisce il sito del corso e lo pubblica nella cartella servita da Caddy.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=${1:-/srv/llamacorso}
export PYTHONPATH="$PWD"   # serve a scripts/mermaid_fence.py, richiamato da mkdocs.yml
python3 scripts/genera-nav.py
.venv/bin/mkdocs build --strict -d "$DEST.tmp"
find "$DEST.tmp" -name '*.map' -delete   # mappe di debug di Material (1 MB): inutili online
rm -rf "$DEST" && mv "$DEST.tmp" "$DEST"
chmod -R a+rX "$DEST"
echo "Pubblicato in $DEST ($(du -sh "$DEST" | cut -f1))"

# Il sito è pubblico (decisione di Giuseppe, 28/10/2026): deve rispondere 200 SENZA password.
SITO=https://corso-llamacpp.giuseppebosi.com
for p in / /informazioni/ /moduli/01-installazione/ /en/ /en/moduli/01-installazione/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$SITO$p" || echo 000)
  if [ "$code" != "200" ]; then
    echo "ERRORE: $SITO$p risponde $code senza password (atteso 200). Controllare Caddy (non toccarlo da qui: avvisare il Controller)." >&2
    exit 1
  fi
done
echo "Controllo accesso pubblico: 200 su /, /informazioni/, /moduli/01-installazione/, /en/, /en/moduli/01-installazione/"
