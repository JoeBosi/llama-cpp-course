#!/usr/bin/env python3
"""
anatomia_gguf.py - legge un file GGUF con l'API GGUFReader (pacchetto `gguf`,
lo stesso che usa llama.cpp per scrivere i file) e ne riassume:

  1. i metadati "generali" (architettura, nome, licenza, tipo di file)
  2. i parametri architetturali che servono a stimare la KV cache
  3. la quantita' di byte occupata da ogni tipo di tensore (Q8_0, F32, ...)
  4. i primi caratteri del chat template

Uso:
  pip install gguf
  python3 anatomia_gguf.py modello.gguf [--tensori]   # --tensori elenca anche i tensori
"""

import argparse
import sys
from collections import Counter, defaultdict

from gguf import GGUFReader, GGUFValueType

MiB = 1024 ** 2


def valore(field):
    """Estrae il valore Python di un campo di metadati (scalare, stringa o array)."""
    tipo = field.types[0]
    if tipo == GGUFValueType.ARRAY:
        n = len(field.data)
        # Per gli array lunghi (vocabolario, merges) mostriamo solo la dimensione.
        if n > 8:
            return f"[array di {n} elementi]"
        return field.contents()
    return field.contents()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", help="percorso del file .gguf")
    p.add_argument("--tensori", action="store_true", help="elenca tutti i tensori (nome, forma, tipo, byte)")
    args = p.parse_args()

    r = GGUFReader(args.file)                     # (1)! mappa il file in memoria, non lo carica tutto
    arch = r.fields["general.architecture"].contents()

    print(f"== File: {args.file}")
    print(f"   versione GGUF {r.fields['GGUF.version'].contents()}, "
          f"{len(r.fields)} coppie chiave/valore, {len(r.tensors)} tensori")

    print("\n== Metadati generali")
    for k in ("general.name", "general.architecture", "general.size_label", "general.license",
              "general.file_type", "general.quantization_version"):
        if k in r.fields:
            print(f"   {k:32s} = {valore(r.fields[k])}")

    print(f"\n== Parametri architetturali (prefisso '{arch}.')")
    chiavi = ("block_count", "context_length", "embedding_length", "feed_forward_length",
              "attention.head_count", "attention.head_count_kv", "attention.key_length",
              "attention.value_length", "full_attention_interval", "expert_count", "expert_used_count")
    for suffisso in chiavi:
        k = f"{arch}.{suffisso}"
        if k in r.fields:
            print(f"   {k:40s} = {valore(r.fields[k])}")

    print("\n== Tokenizer")
    for k in ("tokenizer.ggml.model", "tokenizer.ggml.pre", "tokenizer.ggml.tokens",
              "tokenizer.ggml.bos_token_id", "tokenizer.ggml.eos_token_id", "tokenizer.ggml.add_bos_token"):
        if k in r.fields:
            print(f"   {k:32s} = {valore(r.fields[k])}")
    if "tokenizer.chat_template" in r.fields:
        tmpl = r.fields["tokenizer.chat_template"].contents()
        print(f"   tokenizer.chat_template          = {len(tmpl)} caratteri, inizia con: {tmpl[:60]!r}")

    print("\n== Tensori per tipo (byte su disco)")
    conteggio = Counter()
    byte_per_tipo = defaultdict(int)
    elementi = 0
    totale = 0
    for t in r.tensors:
        nome_tipo = t.tensor_type.name
        conteggio[nome_tipo] += 1
        byte_per_tipo[nome_tipo] += t.n_bytes
        elementi += t.n_elements
        totale += t.n_bytes
    for nome_tipo, n in conteggio.most_common():
        b = byte_per_tipo[nome_tipo]
        print(f"   {nome_tipo:8s} {n:4d} tensori  {b / MiB:9.1f} MiB  ({100 * b / totale:5.1f} %)")
    print(f"   {'totale':8s} {len(r.tensors):4d} tensori  {totale / MiB:9.1f} MiB")
    print(f"\n   parametri totali = {elementi / 1e6:.2f} M  ->  {8 * totale / elementi:.2f} bit per peso medi")

    if args.tensori:
        print("\n== Elenco tensori")
        for t in r.tensors:
            forma = "x".join(str(int(d)) for d in t.shape)
            print(f"   {t.name:40s} {forma:>20s}  {t.tensor_type.name:6s} {t.n_bytes / MiB:8.2f} MiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
