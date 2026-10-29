# Italian → English glossary for the course translation

Use these terms every time. Rules for translators:

- Translate **prose only**. Code blocks, commands, flags, output, file names, paths, URLs, Mermaid node IDs and
  HTML/attr_list markup stay identical. Translate comments inside code blocks only if they are plain prose
  comments (`# avvia il server` → `# start the server`); never change the code itself.
- Mermaid diagrams: translate the visible labels only, keep IDs, arrows and syntax.
- Admonition titles (`!!! tip "Suggerimento"`) and tab labels (`=== "Linux"`) are prose: translate them.
- Internal links to other pages stay the same (`../02-primi-passi/README.md`); anchors to headings may change
  (MkDocs builds them from the English heading), so update `#anchor` links to match the translated headings.
- Plain, direct US English, second person ("you"), present tense. Same tone as the Italian: every sentence teaches.
- Keep numbers, units and measured values exactly. Italian decimal comma becomes a point (`4,85` → `4.85`),
  thousands space becomes a comma (`8 192` → `8,192`) in prose only, never inside code or output.
- File name: `pagina.md` → `pagina.en.md` next to it (`README.md` → `README.en.md`).
- Author: "Prof. Giuseppe Bosi" in both languages. English degree: "Master's-level degree in Electronic Engineering
  (5-year Italian Laurea, pre-reform, EQF level 7)". Never "M.Sc.", "Ing.", "licensed engineer".
- Personal site link in English pages: https://www.giuseppebosi.com/en/

| Italiano | English |
|---|---|
| corso pratico | hands-on course |
| modulo | module |
| laboratorio (lab) | lab |
| progetto finale | final project |
| risorse | resources |
| obiettivi | objectives |
| prerequisiti | prerequisites |
| durata | duration |
| livello: base / intermedio / avanzato | level: beginner / intermediate / advanced |
| cosa ti serve | what you need |
| passi / procedimento | steps |
| risultato atteso / atteso | expected result / expected |
| verifica | check |
| riepilogo | summary |
| esercizi | exercises |
| domande di verifica | review questions |
| per approfondire | further reading |
| errori comuni | common mistakes |
| risoluzione dei problemi | troubleshooting |
| suggerimento | tip |
| attenzione | warning |
| nota | note |
| esempio | example |
| scheda / schede | tab / tabs |
| schema / diagramma | diagram |
| modello | model |
| pesi | weights |
| quantizzazione / quantizzare | quantization / quantize |
| contesto / finestra di contesto | context / context window |
| campionamento | sampling |
| temperatura | temperature |
| inferenza | inference |
| generazione di token | token generation |
| elaborazione del prompt | prompt processing |
| velocità (token/s) | speed (tokens/s) |
| memoria (RAM / VRAM) | memory (RAM / VRAM) |
| banda di memoria | memory bandwidth |
| scheda video / GPU | GPU |
| scaricamento su GPU (offload) | GPU offload |
| strati (layer) | layers |
| compilare / compilazione dai sorgenti | build / building from source |
| binari precompilati | prebuilt binaries |
| gestore di pacchetti | package manager |
| installazione | installation |
| riga di comando / terminale | command line / terminal |
| server di inferenza | inference server |
| interfaccia web | web UI |
| chiamata di funzioni / strumenti | tool calling |
| output strutturato | structured output |
| grammatica | grammar |
| multimodalità / visione / audio / voce | multimodality / vision / audio / voice |
| integrare nelle applicazioni | integrate into applications |
| messa in produzione | going to production / production deployment |
| servizio (systemd) | service (systemd) |
| monitoraggio | monitoring |
| decodifica speculativa | speculative decoding |
| modello bozza | draft model |
| matrice di importanza | importance matrix |
| approfondimenti | deep dives |
| macchina | machine |
| la tua macchina | your machine |
| il VPS del corso | the course VPS |
| build di riferimento | reference build |
| ultimo aggiornamento | last updated |
| Informazioni (pagina) | About |
| Glossario | Glossary |
| Modelli consigliati | Recommended models |
| Strumenti | Tools |
| Link utili | Useful links |
| Versione di riferimento | Reference version |
| Clic per ingrandire | Click to enlarge |
