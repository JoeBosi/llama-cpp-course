# Lab 06-01: Scrivere una grammatica

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/06-output-strutturato/README.md">06: Output strutturato: grammatiche GBNF e JSON Schema</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minuti</span>
<span class="stato stato-verificato">verificato su b11046</span>
</div>

## Obiettivo

Scrivere da zero una grammatica GBNF per un formato tuo, comandi domotici del tipo `accendi luce cucina` /
`imposta termostato soggiorno 22`, e provarla con `llama cli --grammar-file` e via API con il campo `grammar`.
Poi trasformarla nella versione JSON e vedere come cambiano le regole. Alla fine hai capito con le mani perché
la grammatica garantisce la forma e non il senso.

## Prerequisiti

- Modulo 06 § 2 letto (tabella della sintassi GBNF).
- `llama` installato, modello del corso in cache; per la parte API un server come nel lab 04-01.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (file `Qwen3.5-0.8B-Q8_0.gguf`, Apache 2.0) | Hugging Face, via `-hf` | 785 MiB |
| [`domotica.gbnf`](domotica.gbnf): comandi testuali, uno per riga | cartella del lab | 1 KB |
| [`domotica-json.gbnf`](domotica-json.gbnf): stesso vocabolario, output = array JSON di oggetti | cartella del lab | 1 KB |

## Procedura

1. **Progetta il linguaggio** prima della grammatica. Due tipi di comando:

    - `accendi|spegni <dispositivo> <stanza>` con dispositivo ∈ {luce, presa, tapparella, ventola} e
      stanza ∈ {cucina, soggiorno, camera, bagno, ingresso};
    - `imposta termostato <stanza> <gradi>` con gradi da 15 a 30.

    Più comandi, uno per riga. Il vocabolario è **chiuso**: è questo che rende la grammatica utile (un programma
    a valle può fare `split(" ")` senza controlli).

2. **Leggi `domotica.gbnf`** e associa ogni riga a un costrutto del § 2 del modulo:

    ```
    root      ::= comando ("\n" comando)*             # (1)!
    comando   ::= onoff | termo
    onoff     ::= ("accendi" | "spegni") " " dispositivo " " stanza     # (2)!
    termo     ::= "imposta termostato " stanza " " gradi
    dispositivo ::= "luce" | "presa" | "tapparella" | "ventola"
    stanza      ::= "cucina" | "soggiorno" | "camera" | "bagno" | "ingresso"
    gradi       ::= "1" [5-9] | "2" [0-9] | "30"        # (3)!
    ```

    1. Almeno un comando; gli altri separati da newline. Nessun newline finale: il modello chiude con EOS.
    2. Gruppo con alternanza, poi spazi **letterali**: GBNF non ha spazi impliciti.
    3. Un intervallo numerico si scrive per cifre: 15-19, 20-29, 30. Non esiste `[15-30]`.

