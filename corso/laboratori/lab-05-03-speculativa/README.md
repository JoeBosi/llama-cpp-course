# Lab 05-03 · Decodifica speculativa

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Modulo <a href="../../moduli/05-prestazioni/README.md">05: Prestazioni e ottimizzazione</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minuti</span>
<span class="stato stato-verificato">metodi n-gram verificati su b11046 (CPU)</span> <span class="stato stato-bozza">coppie target+bozza: dalla documentazione, da verificare su GPU</span>
</div>

## Obiettivo

Misurare quanto un modello **bozza** accelera un modello **target** su due tipi di testo (prosa e codice), capire da
cosa dipende il tasso di accettazione e provare la variante senza modello bozza (n-gram) e quella a testa MTP.

## Prerequisiti

- Modulo 05 letto (sezione "Decodifica speculativa") e lab 05-01 fatto.
- Per la parte principale: GPU con almeno 10 GB di VRAM (target da 7,7 GB + bozza), oppure pazienza su CPU con la coppia piccola.
- Per la variante MTP: 6 GB liberi (VRAM o RAM).

## Materiale

| Ruolo | Repository | File | Dimensione | Licenza |
|---|---|---|---|---|
| Target (codice) | `ggml-org/Qwen2.5-Coder-7B-Q8_0-GGUF` | `qwen2.5-coder-7b-q8_0.gguf` | 7,72 GB | Apache 2.0 |
| Bozza | `ggml-org/Qwen2.5-Coder-0.5B-Q8_0-GGUF` | `qwen2.5-coder-0.5b-q8_0.gguf` | 506 MB | Apache 2.0 |
| Target piccolo (CPU) | `ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF` | `qwen2.5-coder-1.5b-q8_0.gguf` | 1,57 GB | Apache 2.0 |
| Target con testa MTP | `ggml-org/gemma-4-e4b-it-GGUF:Q4_0` | `gemma-4-E4B-it-Q4_0.gguf` + `mtp-gemma-4-E4B-it-Q4_0.gguf` | 4,4 GB + 57 MB | Gemma |
| Metodi n-gram | qualsiasi modello, es. `ggml-org/Qwen3.5-0.8B-GGUF` | `Qwen3.5-0.8B-Q8_0.gguf` | 795 MB | Apache 2.0 |

La coppia Qwen2.5-Coder 7B + 0.5B è quella "ufficiale": `llama serve --fim-qwen-7b-spec` la scarica e la configura da solo.
Bozza e target devono avere lo **stesso vocabolario** (stessa famiglia e generazione): Qwen2.5 con Qwen2.5, Gemma con la
propria testa MTP. Una coppia sbagliata dà errore all'avvio o accettazione zero.

Prepara due prompt in file di testo:

```bash
cat > prosa.txt <<'EOF'
Scrivi un racconto di 300 parole su un faro abbandonato, con un finale a sorpresa.
EOF
cat > codice.txt <<'EOF'
Scrivi in Python una classe LRUCache con metodi get e put, complessità O(1), con docstring e un piccolo test.
EOF
```

## Procedura

1. **Riferimento senza bozza.** Genera 300 token per ciascun prompt e annota la riga finale
    `[ Prompt: … t/s | Generation: … t/s ]`. Usa un seed fisso e temperatura 0 per confrontare testi uguali:

    ```bash
    T=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen2.5-Coder-7B-Q8_0-GGUF/snapshots/*/qwen2.5-coder-7b-q8_0.gguf)
    D=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen2.5-Coder-0.5B-Q8_0-GGUF/snapshots/*/qwen2.5-coder-0.5b-q8_0.gguf)
    llama cli -m "$T" -ngl all -st -f prosa.txt  -n 300 --temp 0 -s 42
    llama cli -m "$T" -ngl all -st -f codice.txt -n 300 --temp 0 -s 42
    ```

2. **Con la bozza, `draft-simple`.** Stesso comando più `-md` e `--spec-type`:

    ```bash
    llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -ngld all -st -f prosa.txt  -n 300 --temp 0 -s 42
    llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -ngld all -st -f codice.txt -n 300 --temp 0 -s 42
    ```

    Attesa (documentazione e esperienza della comunità, da confermare sulla tua GPU): sul codice la generazione sale di
    1,5-2,5×, sulla prosa di 1,2-1,6×. Il testo prodotto a temperatura 0 deve essere **identico** a quello del passo 1.

