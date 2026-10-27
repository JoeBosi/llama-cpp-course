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
