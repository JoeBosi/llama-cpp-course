# Lab 05-03 · Speculative decoding

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/05-prestazioni/README.md">05: Performance and optimization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes</span>
</div>

## Objective

Measure how much a **draft** model speeds up a **target** model on two kinds of text (prose and code), understand what
the acceptance rate depends on, and try the variant without a draft model (n-gram) and the one with an MTP head.

## Prerequisites

- Module 05 read (section "Speculative decoding") and lab 05-01 done.
- For the main part: a GPU with at least 10 GB of VRAM (7.7 GB target + draft), or patience on CPU with the small pair.
- For the MTP variant: 6 GB free (VRAM or RAM).

## Materials

| Role | Repository | File | Size | License |
|---|---|---|---|---|
| Target (code) | `ggml-org/Qwen2.5-Coder-7B-Q8_0-GGUF` | `qwen2.5-coder-7b-q8_0.gguf` | 7.72 GB | Apache 2.0 |
| Draft | `ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF` | `qwen2.5-coder-0.5b-q8_0.gguf` | 506 MB | Apache 2.0 |
| Small target (CPU) | `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` | `qwen2.5-coder-1.5b-q8_0.gguf` | 1.57 GB | Apache 2.0 |
| Target with MTP head | `ggml-org/gemma-4-e4b-it-GGUF:Q4_0` | `gemma-4-E4B-it-Q4_0.gguf` + `mtp-gemma-4-E4B-it-Q4_0.gguf` | 4.4 GB + 57 MB | Gemma |
| n-gram methods | any model, e.g. `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf` | 795 MB | Apache 2.0 |

The Qwen2.5-Coder 7B + 0.5B pair is the "official" one: `llama serve --fim-qwen-7b-spec` downloads and configures it by itself.
Draft and target must have the **same vocabulary** (same family and generation): Qwen2.5 with Qwen2.5, Gemma with its
own MTP head. A wrong pair gives an error at startup or zero acceptance.

Prepare two prompts in text files:

```bash
cat > prosa.txt <<'EOF'
Scrivi un racconto di 300 parole su un faro abbandonato, con un finale a sorpresa.
EOF
cat > codice.txt <<'EOF'
Scrivi in Python una classe LRUCache con metodi get e put, complessità O(1), con docstring e un piccolo test.
EOF
```

## Steps

1. **Baseline without a draft.** Generate 300 tokens for each prompt and note the final line
    `[ Prompt: … t/s | Generation: … t/s ]`. Use a fixed seed and temperature 0 to compare identical texts:

    ```bash
    T=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen2.5-Coder-7B-Q8_0-GGUF/snapshots/*/qwen2.5-coder-7b-q8_0.gguf)
    D=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen2.5-Coder-0.5B-Q8_0-GGUF/snapshots/*/qwen2.5-coder-0.5b-q8_0.gguf)
    llama cli -m "$T" -ngl all -st -f prosa.txt  -n 300 --temp 0 -s 42
    llama cli -m "$T" -ngl all -st -f codice.txt -n 300 --temp 0 -s 42
    ```

2. **With the draft, `draft-simple`.** Same command plus `-md` and `--spec-type`:

    ```bash
    llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -ngld all -st -f prosa.txt  -n 300 --temp 0 -s 42
    llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -ngld all -st -f codice.txt -n 300 --temp 0 -s 42
    ```

    Indicative values on GPU: on code generation goes up 1.5-2.5×, on prose 1.2-1.6×; the exact ratio
    depends on your card. The text produced at temperature 0 must be **identical** to the one from step 1.

3. **How many tokens to propose?** Repeat the code prompt with `--spec-draft-n-max 2`, `4`, `8`, `16`:

    ```bash
    for k in 2 4 8 16; do
      echo "== n-max $k"
      llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -st -f codice.txt -n 300 --temp 0 -s 42 2>/dev/null | tail -2
    done
    ```

    A `k` that is too high makes the draft work for nothing (tokens after the first rejection are discarded); too low
    leaves gain on the table. The default is 3. Write down the best one.

4. **High temperature.** Run step 2 again with `--temp 1.0`: acceptance drops because the target "changes its mind" more
    often compared with the draft. How much do you lose?

5. **On the server.** The same flags work for `llama serve`; the `timings` field of the response gives you `predicted_per_second`
    without reading the terminal:

    ```bash
    llama serve -m "$T" -md "$D" --spec-type draft-simple -ngl all --port 18104
    curl -s localhost:18104/v1/chat/completions -H 'content-type: application/json' \
      -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$(cat codice.txt)\"}],\"max_tokens\":300,\"temperature\":0}" \
      | python3 -c "import json,sys; t=json.load(sys.stdin)['timings']; print(t['predicted_n'], 'token a', round(t['predicted_per_second'],1), 't/s')"
    ```

6. **Without a draft: n-gram.** The `ngram-*` methods propose tokens already seen in the context: no second model,
    useful when the output repeats the input (rewrites, repetitions). Example on CPU with the 0.8 billion model:

    ```bash
    M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    llama cli -m "$M" -st -n 80 -t 3 -rea off --spec-type ngram-simple \
      -p "Scrivi la frase 'il gatto dorme sul divano' esattamente cinque volte, una per riga."
    ```

    Expected output: the five lines and `[ Prompt: 11.2 t/s | Generation: 6.0 t/s ]` (on a 6 vCPU machine without GPU). Repeat
    without `--spec-type` and compare; then try a prompt without repetitions and observe that the gain disappears.

7. **MTP variant (Gemma 4).** The draft is a small head in the same repository, the type is `draft-mtp`:

    ```bash
    llama cli -hf ggml-org/gemma-4-e4b-it-GGUF:Q4_0 --hf-repo-draft ggml-org/gemma-4-e4b-it-GGUF:Q4_0 \
      --spec-type draft-mtp -st -f codice.txt -n 300 --temp 0
    ```

    `-hf` with `--hf-repo-draft` on the same repository downloads the `mtp-*.gguf` file as the draft. Compare with the same
    command without the two speculative options.

## Check the result

- [ ] You have four tg numbers: prose and code, with and without draft; the text at temperature 0 is identical in both cases.
- [ ] You can name the best `--spec-draft-n-max` for your hardware and your kind of text.
- [ ] The n-gram test worked and you can explain when it helps.
- [ ] (If done) the MTP variant starts and reports a higher speed than the model alone.

## Questions and variants

- Why is the gain larger on code than on prose? Think about how "predictable" the next token is.
- Try the small pair on CPU (1.5B target, 0.5B draft, `-t` = physical cores): is there still a gain? Why is memory bandwidth already saturated even with the target alone?
- Put the draft on CPU and the target on GPU (`-devd none` or `-ngld 0`): sometimes it pays off when VRAM is almost full. Measure it.
- `--spec-draft-p-min 0.5`: the draft proposes only tokens it is fairly sure of. Does acceptance change? And speed?
- With `-lv 3` look in the log for the accepted-token statistics and compute the average acceptance rate.

## Deliverable

A table with rows {prose, code} × {no draft, draft-simple n-max 3, best n-max, n-gram, MTP if done} and
columns for generation t/s and notes; plus a paragraph on which configuration you would use for a coding assistant and
which for a general chat, and why.