3. **Quanti token proporre?** Ripeti il prompt di codice con `--spec-draft-n-max 2`, `4`, `8`, `16`:

    ```bash
    for k in 2 4 8 16; do
      echo "== n-max $k"
      llama cli -m "$T" -md "$D" --spec-type draft-simple -ngl all -st -f codice.txt -n 300 --temp 0 -s 42 2>/dev/null | tail -2
    done
    ```

    Un `k` troppo alto fa lavorare la bozza per niente (i token oltre il primo rifiuto vengono scartati); troppo basso
    lascia guadagno sul tavolo. Il default è 3. Segna il migliore.

4. **Temperatura alta.** Rilancia il passo 2 con `--temp 1.0`: l'accettazione cala perché il target "cambia idea" più
    spesso rispetto alla bozza. Quanto perdi?

5. **Sul server.** Gli stessi flag valgono per `llama serve`; il campo `timings` della risposta ti dà `predicted_per_second`
    senza dover leggere il terminale:

    ```bash
    llama serve -m "$T" -md "$D" --spec-type draft-simple -ngl all --port 18104
    curl -s localhost:18104/v1/chat/completions -H 'content-type: application/json' \
      -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$(cat codice.txt)\"}],\"max_tokens\":300,\"temperature\":0}" \
      | python3 -c "import json,sys; t=json.load(sys.stdin)['timings']; print(t['predicted_n'], 'token a', round(t['predicted_per_second'],1), 't/s')"
    ```

6. **Senza bozza: n-gram.** I metodi `ngram-*` propongono token già visti nel contesto: nessun secondo modello,
    utili quando l'output ripete l'input (riscritture, ripetizioni). Verificato sul VPS del corso con il modello
    da 0,8 miliardi:

    ```bash
    M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    llama cli -m "$M" -st -n 80 -t 3 -rea off --spec-type ngram-simple \
      -p "Scrivi la frase 'il gatto dorme sul divano' esattamente cinque volte, una per riga."
    ```

    Output atteso: le cinque righe e `[ Prompt: 11.2 t/s | Generation: 6.0 t/s ]` (valori del VPS condiviso). Ripeti
    senza `--spec-type` e confronta; poi prova un prompt senza ripetizioni e osserva che il guadagno sparisce.

7. **Variante MTP (Gemma 4).** La bozza è una piccola testa nello stesso repository, il tipo è `draft-mtp`:

    ```bash
    llama cli -hf ggml-org/gemma-4-e4b-it-GGUF:Q4_0 --hf-repo-draft ggml-org/gemma-4-e4b-it-GGUF:Q4_0 \
      --spec-type draft-mtp -st -f codice.txt -n 300 --temp 0
    ```

    `-hf` con `--hf-repo-draft` sullo stesso repository scarica il file `mtp-*.gguf` come bozza. Confronta con lo stesso
    comando senza le due opzioni speculative.

## Verifica del risultato

- [ ] Hai quattro numeri di tg: prosa e codice, con e senza bozza; il testo a temperatura 0 è identico nei due casi.
- [ ] Sai indicare il `--spec-draft-n-max` migliore per il tuo hardware e il tuo tipo di testo.
- [ ] Il test n-gram ha funzionato e sai spiegare quando aiuta.
- [ ] (Se fatta) la variante MTP parte e riporta una velocità maggiore del modello da solo.

## Domande e varianti

- Perché il guadagno è maggiore sul codice che sulla prosa? Pensa a quanto è "prevedibile" il token successivo.
- Prova la coppia piccola su CPU (target 1.5B, bozza 0.5B, `-t` = core fisici): il guadagno c'è ancora? Perché la banda di memoria è già satura anche con il target da solo?
- Metti la bozza su CPU e il target su GPU (`-devd none` oppure `-ngld 0`): a volte conviene quando la VRAM è quasi piena. Misura.
- `--spec-draft-p-min 0.5`: la bozza propone solo token di cui è abbastanza sicura. Cambia l'accettazione? E la velocità?
- Con `-lv 3` cerca nel log le statistiche dei token accettati e calcola il tasso di accettazione medio.

## Consegna

Una tabella con le righe {prosa, codice} × {senza bozza, draft-simple n-max 3, n-max migliore, n-gram, MTP se fatta} e
le colonne t/s di generazione e note; più un paragrafo su quale configurazione useresti per un assistente di codice e
quale per una chat generale, e perché.
