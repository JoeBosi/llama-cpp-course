#!/usr/bin/env python3
"""Agente minimo con tool calling su llama serve: il modello chiama `get_weather`, noi la eseguiamo,
gli restituiamo il risultato e lui formula la risposta finale.

Uso:
    python agente_meteo.py                       # meteo FINTO (valori fissi, nessuna rete)
    python agente_meteo.py --reale               # meteo REALE da Open-Meteo (API pubblica, senza chiave)
    python agente_meteo.py --reale "Che tempo fa a Palermo e a Torino?"
    python agente_meteo.py --forza               # obbliga la prima chiamata allo strumento (tool_choice="required")

Richiede: pip install openai. Variabile LLAMA_URL per cambiare server (default http://127.0.0.1:8080).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from openai import OpenAI

# LLAMA_URL=http://host:porta per puntare a un server diverso da quello di default
client = OpenAI(base_url=os.environ.get("LLAMA_URL", "http://127.0.0.1:8080") + "/v1", api_key="no-key-required")
MODEL = "local"
EXTRA = {"chat_template_kwargs": {"enable_thinking": False}}

# 1) La descrizione dello strumento nel formato OpenAI: nome, descrizione, parametri in JSON Schema.
#    Questa descrizione viene iniettata nel prompt dal chat template del modello.
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Restituisce il meteo attuale di una città (temperatura in °C, vento, condizioni).",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Nome della città, es. 'Bologna'"},
            },
            "required": ["city"],
        },
    },
}]

CODICI_WMO = {0: "sereno", 1: "prevalentemente sereno", 2: "parzialmente nuvoloso", 3: "coperto",
              45: "nebbia", 48: "nebbia con brina", 51: "pioviggine", 61: "pioggia debole",
              63: "pioggia", 65: "pioggia forte", 71: "neve", 80: "rovesci", 95: "temporale"}


def get_weather_finto(city: str) -> dict:
    """Versione finta: nessuna rete, valori fissi. Utile per capire il ciclo senza variabili esterne."""
    return {"city": city, "temperatura_c": 24.5, "vento_kmh": 12, "condizioni": "sereno", "fonte": "finto"}


def get_weather_reale(city: str) -> dict:
    """Versione reale: geocoding + meteo attuale da Open-Meteo (nessuna chiave API richiesta)."""
    q = urllib.parse.urlencode({"name": city, "count": 1, "language": "it"})
    with urllib.request.urlopen(f"https://geocoding-api.open-meteo.com/v1/search?{q}", timeout=15) as r:
        geo = json.load(r)
    if not geo.get("results"):
        return {"error": f"città '{city}' non trovata"}
    g = geo["results"][0]
    q = urllib.parse.urlencode({"latitude": g["latitude"], "longitude": g["longitude"],
                                "current": "temperature_2m,wind_speed_10m,weather_code"})
    with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{q}", timeout=15) as r:
        w = json.load(r)["current"]
    return {"city": g["name"], "temperatura_c": w["temperature_2m"], "vento_kmh": w["wind_speed_10m"],
            "condizioni": CODICI_WMO.get(w["weather_code"], f"codice WMO {w['weather_code']}"),
            "fonte": "open-meteo.com"}


def esegui_tool(nome: str, argomenti: dict, reale: bool) -> dict:
    if nome == "get_weather":
        return (get_weather_reale if reale else get_weather_finto)(**argomenti)
    return {"error": f"strumento sconosciuto: {nome}"}


def agente(domanda: str, reale: bool, forza: bool, max_giri: int = 4) -> str:
    # Con modelli piccoli il prompt di sistema conta molto: uno troppo "narrativo" ("Sei un assistente meteo…")
    # può spingere il modello a INVENTARE i dati invece di chiamare lo strumento. Questo è sobrio e funziona.
    messaggi = [
        {"role": "system", "content": "Usa gli strumenti quando servono. Rispondi in italiano, in breve."},
        {"role": "user", "content": domanda},
    ]
    for giro in range(max_giri):
        # 2) Chiediamo al modello; gli passiamo l'elenco degli strumenti a ogni chiamata.
        #    tool_choice: "auto" lascia decidere al modello; "required" (solo al primo giro, con --forza)
        #    lo obbliga a chiamare uno strumento; "none" vieta le chiamate.
        scelta = "required" if (forza and giro == 0) else "auto"
        r = client.chat.completions.create(model=MODEL, messages=messaggi, tools=TOOLS,
                                           tool_choice=scelta, temperature=0, max_tokens=120,
                                           extra_body=EXTRA)
        msg = r.choices[0].message
        # 3) Nessuna tool call: è la risposta finale.
        if not msg.tool_calls:
            return msg.content or "(risposta vuota)"
        # 4) Il modello vuole chiamare uno o più strumenti: eseguiamo NOI la funzione...
        messaggi.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            argomenti = json.loads(tc.function.arguments)
            print(f"  [giro {giro + 1}] il modello chiama {tc.function.name}({argomenti})")
            risultato = esegui_tool(tc.function.name, argomenti, reale)
            print(f"  [giro {giro + 1}] risultato: {risultato}")
            # 5) ...e rimandiamo il risultato con role="tool", agganciato all'id della chiamata.
            messaggi.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(risultato, ensure_ascii=False)})
    return "(troppi giri senza risposta finale)"


if __name__ == "__main__":
    reale = "--reale" in sys.argv
    forza = "--forza" in sys.argv  # obbliga la chiamata allo strumento al primo giro (tool_choice="required")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    domanda = args[0] if args else "Che tempo fa a Bologna?"
    print(f"Domanda: {domanda}  (meteo {'REALE' if reale else 'finto'}{', tool forzato' if forza else ''})")
    print("Risposta:", agente(domanda, reale, forza))
