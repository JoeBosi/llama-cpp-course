# Lab 05-02 · Hybrid CPU+GPU offload

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/05-prestazioni/README.md">05: Performance and optimization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes</span>
</div>

## Objective

Take a model **larger than the available VRAM**, find experimentally the `-ngl` value that gives the
fastest generation, and then win back VRAM with a quantized KV cache and (for a MoE) with the experts on CPU.
Finally you compare your choice with the automatic one from `llama fit-params`.

## Prerequisites

- A binary with a GPU backend (`llama cli --list-devices` must list at least one device: CUDA, Vulkan, Metal, HIP…).
- At least 16 GB of system RAM and 6-8 GB of VRAM (with more VRAM pick a larger model: the exercise makes sense only if the model does **not** fit entirely).
- Lab 05-01 completed (you can read the `llama bench` output).

## Materials

| What | Source | Size | Notes |
|---|---|---|---|
| Dense model | `ggml-org/gemma-3-12b-it-GGUF` → `gemma-3-12b-it-Q4_K_M.gguf` (Gemma license) | 6.96 GB | 48 layers; does not fit in 8 GB with context and buffers |
| MoE model (variant) | `ggml-org/Qwen3-30B-A3B-GGUF` → `Qwen3-30B-A3B-Q4_K_M.gguf` (Apache 2.0) | 17.7 GB | 30 billion parameters, 3 active per token: perfect for `-ncmoe` |
| Script | [`scan-ngl.sh`](scan-ngl.sh) in this folder | | runs `llama bench` over a list of `-ngl` values and prints a table |

```bash
llama download -hf ggml-org/gemma-3-12b-it-GGUF:Q4_K_M --no-mmproj
G=$(ls ~/.cache/huggingface/hub/models--ggml-org--gemma-3-12b-it-GGUF/snapshots/*/gemma-3-12b-it-Q4_K_M.gguf)
```

## Steps

1. **How many layers does the model have and how much does a layer weigh?** Start with info-level logging and look for `n_layer`:

    ```bash
    llama cli -m "$G" -st -p "ciao" -n 1 -lv 3 2>&1 | grep -E "n_layer|model size|offloaded"
    ```

    With 48 layers and 6.96 GB, each layer weighs ~140 MB on average (the embedding and the output weigh more). Also note the
    line `load_tensors: offloaded N/49 layers to GPU`: with `-ngl auto` (the default) the fit function picks N.

2. **What did the fit decide?** Before measuring, ask for the estimate:

    ```bash
    llama fit-params -m "$G" -c 8192
    ```

    It prints a line like `-c 8192 -ngl 37`: note it, it is the value to beat.

3. **`-ngl` sweep.** The script takes the model, the list of values and the context; it turns off the fit (`--fit off`
    does not exist in `llama bench`, which uses `-ngl` exactly as given) and uses `-fa on`:

    ```bash
    ./scan-ngl.sh "$G" "0,16,24,32,36,40,44,48" 8192
    ```

    Expected output (indicative values for an 8 GB GPU; yours will differ):

    ```
      ngl     test        t/s    ± dev
        0    pp512      45.10     0.80
        0    tg128       4.90     0.05
       16    pp512     120.30     1.10
       16    tg128       7.80     0.10
       …
       40    pp512     390.00     3.00
       40    tg128      19.50     0.30
       44    pp512   (errore: out of memory)
    ```

    The highest `-ngl` value that does **not** go out of memory is your candidate. If the large tests go OOM, the
    table stops: run again with a denser list around the last successful value (e.g. `"38,39,40,41,42"`).

4. **Win back VRAM with a quantized KV cache.** Repeat the values around the limit with `-ctk q8_0 -ctv q8_0`:

    ```bash
    llama bench -m "$G" -ngl 40,42,44,46,48 -p 512 -n 128 -r 3 -fa on -ctk q8_0 -ctv q8_0 --progress
    ```

    With 8192 tokens of context the f16 cache of Gemma 3 12B takes about 1.5 GB; q8_0 frees half of it, often
    enough for 2-4 more layers. If you reach `-ngl 48` (everything in VRAM) you see the tg "jump" described in the module.

5. **Comparison with the automatic choice.** Start the server with the best parameters you found and with the fit ones, and
    compare `predicted_per_second` in the `timings` field of a request (module 04):

    ```bash
    llama serve -m "$G" -ngl 44 -c 8192 -fa on -ctk q8_0 -ctv q8_0 --port 18104
    curl -s localhost:18104/v1/chat/completions -H 'content-type: application/json' \
      -d '{"messages":[{"role":"user","content":"Descrivi Roma in 200 parole."}],"max_tokens":200}' | python3 -c "import json,sys; print(json.load(sys.stdin)['timings'])"
    ```

    When the server closes (++ctrl+c++) read `llama_memory_breakdown_print`: for the GPU device you see `total`,
    `free`, `model`, `context`, `compute`. The `free` column tells you how much headroom you left.

6. **MoE variant.** With Qwen3-30B-A3B (17.7 GB) no `-ngl` value fits in 8 GB with all tensors. Try
    instead all layers in VRAM but the experts on CPU:

    ```bash
    Q=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3-30B-A3B-GGUF/snapshots/*/Qwen3-30B-A3B-Q4_K_M.gguf)
    llama fit-params -m "$Q" -c 8192                       # (1)!
    llama bench -m "$Q" -ngl 99 -ncmoe 48,40,32,24 -p 512 -n 128 -r 2 --progress
    ```

    1. It prints `-ngl 48 -ot blk\.NN\.ffn_(up|down|gate)_(ch|)exps=CPU,…`: this is the "explicit" form of `-ncmoe`.

    `-ncmoe N` keeps the experts of the first N layers on CPU: the lower N, the more experts sit in VRAM and the faster the
    generation, until memory runs out. Look for the minimum N that does not go OOM.

## Check the result

- [ ] You have a t/s vs `-ngl` table with at least 6 points and can name the maximum value that fits in VRAM.
- [ ] With the q8_0 KV cache you managed to raise `-ngl` by at least one layer (or you understood why not).
- [ ] The `-ngl` value you found is ≥ the one proposed by `llama fit-params` with a 1024 MiB margin (if it is much higher, the fit is leaving headroom: try `--fit-target 512`).
- [ ] For the MoE: you found the minimum `-ncmoe` and the corresponding tg.

## Questions and variants

- Why can tg double between `-ngl 44` and `-ngl 48` while between 0 and 16 it grows only 60 %?
- What happens to pp and tg if you keep `-ngl 48` but turn off KV cache offload with `-nkvo`? When does it make sense?
- Repeat the sweep with `-c 32768`: how much does the maximum allowed `-ngl` drop? First compute the KV cache size by hand (formula in the module).
- With two GPUs: `-ts 3,1` against the default proportional to memory; and `-sm tensor -fa on -ctk f16 -ctv f16` (CUDA only, dense model).
- Without a GPU you can still do steps 1, 2 and read `llama_memory_breakdown_print`: the `fit-params` output will be `-c <contesto del modello> -ngl -1`.

## Deliverable

The table from step 3 (or the `risultati.csv` CSV produced by the script), the `llama fit-params` line, the `timings`
from step 5 and a 10-line report: chosen `-ngl` value, with which KV cache options, how much VRAM headroom
you left and why.
