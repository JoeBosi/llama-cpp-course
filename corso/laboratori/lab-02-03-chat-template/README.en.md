# Lab 02-03: Chat template and system prompt

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/02-primi-passi/README.md">02: First steps: `llama cli`</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

See with your own eyes the text that the chat template builds from the messages, understand why the
wrong template destroys the answers, and measure how much a system prompt changes the behavior
of the same model on the same input.

## Prerequisites

- Lab [02-01](../lab-02-01-primo-modello/README.md) completed; `curl` installed.
- You have read [section 8 of the module](../../moduli/02-primi-passi/README.md#8-the-chat-template).
- Optional: the `gguf` Python package from [lab 00-02](../lab-00-02-anatomia-gguf/README.md) to read the template from the file.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (`Q8_0`, Apache 2.0) | HF cache | 785 MiB |
| Three system prompts (you write them in step 5) | `sys-*.txt` files | – |

## Steps

1. **The template as it is in the GGUF**. The quickest way is the verbose log, which shows a rendered example:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao" -n 1 -rea off -v 2>&1 | grep -A6 "example_format"
    ```

    Expected: `init: chat template, example_format: '<|im_start|>system\n…<|im_end|>\n<|im_start|>user\n…<|im_start|>assistant\n…`.
    The full template (Jinja, 7,755 characters for Qwen3.5) is in the `tokenizer.chat_template` key; with the
    `gguf` package (`pip install gguf`):

    ```bash
    python3 - <<'EOF'
    import glob, os; from gguf import GGUFReader
    f = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/*.gguf"))[0]
    r = GGUFReader(f); fld = r.fields["tokenizer.chat_template"]
    t = bytes(fld.parts[fld.data[0]]).decode()
    print(len(t)); print(t[:1500])
    for k in ["<|im_start|>", "enable_thinking", "<think>", "tools"]: print(k, k in t)
    EOF
    ```

    The template starts with `{%- set image_count = namespace(value=0) %}` (it counts the images in the messages) and
    contains the `enable_thinking`, `<think>`, `tools` branches: they are the pieces of program that `-rea off`, `-sys` and
    tool calling activate.

2. **The rendered prompt, without generating**. Start the server ([module 04](../../moduli/04-server-api/README.md)) on a
   free port and ask `/apply-template` to transform some messages:

    ```bash
    llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF --port 8080 -c 2048 &
    sleep 15
    curl -s http://127.0.0.1:8080/apply-template -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"system","content":"Sei un assistente."},{"role":"user","content":"Ciao"}]}'; echo
    ```

    ```json
    {"prompt":"<|im_start|>system\nSei un assistente.<|im_end|>\n<|im_start|>user\nCiao<|im_end|>\n<|im_start|>assistant\n<think>\n"}
    ```

    Repeat (a) **without** the `system` message, (b) with `"chat_template_kwargs": {"enable_thinking": false}` in the
    body, (c) with a three-message conversation (`user`, `assistant`, `user`). Observe: where the system
    prompt ends up, how the `<think>` block is closed when thinking is off, how past turns are
    framed. Stop the server with `kill %1` (or ++ctrl+c++).

3. **The wrong template**. Force the Llama 2 template on Qwen3.5, then the Gemma one:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao, chi sei?" -n 40 -rea off --chat-template llama2
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao, chi sei?" -n 40 -rea off --chat-template gemma
    ```

    With `llama2` the model answers with a fake source file header («// llama2 // Copyright
    2016-2017 // All rights reserved…»): since it does not recognize `[INST]`, it completes the text as if it were code.
    With `gemma` the answer is the word «gemma» repeated line after line until `-n` runs out. The
    model saw `<start_of_turn>` without knowing it and never finds the right EOS: the **loop** is the classic
    symptom of the wrong template.

4. **The right template, explicit**. `--chat-template chatml` is Qwen's format, and indeed the answer becomes
   sensible again, but with one difference: the built-in `chatml` template does not know `enable_thinking`,
   so `-rea off` has no effect and the model opens `<think>` **inside the text** («<think>\nOkay, the user
   asked in Italian "Ciao, chi sei?"…»). Only the GGUF's Jinja template can turn reasoning off. Then try
   `--chat-template-file` with a modified copy of the original template (step 1), for example changing the
   default system message.

5. **Three system prompts, one question**. Write three files:

    ```text
    sys-neutro.txt   → Sei un assistente utile. Rispondi in italiano.
    sys-esperto.txt  → Sei un esperto di modelli linguistici. Rispondi in italiano, in una sola frase, con precisione tecnica.
    sys-bambini.txt  → Spiega le cose a un bambino di 8 anni, in italiano, con un esempio concreto, in due frasi.
    ```

    and run the same question with each one:

    ```bash
    for s in neutro esperto bambini; do
      echo "== $s"; llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -n 80 --temp 0 -sysf sys-$s.txt -p "Cos'è un token?" 2>&1 | sed -n '/^> /,/Prompt:/p'
    done
    ```

    With the "expert" prompt the answer is: «Un token è una parte dell'input dell'LLM, che rappresenta una parte della
    sequenza dei caratteri.»; without a system prompt the same model talks about cryptographic tokens
    ([lab 02-01](../lab-02-01-primo-modello/README.md)). With `--temp 0` the comparison is deterministic: the only
    variable is the system prompt.

6. **What the system prompt costs**. Every token of the system prompt is processed at every new conversation
   (in the server: at every request that does not find it in the cache). Measure with the server's `/tokenize` or by looking at
   `Prompt: N t/s` and the time: a 300-word system prompt on CPU can cost several seconds on the first
   message. Use `/apply-template` and `/tokenize` to count the tokens of the three prompts.

## Check

- [ ] You saw the Jinja template (or its `example_format`) and you recognize the ChatML markers.
- [ ] `/apply-template` with and without `enable_thinking:false` produces two different prompts and you can explain the difference.
- [ ] With `--chat-template llama2` the model answers absurdly; with `chatml` it becomes sensible again.
- [ ] You have three different answers to the same question, one per system prompt, obtained at `--temp 0`.
- [ ] You know how many tokens each system prompt costs.

## Questions and variations

- Why does Gemma 3 not have a real `system` role? Look at the template of `ggml-org/gemma-3-1b-it-GGUF` with the same
  method as step 1 and find where the system prompt text ends up.
- What happens if you put two consecutive `user` messages in `/apply-template`? Some templates reject it.
- Variation: a custom template that adds today's date to the system prompt (`--chat-template-file`),
  passing the value with `--chat-template-kwargs '{"oggi":"2026-09-23"}'` and using it in the Jinja as `{{ oggi }}`.
- Variation: `--no-jinja` with the built-in template: what differences do you notice in the rendered prompt?

## Deliverable

`lab-02-03.md` with: the four prompts rendered by `/apply-template` (step 2), commented; the answer with the
`llama2` template and the one with `chatml`; the three answers from step 5 and the token count of the three system prompts; a
sentence on which system prompt you would use for a technical support assistant and why.
