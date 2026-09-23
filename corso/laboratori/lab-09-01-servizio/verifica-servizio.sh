#!/usr/bin/env bash
# Verifica di un'istanza di `llama serve` in produzione: health, richiesta di prova, velocità.
# Uso: ./verifica-servizio.sh [URL] [FILE_CHIAVI]
#   URL          base del server (default http://127.0.0.1:8080)
#   FILE_CHIAVI  file con le chiavi API, una per riga (default /etc/llama/api-keys.txt); usa la prima
# Esce con 0 se tutto risponde, 1 altrimenti: adatto a cron, a un hook post-aggiornamento o a un uptime check.
set -u
URL=${1:-http://127.0.0.1:8080}
KEYFILE=${2:-/etc/llama/api-keys.txt}
KEY=""
if [ -r "$KEYFILE" ]; then
  KEY=$(grep -v '^#' "$KEYFILE" | grep -m1 .)
fi
AUTH=()
[ -n "$KEY" ] && AUTH=(-H "Authorization: Bearer $KEY")

echo "== /health"
code=$(curl -s -o /dev/null -w '%{http_code}' "$URL/health")
case "$code" in
  200) echo "  ok (200)";;
  503) echo "  il modello sta ancora caricando (503)"; exit 1;;
  *)   echo "  server non raggiungibile (HTTP $code)"; exit 1;;
esac

echo "== versione"
curl -s "${AUTH[@]}" "$URL/v1/models" | python3 -c '
import sys, json
d = json.load(sys.stdin)
for m in d.get("data", []):
    print("  modello:", m.get("id"))
' 2>/dev/null || echo "  /v1/models non leggibile (chiave mancante o errata?)"

echo "== richiesta di prova"
# max_tokens basso: vogliamo solo sapere che risponde e quanto e' veloce
resp=$(curl -s "${AUTH[@]}" -H "Content-Type: application/json" "$URL/v1/chat/completions" -d '{
  "messages": [{"role": "user", "content": "Rispondi solo: ok"}],
  "max_tokens": 8,
  "chat_template_kwargs": {"enable_thinking": false}
}')
echo "$resp" | python3 -c '
import sys, json
d = json.load(sys.stdin)
if "error" in d:
    print("  ERRORE:", d["error"]); sys.exit(1)
print("  risposta:", repr(d["choices"][0]["message"]["content"].strip()))
t = d.get("timings", {})
print("  prompt: %.1f t/s | generazione: %.1f t/s | build: %s" % (
    t.get("prompt_per_second", 0), t.get("predicted_per_second", 0), d.get("system_fingerprint")))
' || exit 1

echo "== /metrics (se abilitato)"
curl -s "${AUTH[@]}" "$URL/metrics" | grep -E '^llamacpp:(requests_processing|requests_deferred|tokens_predicted_total) ' | sed 's/^/  /'
exit 0
