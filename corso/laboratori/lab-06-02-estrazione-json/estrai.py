#!/usr/bin/env python3
"""Estrazione di dati strutturati da testi liberi con `response_format` json_schema su llama serve.

Uso:
    python estrai.py                      # legge annunci.txt (blocchi separati da "===") e schema-annuncio.json
    python estrai.py --senza-schema       # confronto: stesso prompt, nessun vincolo (spesso JSON non valido)

Per ogni annuncio stampa il JSON prodotto e i controlli superati/falliti. Solo libreria standard.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080")
QUI = Path(__file__).parent
SCHEMA = json.loads((QUI / "schema-annuncio.json").read_text(encoding="utf-8"))

SYSTEM = (
    "Sei un estrattore di dati. Dal testo dell'annuncio immobiliare ricava un oggetto JSON con i campi: "
    "titolo (breve, max 80 caratteri), tipo (appartamento|villa|ufficio|altro), citta, metri_quadri (intero), "
    "locali (intero; se non indicato stima dal testo), prezzo_euro (intero, senza separatori; per gli affitti il canone "
    "mensile), ascensore (true/false), note (opzionale). Rispondi SOLO con il JSON."  # (1) lo schema NON viene mostrato al modello: descrivilo tu
)


def chiedi(testo: str, con_schema: bool) -> str:
    body = {
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": testo}],
        "temperature": 0,
        "max_tokens": 200,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if con_schema:
        # Forma OpenAI: response_format.json_schema.schema (è quella che l'SDK openai produce).
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "annuncio", "schema": SCHEMA}}
    req = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"]


def controlla(obj: dict) -> list[str]:
    """Controlli semantici minimi: la grammatica garantisce la FORMA, non la VERITÀ dei valori."""
    errori = []
    for campo in SCHEMA["required"]:
        if campo not in obj:
            errori.append(f"manca il campo obbligatorio '{campo}'")
    if obj.get("tipo") not in SCHEMA["properties"]["tipo"]["enum"]:
        errori.append(f"tipo non ammesso: {obj.get('tipo')!r}")
    for campo in ("metri_quadri", "locali", "prezzo_euro"):
        v = obj.get(campo)
        if not isinstance(v, int) or isinstance(v, bool):
            errori.append(f"{campo} non è un intero: {v!r}")
    if not isinstance(obj.get("ascensore"), bool):
        errori.append("ascensore non è booleano")
    return errori


def main() -> None:
    con_schema = "--senza-schema" not in sys.argv
    annunci = [a.strip() for a in (QUI / "annunci.txt").read_text(encoding="utf-8").split("===") if a.strip()]
    print(f"server {URL} · {len(annunci)} annunci · vincolo schema: {'SÌ' if con_schema else 'NO'}\n")
    ok = 0
    for i, testo in enumerate(annunci, 1):
        print(f"--- annuncio {i}: {testo[:60]}…")
        risposta = chiedi(testo, con_schema)
        try:
            obj = json.loads(risposta)
        except json.JSONDecodeError as e:
            print(f"  JSON NON VALIDO ({e}):\n  {risposta[:300]!r}\n")
            continue
        print("  " + json.dumps(obj, ensure_ascii=False))
        errori = controlla(obj)
        if errori:
            print("  controlli falliti: " + "; ".join(errori))
        else:
            ok += 1
            print("  controlli superati")
        print()
    print(f"risultato: {ok}/{len(annunci)} annunci validi. Ora confronta i VALORI con il testo: sono giusti?")


if __name__ == "__main__":
    main()
