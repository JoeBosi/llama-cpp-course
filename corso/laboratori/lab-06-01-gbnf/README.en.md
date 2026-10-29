# Lab 06-01: Writing a grammar

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/06-output-strutturato/README.md">06: Structured output: GBNF grammars and JSON Schema</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes</span>
</div>

## Objective

Write a GBNF grammar from scratch for a format of your own, home automation commands such as `accendi luce cucina` /
`imposta termostato soggiorno 22`, and test it with `llama cli --grammar-file` and through the API with the `grammar` field.
Then turn it into the JSON version and see how the rules change. By the end you understand hands-on why
a grammar guarantees the form and not the meaning.

## Prerequisites

- Module 06 § 2 read (GBNF syntax table).
- `llama` installed, course model in cache; for the API part, a server as in lab 04-01.

## Materials

| What | Where | Size |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, Apache 2.0) | Hugging Face, via `-hf` | 785 MiB |
| [`domotica.gbnf`](domotica.gbnf): text commands, one per line | lab folder | 1 KB |
| [`domotica-json.gbnf`](domotica-json.gbnf): same vocabulary, output = JSON array of objects | lab folder | 1 KB |

## Steps

1. **Design the language** before the grammar. Two kinds of command:

    - `accendi|spegni <dispositivo> <stanza>` (turn on/off) with device ∈ {luce, presa, tapparella, ventola} and
      room ∈ {cucina, soggiorno, camera, bagno, ingresso};
    - `imposta termostato <stanza> <gradi>` (set thermostat) with degrees from 15 to 30.

    Multiple commands, one per line. The vocabulary is **closed**: that is what makes the grammar useful (a downstream
    program can do `split(" ")` without checks).

2. **Read `domotica.gbnf`** and match each line to a construct from § 2 of the module:

    ```
    root      ::= comando ("\n" comando)*             # (1)!
    comando   ::= onoff | termo
    onoff     ::= ("accendi" | "spegni") " " dispositivo " " stanza     # (2)!
    termo     ::= "imposta termostato " stanza " " gradi
    dispositivo ::= "luce" | "presa" | "tapparella" | "ventola"
    stanza      ::= "cucina" | "soggiorno" | "camera" | "bagno" | "ingresso"
    gradi       ::= "1" [5-9] | "2" [0-9] | "30"        # (3)!
    ```

    1. At least one command; the others separated by newlines. No trailing newline: the model ends with EOS.
    2. A group with alternation, then **literal** spaces: GBNF has no implicit spaces.
    3. A numeric range is written digit by digit: 15-19, 20-29, 30. There is no `[15-30]`.

3. **Test it from the CLI**. The small model needs help from a system prompt that explains the format (the grammar
   does not tell it):

    ```bash
    cd corso/laboratori/lab-06-01-gbnf
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 40 --temp 0 --grammar-file domotica.gbnf \
      -sys "Traduci la richiesta in comandi domotici, uno per riga, forma: 'accendi|spegni <luce|presa|tapparella|ventola> <cucina|soggiorno|camera|bagno|ingresso>' oppure 'imposta termostato <stanza> <gradi>'. Solo i comandi necessari." \
      -p "Sono in cucina, fa buio e ho freddo in soggiorno: voglio 22 gradi."
    ```

    Output:

    ```
    accendi ventola soggiorno
    spegni luce camera
    imposta termostato soggiorno 22
    [ Prompt: 29.4 t/s | Generation: 2.6 t/s ]
    ```

    Three lines, all syntactically perfect. But read them: "it's dark in the kitchen" became `accendi ventola
    soggiorno` (fan on in the living room) and `spegni luce camera` (bedroom light off; nobody asked for that); only the thermostat is right. The grammar did
    its job; the 0.8B model did not. **Form guaranteed, meaning not.** A 4B+ model gets this right almost every time.

