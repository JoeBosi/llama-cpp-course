# Regole di tono (richiesta di Giuseppe, 28/10/2026)

Il corso **dà conoscenze, non si scusa**. Via tutte le frasi da "avvertenza":

## Da togliere sempre
- Badge `<span class="stato stato-verificato">…</span>` e `<span class="stato stato-bozza">…</span>` (ovunque, anche nel testo).
- Frasi tipo: "verificato su b11046", "verificato sul VPS", "non verificato", "da verificare", "bozza",
  "non eseguito", "non sono state eseguite", "scritto dalla documentazione ufficiale, non provato",
  "non provato su questa piattaforma", "non testato", "cosa è stato provato davvero", "l'abbiamo provato/letto",
  "con l'aiuto di un assistente IA", "rivisti dall'autore", "stime da confermare", "macchina condivisa"
  (come scusa per la varianza), "non è stato possibile provare…".
- Note a piè di pagina o parentesi che dicono *se* una cosa è stata provata.

## Come riscrivere
- Il contenuto non provato diventa **contenuto normale**, scritto al presente, con tono sicuro, e dove serve il
  rimando alla documentazione ufficiale: "Per i dettagli vedi [docs/build.md](…)". Nessun "dovrebbe", nessun "in teoria".
- I numeri misurati restano, con il contesto tecnico ma senza giustificazioni: "sul VPS del corso (6 vCPU condivise,
  macchina carica)" → "su una macchina a 6 vCPU senza GPU". "Output verificato su questo VPS" → "Output su una
  macchina a 6 vCPU senza GPU". Va bene dire "su CPU" o "su GPU" come contesto, non come scusa.
- "sul VPS del corso" come riferimento di laboratorio (es. "l'esempio usa il VPS del corso") → "sulla macchina di
  prova" o semplicemente il contesto tecnico (Linux, CPU).
- Le stime (velocità su GPU, Mac, Raspberry) restano come stime tecniche: "valori indicativi" va bene; "da confermare
  sul tuo hardware" va bene se è un consiglio pratico, non una scusa. Toglierei "stime da esperienza".
- Il blocco `<div class="meta" markdown>` resta solo se contiene ancora qualcosa (modulo di appartenenza, durata,
  difficoltà); se resta vuoto va tolto del tutto, senza lasciare righe vuote doppie.
- Non cambiare contenuto tecnico, comandi, output, tabelle, link: solo il tono delle frasi di avvertenza.
- Non toccare `mkdocs.yml`, `corso/index.md`, `corso/informazioni.md`, `corso/versione.md` (li fa il coordinatore).

## Verifica finale
`grep -rniE "verificat|bozza|da verificare|non eseguit|non provat|provato davvero|assistente IA|VPS del corso|questo VPS|macchina condivisa" corso --include='*.md'`
deve restituire zero righe nei file assegnati (eccezione ammessa: "verifica"/"verificare" come azione dello studente,
es. "Verifica del risultato", "verifica che il server risponda": quelle restano).
