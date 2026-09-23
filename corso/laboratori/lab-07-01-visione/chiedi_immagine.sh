#!/usr/bin/env bash
# chiedi_immagine.sh - manda un'immagine e una domanda a `llama serve` (API OpenAI-compatibile)
# codificando il file come data URI base64.
#
# Uso: ./chiedi_immagine.sh immagine.png "Domanda sull'immagine" [URL del server]
set -euo pipefail

IMMAGINE=${1:?immagine mancante}
DOMANDA=${2:-"Describe this image."}
URL=${3:-http://127.0.0.1:8080}

# tipo MIME dal suffisso (basta per png/jpg/gif/webp)
case "${IMMAGINE##*.}" in
  png)      MIME=image/png ;;
  jpg|jpeg) MIME=image/jpeg ;;
  gif)      MIME=image/gif ;;
  webp)     MIME=image/webp ;;
  *)        MIME=application/octet-stream ;;
esac

# base64 su una riga sola (-w0 su GNU; su macOS usa `base64 -i file | tr -d '\n'`)
B64=$(base64 -w0 "$IMMAGINE" 2>/dev/null || base64 -i "$IMMAGINE" | tr -d '\n')

# il body JSON: testo + image_url con data URI; max_tokens contenuto per le prove su CPU
BODY=$(printf '{"messages":[{"role":"user","content":[{"type":"text","text":%s},{"type":"image_url","image_url":{"url":"data:%s;base64,%s"}}]}],"max_tokens":120}' \
       "$(printf '%s' "$DOMANDA" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" "$MIME" "$B64")

curl -s "$URL/v1/chat/completions" -H "Content-Type: application/json" -d "$BODY" \
  | python3 -c '
import json, sys
r = json.load(sys.stdin)
if "error" in r:
    print("ERRORE:", r["error"]); sys.exit(1)
print(r["choices"][0]["message"]["content"].strip())
u = r.get("usage", {}); t = r.get("timings", {})
print("\n[prompt %s token, risposta %s token, prompt %.1f t/s, generazione %.1f t/s]" % (
      u.get("prompt_tokens"), u.get("completion_tokens"),
      t.get("prompt_per_second", 0), t.get("predicted_per_second", 0)))
'
