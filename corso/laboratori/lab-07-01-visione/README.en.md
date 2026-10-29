# Lab 07-01: Describing and querying images

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/07-multimodale/README.md">07: Multimodality: vision, audio, voice</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 min</span>
</div>

## Objective

Make a model "see" an image with llama.cpp in three ways: from the command line (`--image`), in chat (`/image`) and
through the API (`image_url` with a base64 data URI). Then use the same mechanism to read a document (receipt, form)
and compare a tiny model with a laptop-sized one.

## Prerequisites

- `llama` installed (module 01) and module 04 for the server and `curl`.
- `ffmpeg` (to generate the test image; alternatively any PNG/JPEG of your own).
- 2 GB of free RAM for part A; 8 GB for part B (optional).

## Materials

| What | Source | Size | License |
|---|---|---|---|
| `ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0` | Hugging Face | 175 MB + `mmproj` 104 MB | Apache 2.0 |
| `ggml-org/gemma-3-4b-it-GGUF` (part B) | Hugging Face | 2.5 GB (Q4_K_M) + `mmproj` 851 MB | Gemma Terms |
| [`chiedi_immagine.sh`](chiedi_immagine.sh) | this folder | bash script: base64 → `/v1/chat/completions` | |

## Steps

### 1. A test image

A "synthetic" image has the advantage that you already know the right answer. With `ffmpeg`:

```bash
mkdir -p ~/lab07 && cd ~/lab07
ffmpeg -loglevel error -y -f lavfi \
  -i "color=c=white:s=320x240:d=1,drawbox=x=40:y=40:w=120:h=120:color=red@1:t=fill,drawbox=x=200:y=60:w=80:h=140:color=blue@1:t=fill" \
  -frames:v 1 forme.png
```

You get `forme.png` (1.7 KB): white background, a red square on the left and a blue rectangle on the right.

### 2. A one-shot question from the command line

```bash
llama cli -hf ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0 --image forme.png -p "Describe this image." -st -n 60
```

On first run it downloads the model **and** the `mmproj` (280 MB in total). Output on a 6 vCPU machine without a GPU (`-t 3`):

```text
modalities : text, vision, video
…
Loaded media from 'forme.png'

> Describe this image.
 The image features two rectangular shapes: a red rectangle and a blue rectangle. Both rectangles have a
 distinct and classic rectangular form. …

[ Prompt: 5.1 t/s | Generation: 5.6 t/s ]
```

Check the `modalities` line: if it says only `text`, the projector was not loaded.

### 3. In chat: media first, then the question

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

Attached media applies to the next message; for a new question on the same image, attach it again (each
attachment costs its context tokens again). `/exit` to quit.

### 4. Through the API with base64

Start the server (any port) and wait for `/health`:

```bash
llama serve -hf ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0 --port 8080 -c 4096
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}
curl -s http://127.0.0.1:8080/models | python3 -m json.tool | grep -A2 capabilities
```

The native `/models` endpoint lists `"capabilities": ["completion", "multimodal"]`: this is how a client finds out whether it can
send images. Now the script:

```bash
./chiedi_immagine.sh forme.png "Describe this image." http://127.0.0.1:8080
```

The script encodes the file (`base64 -w0`), builds the `text` + `image_url` content parts with
`data:image/png;base64,…`, calls `/v1/chat/completions` and prints the answer and `usage`. The server log shows
`srv load_model: loaded multimodal model, '…/mmproj-SmolVLM-256M-Instruct-Q8_0.gguf'`.

With the `openai` SDK (module 04) the body is identical:

```python
import base64, openai
client = openai.OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="no-key")
uri = "data:image/png;base64," + base64.b64encode(open("forme.png", "rb").read()).decode()
r = client.chat.completions.create(model="x", messages=[{"role": "user", "content": [
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": uri}}]}], max_tokens=80)
print(r.choices[0].message.content, r.usage.prompt_tokens)
```

### 5. What an image costs

Ask the same question **without** the image and compare `usage.prompt_tokens`:

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Describe this image."}],"max_tokens":5}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["usage"])'
```

Result: **146 tokens** with the image, **12** without → the 320×240 image is worth ~134 tokens for SmolVLM. Try a
large photo and watch how it changes (and how long prompt processing takes on CPU: 150 tokens at ~4-13 t/s).

### 6. (Part B, with 8 GB) Reading a document

Stop the server (++ctrl+c++) and restart it with Gemma 3 4B, which reads text in images much better:

```bash
llama serve -hf ggml-org/gemma-3-4b-it-GGUF --port 8080 -c 8192
./chiedi_immagine.sh scontrino.jpg "Elenca le voci e il totale in formato JSON." http://127.0.0.1:8080
```

Take a photo of a receipt or a form (or use a sample invoice image). For guaranteed JSON, pair it with
`response_format` and a schema (module 06). On GPU add `-ngl all`; with little VRAM, `--no-mmproj-offload`.

## Check the result

- [ ] The cli banner shows `modalities : text, vision, video` with SmolVLM.
- [ ] The cli description names two shapes and the colors red and blue.
- [ ] `/models` reports the `multimodal` capability and the script prints an answer with `prompt` > 100 tokens.
- [ ] You measured the token difference with and without the image.

## Questions and variations

1. Why does the 256M model describe the image well in chat but answer only "Blue" through the API with `temperature: 0`?
   Try varying the temperature and the wording of the question.
2. Send **two** images in the same message (`--image a.png,b.png` or two content parts) and ask for the differences.
3. Start with `--no-mmproj` and repeat the script: what error do you get?
4. Resize a photo to 512 px per side and compare tokens and time with the original.
5. Web UI variation: open `http://127.0.0.1:8080/`, drag `forme.png` into the chat, then a PDF.

## Deliverable

A file `lab07-01.md` with: the cli output (step 2), the script's answer and `usage` (step 4), the table of
tokens with/without the image (step 5) and, if you did part B, the JSON extracted from the document with a note on what
the model got wrong.
