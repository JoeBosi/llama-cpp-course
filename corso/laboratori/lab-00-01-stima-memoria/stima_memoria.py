#!/usr/bin/env python3
"""
stima_memoria.py - stima la memoria (RAM o VRAM) necessaria per far girare un
modello con llama.cpp: pesi + KV cache + margine per i buffer di calcolo.

Formule usate (vedi modulo 00):
  pesi     = n_parametri x bit_per_peso / 8
  KV cache = 2 x n_layer x n_kv_heads x head_dim x ctx x byte_per_elemento
             (il "2" conta le matrici K e V; byte_per_elemento = 2 per F16,
             1 per q8_0, 0.5625 per q4_0 = 4.5 bit)
  overhead = buffer di calcolo + grafo + tokenizer: stimato al 10 % dei pesi,
             con un minimo di 300 MiB (regola empirica, non una misura)

Uso:
  python3 stima_memoria.py --params 7.6e9 --bpw 4.85 --ctx 8192 \
      --layers 28 --kv-heads 4 --head-dim 128
  python3 stima_memoria.py --preset qwen3.5-0.8b --ctx 32768 --kv-type q8_0
  python3 stima_memoria.py --lista-preset

Solo libreria standard: nessuna dipendenza da installare.
"""

import argparse
import sys

MiB = 1024 ** 2
GiB = 1024 ** 3

# Byte per elemento della KV cache, in base al tipo scelto con -ctk/-ctv.
# q8_0 e q4_0 sono quantizzazioni a blocchi: 32 valori + una scala F16 ogni blocco.
KV_BYTES = {
    "f32": 4.0,
    "f16": 2.0,
    "bf16": 2.0,
    "q8_0": 34 / 32,      # 8 bit + 16 bit di scala ogni 32 valori = 8.5 bit
    "q4_0": 18 / 32,      # 4 bit + 16 bit di scala ogni 32 valori = 4.5 bit
}

# Bit per peso "effettivi" dei formati di quantizzazione piu comuni (dimensione del
# file / numero di parametri, valori tipici misurati su modelli reali).
BPW = {
    "f32": 32.0, "f16": 16.0, "bf16": 16.0,
    "q8_0": 8.5, "q6_k": 6.56, "q5_k_m": 5.68, "q5_0": 5.5,
    "q4_k_m": 4.85, "q4_k_s": 4.58, "q4_0": 4.5, "iq4_xs": 4.25,
    "q3_k_m": 3.91, "q2_k": 2.63, "iq2_xxs": 2.06,
}

# Alcuni modelli con i parametri architetturali letti dai metadati GGUF
# (chiavi <arch>.block_count, <arch>.attention.head_count_kv, <arch>.attention.key_length).
# "attn_layers" = strati che hanno davvero una KV cache: nei modelli ibridi
# (SSM + attention, es. Qwen3.5) sono solo una parte di block_count.
PRESET = {
    # nome:            (parametri, layer con KV cache, kv_heads, head_dim, nota)
    "qwen3.5-0.8b":    (772.85e6, 6, 2, 256, "25 blocchi, 1 su 4 e' attention piena (metadato full_attention_interval=4)"),
    "gemma-3-4b":      (3.88e9, 34, 4, 256, "34 layer; 5 su 6 sono a finestra scorrevole (KV limitata a 1024 token)"),
    "qwen3-8b":        (8.19e9, 36, 8, 128, "attention piena su tutti i layer, GQA 8 teste KV"),
    "llama-3.1-8b":    (8.03e9, 32, 8, 128, "attention piena, GQA 8 teste KV"),
    "qwen3-32b":       (32.8e9, 64, 8, 128, "attention piena, GQA 8 teste KV"),
    "llama-3.3-70b":   (70.6e9, 80, 8, 128, "attention piena, GQA 8 teste KV"),
}


def fmt(nbytes: float) -> str:
    """Formatta i byte in MiB o GiB, come fanno i log di llama.cpp."""
    if nbytes >= GiB:
        return f"{nbytes / GiB:6.2f} GiB"
    return f"{nbytes / MiB:6.0f} MiB"


