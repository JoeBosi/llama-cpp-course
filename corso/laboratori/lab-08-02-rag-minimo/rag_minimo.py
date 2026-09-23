#!/usr/bin/env python3
"""RAG minimo con `llama serve`: documenti -> chunk -> embedding -> indice -> query -> top-k -> prompt -> risposta.

Usa solo due endpoint del server: POST /v1/embeddings (modello di embedding) e
POST /v1/chat/completions (modello di chat). Dipendenze: numpy, requests.

Uso:
    python rag_minimo.py indicizza                 # legge documenti/*.txt e salva indice.npz
    python rag_minimo.py cerca "domanda"           # mostra i frammenti piu' simili
    python rag_minimo.py rispondi "domanda"        # cerca + chiede al modello di rispondere citando [n]

Variabili d'ambiente (con i valori di default):
    RAG_URL=http://127.0.0.1:8080          server (unico, in modalita' router, o quello di embedding)
    RAG_CHAT_URL=$RAG_URL                  server di chat, se diverso da quello di embedding
    RAG_EMBED_MODEL=ggml-org/embeddinggemma-300M-GGUF:Q8_0
    RAG_CHAT_MODEL=ggml-org/Qwen3.5-0.8B-GGUF:Q8_0
    RAG_TOP_K=3
"""
import glob
import json
import os
import sys

import numpy as np
import requests

URL = os.environ.get("RAG_URL", "http://127.0.0.1:8080").rstrip("/")
CHAT_URL = os.environ.get("RAG_CHAT_URL", URL).rstrip("/")
EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "ggml-org/embeddinggemma-300M-GGUF:Q8_0")
CHAT_MODEL = os.environ.get("RAG_CHAT_MODEL", "ggml-org/Qwen3.5-0.8B-GGUF:Q8_0")
TOP_K = int(os.environ.get("RAG_TOP_K", "3"))

QUI = os.path.dirname(os.path.abspath(__file__))
CARTELLA_DOC = os.path.join(QUI, "documenti")
FILE_INDICE = os.path.join(QUI, "indice.npz")

# EmbeddingGemma e' addestrato con questi prefissi (vedi la scheda del modello su HF):
# uno per le domande, uno per i documenti. Con altri modelli di embedding vanno tolti.
PREFISSO_QUERY = "task: search result | query: "
PREFISSO_DOC = "title: none | text: "

MAX_CARATTERI_CHUNK = 500


def spezza_in_chunk(testo):
    """Divide il testo per paragrafi (righe vuote) e li accorpa fino a ~500 caratteri."""
    chunk, corrente = [], ""
    for paragrafo in testo.split("\n\n"):
        paragrafo = " ".join(paragrafo.split())  # normalizza spazi e a capo
        if not paragrafo:
            continue
        if corrente and len(corrente) + len(paragrafo) > MAX_CARATTERI_CHUNK:
            chunk.append(corrente)
            corrente = ""
        corrente = (corrente + " " + paragrafo).strip()
    if corrente:
        chunk.append(corrente)
    return chunk


def embedding(testi):
    """Chiama /v1/embeddings e restituisce una matrice (n, dim) gia' normalizzata dal server."""
    r = requests.post(f"{URL}/v1/embeddings",
                      json={"model": EMBED_MODEL, "input": testi}, timeout=600)
    r.raise_for_status()
    dati = sorted(r.json()["data"], key=lambda d: d["index"])
    return np.array([d["embedding"] for d in dati], dtype=np.float32)


def indicizza():
    frammenti = []  # (file, testo)
    for percorso in sorted(glob.glob(os.path.join(CARTELLA_DOC, "*.txt"))):
        with open(percorso, encoding="utf-8") as f:
            for c in spezza_in_chunk(f.read()):
                frammenti.append((os.path.basename(percorso), c))
    if not frammenti:
        sys.exit(f"nessun .txt in {CARTELLA_DOC}")
    print(f"{len(frammenti)} frammenti da {CARTELLA_DOC}")
    matrice = embedding([PREFISSO_DOC + t for _, t in frammenti])
    np.savez(FILE_INDICE, matrice=matrice,
             fonti=np.array([f for f, _ in frammenti]),
             testi=np.array([t for _, t in frammenti]))
    print(f"indice salvato in {FILE_INDICE}: matrice {matrice.shape}")


def cerca(domanda, k=TOP_K):
    if not os.path.exists(FILE_INDICE):
        sys.exit("indice mancante: esegui prima `rag_minimo.py indicizza`")
    idx = np.load(FILE_INDICE)
    q = embedding([PREFISSO_QUERY + domanda])[0]
    # similarita' coseno: i vettori sono gia' a norma 1 (embd_normalize=2), basta il prodotto scalare
    punteggi = idx["matrice"] @ q
    migliori = np.argsort(-punteggi)[:k]
    return [(float(punteggi[i]), str(idx["fonti"][i]), str(idx["testi"][i])) for i in migliori]


def rispondi(domanda):
    risultati = cerca(domanda)
    contesto = "\n\n".join(f"[{n}] ({fonte}) {testo}"
                           for n, (_, fonte, testo) in enumerate(risultati, start=1))
    messaggi = [
        {"role": "system", "content":
            "Rispondi in italiano usando SOLO i frammenti forniti. Cita il numero del frammento "
            "tra parentesi quadre, es. [1]. Se i frammenti non bastano, di' che non lo sai."},
        {"role": "user", "content": f"Frammenti:\n{contesto}\n\nDomanda: {domanda}"},
    ]
    r = requests.post(f"{CHAT_URL}/v1/chat/completions", timeout=600, json={
        "model": CHAT_MODEL,
        "messages": messaggi,
        "temperature": 0.2,
        "max_tokens": 200,
        "chat_template_kwargs": {"enable_thinking": False},  # Qwen3.5: niente "thinking"
    })
    r.raise_for_status()
    risposta = r.json()["choices"][0]["message"]["content"]
    print("RISPOSTA:\n" + risposta.strip())
    print("\nFONTI:")
    for n, (punteggio, fonte, testo) in enumerate(risultati, start=1):
        print(f"  [{n}] {fonte} (sim {punteggio:.3f}): {testo[:90]}...")


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "indicizza":
        indicizza()
    elif comando == "cerca" and len(sys.argv) > 2:
        for punteggio, fonte, testo in cerca(" ".join(sys.argv[2:])):
            print(f"{punteggio:.3f}  {fonte}: {testo[:110]}...")
    elif comando == "rispondi" and len(sys.argv) > 2:
        rispondi(" ".join(sys.argv[2:]))
    else:
        print(__doc__)
        sys.exit(1)
