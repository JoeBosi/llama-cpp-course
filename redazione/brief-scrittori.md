# Brief per chi scrive un modulo

Stai scrivendo una parte del "Corso pratico di llama.cpp" (italiano, aggiornato a settembre 2026), sito MkDocs
Material in `/root/Developer/Inferenza-LLAMA-cpp` (docs_dir = `corso/`).

## Leggi PRIMA (obbligatorio)
1. `redazione/fatti-verificati.md`: versioni, comandi e output **provati**. Non contraddirlo, non inventare flag.
2. `redazione/convenzioni.md`: stile, kit MkDocs (ammonizioni, schede, Mermaid, SVG, badge di stato).
3. `redazione/upstream/`: documentazione ufficiale scaricata il 22/09/2026 (README, docs/*.md, tools/*/README.md,
   `llamaapp_*.md` = pagine di https://llama.app/docs, `help_<comando>.txt` = output reale di `llama <comando> --help`).
   Per ogni flag che citi, cerca conferma con grep in `help_*.txt` o nei README.
4. Le pagine scheletro già presenti in `corso/moduli/...` e `corso/laboratori/...`: contengono la scaletta concordata.
   Sostituiscile con contenuto completo mantenendo gli stessi percorsi/nomi file (i link incrociati dipendono da questi).

## Cosa produrre
- **Modulo** (`corso/moduli/NN-nome/README.md`): 1500-3500 parole. Struttura: H1 · badge di stato · "Cosa imparerai" ·
  sezioni per argomento con spiegazione + schema (Mermaid o SVG) + comandi verificati + output atteso · tabella di riepilogo
  flag/concetti · "Errori comuni" (ammonizioni warning) · "Laboratori di questo modulo" (link) · "Verifica" (5-8 domande
  a risposta breve, con le risposte in un blocco `??? success "Soluzioni"`) · "Riferimenti" (link ufficiali).
- **Laboratori** (`corso/laboratori/lab-NN-MM-nome/README.md`): 600-1500 parole ciascuno. Struttura già presente nello
  scheletro: Obiettivo · Prerequisiti · Materiale (modelli con repo HF, file, dimensione) · Procedura numerata con comandi
  e output atteso · Verifica del risultato · Domande e varianti · Consegna. Se il lab richiede uno script, scrivilo nella
  cartella del lab (Python o bash, corto, commentato in italiano) e citalo.
- **Schemi**: almeno 1 per modulo e 1 ogni 2 lab. Mermaid per flussi/sequenze; SVG in `corso/assets/img/` per layout
  e scale. Gli SVG devono essere leggibili sia in chiaro sia in scuro (vedi convenzioni).

## Verifica sul VPS (facoltativa ma gradita)
Puoi eseguire comandi reali: `export PATH=$HOME/.local/bin:$PATH SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`.
Usa SOLO il modello già in cache `ggml-org/Qwen3.5-0.8B-GGUF` (785 MB) o modelli ≤ 400 MB; la macchina ha ~4 GB liberi
e nessuna GPU ed è condivisa con altri scrittori: un solo processo llama alla volta, `-n` ≤ 100, `-t 3`, porte server
diverse da 18080 (usa quella indicata nel tuo incarico), e termina sempre i server che avvii (`pkill -f "port TUAPORTA"`).
Tarball release con tutti i binari (imatrix, gguf-split, tokenize, tts, mtmd, rpc): `~/llama-lab/rel/llama-b11046/`.
Non compilare llama.cpp dai sorgenti (troppo pesante per la macchina condivisa): descrivi la build dalla doc ufficiale.
Ciò che non puoi verificare (GPU, macOS, Windows, Android) va scritto dalla documentazione ufficiale e marcato con il
badge `stato-bozza` o una nota "non verificato su questa piattaforma".

## Alla fine
- Esegui `cd /root/Developer/Inferenza-LLAMA-cpp && .venv/bin/mkdocs build --strict -d /tmp/claude-0/-root-Developer-Inferenza-LLAMA-cpp/9082f0c4-0162-43e0-9284-f9135248400b/scratchpad/site-<tuo-id> 2>&1 | grep -E "WARNING|ERROR|Aborted"`
  e correggi i link rotti nelle TUE pagine (ignora avvisi su pagine altrui).
- NON fare commit git. Non toccare `mkdocs.yml`, `corso/index.md`, né pagine assegnate ad altri.
- Rispondi con: elenco file scritti, cosa hai verificato davvero sul VPS, cosa è rimasto "da verificare".
