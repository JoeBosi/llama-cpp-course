#!/usr/bin/env python3
"""Genera corso/.nav.yml: ogni modulo è una sezione che contiene la lezione e i suoi laboratori.

Convenzione: moduli in corso/moduli/NN-nome/README.md, laboratori in corso/laboratori/lab-NN-MM-nome/README.md.
Il lab con prefisso NN finisce sotto il modulo NN. Aggiungere un file = compare da solo alla prossima build.
Eseguito automaticamente da scripts/pubblica.sh; si può lanciare a mano: python3 scripts/genera-nav.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "corso"


def h1(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.parent.name


def yaml_str(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


moduli = sorted(p for p in (ROOT / "moduli").iterdir() if (p / "README.md").exists())
labs = sorted(p for p in (ROOT / "laboratori").iterdir() if (p / "README.md").exists())

lines = ["# GENERATO da scripts/genera-nav.py: non modificare a mano.", "nav:", "  - Home: index.md", "  - Il corso:"]
for m in moduli:
    num = re.match(r"(\d+[a-z]?)-", m.name).group(1)
    titolo = h1(m / "README.md")
    titolo_breve = re.sub(r"^Modulo \S+:\s*", "", titolo).replace("`", "")
    lines.append(f"      - {yaml_str(f'{num} · {titolo_breve}')}:")
    lines.append(f"          - moduli/{m.name}/README.md")
    for lab in labs:
        if re.match(rf"lab-{re.escape(num)}-", lab.name):
            lines.append(f"          - laboratori/{lab.name}/README.md")
lines += [
    "  - Progetti finali: progetti-finali",
    "  - Risorse:",
    "      - risorse/*",
    "      - versione.md",
]
(ROOT / ".nav.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"corso/.nav.yml: {len(moduli)} moduli, {len(labs)} laboratori")
