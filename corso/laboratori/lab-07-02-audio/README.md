# Audio e voce

> Modulo: [07: Multimodalità: visione, audio, voce](../../moduli/07-multimodale/README.md) · <span class="stato stato-bozza">bozza · comandi dalla documentazione ufficiale, da verificare (i modelli audio superano 1 GB e non sono stati provati sul VPS del corso)</span> · Durata stimata: 45 min

## Obiettivo

Dare un file audio in ingresso a un modello (trascrizione e comprensione) da cli e via API, e generare un file WAV
parlato con `llama-tts`. Il flusso è lo stesso delle immagini del lab 07-01: cambia solo il tipo di media e il modello.

## Prerequisiti

- Lab 07-01 completato (sai già cosa sono `mmproj` e le content parts).
- `ffmpeg` per creare/convertire l'audio; un microfono o un file di voce (MP3/WAV) tuo.
- Il **tarball della release** per `llama-tts` (non è nel binario dell'installer, vedi modulo 01):
  su Linux `~/llama-lab/rel/llama-b11046/llama-tts`, da avviare con `LD_LIBRARY_PATH` puntato alla stessa cartella
  se non è installato a sistema.
- RAM: 3 GB per Qwen3-ASR 0.6B, 8 GB per Gemma 4 E4B o Qwen3-TTS.

## Materiale

| Cosa | Repository | Dimensione | Uso |
|---|---|---|---|
| `ggml-org/Qwen3-ASR-0.6B-GGUF` | Hugging Face | 805 MB (Q8_0) + `mmproj` 214 MB | trascrizione |
| `ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF` | Hugging Face | 808 MB (Q4_K_M) + `mmproj` 1,37 GB | comprensione dell'audio |
| `ggml-org/gemma-4-E4B-it-GGUF` (Q4_0) | Hugging Face | 4,6 GB + `mmproj` 560 MB | testo + immagini + audio |
| `ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF` | Hugging Face | 1,0 GB (Q4_K_M) + `mmproj` 446 MB | sintesi vocale |

Dimensioni lette dall'API di Hugging Face il 23/09/2026.

## Procedura

### 1. Un audio di prova

Registra 5-10 secondi di voce (`arecord`, QuickTime, il telefono) e converti in WAV mono 16 kHz, il formato più
"neutro" per gli encoder audio:

```bash
mkdir -p ~/lab07 && cd ~/lab07
ffmpeg -loglevel error -y -i registrazione.m4a -ac 1 -ar 16000 voce.wav
```

Se non hai un microfono a portata, un tono sintetico serve almeno a verificare che la catena funzioni (il modello
descriverà "un suono continuo"), comando provato sul VPS:

```bash
ffmpeg -loglevel error -y -f lavfi -i "sine=frequency=440:duration=2" -ac 1 -ar 16000 tono.wav   # 64 KB
```

### 2. Trascrizione da riga di comando

```bash
llama cli -hf ggml-org/Qwen3-ASR-0.6B-GGUF --audio voce.wav -p "Transcribe this audio." -st
```

Il banner deve mostrare `modalities : text, audio`. In chat il comando è `/audio voce.wav` seguito dalla richiesta,
esattamente come da documentazione llama.app:

```text
> /audio voce.wav

Loaded media from 'voce.wav'

> transcribe this audio
```

Output atteso: il testo pronunciato, senza timestamp (Qwen3-ASR è un modello di trascrizione, non un modello di chat:
domande diverse da "trascrivi" danno risultati poveri).

### 3. Capire l'audio (non solo trascriverlo)

Con un modello "audio-language" (Ultravox, Voxtral, Gemma 4) puoi fare domande sul contenuto:

```bash
llama cli -hf ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF --audio voce.wav \
  -p "Riassumi in una frase quello che dice la persona e indica il suo stato d'animo." -st
```

### 4. Via API: `input_audio`

Avvia il server con un modello audio e manda l'audio in base64. `input_audio.format` viene ignorato (il formato è
rilevato dal contenuto); sono accettati MP3, WAV, FLAC (miniaudio):

```bash
llama serve -hf ggml-org/Qwen3-ASR-0.6B-GGUF --port 8080 -c 4096
```

