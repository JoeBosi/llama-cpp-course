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

## Kit di scrittura MkDocs Material (usarlo, non solo testo piatto)
Il sito è generato con MkDocs Material (`mkdocs.yml`). Ogni pagina deve avere **almeno uno schema** (Mermaid o SVG)
dove aiuta a capire, e usare questi blocchi:

- **Ammonizioni**: `!!! tip "Titolo"`, `!!! warning`, `!!! note`, `!!! example`, `!!! danger`; ripiegabili con `??? info "Titolo"`.
- **Schede per piattaforma**:
  ```
  === "Linux"
      ```bash
      ...
      ```
  === "macOS"
  === "Windows (PowerShell)"
  ```
- **Diagrammi Mermaid** in un fence ` ```mermaid ` (flowchart, sequenceDiagram, pie, gantt, classDiagram sono resi
  automaticamente in chiaro e scuro). Etichette brevi, in italiano.
- **SVG**: per gli schemi "da lavagna" (layout di memoria, pipeline, scale di quantizzazione) scrivere un file in
  `corso/assets/img/<modulo>-<nome>.svg` (viewBox, font `sans-serif`, dimensioni ≤ 900×500, colori leggibili su
  sfondo chiaro E scuro: usare riempimenti pieni con testo scuro su riempimenti chiari, es. `#ccfbf1`/`#134e4a`,
  `#ffedd5`/`#7c2d12`, `#e0e7ff`/`#312e81`, `#f3f4f6`/`#111827`, e **non** usare testo nero su sfondo trasparente).
  Inserirlo con:
  ```
  <figure class="schema" markdown>
  ![Descrizione](../../assets/img/03-scala-quantizzazioni.svg)
  <figcaption>Didascalia</figcaption>
  </figure>
  ```
- **Tabelle** per confronti (flag, formati, dimensioni). **Tasti**: `++ctrl+c++`. Liste di attività `- [ ]`.
- **Annotazioni sul codice**: `# (1)!` nel blocco + lista `1. spiegazione` sotto.
- Stato in cima alla pagina, subito sotto l'H1: `<span class="stato stato-verificato">verificato su b11046</span>`
  oppure `<span class="stato stato-bozza">bozza · da verificare su GPU</span>`.
- Link interni **relativi ai file .md** (es. `../../laboratori/lab-02-01-primo-modello/README.md`): MkDocs li
  converte e `mkdocs build --strict` fallisce se sono rotti.
- Le pagine indice delle cartelle si chiamano `README.md` (funzionano sia su GitHub sia su MkDocs).
- La navigazione è automatica (plugin awesome-nav): titolo = H1 della pagina, ordine = nome file. Per aggiungere
  una pagina basta creare il file; per toglierla basta cancellarlo. `.nav.yml` nelle cartelle solo se serve un ordine diverso.
