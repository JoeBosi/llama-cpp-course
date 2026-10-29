# Lab 05-01 · Reproducible benchmarks

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/05-prestazioni/README.md">05: Performance and optimization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Measure prompt processing (pp) and token generation (tg) with `llama bench` while varying the number of threads and the
quantization, save the results as JSON and produce a chart with the `grafico_bench.py` script in this folder.
By the end you can say, with numbers in hand, how many threads to use on your machine and how much a Q4 costs (or gains) you
compared with a Q8.

## Prerequisites

- `llama` installed (module 01) and the module 02 model already in cache (`llama cli -cl`).
- Python 3 with matplotlib: `pip install matplotlib` (or `python3 -m pip install --user matplotlib`).
- A machine as **idle** as possible: close the browser, IDE and other running models.

## Materials

| What | Source | Size |
|---|---|---|
| Q8_0 model | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0 license) | 795 MB |
| Q4_0 model from the same repository | `llama download -hf ggml-org/Qwen3.5-0.8B-GGUF:Q4_0` → `Qwen3.5-0.8B-Q4_0.gguf` | 537 MB |
| Chart script | [`grafico_bench.py`](grafico_bench.py) in this folder | |

Below, `$M8` and `$M4` are the paths of the two files in the Hugging Face cache:

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt     # (1)!
M8=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
M4=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q4_0.gguf)
```

1. Needed only with the installer binary on some Linux distributions (see module 01); it does no harm elsewhere.

## Steps

1. **First measurement, table format.** A short test to check that everything works:

    ```bash
    llama bench -m "$M8" -p 64 -n 32 -r 2
    ```

    Expected output (6 vCPU AMD EPYC machine, no GPU):

    ```
    | model             |       size |   params | backend | threads | test |          t/s |
    | qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | pp64 | 56.90 ± 15.86 |
    | qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | tg32 |  4.29 ± 0.80 |
    ```

    Look at the `±`: a 30 % deviation tells you the machine is not quiet. Note the number of threads used by
    default (column `threads`: it is the number of CPUs the system sees).

2. **Thread sweep, JSON output.** Try 1, 2, 4 and all physical cores (here 6). `--progress` writes
    progress to stderr, so the JSON on stdout stays clean:

    ```bash
    llama bench -m "$M8" -p 64 -n 32 -r 3 -t 1,2,4,6 --progress -o json > thread.json
    ```

    On an idle machine it takes 2-4 minutes. If you are in a hurry or the CPU is busy with other processes, use
    `-p 32 -n 16 -r 1`, one thread value at a time. Example on 6 vCPU with other processes running:

    ```
    | threads | test |   t/s |
    |       1 | pp32 |  9.55 |
    |       1 | tg16 |  2.82 |
    |       2 | pp32 | 10.21 |
    |       2 | tg16 |  3.10 |
    |       4 | pp32 | 12.23 |
    |       4 | tg16 |  1.20 |
    |       6 | pp32 |  4.00 |
    |       6 | tg16 |  0.13 |
    ```

3. **Look inside the JSON.** Each list item is a test with all its conditions:

    ```bash
    python3 -c "import json; r=json.load(open('thread.json')); print(r[0]['cpu_info'], r[0]['build_number']); \
    [print(x['n_threads'], x['n_prompt'], x['n_gen'], round(x['avg_ts'],2), x['samples_ts']) for x in r]"
    ```

    Fields you will use: `n_threads`, `n_prompt`/`n_gen` (one of the two is 0 and tells you whether the test is pp or tg), `avg_ts`,
    `stddev_ts`, `samples_ts` (the single repetitions).

4. **The chart.**

    ```bash
    python3 grafico_bench.py thread.json -o thread.png
    ```

    Expected output:

    ```
    salvato thread.png
    pp64: t=1 → 9.55 t/s, t=2 → 10.21 t/s, t=4 → 12.23 t/s, t=6 → 4.00 t/s
    tg32: t=1 → 2.82 t/s, t=2 → 3.10 t/s, t=4 → 1.20 t/s, t=6 → 0.13 t/s
    ```

    Open `thread.png`: two curves (pp and tg) with error bars. On an idle machine the curve rises up to the
    physical cores and then flattens (tg) or keeps rising a little (pp). On a CPU already busy with other processes it collapses beyond
    2 threads: the CPU is "oversaturated", exactly the symptom described in the official performance guide.

5. **Q8_0 against Q4_0.** With the best thread count found in step 4 (here `T=2`):

    ```bash
    llama bench -m "$M8" -m "$M4" -p 64 -n 32 -r 3 -t "$T" -o md
    ```

    The Q4_0 model weighs 68 % of the Q8_0: expect a proportionally higher tg (generation is limited
    by memory bandwidth) and a similar or slightly lower pp (it depends on your CPU's kernels).

6. **Effect of a full context.** Repeat tg with the KV cache filled with 0 and with 1024 tokens:

    ```bash
    llama bench -m "$M8" -p 0 -n 32 -d 0,1024 -t "$T" -r 3
    ```

    The test is called `tg32 @ d1024` in the table: with more context the attention reads a larger cache and tg drops.

7. **The "real" test.** `-pg 128,64` measures prompt and generation in sequence, as in a chat:

    ```bash
    llama bench -m "$M8" -pg 128,64 -t "$T" -r 3
    ```

## Check the result

- [ ] `thread.json` exists and is a JSON list with 8 items (4 thread values × 2 tests).
- [ ] `thread.png` shows two curves with numeric labels on the points.
- [ ] You can say which thread count is "right" for your machine and why it is not the maximum available.
- [ ] You have a number for the ratio tg(Q4_0)/tg(Q8_0) and can explain it with memory bandwidth.

## Questions and variants

- Does the speed ratio between Q4_0 and Q8_0 match the size ratio? If not, what is missing from the "bandwidth / size" model?
- Repeat step 2 with `--prio 2` (high priority) and with `--poll 0`: does anything change? On a laptop on battery, `--poll 0` reduces idle power use.
- Repeat step 2 with `-t 1,2,4,6 -tb 6`: prompt threads fixed at 6 and generation threads varying. What does it say about the pp/tg difference?
- Also save `-o sql | sqlite3 misure.db` and add one measurement per day for a week: is the machine stable?
- If you have a GPU: `-ngl 0,all` in the same command and compare the two backends in the same table.

## Deliverable

A folder with `thread.json`, `thread.png`, the Markdown table from step 5 and a 10-15 line `RELAZIONE.md` file
with: model and build (`llama version`), CPU (`cpu_info` from the JSON), chosen thread count, measured Q4/Q8 ratio,
and the highest standard deviation observed with a sentence on what explains it.
