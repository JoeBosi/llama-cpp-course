#!/usr/bin/env python3
"""Client minimo per llama serve con l'SDK ufficiale `openai`.

Uso:
    python chat.py                 # domanda singola, risposta intera
    python chat.py --stream        # stessa domanda, token per token
    python chat.py --stream "Spiegami cos'è un token in due frasi"

Cambia solo `base_url`: il resto del codice è identico a quello che useresti con l'API di OpenAI.
"""
import os
import sys
import time

from openai import OpenAI

BASE_URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080") + "/v1"  # LLAMA_URL=http://host:porta per cambiare
API_KEY = "no-key-required"  # serve un valore qualsiasi se il server non ha --api-key

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# Parametri extra di llama.cpp (non esistono nell'API OpenAI) passano da `extra_body`.
EXTRA = {"chat_template_kwargs": {"enable_thinking": False}}  # (1) spegne il "thinking" di Qwen3.5


def chat_intero(domanda: str) -> None:
    """Richiesta classica: aspetta la risposta completa e stampa anche i timings del server."""
    t0 = time.perf_counter()
    r = client.chat.completions.create(
        model="local",  # (2) ignorato in modalità singolo modello; obbligatorio in router mode
        messages=[
            {"role": "system", "content": "Rispondi in italiano, in modo conciso."},
            {"role": "user", "content": domanda},
        ],
        max_tokens=80,
        temperature=0.2,
        extra_body=EXTRA,
    )
    dt = time.perf_counter() - t0
    print(r.choices[0].message.content)
    print(f"\n[finish_reason={r.choices[0].finish_reason} "
          f"prompt={r.usage.prompt_tokens} tok, completion={r.usage.completion_tokens} tok, {dt:.1f}s]")
    # Il campo `timings` è specifico di llama.cpp: l'SDK lo conserva in `model_extra`.
    timings = (r.model_extra or {}).get("timings")
    if timings:
        print(f"[server: cache_n={timings['cache_n']} "
              f"prompt {timings['prompt_per_second']:.1f} t/s, generazione {timings['predicted_per_second']:.1f} t/s]")


def chat_streaming(domanda: str) -> None:
    """Streaming: ogni chunk SSE diventa un oggetto con `delta.content`."""
    stream = client.chat.completions.create(
        model="local",
        messages=[{"role": "user", "content": domanda}],
        max_tokens=80,
        temperature=0.2,
        stream=True,
        extra_body=EXTRA,
    )
    t0 = time.perf_counter()
    primo = None
    n = 0
    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            if primo is None:
                primo = time.perf_counter() - t0  # tempo al primo token (TTFT)
            n += 1
            print(delta.content, end="", flush=True)
    print(f"\n[{n} chunk, primo token dopo {primo:.2f}s, totale {time.perf_counter() - t0:.1f}s]")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    domanda = args[0] if args else "Cos'è llama.cpp? Rispondi in due frasi."
    if "--stream" in sys.argv:
        chat_streaming(domanda)
    else:
        chat_intero(domanda)
