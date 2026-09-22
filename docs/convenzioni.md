# Convenzioni di scrittura

## Lingua e tono
- Italiano, seconda persona singolare ("apri il terminale"), frasi brevi.
- Termini tecnici inglesi lasciati in inglese quando sono quelli che lo studente troverà nei log
  e nella documentazione (token, prompt, KV cache, offload); spiegati alla prima occorrenza e nel
  [glossario](../risorse/glossario.md).

## Comandi
- Ogni comando è **verificato** sulla versione di [`VERSIONE.md`](../VERSIONE.md) prima di essere pubblicato.
- Blocchi di codice con la shell indicata (` ```bash `, ` ```powershell `).
- Quando un comando differisce per piattaforma, usare tre blocchi etichettati: Linux / macOS / Windows.
- Mostrare l'output atteso (accorciato con `…`) quando serve a verificare il risultato.

## Modelli
- Nei laboratori usare modelli **piccoli** (≤ 4B parametri, quantizzati Q4_K_M o simili) in modo che girino
  su un portatile con 8 GB senza GPU. Varianti più grandi solo come "per chi ha una GPU".
- Indicare sempre repository Hugging Face, file, dimensione su disco e licenza. Elenco in
  [`risorse/modelli-consigliati.md`](../risorse/modelli-consigliati.md).

## Nomi di file e cartelle
- Moduli: `moduli/NN-nome/`; laboratori: `laboratori/lab-NN-MM-nome/` (NN = modulo, MM = progressivo).
- Script e file di supporto di un lab restano nella cartella del lab.
- Modelli scaricati e build **non** vanno nel repository (vedi `.gitignore`).

## Stato delle pagine
In cima a ogni pagina: 🟡 scaletta / da scrivere · 🟠 bozza · 🟢 verificato (comandi provati) · 🔵 revisionato.
