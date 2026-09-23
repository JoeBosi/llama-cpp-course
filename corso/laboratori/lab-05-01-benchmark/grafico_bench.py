#!/usr/bin/env python3
"""
grafico_bench.py: disegna un grafico t/s vs thread dai risultati JSON di `llama bench -o json`.

Uso:
    llama bench -m modello.gguf -p 64 -n 32 -t 1,2,4,8 -r 3 -o json > bench.json
    python3 grafico_bench.py bench.json                   # produce bench.png
    python3 grafico_bench.py bench.json -o thread.png     # nome file a scelta
    python3 grafico_bench.py run1.json run2.json          # più file: vengono uniti

Legge i campi standard dell'output JSON (`n_threads`, `n_prompt`, `n_gen`, `avg_ts`, `stddev_ts`,
`model_type`, `cpu_info`, `backends`) e traccia due serie: pp (prompt processing) e tg (token generation).
Richiede matplotlib (`pip install matplotlib`).
"""

import argparse
import json
import sys
from collections import defaultdict


def carica(percorsi):
    """Legge uno o più file JSON (lista di risultati, oppure JSONL una riga per test)."""
    risultati = []
    for p in percorsi:
        with open(p, encoding="utf-8") as f:
            testo = f.read().strip()
        if not testo:
            continue
        if testo.startswith("["):
            risultati.extend(json.loads(testo))            # formato -o json
        else:
            for riga in testo.splitlines():                # formato -o jsonl
                riga = riga.strip()
                if riga:
                    risultati.append(json.loads(riga))
    return risultati


def raggruppa(risultati):
    """Ritorna {"pp64": {thread: (media, dev)}, "tg32": {...}} e le info macchina."""
    serie = defaultdict(dict)
    info = {}
    for r in risultati:
        if r.get("n_prompt", 0) > 0 and r.get("n_gen", 0) == 0:
            nome = f"pp{r['n_prompt']}"
        elif r.get("n_gen", 0) > 0 and r.get("n_prompt", 0) == 0:
            nome = f"tg{r['n_gen']}"
        else:                                              # test -pg: prompt + generazione
            nome = f"pp{r.get('n_prompt', 0)}+tg{r.get('n_gen', 0)}"
        serie[nome][r["n_threads"]] = (r["avg_ts"], r.get("stddev_ts", 0.0))
        info.setdefault("model", r.get("model_type", "?"))
        info.setdefault("cpu", r.get("cpu_info", "?"))
        info.setdefault("backend", r.get("backends", "?"))
        info.setdefault("build", r.get("build_number", "?"))
    return serie, info


def main():
    ap = argparse.ArgumentParser(description="Grafico t/s vs thread da llama bench -o json")
    ap.add_argument("file", nargs="+", help="file JSON/JSONL prodotti da llama bench")
    ap.add_argument("-o", "--output", default="bench.png", help="immagine di uscita (default: bench.png)")
    ap.add_argument("--titolo", default=None, help="titolo personalizzato")
    args = ap.parse_args()

    risultati = carica(args.file)
    if not risultati:
        sys.exit("nessun risultato trovato nei file indicati")
    serie, info = raggruppa(risultati)

    try:
        import matplotlib
        matplotlib.use("Agg")                              # nessuna finestra: salva solo il file
        import matplotlib.pyplot as plt
    except ImportError:
        sys.exit("matplotlib non installato: pip install matplotlib")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for nome in sorted(serie):
        punti = sorted(serie[nome].items())               # ordina per numero di thread
        x = [t for t, _ in punti]
        y = [m for _, (m, _) in punti]
        err = [d for _, (_, d) in punti]
        ax.errorbar(x, y, yerr=err, marker="o", capsize=3, label=nome)
        for xi, yi in zip(x, y):                           # etichetta il valore su ogni punto
            ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 6),
                        ha="center", fontsize=8)

    ax.set_xlabel("thread (-t)")
    ax.set_ylabel("token/s")
    ax.set_xticks(sorted({t for s in serie.values() for t in s}))
    ax.grid(True, alpha=0.3)
    ax.legend()
    titolo = args.titolo or f"{info['model']} · {info['backend']} · build {info['build']}"
    ax.set_title(titolo, fontsize=11)
    fig.text(0.5, 0.005, info["cpu"], ha="center", fontsize=8, color="gray")
    fig.tight_layout()
    fig.savefig(args.output, dpi=150)
    print(f"salvato {args.output}")

    # Riepilogo testuale, utile per la consegna
    for nome in sorted(serie):
        print(nome + ":", ", ".join(f"t={t} → {m:.2f} t/s" for t, (m, _) in sorted(serie[nome].items())))


if __name__ == "__main__":
    main()
