# Lab 02-03: Chat template e prompt di sistema

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/02-primi-passi/README.md">02: Primi passi: `llama cli`</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
<span class="stato stato-verificato">verificato su b11046</span>
</div>

## Obiettivo

Vedere con i tuoi occhi il testo che il chat template costruisce a partire dai messaggi, capire perché il
template sbagliato distrugge le risposte, e misurare quanto un prompt di sistema cambia il comportamento
dello stesso modello sullo stesso input.

## Prerequisiti

- Lab [02-01](../lab-02-01-primo-modello/README.md) completato; `curl` installato.
- Aver letto la sezione [8 del modulo](../../moduli/02-primi-passi/README.md#8-il-chat-template).
- Facoltativo: il pacchetto Python `gguf` del [lab 00-02](../lab-00-02-anatomia-gguf/README.md) per leggere il template dal file.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (`Q8_0`, Apache 2.0) | cache HF | 785 MiB |
| Tre prompt di sistema (li scrivi tu al punto 5) | file `sys-*.txt` | – |

## Procedura

1. **Il template così com'è nel GGUF**. Il modo più rapido è il log verbose, che ne mostra un esempio reso:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao" -n 1 -rea off -v 2>&1 | grep -A6 "example_format"
    ```

    Atteso: `init: chat template, example_format: '<|im_start|>system\n…<|im_end|>\n<|im_start|>user\n…<|im_start|>assistant\n…`.
    Il template completo (Jinja, 7 755 caratteri per Qwen3.5) è nella chiave `tokenizer.chat_template`; con il
    pacchetto `gguf` (`pip install gguf`, verificato):

    ```bash
    python3 - <<'EOF'
    import glob; from gguf import GGUFReader
    f = glob.glob("/root/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/*.gguf")[0]
    r = GGUFReader(f); fld = r.fields["tokenizer.chat_template"]
    t = bytes(fld.parts[fld.data[0]]).decode()
    print(len(t)); print(t[:1500])
    for k in ["<|im_start|>", "enable_thinking", "<think>", "tools"]: print(k, k in t)
    EOF
    ```

    Il template comincia con `{%- set image_count = namespace(value=0) %}` (conta le immagini nei messaggi) e
    contiene i rami `enable_thinking`, `<think>`, `tools`: sono i pezzi di programma che `-rea off`, `-sys` e il
    tool calling attivano.

2. **Il prompt reso, senza generare**. Avvia il server ([modulo 04](../../moduli/04-server-api/README.md)) su una
   porta libera e chiedi a `/apply-template` di trasformare dei messaggi:

    ```bash
    llama serve -hf ggml-org/Qwen3.5-0.8B-GGUF --port 8080 -c 2048 &
    sleep 15
    curl -s http://127.0.0.1:8080/apply-template -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"system","content":"Sei un assistente."},{"role":"user","content":"Ciao"}]}'; echo
    ```

    ```json
    {"prompt":"<|im_start|>system\nSei un assistente.<|im_end|>\n<|im_start|>user\nCiao<|im_end|>\n<|im_start|>assistant\n<think>\n"}
    ```

    Ripeti (a) **senza** il messaggio `system`, (b) con `"chat_template_kwargs": {"enable_thinking": false}` nel
    body, (c) con una conversazione di tre messaggi (`user`, `assistant`, `user`). Osserva: dove finisce il system
    prompt, come viene chiuso il blocco `<think>` quando il thinking è spento, come vengono incorniciati i turni
    passati. Ferma il server con `kill %1` (o ++ctrl+c++).

3. **Il template sbagliato**. Forza su Qwen3.5 il template di Llama 2 e poi quello di Gemma:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao, chi sei?" -n 40 -rea off --chat-template llama2
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Ciao, chi sei?" -n 40 -rea off --chat-template gemma
    ```

    Verificato con `llama2`: il modello risponde con un finto header di file sorgente («// llama2 // Copyright
    2016-2017 // All rights reserved…»): non riconoscendo `[INST]`, completa il testo come se fosse codice.
    Verificato con `gemma`: la risposta è la parola «gemma» ripetuta riga dopo riga fino a esaurire `-n`. Il
    modello ha visto `<start_of_turn>` senza conoscerlo e non trova mai l'EOS giusto: il **loop** è il sintomo
    classico del template sbagliato.

4. **Il template giusto, esplicito**. `--chat-template chatml` è il formato di Qwen, e infatti la risposta torna
   sensata, ma con una differenza (verificata): il template incorporato `chatml` non conosce `enable_thinking`,
   quindi `-rea off` non ha effetto e il modello apre `<think>` **dentro il testo** («<think>\nOkay, the user
   asked in Italian "Ciao, chi sei?"…»). Solo il template Jinja del GGUF sa spegnere il ragionamento. Poi prova
   `--chat-template-file` con una copia del template originale (punto 1) modificata, ad esempio cambiando il
   messaggio di sistema predefinito.

5. **Tre prompt di sistema, una domanda**. Scrivi tre file:

    ```text
    sys-neutro.txt   → Sei un assistente utile. Rispondi in italiano.
    sys-esperto.txt  → Sei un esperto di modelli linguistici. Rispondi in italiano, in una sola frase, con precisione tecnica.
    sys-bambini.txt  → Spiega le cose a un bambino di 8 anni, in italiano, con un esempio concreto, in due frasi.
    ```

    e lancia la stessa domanda con ciascuno:

    ```bash
    for s in neutro esperto bambini; do
      echo "== $s"; llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -rea off -n 80 --temp 0 -sysf sys-$s.txt -p "Cos'è un token?" 2>&1 | sed -n '/^> /,/Prompt:/p'
    done
    ```

    Verificato con il prompt "esperto": «Un token è una parte dell'input dell'LLM, che rappresenta una parte della
    sequenza dei caratteri.»; senza prompt di sistema lo stesso modello parla di token crittografici
    ([lab 02-01](../lab-02-01-primo-modello/README.md)). Con `--temp 0` il confronto è deterministico: l'unica
    variabile è il prompt di sistema.

6. **Quanto costa il prompt di sistema**. Ogni token del system prompt viene elaborato a ogni nuova conversazione
   (nel server: a ogni richiesta che non lo trova in cache). Misura con `/tokenize` del server o guardando
   `Prompt: N t/s` e il tempo: un prompt di sistema di 300 parole su CPU può costare diversi secondi al primo
   messaggio. Usa `/apply-template` e `/tokenize` per contare i token dei tre prompt.

## Verifica del risultato

- [ ] Hai visto il template Jinja (o il suo `example_format`) e riconosci i marcatori ChatML.
- [ ] `/apply-template` con e senza `enable_thinking:false` produce due prompt diversi e sai spiegare la differenza.
- [ ] Con `--chat-template llama2` il modello risponde in modo assurdo; con `chatml` torna sensato.
- [ ] Hai tre risposte diverse alla stessa domanda, una per prompt di sistema, ottenute a `--temp 0`.
- [ ] Sai quanti token costa ciascun prompt di sistema.

## Domande e varianti

- Perché Gemma 3 non ha un vero ruolo `system`? Guarda il template di `ggml-org/gemma-3-1b-it-GGUF` con lo stesso
  metodo del punto 1 e trova dove finisce il testo del system prompt.
- Cosa succede se in `/apply-template` metti due messaggi `user` consecutivi? Alcuni template lo rifiutano.
- Variante: un template personalizzato che aggiunge la data odierna al system prompt (`--chat-template-file`),
  passando il valore con `--chat-template-kwargs '{"oggi":"2026-09-23"}'` e usandolo nel Jinja come `{{ oggi }}`.
- Variante: `--no-jinja` con il template incorporato: quali differenze noti nel prompt reso?

## Consegna

`lab-02-03.md` con: i quattro prompt resi da `/apply-template` (punto 2) commentati; la risposta con il template
`llama2` e quella con `chatml`; le tre risposte del punto 5 e il conteggio dei token dei tre prompt di sistema; una
frase su quale prompt di sistema useresti per un assistente di supporto tecnico e perché.
