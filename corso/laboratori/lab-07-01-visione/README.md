# Descrivere e interrogare immagini

> Modulo: [07: Multimodalità: visione, audio, voce](../../moduli/07-multimodale/README.md) · <span class="stato stato-verificato">verificato su b11046 (CPU)</span> · Durata stimata: 45 min

## Obiettivo

Far "vedere" un'immagine a un modello con llama.cpp in tre modi: da riga di comando (`--image`), in chat (`/image`) e
via API (`image_url` con data URI base64). Poi usare lo stesso meccanismo per leggere un documento (scontrino, modulo)
e confrontare un modello piccolissimo con uno da portatile.

## Prerequisiti

- `llama` installato (modulo 01) e il modulo 04 per il server e `curl`.
- `ffmpeg` (per generare l'immagine di prova; in alternativa qualsiasi PNG/JPEG tuo).
- 2 GB di RAM liberi per la parte A; 8 GB per la parte B (facoltativa).

## Materiale

| Cosa | Fonte | Dimensione | Licenza |
|---|---|---|---|
| `ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0` | Hugging Face | 175 MB + `mmproj` 104 MB | Apache 2.0 |
| `ggml-org/gemma-3-4b-it-GGUF` (parte B) | Hugging Face | 2,5 GB (Q4_K_M) + `mmproj` 851 MB | Gemma Terms |
| [`chiedi_immagine.sh`](chiedi_immagine.sh) | questa cartella | script bash: base64 → `/v1/chat/completions` | |

## Procedura

### 1. Un'immagine di prova

Un'immagine "sintetica" ha il vantaggio che sai già la risposta giusta. Con `ffmpeg`:

```bash
mkdir -p ~/lab07 && cd ~/lab07
ffmpeg -loglevel error -y -f lavfi \
  -i "color=c=white:s=320x240:d=1,drawbox=x=40:y=40:w=120:h=120:color=red@1:t=fill,drawbox=x=200:y=60:w=80:h=140:color=blue@1:t=fill" \
  -frames:v 1 forme.png
```

Ottieni `forme.png` (1,7 KB): sfondo bianco, un quadrato rosso a sinistra e un rettangolo blu a destra.

### 2. Domanda secca da riga di comando

```bash
llama cli -hf ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0 --image forme.png -p "Describe this image." -st -n 60
```

Al primo avvio scarica modello **e** `mmproj` (280 MB in tutto). Output ottenuto sul VPS del corso (`-t 3`):

```text
modalities : text, vision, video
…
Loaded media from 'forme.png'

> Describe this image.
 The image features two rectangular shapes: a red rectangle and a blue rectangle. Both rectangles have a
 distinct and classic rectangular form. …

[ Prompt: 5.1 t/s | Generation: 5.6 t/s ]
```

Controlla la riga `modalities`: se dice solo `text`, il proiettore non è stato caricato.

### 3. In chat: prima il media, poi la domanda

```bash
llama cli -hf ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0
```

```text
> /image forme.png
Loaded media from 'forme.png'
> Which shape is on the left?
> /image forme.png
> How many shapes are there?
```

Il media allegato vale per il messaggio successivo; per una nuova domanda sulla stessa immagine riallegala (ogni
allegato costa di nuovo i suoi token di contesto). `/exit` per uscire.

### 4. Via API con base64

Avvia il server (porta a scelta) e attendi `/health`:

```bash
llama serve -hf ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0 --port 8080 -c 4096
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}
curl -s http://127.0.0.1:8080/models | python3 -m json.tool | grep -A2 capabilities
```

L'endpoint nativo `/models` elenca `"capabilities": ["completion", "multimodal"]`: è così che un client scopre se può
mandare immagini. Ora lo script:

```bash
./chiedi_immagine.sh forme.png "Describe this image." http://127.0.0.1:8080
```

Lo script codifica il file (`base64 -w0`), costruisce le content parts `text` + `image_url` con
`data:image/png;base64,…`, chiama `/v1/chat/completions` e stampa risposta e `usage`. Nel log del server compare
`srv load_model: loaded multimodal model, '…/mmproj-SmolVLM-256M-Instruct-Q8_0.gguf'`.

Con l'SDK `openai` (modulo 04) il body è identico:

```python
import base64, openai
client = openai.OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="no-key")
uri = "data:image/png;base64," + base64.b64encode(open("forme.png", "rb").read()).decode()
r = client.chat.completions.create(model="x", messages=[{"role": "user", "content": [
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": uri}}]}], max_tokens=80)
print(r.choices[0].message.content, r.usage.prompt_tokens)
```

### 5. Quanto costa un'immagine

Fai la stessa domanda **senza** immagine e confronta `usage.prompt_tokens`:

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Describe this image."}],"max_tokens":5}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["usage"])'
```

Sul VPS: **146 token** con l'immagine, **12** senza → l'immagine 320×240 vale ~134 token per SmolVLM. Prova con una
foto grande e osserva come cambia (e quanto tempo impiega il prompt processing su CPU: 150 token a ~4-13 t/s).

### 6. (Parte B, con 8 GB) Leggere un documento

Ferma il server (++ctrl+c++) e riavvialo con Gemma 3 4B, che legge testo nelle immagini molto meglio:

```bash
llama serve -hf ggml-org/gemma-3-4b-it-GGUF --port 8080 -c 8192
./chiedi_immagine.sh scontrino.jpg "Elenca le voci e il totale in formato JSON." http://127.0.0.1:8080
```

Fotografa uno scontrino o un modulo (o usa l'immagine di una fattura di prova). Per un JSON garantito abbina
`response_format` con uno schema (modulo 06). Su GPU aggiungi `-ngl all`; con poca VRAM `--no-mmproj-offload`.

## Verifica del risultato

- [ ] Il banner della cli mostra `modalities : text, vision, video` con SmolVLM.
- [ ] La descrizione da cli nomina due forme e i colori rosso e blu.
- [ ] `/models` riporta la capacità `multimodal` e lo script stampa una risposta con `prompt` > 100 token.
- [ ] Hai misurato la differenza di token con e senza immagine.

## Domande e varianti

1. Perché il modello da 256M descrive bene l'immagine in chat ma via API con `temperature: 0` ha risposto solo "Blue"?
   (Sul VPS è successo davvero.) Prova a variare temperatura e formulazione della domanda.
2. Manda **due** immagini nello stesso messaggio (`--image a.png,b.png` o due content parts) e chiedi le differenze.
3. Avvia con `--no-mmproj` e ripeti lo script: che errore ottieni?
4. Ridimensiona una foto a 512 px di lato e confronta token e tempo con l'originale.
5. Variante web UI: apri `http://127.0.0.1:8080/`, trascina `forme.png` nella chat e poi un PDF.

## Consegna

Un file `lab07-01.md` con: l'output della cli (passo 2), la risposta e `usage` dello script (passo 4), la tabella
token con/senza immagine (passo 5) e, se hai fatto la parte B, il JSON estratto dal documento con una nota su cosa
il modello ha sbagliato.
