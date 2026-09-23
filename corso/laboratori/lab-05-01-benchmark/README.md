# Lab 05-01 · Benchmark riproducibili

> Modulo: [05: Prestazioni e ottimizzazione](../../moduli/05-prestazioni/README.md) · <span class="stato stato-verificato">verificato su b11046 (CPU)</span> · Durata stimata: 45 minuti

## Obiettivo

Misurare prompt processing (pp) e token generation (tg) con `llama bench` al variare del numero di thread e della
quantizzazione, salvare i risultati in JSON e produrre un grafico con lo script `grafico_bench.py` di questa cartella.
Alla fine saprai dire, numeri alla mano, quanti thread usare sulla tua macchina e quanto ti costa (o ti rende) un Q4
rispetto a un Q8.

## Prerequisiti

- `llama` installato (modulo 01) e il modello del modulo 02 già in cache (`llama cli -cl`).
- Python 3 con matplotlib: `pip install matplotlib` (o `python3 -m pip install --user matplotlib`).
- Una macchina il più possibile **scarica**: chiudi browser, IDE e altri modelli in esecuzione.

## Materiale

| Cosa | Fonte | Dimensione |
|---|---|---|
| Modello Q8_0 | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (licenza Apache 2.0) | 795 MB |
| Modello Q4_0 dello stesso repository | `llama download -hf ggml-org/Qwen3.5-0.8B-GGUF:Q4_0` → `Qwen3.5-0.8B-Q4_0.gguf` | 537 MB |
| Script grafico | [`grafico_bench.py`](grafico_bench.py) in questa cartella | |

Nel seguito `$M8` e `$M4` sono i percorsi dei due file nella cache Hugging Face:

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt     # (1)!
M8=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
M4=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q4_0.gguf)
```

1. Serve solo con il binario dell'installer su alcune distribuzioni Linux (vedi modulo 01); non fa male altrove.

## Procedura

1. **Prima misura, formato tabella.** Un test corto per verificare che tutto funzioni:

    ```bash
    llama bench -m "$M8" -p 64 -n 32 -r 2
    ```

    Output atteso (VPS del corso, 6 vCPU AMD EPYC condivise):

    ```
    | model             |       size |   params | backend | threads | test |          t/s |
    | qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | pp64 | 56.90 ± 15.86 |
    | qwen35 0.8B Q8_0  | 784.52 MiB | 772.85 M | CPU     |       6 | tg32 |  4.29 ± 0.80 |
    ```

    Guarda il `±`: una deviazione del 30 % dice che la macchina non è tranquilla. Annota il numero di thread usato per
    default (colonna `threads`: è il numero di CPU viste dal sistema).

2. **Scansione dei thread, uscita JSON.** Prova 1, 2, 4 e tutti i core fisici (qui 6). `--progress` scrive
    l'avanzamento su stderr, così il JSON su stdout resta pulito:

    ```bash
    llama bench -m "$M8" -p 64 -n 32 -r 3 -t 1,2,4,6 --progress -o json > thread.json
    ```

    Su una macchina scarica ci vogliono 2-4 minuti. Se hai fretta o la macchina è condivisa, usa `-p 32 -n 16 -r 1`
    (è ciò che è stato fatto sul VPS del corso, un valore per volta):

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

3. **Guarda dentro il JSON.** Ogni elemento della lista è un test con tutte le condizioni:

    ```bash
    python3 -c "import json; r=json.load(open('thread.json')); print(r[0]['cpu_info'], r[0]['build_number']); \
    [print(x['n_threads'], x['n_prompt'], x['n_gen'], round(x['avg_ts'],2), x['samples_ts']) for x in r]"
    ```

    Campi che userai: `n_threads`, `n_prompt`/`n_gen` (uno dei due è 0 e dice se il test è pp o tg), `avg_ts`,
    `stddev_ts`, `samples_ts` (le singole ripetizioni).

4. **Il grafico.**

    ```bash
    python3 grafico_bench.py thread.json -o thread.png
    ```

    Output atteso:

    ```
    salvato thread.png
    pp64: t=1 → 9.55 t/s, t=2 → 10.21 t/s, t=4 → 12.23 t/s, t=6 → 4.00 t/s
    tg32: t=1 → 2.82 t/s, t=2 → 3.10 t/s, t=4 → 1.20 t/s, t=6 → 0.13 t/s
    ```

    Apri `thread.png`: due curve (pp e tg) con le barre di errore. Su una macchina scarica la curva sale fino ai
    core fisici e poi si appiattisce (tg) o continua un po' (pp). Sul VPS condiviso crolla oltre i 2 thread: la CPU
    è "oversaturata", esattamente il sintomo descritto nella guida ufficiale sulle prestazioni.

5. **Q8_0 contro Q4_0.** Con il numero di thread migliore trovato al passo 4 (qui `T=2`):

    ```bash
    llama bench -m "$M8" -m "$M4" -p 64 -n 32 -r 3 -t "$T" -o md
    ```

    Il modello Q4_0 pesa il 68 % del Q8_0: aspettati una tg proporzionalmente più alta (la generazione è limitata
    dalla banda di memoria) e un pp simile o un po' più basso (dipende dai kernel della tua CPU).

6. **Effetto del contesto pieno.** Ripeti tg con la KV cache riempita da 0 e da 1024 token:

    ```bash
    llama bench -m "$M8" -p 0 -n 32 -d 0,1024 -t "$T" -r 3
    ```

    Il test si chiama `tg32 @ d1024` nella tabella: con più contesto l'attention legge una cache più grande e tg cala.

7. **Il test "reale".** `-pg 128,64` misura prompt e generazione in sequenza, come in una chat:

    ```bash
    llama bench -m "$M8" -pg 128,64 -t "$T" -r 3
    ```

## Verifica del risultato

- [ ] `thread.json` esiste ed è una lista JSON con 8 elementi (4 valori di thread × 2 test).
- [ ] `thread.png` mostra due curve con etichette numeriche sui punti.
- [ ] Sai dire qual è il numero di thread "giusto" per la tua macchina e perché non è il massimo disponibile.
- [ ] Hai un numero per il rapporto tg(Q4_0)/tg(Q8_0) e sai spiegarlo con la banda di memoria.

## Domande e varianti

- Il rapporto di velocità tra Q4_0 e Q8_0 coincide con il rapporto delle dimensioni? Se no, cosa manca nel modello "banda / dimensione"?
- Ripeti il passo 2 con `--prio 2` (priorità alta) e con `--poll 0`: cambia qualcosa? Su un portatile a batteria, `--poll 0` riduce il consumo a riposo.
- Ripeti il passo 2 con `-t 1,2,4,6 -tb 6`: thread di prompt fissi a 6 e thread di generazione variabili. Cosa dice della differenza pp/tg?
- Salva anche `-o sql | sqlite3 misure.db` e aggiungi una misura al giorno per una settimana: la macchina è stabile?
- Se hai una GPU: `-ngl 0,all` nello stesso comando e confronta i due backend nella stessa tabella.

## Consegna

Una cartella con `thread.json`, `thread.png`, la tabella Markdown del passo 5 e un file `RELAZIONE.md` di 10-15 righe
con: modello e build (`llama version`), CPU (`cpu_info` dal JSON), numero di thread scelto, rapporto Q4/Q8 misurato,
e la deviazione standard più alta osservata con una frase su cosa la spiega.