```bash
B64=$(base64 -w0 voce.wav)
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d @- <<EOF | python3 -c 'import sys,json; r=json.load(sys.stdin); print(r["choices"][0]["message"]["content"]); print(r["usage"])'
{"messages":[{"role":"user","content":[
  {"type":"text","text":"Transcribe this audio."},
  {"type":"input_audio","input_audio":{"data":"$B64","format":"wav"}}]}],
 "max_tokens":200}
EOF
```

In alternativa `"input_audio":{"url":"https://…/file.mp3"}` oppure, con `--media-path DIR`, `"url":"file://voce.wav"`.
Annota `usage.prompt_tokens`: è il costo dell'audio in token, proporzionale alla durata.

Nella web UI (`http://127.0.0.1:8080/`) lo stesso file si allega dal menu media (MP3/WAV); la UI mostra il pulsante
solo se il modello caricato accetta audio.

### 5. Sintesi vocale con `llama-tts`

`llama-tts` usa un modello "backbone" più un `mmproj` che trasforma i token acustici in onda sonora. Comandi dal
README ufficiale (`tools/tts/README.md`) e dall'`--help` di b11046:

```bash
# inglese, voce di default
llama-tts -hf ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF -p "Hello world" --output out.wav

# italiano, clonando la voce del tuo file di riferimento
llama-tts -hf ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF \
    -p "Benvenuti al corso pratico di llama punto cpp." \
    --tts-lang it --tts-speaker-file voce.wav --output benvenuto.wav -n 800
```

- `--tts-lang`: `zh en de it pt es ja ko fr ru` (default `en`).
- `--tts-speaker-file`: WAV/MP3 di riferimento; con **Pocket TTS** è obbligatorio (senza, "il modello produce quasi
  nessun audio"); Pocket TTS si usa da file locali: `llama-tts -m pocket-tts.gguf -mm mmproj-pocket-tts.gguf …`.
- `-n`: limite in frame audio; quanti millisecondi vale un frame dipende dal modello. Se l'audio si interrompe, alzalo.
- Sampling (`--temp`, `--top-k`, `--top-p`) e `-ngl` funzionano come per il testo.

Ascolta il risultato (`ffplay benvenuto.wav`, `aplay`, o aprilo dal file manager) e controlla durata e frequenza di
campionamento con `ffprobe benvenuto.wav`.

!!! note "OuteTTS e WavTokenizer"
    Le versioni precedenti di `llama-tts` erano la demo di OuteTTS con il vocoder WavTokenizer come secondo modello.
    Il README corrente descrive lo strumento come indipendente dal modello (Qwen3-TTS, Pocket TTS) e l'`--help` di
    b11046 non ha più un flag per il vocoder: se trovi guide con `-mv WavTokenizer…`, sono relative a build vecchie.

### 6. Il giro completo (facoltativo)

Registra una domanda → trascrivila (passo 2) → passa il testo a un modello di chat (`llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$TESTO" -rea off`)
→ leggi la risposta con `llama-tts`. Sono tre processi e tre modelli: misura la latenza totale e ragiona su dove si
perde tempo (caricamento, encoding, generazione, sintesi).

## Verifica del risultato

- [ ] Il banner della cli con Qwen3-ASR mostra `audio` fra le modalità e la trascrizione corrisponde a ciò che hai detto.
- [ ] La richiesta API con `input_audio` restituisce testo e un `usage.prompt_tokens` maggiore di quello della sola domanda.
- [ ] `llama-tts` produce un WAV che si ascolta e ha durata coerente con la frase.

## Domande e varianti

1. Perché `input_audio.format` viene ignorato dal server? Cosa succede se mandi un file OGG?
2. Con Gemma 4 E4B (se hai 8 GB) manda **immagine e audio nello stesso messaggio**: come compone la risposta?
3. Quanti token costa un audio di 10 s rispetto a uno di 30 s? Il rapporto è lineare?
4. Prova `--tts-lang en` su una frase italiana e viceversa: cosa cambia nella pronuncia?
5. Trascrizione con `whisper.cpp` (progetto gemello di ggml) e con Qwen3-ASR: confronta accuratezza e velocità.

## Consegna

`lab07-02.md` con: la trascrizione ottenuta e il testo reale (con gli errori evidenziati), l'`usage` della richiesta
API, il comando `llama-tts` usato e l'output di `ffprobe` sul WAV generato, più una riga sulla latenza del giro completo
se l'hai fatto.