3. **Provala dal CLI**. Il modello piccolo va aiutato con un prompt di sistema che spiega il formato (la grammatica
   non glielo dice):

    ```bash
    cd corso/laboratori/lab-06-01-gbnf
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 40 --temp 0 --grammar-file domotica.gbnf \
      -sys "Traduci la richiesta in comandi domotici, uno per riga, forma: 'accendi|spegni <luce|presa|tapparella|ventola> <cucina|soggiorno|camera|bagno|ingresso>' oppure 'imposta termostato <stanza> <gradi>'. Solo i comandi necessari." \
      -p "Sono in cucina, fa buio e ho freddo in soggiorno: voglio 22 gradi."
    ```

    Output reale:

    ```
    accendi ventola soggiorno
    spegni luce camera
    imposta termostato soggiorno 22
    [ Prompt: 29.4 t/s | Generation: 2.6 t/s ]
    ```

    Tre righe, tutte sintatticamente perfette. Ma leggile: "fa buio in cucina" è diventato `accendi ventola
    soggiorno` e `spegni luce camera` (nessuno l'ha chiesto); solo il termostato è giusto. La grammatica ha fatto
    il suo lavoro; il modello da 0,8B no. **Forma garantita, senso no.** Un modello da 4B+ qui ci prende quasi sempre.

4. **Senza grammatica**, stesso prompt di sistema, togli `--grammar-file`. Output reale (accorciato):

    ````
    2. **Imposta termostato soggiorno 22**
       ```
       imposta termostato soggiorno
    ````

    Markdown, numerazione, un blocco di codice aperto: per un parser è spazzatura. Ecco il caso d'uso della grammatica.

5. **Rompila apposta**. Apri `domotica.gbnf`, spezza la regola `onoff` su due righe **senza** parentesi:

    ```
    onoff     ::= ("accendi" | "spegni") " "
                  dispositivo " " stanza
    ```

    Rilancia: `parse: error parsing grammar: expecting ::= at …`. Rimetti le parentesi attorno all'intera parte
    destra (o l'a-capo dopo un `|`) e torna a funzionare: è il vincolo di sintassi più frequente da ricordare.

6. **Versione JSON**. Leggi `domotica-json.gbnf`: stesso vocabolario, ma l'output è
   `[{"azione":"accendi","dispositivo":"luce","stanza":"cucina"}, {"azione":"termostato","stanza":"camera","gradi":21}]`.
   Nota cosa cambia rispetto alla versione testuale:

    - le virgolette vanno **escapate** nei terminali: `"\"azione\""`;
    - gli spazi non sono più letterali ma passano da una regola `ws ::= [ \n]{0,4}`, **limitata** (con `[ \n]*` la
      grammatica resta corretta ma il campionamento rallenta: § 5 del modulo);
    - le regole lunghe stanno fra parentesi per poter andare a capo.

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -t 4 -n 90 --temp 0 --grammar-file domotica-json.gbnf \
      -sys "Traduci la richiesta in comandi domotici … Rispondi con un array JSON di oggetti {azione, dispositivo, stanza} o {azione:'termostato', stanza, gradi}." \
      -p "Sono in cucina, fa buio e ho freddo in soggiorno: voglio 22 gradi."
    ```
    ```
    [{"azione": "termostato", "stanza": "soggiorno", "gradi": 22}]
    [ Prompt: 18.1 t/s | Generation: 6.5 t/s ]
    ```

    Stavolta un solo comando, corretto, e ha dimenticato la luce: risultato diverso perché il prompt e la forma
    sono diversi. Con `--temp 0` il risultato è ripetibile: rilancia e ottieni lo stesso.

7. **Via API** (server del lab 04-01 attivo): la grammatica è una stringa nel campo `grammar`, valido anche su
   `/v1/chat/completions`. In Python:

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

    Output reale: le stesse tre righe del punto 3 e `finish_reason: stop` (stesso modello, stesso prompt, temperatura 0).
    Con una grammatica errata il server risponde `400 {"error":{"message":"Failed to initialize samplers: failed to parse grammar",…}}`.

8. **Un vincolo minimo**: una grammatica inline per una risposta chiusa.

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -n 20 --temp 0 \
      --grammar 'root ::= ("sì" | "no")' -p "Bologna è in Italia? Rispondi sì o no."
    # → sì
    ```

    È il modo più economico per ottenere un classificatore: la grammatica elenca le classi, il modello ne
    sceglie una, il tuo programma non deve interpretare nulla.

## Verifica del risultato

- [ ] `domotica.gbnf` produce solo righe nel formato previsto (controlla con `grep -vE '^(accendi|spegni) … $'`).
- [ ] Hai visto l'errore `expecting ::=` e sai come evitarlo.
- [ ] `domotica-json.gbnf` produce un array JSON che `python3 -m json.tool` accetta.
- [ ] La stessa grammatica funziona via API con il campo `grammar`; una grammatica rotta dà 400.
- [ ] Sai indicare almeno un comando *sintatticamente valido ma sbagliato nel senso* uscito dal modello.

## Domande e varianti

- Aggiungi un terzo tipo di comando `tapparella <stanza> <0-100>%` (percentuale di apertura). Quante regole servono
  per 0-100? (suggerimento: `[0-9] | [1-9] [0-9] | "100"`).
- Rendi opzionale la stanza in `onoff` (`" " stanza` diventa `(" " stanza)?`): il modello la omette più spesso o meno?
- Cambia `ws ::= [ \n]{0,4}` in `[ \n]*` nella versione JSON: la generazione cambia velocità? (misura `Generation: t/s`
  su 3 esecuzioni; con un modello così piccolo la differenza può essere nel rumore).
- Scrivi una grammatica per un orario `HH:MM` e chiedi "a che ora è mezzogiorno e mezza?".
- Con un modello più grande (`ggml-org/gemma-3-4b-it-qat-GGUF`, ~3 GB, se hai la RAM) ripeti il punto 3: i comandi
  sono giusti anche nel senso?
- Nella web UI non c'è un campo per la grammatica GBNF, solo `json_schema`: come otterresti l'equivalente di
  `domotica-json.gbnf` con uno schema? (lab 06-02 e § 3 del modulo: `enum` per dispositivo e stanza, `integer`
  con `minimum`/`maximum` per i gradi).

## Consegna

Un file `lab-06-01.md` con: la tua grammatica estesa (variante 1) con un commento per regola; tre esecuzioni
con prompt diversi e, per ognuna, quali comandi sono giusti anche nel senso; l'errore del punto 5 e la correzione;
lo schema JSON dell'ultima variante.
