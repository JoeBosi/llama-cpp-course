#!/usr/bin/env bash
# Ricostruisce il sito del corso e lo pubblica nella cartella servita da Caddy.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=${1:-/srv/llamacorso}
.venv/bin/mkdocs build --strict -d "$DEST.tmp"
rm -rf "$DEST" && mv "$DEST.tmp" "$DEST"
chmod -R a+rX "$DEST"
echo "Pubblicato in $DEST ($(du -sh "$DEST" | cut -f1))"
