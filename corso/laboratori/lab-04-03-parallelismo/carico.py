#!/usr/bin/env python3
"""Piccolo generatore di carico per llama serve: N richieste in parallelo, misura latenza e throughput.

Uso:
    python carico.py --url http://127.0.0.1:8080 --richieste 4 --parallele 4 --token 32

Stampa, per ogni richiesta, latenza totale e token generati; alla fine riassume:
- latenza media/massima per richiesta
- throughput aggregato (token generati al secondo, sommando tutte le richieste)
- il numero di slot visti occupati contemporaneamente (da /slots) durante il test
Solo libreria standard: nessuna dipendenza da installare.
"""
import argparse
import json
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PROMPTS = [  # prompt diversi, così la prompt cache non falsa il confronto
    "Descrivi in tre frasi la città di Bologna.",
    "Spiega cos'è una KV cache in due frasi.",
    "Elenca tre vantaggi dei modelli quantizzati.",
    "Scrivi una breve poesia sul mare.",
    "Cosa fa un tokenizer? Rispondi brevemente.",
    "Suggerisci tre nomi per un gatto nero.",
    "Perché il cielo è azzurro? Due frasi.",
    "Descrivi il sapore del caffè in una frase.",
]


def post(url: str, path: str, body: dict) -> dict:
    req = urllib.request.Request(url + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def get(url: str, path: str):
    with urllib.request.urlopen(url + path, timeout=10) as r:
        return json.load(r)


def una_richiesta(url: str, i: int, n_token: int) -> dict:
    body = {
        "messages": [{"role": "user", "content": PROMPTS[i % len(PROMPTS)]}],
        "max_tokens": n_token,
        "temperature": 0.7,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    t0 = time.perf_counter()
    r = post(url, "/v1/chat/completions", body)
    dt = time.perf_counter() - t0
    t = r["timings"]
    return {"i": i, "latenza": dt, "generati": t["predicted_n"], "prompt": t["prompt_n"],
            "tg_tps": t["predicted_per_second"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--richieste", type=int, default=4, help="richieste totali")
    ap.add_argument("--parallele", type=int, default=4, help="richieste inviate insieme (client)")
    ap.add_argument("--token", type=int, default=32, help="max_tokens per richiesta")
    a = ap.parse_args()

    slots = get(a.url, "/slots")
    print(f"server: {len(slots)} slot, n_ctx per slot = {slots[0]['n_ctx']}")

    # Un thread di monitoraggio campiona /slots ogni 0,5 s e ricorda il massimo di slot occupati insieme.
    stop = threading.Event()
    picco = {"busy": 0, "coda": 0}

    def monitor():
        while not stop.is_set():
            try:
                s = get(a.url, "/slots")
                busy = sum(1 for x in s if x["is_processing"])
                picco["busy"] = max(picco["busy"], busy)
            except Exception:
                pass
            time.sleep(0.5)

    threading.Thread(target=monitor, daemon=True).start()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.parallele) as ex:
        risultati = list(ex.map(lambda i: una_richiesta(a.url, i, a.token), range(a.richieste)))
    totale = time.perf_counter() - t0
    stop.set()

    for r in risultati:
        print(f"  req {r['i']}: {r['latenza']:6.2f} s  {r['generati']:3d} token  "
              f"({r['tg_tps']:.1f} t/s nel proprio slot)")
    gen = sum(r["generati"] for r in risultati)
    lat = [r["latenza"] for r in risultati]
    print(f"\nrichieste={a.richieste} parallele={a.parallele} slot={len(slots)}  "
          f"picco slot occupati insieme={picco['busy']}")
    print(f"tempo totale {totale:.2f} s  |  latenza media {sum(lat)/len(lat):.2f} s, max {max(lat):.2f} s")
    print(f"throughput aggregato {gen/totale:.2f} token/s  ({gen} token generati)")


if __name__ == "__main__":
    main()
