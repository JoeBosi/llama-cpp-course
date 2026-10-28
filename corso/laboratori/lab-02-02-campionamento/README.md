# Lab 02-02: Esperimenti di campionamento

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/02-primi-passi/README.md">02: Primi passi: `llama cli`</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minuti</span>
</div>

## Obiettivo

Isolare l'effetto di ogni parametro di campionamento: stesso modello, stesso prompt, stesso seed, un solo
flag cambiato per volta. Alla fine avrai una tabella di risposte reali che mostra cosa fanno temperatura,
top-k, top-p, min-p e repeat penalty, e una regola personale su quali valori usare per quali compiti.

## Prerequisiti

- Lab [02-01](../lab-02-01-primo-modello/README.md) completato (modello in cache).
- Aver letto la sezione [4 del modulo](../../moduli/02-primi-passi/README.md#4-il-campionamento-da-248-320-logit-a-un-token) e lo schema della catena di campionamento.

## Materiale

| Cosa | Dove | Dimensione |
|---|---|---|
| `ggml-org/Qwen3.5-0.8B-GGUF` (`Q8_0`, Apache 2.0) | cache HF | 785 MiB |
| [`campiona.sh`](campiona.sh) | in questa cartella | script bash che esegue le prove e scrive `risultati.md` |

## Procedura

1. **Il protocollo**. Ogni prova usa `-st -p "Scrivi una frase su un gatto." -n 25 -rea off -s 1` e cambia solo i
   flag di campionamento. Il seed fisso serve a rendere il confronto onesto: se cambi un parametro e la
   risposta cambia, è il parametro. Prima verifica che il protocollo sia riproducibile:

    ```bash
    for i in 1 2; do llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Inventa un nome per un gatto." -n 12 -rea off -s 42 --temp 1.0 -t 4 2>&1 | sed -n '/^> /,/Prompt:/p'; done
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Inventa un nome per un gatto." -n 12 -rea off -s 7 --temp 1.0 -t 4 2>&1 | sed -n '/^> /,/Prompt:/p'
    ```

    Le prime due esecuzioni (`-s 42`) danno la stessa risposta parola per parola («Certamente! Ecco
    alcune idee per un nome gatto con»), la terza (`-s 7`) è diversa («Ecco un elenco di nomi per un gatto divisi»).

2. **Greedy in tre modi**. Esegui la frase sul gatto con `--temp 0`, poi ancora con `--temp 0`, poi con
   `--top-k 1 --temp 1.0`:

    ```bash
    P="Scrivi una frase su un gatto."
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 --temp 0
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 --top-k 1 --temp 1.0
    ```

    Le tre risposte sono identiche («Il gatto è un animale di compagnia che si sente sempre più come un
    amico, un compagno di vita e un compagno di»). Temperatura 0 e top-k 1 sono due strade per lo stesso posto: il
    token più probabile, sempre.

3. **La temperatura senza rete di protezione**. Spegni tutti i filtri e alza la temperatura:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 -s 1 --temp 1.8 --top-k 0 --top-p 1 --min-p 0
    ```

    Risultato: «Ukra bedaní震災 Hen.uuid Nin:on şəbilidad bra aba Hollowoi Sever spalle diesen—…». Con la
    distribuzione appiattita e nessun filtro, la coda dei 248 000 token improbabili diventa raggiungibile.

4. **min-p come rete**. Stessa temperatura, riaccendi solo min-p:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "$P" -n 25 -rea off -t 4 -s 1 --temp 1.8 --top-k 0 --top-p 1 --min-p 0.1
    ```

    Risultato: «Il gatto è un vero e proprio animale spirituale: il sole che passa sotto i suoi occhi si sente
    un'altra». Un solo filtro relativo (scarta ciò che ha meno del 10 % della probabilità del token migliore)
    basta a rendere utilizzabile anche una temperatura estrema: è il motivo per cui min-p è oggi il filtro
    preferito. Nota che nell'ordine di default min-p si applica **prima** della temperatura, quindi filtra sulla
    distribuzione "fredda" e poi lascia che la temperatura mescoli i sopravvissuti.

5. **Repeat penalty**. Un compito con parole ripetute per natura:

    ```bash
    llama cli -hf ggml-org/Qwen3.5-0.8B-GGUF -st -p "Elenca 5 sinonimi di 'bello'." -n 40 -rea off -t 4 --temp 0 --repeat-penalty 1.3
    ```

    Risultato: «Ecco i cinque sinonIMI più comuni…»: con 1.3 la penalità colpisce anche i token di *sinonimi*
    già visti nel prompt e il modello inventa una grafia. Ripeti con `1.1` e con il default `1.0` e confronta.

6. **Tutte le prove in una volta**. Lo script esegue otto combinazioni e produce una tabella Markdown:

    ```bash
    bash campiona.sh                    # oppure: bash campiona.sh "-m /percorso/modello.gguf"
    cat risultati.md
    ```

    Modifica l'array `PROVE` per aggiungere le tue (ad esempio `--top-p 0.5`, `--min-p 0.3`, `--dry-multiplier 0.8`,
    `--mirostat 2`). Ogni prova dura pochi secondi con `-n 25`.

7. **Un compito serio**. Ripeti con un prompt di estrazione dati, ad esempio
   `-p "Estrai la città dalla frase: 'Domani parto per Bologna in treno.' Rispondi solo con il nome."` a
   `--temp 0` e a `--temp 1.2`, dieci volte ciascuno (cambia il seed). Conta quante volte la risposta è esattamente
   «Bologna». È la misura che conta quando il modello lavora dentro un programma.

## Verifica del risultato

- [ ] Due esecuzioni con lo stesso seed danno lo stesso testo; con seed diversi no.
- [ ] `--temp 0` e `--top-k 1` producono la stessa risposta.
- [ ] Hai visto la temperatura alta senza filtri produrre testo senza senso e min-p rimetterlo in riga.
- [ ] `risultati.md` contiene almeno otto righe con risposta e token/s.
- [ ] Sai dire per il compito del punto 7 quale temperatura conviene e perché.

## Domande e varianti

- Perché con `--temp 0` il valore di `-s` è irrilevante? E con `--top-k 1`?
- Nel punto 4 abbiamo usato `--top-k 0 --top-p 1`: cosa sarebbe successo lasciando i default 40 e 0.95?
  Prova: la risposta cambia?
- `--samplers "temperature;min_p"` inverte l'ordine (temperatura prima, min-p dopo). Ripeti il punto 4: min-p
  ora filtra sulla distribuzione già appiattita. Cosa cambia?
- Variante: `--dry-multiplier 0.8` su un prompt che invita alla ripetizione («Scrivi una filastrocca con il ritornello…»).
- Variante: gli stessi esperimenti dal server con `temperature`, `top_p`, `min_p`, `seed` nel body di
  `/v1/chat/completions` ([modulo 04](../../moduli/04-server-api/README.md)).

## Consegna

`risultati.md` prodotto dallo script (con almeno due prove aggiunte da te), più un paragrafo con: la risposta alla
prima domanda, il conteggio del punto 7 per le due temperature, e la tua regola pratica «per estrazione dati uso …,
per scrittura creativa uso …».