def stima(params, bpw, ctx, layers, kv_heads, head_dim, kv_bytes, overhead_pct=0.10, overhead_min=300 * MiB):
    """Restituisce (pesi, kv, overhead, totale) in byte."""
    pesi = params * bpw / 8
    kv = 2 * layers * kv_heads * head_dim * ctx * kv_bytes
    overhead = max(pesi * overhead_pct, overhead_min)
    return pesi, kv, overhead, pesi + kv + overhead


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--preset", choices=sorted(PRESET), help="usa i parametri architetturali di un modello noto")
    p.add_argument("--lista-preset", action="store_true", help="elenca i preset e esci")
    p.add_argument("--params", type=float, help="numero di parametri (es. 7.6e9)")
    p.add_argument("--bpw", type=float, help="bit per peso (es. 4.85 per Q4_K_M)")
    p.add_argument("--quant", choices=sorted(BPW), help="in alternativa a --bpw: nome della quantizzazione")
    p.add_argument("--ctx", type=int, default=4096, help="lunghezza del contesto in token (default 4096)")
    p.add_argument("--layers", type=int, help="numero di layer con KV cache")
    p.add_argument("--kv-heads", type=int, help="teste K/V (head_count_kv)")
    p.add_argument("--head-dim", type=int, help="dimensione di una testa (key_length)")
    p.add_argument("--kv-type", choices=sorted(KV_BYTES), default="f16", help="tipo della KV cache (-ctk/-ctv), default f16")
    p.add_argument("--slots", type=int, default=1, help="richieste parallele del server (-np): il contesto totale si moltiplica")
    args = p.parse_args()

    if args.lista_preset:
        for nome, (params, layers, kvh, hd, nota) in PRESET.items():
            print(f"{nome:16s} {params/1e9:6.2f} B param  layer KV={layers:3d}  kv_heads={kvh:2d}  head_dim={hd:3d}  ({nota})")
        return 0

    if args.preset:
        params, layers, kv_heads, head_dim, nota = PRESET[args.preset]
        params = args.params or params
        layers = args.layers or layers
        kv_heads = args.kv_heads or kv_heads
        head_dim = args.head_dim or head_dim
    else:
        mancanti = [n for n in ("params", "layers", "kv_heads", "head_dim") if getattr(args, n) is None]
        if mancanti:
            p.error("senza --preset servono: " + ", ".join("--" + m.replace("_", "-") for m in mancanti))
        params, layers, kv_heads, head_dim, nota = args.params, args.layers, args.kv_heads, args.head_dim, ""

    if args.bpw is None and args.quant is None:
        p.error("indica --bpw oppure --quant")
    bpw = args.bpw if args.bpw is not None else BPW[args.quant]
    kv_bytes = KV_BYTES[args.kv_type]
    ctx_tot = args.ctx * args.slots

    pesi, kv, overhead, totale = stima(params, bpw, ctx_tot, layers, kv_heads, head_dim, kv_bytes)

    print(f"Modello: {args.preset or 'personalizzato'}  {nota}")
    print(f"  parametri = {params/1e9:.2f} B, {bpw} bit/peso; layer con KV = {layers}, kv_heads = {kv_heads}, head_dim = {head_dim}")
    print(f"  contesto  = {args.ctx} token x {args.slots} slot = {ctx_tot} token, KV cache {args.kv_type} ({kv_bytes*8:.1f} bit/elemento)")
    print()
    print(f"  pesi           {fmt(pesi)}   = {params:.3g} x {bpw} / 8")
    print(f"  KV cache       {fmt(kv)}   = 2 x {layers} x {kv_heads} x {head_dim} x {ctx_tot} x {kv_bytes:.4g}")
    print(f"  overhead       {fmt(overhead)}   (stima: max(10 % dei pesi, 300 MiB))")
    print(f"  -------------------------")
    print(f"  TOTALE stimato {fmt(totale)}")
    print()
    per_token = 2 * layers * kv_heads * head_dim * kv_bytes
    print(f"  KV cache per token: {per_token/1024:.1f} KiB  ->  1 GiB di KV basta per circa {int(GiB/per_token):,} token".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