4. **Without the grammar**, same system prompt, remove `--grammar-file`. Output (shortened):

    ````
    2. **Imposta termostato soggiorno 22**
       ```
       imposta termostato soggiorno
    ````

    Markdown, numbering, an unclosed code block: for a parser this is garbage. That is the use case for a grammar.

5. **Break it on purpose**. Open `domotica.gbnf` and split the `onoff` rule over two lines **without** parentheses:

    ```
    onoff     ::= ("accendi" | "spegni") " "
                  dispositivo " " stanza
    ```

    Run it again: `parse: error parsing grammar: expecting ::= at …`. Put parentheses around the whole right-hand
    side (or break the line after a `|`) and it works again: this is the most common syntax constraint to remember.

6. **JSON version**. Read `domotica-json.gbnf`: same vocabulary, but the output is
   `[{"azione":"accendi","dispositivo":"luce","stanza":"cucina"}, {"azione":"termostato","stanza":"camera","gradi":21}]`.
   Note what changes compared to the text version:

    - quotes must be **escaped** in terminals: `"\"azione\""`;
    - spaces are no longer literal but go through a rule `ws ::= [ \n]{0,4}`, **bounded** (with `[ \n]*` the
      grammar stays correct but sampling slows down: § 5 of the module);
    - long rules sit inside parentheses so they can span lines.

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 90 --temp 0 --grammar-file domotica-json.gbnf \
      -sys "Traduci la richiesta in comandi domotici … Rispondi con un array JSON di oggetti {azione, dispositivo, stanza} o {azione:'termostato', stanza, gradi}." \
      -p "Sono in cucina, fa buio e ho freddo in soggiorno: voglio 22 gradi."
    ```
    ```
    [{"azione": "termostato", "stanza": "soggiorno", "gradi": 22}]
    [ Prompt: 18.1 t/s | Generation: 6.5 t/s ]
    ```

    This time a single command, correct, but it forgot the light: a different result because the prompt and the form
    are different. With `--temp 0` the result is repeatable: run it again and you get the same.

7. **Through the API** (lab 04-01 server running): the grammar is a string in the `grammar` field, valid on
   `/v1/chat/completions` too. In Python:

    ```python
    import json, urllib.request
    g = open("domotica.gbnf", encoding="utf-8").read()
    body = {"messages": [{"role": "system", "content": "Traduci la richiesta in comandi domotici, uno per riga, …"},
                         {"role": "user", "content": "Sono in cucina, fa buio e ho freddo in soggiorno: voglio 22 gradi."}],
            "temperature": 0, "max_tokens": 40, "chat_template_kwargs": {"enable_thinking": False}, "grammar": g}
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req))
    print(d["choices"][0]["message"]["content"], d["choices"][0]["finish_reason"])
    ```

    Output: the same three lines as in step 3 and `finish_reason: stop` (same model, same prompt, temperature 0).
    With a broken grammar the server answers `400 {"error":{"message":"Failed to initialize samplers: failed to parse grammar",…}}`.

8. **A minimal constraint**: an inline grammar for a closed answer.

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -n 20 --temp 0 \
      --grammar 'root ::= ("sì" | "no")' -p "Bologna è in Italia? Rispondi sì o no."
    # → sì
    ```

    It is the cheapest way to get a classifier: the grammar lists the classes, the model picks
    one, your program has nothing to interpret.

## Check the result

- [ ] `domotica.gbnf` produces only lines in the expected format (check with `grep -vE '^(accendi|spegni) … $'`).
- [ ] You have seen the `expecting ::=` error and know how to avoid it.
- [ ] `domotica-json.gbnf` produces a JSON array that `python3 -m json.tool` accepts.
- [ ] The same grammar works through the API with the `grammar` field; a broken grammar returns 400.
- [ ] You can point to at least one command from the model that is *syntactically valid but wrong in meaning*.

## Questions and variations

- Add a third kind of command `tapparella <stanza> <0-100>%` (shutter opening percentage). How many rules do you need
  for 0-100? (tip: `[0-9] | [1-9] [0-9] | "100"`).
- Make the room optional in `onoff` (`" " stanza` becomes `(" " stanza)?`): does the model omit it more or less often?
- Change `ws ::= [ \n]{0,4}` to `[ \n]*` in the JSON version: does generation speed change? (measure `Generation: t/s`
  over 3 runs; with such a small model the difference may be within the noise).
- Write a grammar for a time `HH:MM` and ask "what time is half past noon?".
- With a larger model (`ggml-org/gemma-3-4b-it-qat-GGUF`, ~3 GB, if you have the RAM) repeat step 3: are the commands
  right in meaning too?
- The web UI has no field for a GBNF grammar, only `json_schema`: how would you get the equivalent of
  `domotica-json.gbnf` with a schema? (lab 06-02 and § 3 of the module: `enum` for device and room, `integer`
  with `minimum`/`maximum` for degrees).

## Deliverable

A file `lab-06-01.md` with: your extended grammar (variation 1) with one comment per rule; three runs
with different prompts and, for each, which commands are right in meaning too; the error from step 5 and the fix;
the JSON schema for the last variation.
