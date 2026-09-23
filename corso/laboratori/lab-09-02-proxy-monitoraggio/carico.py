#!/usr/bin/env python3
"""Piccolo generatore di carico per il lab 09-02.

Manda N richieste in parallelo a /v1/chat/completions (attraverso il proxy o direttamente al server),
misura la latenza al primo token e totale, e legge /metrics prima e dopo per mostrare cosa vede Prometheus.
Solo libreria standard: nessun pip install.

Uso:
  python3 carico.py --url https://localhost:8443 --key CHIAVE --n 4 --insecure
  python3 carico.py --url http://127.0.0.1:8080 --key CHIAVE --n 8 --max-tokens 48
"""
import argparse
import json
import ssl
import statistics
import threading
import time
import urllib.request

PROMPTS = [
    "Spiega in due frasi cos'è una KV cache.",
    "Scrivi una lista di tre frutti con un aggettivo ciascuno.",
    "Che differenza c'è tra RAM e VRAM? Rispondi in breve.",
    "Dammi un titolo per un articolo su llama.cpp.",
]


def metrics(base, key, ctx):
    """Legge /metrics e restituisce un dizionario nome -> valore (solo le metriche llamacpp:*)."""
    req = urllib.request.Request(base + "/metrics", headers={"Authorization": f"Bearer {key}"})
    out = {}
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            for line in r.read().decode().splitlines():
                if line.startswith("llamacpp:"):
                    name, val = line.split(" ", 1)
                    out[name] = float(val)
    except Exception as e:  # /metrics disabilitato o chiave errata: non blocchiamo il test
        print(f"  (metrics non disponibili: {e})")
    return out


def una_richiesta(i, base, key, max_tokens, ctx, risultati):
    """Una richiesta in streaming: misura tempo al primo token e tempo totale."""
    body = json.dumps({
        "messages": [{"role": "user", "content": PROMPTS[i % len(PROMPTS)]}],
        "max_tokens": max_tokens,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},  # niente "thinking": misuriamo solo la generazione
    }).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    primo = None
    n = 0
    try:
        with urllib.request.urlopen(req, timeout=600, context=ctx) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                chunk = json.loads(line[6:])
                if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                    if primo is None:
                        primo = time.time() - t0
                    n += 1
        risultati.append({"id": i, "ttft": primo or 0.0, "totale": time.time() - t0, "token": n, "ok": True})
    except Exception as e:
        risultati.append({"id": i, "ttft": 0.0, "totale": time.time() - t0, "token": 0, "ok": False, "err": str(e)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080", help="base URL (proxy o server)")
    ap.add_argument("--key", required=True, help="chiave API (Bearer)")
    ap.add_argument("--n", type=int, default=4, help="richieste in parallelo")
    ap.add_argument("--max-tokens", type=int, default=32)
    ap.add_argument("--insecure", action="store_true", help="accetta il certificato interno di Caddy")
    a = ap.parse_args()

    ctx = ssl.create_default_context()
    if a.insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    prima = metrics(a.url, a.key, ctx)
    risultati = []
    thread = [threading.Thread(target=una_richiesta, args=(i, a.url, a.key, a.max_tokens, ctx, risultati)) for i in range(a.n)]
    t0 = time.time()
    for t in thread:
        t.start()
    for t in thread:
        t.join()
    durata = time.time() - t0
    dopo = metrics(a.url, a.key, ctx)

    ok = [r for r in risultati if r["ok"]]
    print(f"\n== {a.n} richieste in parallelo, max_tokens={a.max_tokens}, durata totale {durata:.1f} s")
    for r in sorted(risultati, key=lambda r: r["id"]):
        if r["ok"]:
            print(f"  #{r['id']}: primo token dopo {r['ttft']:.2f} s, totale {r['totale']:.2f} s, {r['token']} chunk")
        else:
            print(f"  #{r['id']}: ERRORE {r.get('err')}")
    if ok:
        print(f"  latenza al primo token: mediana {statistics.median(r['ttft'] for r in ok):.2f} s, max {max(r['ttft'] for r in ok):.2f} s")
        tok = sum(r["token"] for r in ok)
        print(f"  throughput aggregato: {tok / durata:.1f} token/s")
    if prima and dopo:
        gen = dopo.get("llamacpp:tokens_predicted_total", 0) - prima.get("llamacpp:tokens_predicted_total", 0)
        pt = dopo.get("llamacpp:prompt_tokens_total", 0) - prima.get("llamacpp:prompt_tokens_total", 0)
        print(f"  /metrics: +{gen:.0f} token generati, +{pt:.0f} token di prompt, "
              f"requests_deferred ora = {dopo.get('llamacpp:requests_deferred', 0):.0f}")


if __name__ == "__main__":
    main()
