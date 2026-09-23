# Da Hugging Face a GGUF

> Modulo: [03: Modelli, GGUF e quantizzazione](../../moduli/03-modelli-gguf-quantizzazione/README.md) · <span class="stato stato-bozza">bozza · procedura dalla documentazione ufficiale, non eseguita sul VPS del corso (richiede torch)</span> · Durata stimata: 60 minuti (di cui 20 di download e installazione)

## Obiettivo

Prendere un modello pubblicato in `safetensors`, convertirlo in GGUF F16 con `convert_hf_to_gguf.py`, controllare
che il file sia completo (metadati, tokenizer, chat template), farlo girare con `llama cli` e quantizzarlo in
`Q8_0` e `Q4_K_M`. Alla fine avrai fatto a mano ciò che `ggml-org` e `bartowski` fanno per ogni modello che esce.

## Prerequisiti

- `llama` installato ([modulo 01](../../moduli/01-installazione/README.md)); `git`, `python3` ≥ 3.10 con `venv`.
- ~3 GB di disco (sorgenti + torch CPU ≈ 2 GB, modello ≈ 0,5 GB) e connessione internet.
- Aver letto la sezione [4 del modulo](../../moduli/03-modelli-gguf-quantizzazione/README.md#4-la-pipeline-da-hugging-face-a-un-gguf-quantizzato).

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `HuggingFaceTB/SmolLM2-135M-Instruct` (Apache 2.0, architettura Llama): `config.json`, `model.safetensors`, `tokenizer.json` | Hugging Face | ~270 MB (BF16) |
| Sorgenti di llama.cpp (solo per gli script Python, **non** li compiliamo) | `git clone` | ~250 MB |
| Alternativa senza installare nulla: lo space [GGUF-my-repo](https://huggingface.co/spaces/ggml-org/gguf-my-repo) | browser | – |

Il modello è piccolo apposta: la conversione dura meno di un minuto e il F16 pesa ~270 MB. Il procedimento è
identico per un 8 B (solo con 16 GB di F16 da scrivere su disco).

## Procedura

1. **Sorgenti e ambiente Python**:

    ```bash
    git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/llama.cpp
    cd ~/llama.cpp
    python3 -m venv .venv && source .venv/bin/activate
    python3 -m pip install -r requirements.txt        # torch CPU, transformers, gguf, safetensors…
    python3 convert_hf_to_gguf.py --help | head -40
    ```

    Atteso nell'help: `--outtype {f32,f16,bf16,q8_0,tq1_0,tq2_0,auto}`, `--outfile`, `--remote`, `--mmproj`,
    `--vocab-only`, `--print-supported-models`. Prova anche `python3 convert_hf_to_gguf.py --print-supported-models | grep -i llama`.

2. **Scarica il modello** (o usa `--remote` al punto 3):

    ```bash
    pip install -U "huggingface_hub[cli]"
    hf download HuggingFaceTB/SmolLM2-135M-Instruct --local-dir ~/modelli/smollm2-135m
    ls -la ~/modelli/smollm2-135m
    ```

    Atteso: `config.json`, `generation_config.json`, `model.safetensors` (~270 MB), `tokenizer.json`,
    `tokenizer_config.json` (contiene `chat_template`). Apri `config.json`: `"architectures": ["LlamaForCausalLM"]`,
    `hidden_size 576`, `num_hidden_layers 30`, `torch_dtype bfloat16`.

3. **Converti in F16**:

    ```bash
    python3 convert_hf_to_gguf.py ~/modelli/smollm2-135m --outtype f16 --outfile ~/modelli/smollm2-135m-f16.gguf
    ```

    Atteso nel log: il riconoscimento dell'architettura (`Model architecture: LlamaForCausalLM`), una riga per
    tensore (`token_embd.weight, torch.bfloat16 --> F16, shape = {576, 49152}`, `blk.0.attn_q.weight …`), il
    tokenizer (`gguf: … chat_template`) e alla fine `Model successfully exported to …`. Dimensione ≈ 270 MB.
    Variante senza download: `python3 convert_hf_to_gguf.py --remote HuggingFaceTB/SmolLM2-135M-Instruct --outtype f16 --outfile ~/modelli/smollm2-135m-f16.gguf`.

4. **Ispeziona il GGUF** con gli strumenti del [lab 00-02](../lab-00-02-anatomia-gguf/README.md):

    ```bash
    pip install gguf
    gguf-dump ~/modelli/smollm2-135m-f16.gguf | head -60
    ```

    Controlla: `general.architecture = llama`, `llama.block_count = 30`, `tokenizer.ggml.tokens` con 49 152 voci,
    `tokenizer.chat_template` presente, `general.file_type = 1` (F16), e nell'indice tensori tipi `F16` per i pesi
    e `F32` per le norm.

5. **Eseguilo**:

    ```bash
    llama cli -m ~/modelli/smollm2-135m-f16.gguf -st -p "Ciao! Presentati in una frase." -n 40 -t 4
    ```

    Atteso: banner con `ftype : F16`, una risposta sensata (è un modello da 135 M: sarà breve e in inglese o in un
    italiano approssimativo) e la riga dei tempi. Se il modello risponde a vanvera o non si ferma, il sospetto
    numero uno è il chat template: `llama cli -v … | grep example_format`.

6. **Quantizza** in due tipi e confronta le dimensioni:

    ```bash
    llama quantize ~/modelli/smollm2-135m-f16.gguf ~/modelli/smollm2-135m-Q8_0.gguf Q8_0
    llama quantize ~/modelli/smollm2-135m-f16.gguf ~/modelli/smollm2-135m-Q4_K_M.gguf Q4_K_M
    ls -la ~/modelli/smollm2-135m-*.gguf
    ```

    Atteso: `Q8_0` ≈ 145 MB, `Q4_K_M` ≈ 100 MB (l'embedding da 49 152 × 576 resta a `q6_K` e il vocabolario pesa
    molto su un modello così piccolo: il rapporto non sarà 16:4). Le due righe finali `model size` / `quant size`
    danno i bpw.

7. **Perplexity dei tre file** sullo stesso testo, per vedere quanto costa la quantizzazione su un modello minuscolo:

    ```bash
    for q in f16 Q8_0 Q4_K_M; do llama perplexity -m ~/modelli/smollm2-135m-$q.gguf -f ../lab-03-02-scala-quantizzazioni/testo-it.txt -c 128 -t 4 2>&1 | grep Final; done
    ```

    Atteso: F16 ≈ Q8_0 < Q4_K_M, con uno scarto in proporzione più grande di quello che vedrai sul modello da
    0,8 B nel lab 03-02: più il modello è piccolo, più ogni bit conta.

## Verifica del risultato

- [ ] `convert_hf_to_gguf.py` ha prodotto un file con `general.architecture = llama` e il chat template.
- [ ] `llama cli -m` lo carica e risponde; il banner dice `F16`.
- [ ] Hai tre file (F16, Q8_0, Q4_K_M) e sai spiegare perché il Q4_K_M non è un quarto del F16.
- [ ] Hai tre perplexity in ordine crescente.

## Domande e varianti

- Perché la documentazione consiglia `--outtype auto` (o `bf16`) invece di `f16` per i modelli addestrati in BF16? (Pensa
  all'intervallo di valori rappresentabili.)
- Cosa contiene `tokenizer_config.json` che finisce nel GGUF? E `generation_config.json`, che invece **non** ci finisce?
- Variante: converti un modello con `--vocab-only` e guarda quanto pesa: è un GGUF con solo il tokenizer.
- Variante Docker: `docker run -v ~/modelli:/models ghcr.io/ggml-org/llama.cpp:full --all-in-one /models/ …` come
  da `docs/docker.md`, oppure entra nell'immagine (`--entrypoint bash`) e usa `python3 /app/convert_hf_to_gguf.py`.
- Variante nel browser: carica lo stesso repo in GGUF-my-repo, scegli `Q4_K_M`, e confronta il file prodotto con il tuo
  (`gguf-dump`: stessa build? stesso tipo per l'embedding?).
- Per chi ha un modello multimodale (Gemma 3 4B, Qwen3.5-VL): aggiungi il passaggio `--mmproj --outtype q8_0` e prova
  `llama cli -m … --mmproj … --image foto.jpg`.

## Consegna

`lab-03-01.md` con: le prime 20 righe del log di conversione; l'output di `gguf-dump` filtrato sulle chiavi
`general.*`, `llama.block_count`, `tokenizer.chat_template` (solo l'inizio); la risposta di `llama cli`; la tabella
file → dimensione → bpw → perplexity; le risposte alle prime due domande.
