# Lab 02-02: Sampling experiments

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/02-primi-passi/README.md">02: First steps: `llama cli`</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Isolate the effect of each sampling parameter: same model, same prompt, same seed, only one
flag changed at a time. At the end you have a table of real answers that shows what temperature,
top-k, top-p, min-p and repeat penalty do, and a personal rule about which values to use for which tasks.

## Prerequisites

- Lab [02-01](../lab-02-01-primo-modello/README.md) completed (model in the cache).
- You have read [section 4 of the module](../../moduli/02-primi-passi/README.md#4-sampling-from-248320-logits-to-one-token) and the diagram of the sampling chain.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (`Q8_0`, Apache 2.0) | HF cache | 785 MiB |
| [`campiona.sh`](campiona.sh) | in this folder | bash script that runs the tests and writes `risultati.md` |

## Steps

1. **The protocol**. Every test uses `-st -p "Scrivi una frase su un gatto." -n 25 -rea off -s 1` ("Write a sentence about a cat.") and changes only the
   sampling flags. The fixed seed makes the comparison fair: if you change a parameter and the
   answer changes, it is the parameter. First check that the protocol is reproducible:

    ```bash
    for i in 1 2; do llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Inventa un nome per un gatto." -n 12 -rea off -s 42 --temp 1.0 -t 4 2>&1 | sed -n '/^> /,/Prompt:/p'; done
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Inventa un nome per un gatto." -n 12 -rea off -s 7 --temp 1.0 -t 4 2>&1 | sed -n '/^> /,/Prompt:/p'
    ```

    The first two runs (`-s 42`) give the same answer word for word («Certamente! Ecco
    alcune idee per un nome gatto con»), the third (`-s 7`) is different («Ecco un elenco di nomi per un gatto divisi»).

2. **Greedy in three ways**. Run the cat sentence with `--temp 0`, then again with `--temp 0`, then with
   `--top-k 1 --temp 1.0`:

    ```bash
    P="Scrivi una frase su un gatto."
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 --temp 0
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 --top-k 1 --temp 1.0
    ```

    The three answers are identical («Il gatto è un animale di compagnia che si sente sempre più come un
    amico, un compagno di vita e un compagno di»). Temperature 0 and top-k 1 are two roads to the same place: the
    most probable token, always.

3. **Temperature without a safety net**. Turn off all filters and raise the temperature:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 -s 1 --temp 1.8 --top-k 0 --top-p 1 --min-p 0
    ```

    Result: «Ukra bedaní震災 Hen.uuid Nin:on şəbilidad bra aba Hollowoi Sever spalle diesen—…». With the
    distribution flattened and no filter, the tail of 248,000 improbable tokens becomes reachable.

4. **min-p as a net**. Same temperature, turn only min-p back on:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 -s 1 --temp 1.8 --top-k 0 --top-p 1 --min-p 0.1
    ```

    Result: «Il gatto è un vero e proprio animale spirituale: il sole che passa sotto i suoi occhi si sente
    un'altra». A single relative filter (it discards whatever has less than 10 % of the probability of the best token)
    is enough to make even an extreme temperature usable: this is why min-p is today the preferred
    filter. Note that in the default order min-p is applied **before** the temperature, so it filters on the
    "cold" distribution and then lets the temperature shuffle the survivors.

5. **Repeat penalty**. A task with words that repeat by nature:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Elenca 5 sinonimi di 'bello'." -n 40 -rea off -t 4 --temp 0 --repeat-penalty 1.3
    ```

    Result: «Ecco i cinque sinonIMI più comuni…»: with 1.3 the penalty also hits the tokens of *sinonimi* (synonyms)
    already seen in the prompt, and the model invents a spelling. Repeat with `1.1` and with the default `1.0` and compare.

6. **All the tests at once**. The script runs eight combinations and produces a Markdown table:

    ```bash
    bash campiona.sh                    # or: bash campiona.sh "-m /percorso/modello.gguf"
    cat risultati.md
    ```

    Edit the `PROVE` array to add your own (for example `--top-p 0.5`, `--min-p 0.3`, `--dry-multiplier 0.8`,
    `--mirostat 2`). Each test takes a few seconds with `-n 25`.

7. **A serious task**. Repeat with a data extraction prompt, for example
   `-p "Estrai la città dalla frase: 'Domani parto per Bologna in treno.' Rispondi solo con il nome."` at
   `--temp 0` and at `--temp 1.2`, ten times each (change the seed). Count how many times the answer is exactly
   «Bologna». This is the measure that counts when the model works inside a program.

## Check

- [ ] Two runs with the same seed give the same text; with different seeds they do not.
- [ ] `--temp 0` and `--top-k 1` produce the same answer.
- [ ] You saw high temperature without filters produce nonsense and min-p bring it back in line.
- [ ] `risultati.md` contains at least eight rows with answer and tokens/s.
- [ ] For the task in step 7, you can say which temperature is better and why.

## Questions and variations

- Why is the value of `-s` irrelevant with `--temp 0`? And with `--top-k 1`?
- In step 4 you used `--top-k 0 --top-p 1`: what would have happened with the defaults 40 and 0.95?
  Try it: does the answer change?
- `--samplers "temperature;min_p"` reverses the order (temperature first, min-p after). Repeat step 4: min-p
  now filters on the already flattened distribution. What changes?
- Variation: `--dry-multiplier 0.8` on a prompt that invites repetition («Scrivi una filastrocca con il ritornello…», "Write a nursery rhyme with the refrain…").
- Variation: the same experiments from the server with `temperature`, `top_p`, `min_p`, `seed` in the body of
  `/v1/chat/completions` ([module 04](../../moduli/04-server-api/README.md)).

## Deliverable

`risultati.md` produced by the script (with at least two tests added by you), plus a paragraph with: the answer to the
first question, the count from step 7 for the two temperatures, and your rule of thumb "for data extraction I use …,
for creative writing I use …".
