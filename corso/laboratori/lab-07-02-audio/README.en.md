# Lab 07-02: Audio and voice

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/07-multimodale/README.md">07: Multimodality: vision, audio, voice</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 min</span>
</div>

## Objective

Feed an audio file to a model (transcription and understanding) from the cli and through the API, and generate a spoken WAV
file with `llama-tts`. The flow is the same as for images in lab 07-01: only the media type and the model change.

## Prerequisites

- Lab 07-01 completed (you already know what `mmproj` and content parts are).
- `ffmpeg` to create/convert audio; a microphone or a voice file (MP3/WAV) of your own.
- The **release tarball** for `llama-tts` (it is not in the installer binary, see module 01):
  on Linux `~/llama-lab/rel/llama-b11046/llama-tts`, to run with `LD_LIBRARY_PATH` pointing to the same folder
  if it is not installed system-wide.
- RAM: 3 GB for Qwen3-ASR 0.6B, 8 GB for Gemma 4 E4B or Qwen3-TTS.

## Materials

| What | Repository | Size | Use |
|---|---|---|---|
| `ggml-org/Qwen3-ASR-0.6B-GGUF` | Hugging Face | 805 MB (Q8_0) + `mmproj` 214 MB | transcription |
| `ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF` | Hugging Face | 808 MB (Q4_K_M) + `mmproj` 1.37 GB | audio understanding |
| `ggml-org/gemma-4-E4B-it-GGUF` (Q4_0) | Hugging Face | 4.6 GB + `mmproj` 560 MB | text + images + audio |
| `ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF` | Hugging Face | 1.0 GB (Q4_K_M) + `mmproj` 446 MB | speech synthesis |

Sizes as of 09/23/2026.

## Steps

### 1. A test audio file

Record 5-10 seconds of voice (`arecord`, QuickTime, your phone) and convert to mono 16 kHz WAV, the most
"neutral" format for audio encoders:

```bash
mkdir -p ~/lab07 && cd ~/lab07
ffmpeg -loglevel error -y -i registrazione.m4a -ac 1 -ar 16000 voce.wav
```

If you have no microphone at hand, a synthetic tone at least checks that the chain works (the model
will describe "a continuous sound"):

```bash
ffmpeg -loglevel error -y -f lavfi -i "sine=frequency=440:duration=2" -ac 1 -ar 16000 tono.wav   # 64 KB
```

### 2. Transcription from the command line

```bash
llama cli -hf ggml-org/Qwen3-ASR-0.6B-GGUF --audio voce.wav -p "Transcribe this audio." -st
```

The banner must show `modalities : text, audio`. In chat the command is `/audio voce.wav` followed by the request:

```text
> /audio voce.wav

Loaded media from 'voce.wav'

> transcribe this audio
```

Expected output: the spoken text, without timestamps (Qwen3-ASR is a transcription model, not a chat model:
requests other than "transcribe" give poor results).

### 3. Understanding audio (not just transcribing it)

With an "audio-language" model (Ultravox, Voxtral, Gemma 4) you can ask questions about the content:

```bash
llama cli -hf ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF --audio voce.wav \
  -p "Riassumi in una frase quello che dice la persona e indica il suo stato d'animo." -st
```

### 4. Through the API: `input_audio`

Start the server with an audio model and send the audio as base64. `input_audio.format` is ignored (the format is
detected from the content); MP3, WAV and FLAC are accepted (miniaudio):

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

Alternatively `"input_audio":{"url":"https://…/file.mp3"}` or, with `--media-path DIR`, `"url":"file://voce.wav"`.
Note `usage.prompt_tokens`: it is the cost of the audio in tokens, proportional to its duration.

In the web UI (`http://127.0.0.1:8080/`) you attach the same file from the media menu (MP3/WAV); the UI shows the button
only if the loaded model accepts audio.

### 5. Speech synthesis with `llama-tts`

`llama-tts` uses a "backbone" model plus an `mmproj` that turns acoustic tokens into a waveform. The main commands:

```bash
# English, default voice
llama-tts -hf ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF -p "Hello world" --output out.wav

# Italian, cloning the voice from your reference file
llama-tts -hf ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF \
    -p "Benvenuti al corso pratico di llama punto cpp." \
    --tts-lang it --tts-speaker-file voce.wav --output benvenuto.wav -n 800
```

- `--tts-lang`: `zh en de it pt es ja ko fr ru` (default `en`).
- `--tts-speaker-file`: reference WAV/MP3; with **Pocket TTS** it is mandatory (without it, "the model produces almost
  no audio"); Pocket TTS runs from local files: `llama-tts -m pocket-tts.gguf -mm mmproj-pocket-tts.gguf …`.
- `-n`: limit in audio frames; how many milliseconds a frame is worth depends on the model. If the audio cuts off, raise it.
- Sampling (`--temp`, `--top-k`, `--top-p`) and `-ngl` work as they do for text.

Listen to the result (`ffplay benvenuto.wav`, `aplay`, or open it from the file manager) and check duration and sample
rate with `ffprobe benvenuto.wav`.

!!! note "OuteTTS and WavTokenizer"
    Earlier versions of `llama-tts` were the OuteTTS demo with the WavTokenizer vocoder as a second model.
    Today the tool is model-independent (Qwen3-TTS, Pocket TTS) and the vocoder flag no longer exists: guides with `-mv WavTokenizer…` refer to old builds.

### 6. The full round trip (optional)

Record a question → transcribe it (step 2) → pass the text to a chat model (`llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$TESTO" -rea off`)
→ read the answer aloud with `llama-tts`. That is three processes and three models: measure the total latency and think about where
time goes (loading, encoding, generation, synthesis).

## Check the result

- [ ] The cli banner with Qwen3-ASR shows `audio` among the modalities and the transcription matches what you said.
- [ ] The API request with `input_audio` returns text and a `usage.prompt_tokens` larger than for the question alone.
- [ ] `llama-tts` produces a WAV that plays and has a duration consistent with the sentence.

## Questions and variations

1. Why does the server ignore `input_audio.format`? What happens if you send an OGG file?
2. With Gemma 4 E4B (if you have 8 GB) send **an image and audio in the same message**: how does it compose the answer?
3. How many tokens does a 10 s clip cost compared with a 30 s one? Is the ratio linear?
4. Try `--tts-lang en` on an Italian sentence and vice versa: what changes in the pronunciation?
5. Transcribe with `whisper.cpp` (a sibling project of ggml) and with Qwen3-ASR: compare accuracy and speed.

## Deliverable

`lab07-02.md` with: the transcription you got and the actual text (with errors highlighted), the `usage` of the API
request, the `llama-tts` command you used and the `ffprobe` output on the generated WAV, plus a line on the latency of the full round trip
if you did it.
