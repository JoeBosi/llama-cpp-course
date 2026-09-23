# Lab 10-01 · Un grafo ggml a mano

> Modulo: [10: Approfondimenti: dentro ggml e llama.cpp](../../moduli/10-approfondimenti/README.md) · <span class="stato stato-bozza">bozza · sorgenti confrontati con examples/simple di ggml e verificati contro gli header; compilazione ed esecuzione da verificare (non eseguite sul VPS del corso)</span> · Durata stimata: 60 minuti (+ compilazione di ggml)

## Obiettivo

Scrivere (anzi: leggere riga per riga, compilare ed eseguire) due programmi C che moltiplicano due matrici con
ggml. Il primo, `matmul.c`, usa l'API "a contesto" e gira solo su CPU; il secondo, `matmul-backend.c`, usa l'API
dei backend e lo scheduler, e gira sulla GPU se il binario ne ha una. Alla fine sai riconoscere in qualsiasi
sorgente di llama.cpp i quattro oggetti di ggml (contesto, tensore, grafo, backend) e sai perché il risultato di
`ggml_mul_mat` esce "trasposto".

## Prerequisiti

- Modulo 10, sezioni 1 e 2.
- Un compilatore C/C++ e CMake ≥ 3.14 (gli stessi del [lab 01-02](../lab-01-02-build-sorgenti-cpu/README.md));
  `git`. Per la parte GPU: il toolkit del tuo backend (CUDA, Vulkan SDK, Xcode su macOS).
- Nessun modello: qui si moltiplicano due matrici 4×2 e 3×2.

## Materiale

| Cosa | Fonte | Dimensione |
|---|---|---|
| Sorgenti di ggml | `git clone https://github.com/ggml-org/ggml` (licenza MIT) | ~40 MB con la storia git (`--depth 1` per ridurla) |
| [`matmul.c`](matmul.c) | questa cartella: traduzione in C di `examples/simple/simple-ctx.cpp` | |
| [`matmul-backend.c`](matmul-backend.c) | questa cartella: traduzione in C di `examples/simple/simple-backend.cpp` | |
| [`CMakeLists.txt`](CMakeLists.txt) | questa cartella: compila i due programmi contro `ggml/` come sottoprogetto | |

I due `.cpp` originali sono in [examples/simple](https://github.com/ggml-org/ggml/tree/master/examples/simple)
del repository ggml: tienili aperti accanto ai `.c` per il confronto (stessi dati, stesso risultato atteso).

## Procedura

1. **Prepara la cartella.** Copia i tre file del lab in una cartella di lavoro e clona ggml **dentro** di essa
    (il `CMakeLists.txt` si aspetta `./ggml`):

    ```bash
    mkdir -p ~/lab-ggml && cd ~/lab-ggml
    cp /percorso/del/corso/laboratori/lab-10-01-grafo-ggml/{matmul.c,matmul-backend.c,CMakeLists.txt} .
    git clone --depth 1 https://github.com/ggml-org/ggml
    ls
    ```
    ```
    CMakeLists.txt  ggml  matmul-backend.c  matmul.c
    ```

2. **Leggi `matmul.c`** prima di compilare. Sono cinque passi, gli stessi di `simple-ctx.cpp`:

    ```c
    #include "ggml.h"
    #include "ggml-cpu.h"   // (1)!

    const int righe_A = 4, colonne_A = 2;
    float dati_A[4 * 2] = { 2, 8,  5, 1,  4, 2,  8, 6 };      // (2)!
    const int righe_B = 3, colonne_B = 2;
    float dati_B[3 * 2] = { 10, 5,  9, 9,  5, 4 };            // (3)!

    size_t mem = 0;
    mem += righe_A * colonne_A * ggml_type_size(GGML_TYPE_F32);
    mem += righe_B * colonne_B * ggml_type_size(GGML_TYPE_F32);
    mem += 2 * ggml_tensor_overhead();                         // (4)!
    mem += ggml_graph_overhead();
    mem += 1024;
    struct ggml_init_params params = { mem, NULL, false };     // (5)!
    struct ggml_context * ctx = ggml_init(params);

    struct ggml_tensor * a = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_A, righe_A);   // (6)!
    struct ggml_tensor * b = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_B, righe_B);
    memcpy(a->data, dati_A, ggml_nbytes(a));                   // (7)!
    memcpy(b->data, dati_B, ggml_nbytes(b));

    struct ggml_cgraph * gf        = ggml_new_graph(ctx);
    struct ggml_tensor * risultato = ggml_mul_mat(ctx, a, b);  // (8)!
    ggml_build_forward_expand(gf, risultato);                  // (9)!

    ggml_graph_compute_with_ctx(ctx, gf, 2);                   // (10)!
    struct ggml_tensor * out = ggml_graph_node(gf, -1);        // (11)!
    ```

    1. `ggml.h` è l'API dei tensori e delle operazioni; `ggml-cpu.h` aggiunge `ggml_graph_compute_with_ctx`, che
       esiste solo per il backend CPU.
    2. `A` è 4 righe × 2 colonne, scritta riga per riga (ggml è *row-major*).
    3. `B` è data **già trasposta** (3×2): `ggml_mul_mat` calcola `A·Bᵀ`, quindi passandole `Bᵀ` otteniamo il classico `A·B` con `B` = `[[10, 9, 5], [5, 9, 4]]`.
    4. La stima della memoria: i byte dei dati, i metadati di 2 tensori, il grafo, un margine. Se sbagli per difetto, `ggml_new_tensor_2d` fallisce con un'asserzione.
    5. `mem_buffer = NULL` lascia allocare l'arena a ggml; `no_alloc = false` perché con l'API storica i tensori devono avere i dati nel contesto.
    6. **`ne[0]` = colonne, `ne[1]` = righe**: `a` ha `ne = [2, 4]`, `b` ha `ne = [2, 3]`. È l'ordine inverso di PyTorch.
    7. Con `no_alloc = false` il puntatore `a->data` è memoria valida: si copia direttamente.
    8. Nessun calcolo: `risultato` è un tensore con `op = GGML_OP_MUL_MAT`, `src[0] = a`, `src[1] = b`, `ne = [4, 3]`.
    9. Il grafo viene riempito partendo dal risultato e risalendo le dipendenze: 1 nodo (il `printf` successivo lo stampa).
    10. Esecuzione su CPU con 2 thread. Qui avviene la moltiplicazione.
    11. L'ultimo nodo del grafo è il risultato; con l'API storica `out->data` è leggibile direttamente.

3. **Leggi `matmul-backend.c`.** Stessi dati, stessa `ggml_mul_mat`, ma i dati non stanno più nel contesto:

    ```c
    #include "ggml-backend.h"                                   // (1)!

    ggml_backend_load_all();                                    // (2)!
    ggml_backend_t backend     = ggml_backend_init_best();      // (3)!
    ggml_backend_t backend_cpu = ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_CPU, NULL);
    ggml_backend_t backends[2] = { backend, backend_cpu };
    ggml_backend_sched_t sched = ggml_backend_sched_new(backends, NULL, 2, GGML_DEFAULT_GRAPH_SIZE, false, true);   // (4)!

    size_t mem = ggml_tensor_overhead() * GGML_DEFAULT_GRAPH_SIZE + ggml_graph_overhead();
    void * arena = malloc(mem);
    struct ggml_init_params params = { mem, arena, true };      // (5)!
    struct ggml_context * ctx = ggml_init(params);
    /* ... a, b, gf, risultato come prima ... */

    ggml_backend_sched_reset(sched);
    ggml_backend_sched_alloc_graph(sched, gf);                  // (6)!
    ggml_backend_tensor_set(a, dati_A, 0, ggml_nbytes(a));      // (7)!
    ggml_backend_tensor_set(b, dati_B, 0, ggml_nbytes(b));
    ggml_backend_sched_graph_compute(sched, gf);                // (8)!

    struct ggml_tensor * out = ggml_graph_node(gf, -1);
    ggml_backend_tensor_get(out, dati_out, 0, ggml_nbytes(out)); // (9)!

    ggml_backend_sched_free(sched);                             // (10)!
    ggml_backend_free(backend);
    ggml_backend_free(backend_cpu);
    ```

    1. Al posto di `ggml-cpu.h`: l'API dei backend è indipendente dal dispositivo.
    2. Carica dinamicamente le librerie dei backend trovate accanto all'eseguibile (`libggml-cuda.so`, `libggml-cpu-*.so`…) e le registra.
    3. Il "migliore" tra i backend registrati (GPU se c'è, altrimenti CPU). La CPU viene inizializzata comunque come riserva.
    4. Lo scheduler: lista di backend in ordine di priorità, nessun tipo di buffer forzato (`NULL`), 2 backend, dimensione massima del grafo, senza esecuzione parallela, con allocazione automatica.
    5. `no_alloc = true`: il contesto contiene solo i metadati; l'arena è piccola (solo overhead) e la forniamo noi con `malloc`.
    6. Lo scheduler assegna ogni nodo a un backend e alloca i buffer per **tutti** i tensori del grafo, `a` e `b` compresi, sul dispositivo del backend che li userà.
    7. I dati vanno copiati nel buffer del backend: se è una GPU, questa è una copia host→device. `memcpy` su `a->data` qui sarebbe un errore.
    8. Esecuzione: lo scheduler lancia gli split nell'ordine giusto.
    9. Copia device→host del risultato in un array nostro.
    10. Liberazione in ordine inverso: scheduler, poi backend.

4. **Compila su CPU.** Il `CMakeLists.txt` include `ggml/` con `add_subdirectory` e disattiva esempi e test di ggml:

    ```bash
    cmake -B build
    cmake --build build -j
    ```

    La prima compilazione di ggml richiede qualche minuto (kernel CPU per tutte le varianti SIMD). I binari
    finiscono in `build/` (o `build/bin/` a seconda della versione di CMake e del generatore; `find build -name matmul`).

5. **Esegui e confronta con l'atteso.** L'output atteso è quello scritto nei commenti di `simple-ctx.cpp`:

    ```bash
    ./build/matmul
    ```
    ```
    grafo: 1 nodi, risultato MUL_MAT con ne = [4, 3]
    mul_mat (4 x 3), risultato trasposto:
      60.00  55.00  50.00 110.00
      90.00  54.00  54.00 126.00
      42.00  29.00  28.00  64.00
    ```

    Verifica a mano un elemento: la riga 0 del risultato è `B[0]·A[i]` per i = 0..3: `10·2 + 5·8 = 60`,
    `10·5 + 5·1 = 55`, `10·4 + 5·2 = 50`, `10·8 + 5·6 = 110`. La matrice "vera" `A·B` (4×3) è la trasposta di
    ciò che vedi: ecco il senso di `Cᵀ = A·Bᵀ`.

    ```bash
    ./build/matmul-backend
    ```
    ```
    backend scelto: CPU
    mul_mat (4 x 3), risultato trasposto:
      60.00  55.00  50.00 110.00
      90.00  54.00  54.00 126.00
      42.00  29.00  28.00  64.00
    ```

6. **Ricompila con un backend GPU** (solo se ne hai una; la parte CPU non cambia):

    === "NVIDIA (CUDA)"
        ```bash
        cmake -B build-gpu -DGGML_CUDA=ON
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```
    === "AMD (HIP)"
        ```bash
        HIPCXX="$(hipconfig -l)/clang" cmake -B build-gpu -DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```
    === "Vulkan (qualsiasi GPU)"
        ```bash
        cmake -B build-gpu -DGGML_VULKAN=ON
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```
    === "macOS (Metal)"
        ```bash
        cmake -B build-gpu          # Metal è il default su macOS Apple Silicon
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```

    Atteso: la prima riga diventa `backend scelto: CUDA0` (o `Vulkan0`, `Metal`, `ROCm0`), i numeri sono
    identici. `matmul` invece stampa lo stesso di prima: usa `ggml_graph_compute_with_ctx`, che è CPU e basta.
    Sono le stesse opzioni CMake del [modulo 01](../../moduli/01-installazione/README.md): llama.cpp compila
    ggml esattamente così.

7. **Sperimenta.** Cambia `n_thread` in `matmul.c`; aggiungi un secondo nodo (`ggml_add(ctx, risultato, risultato)`
    prima di `ggml_build_forward_expand` e conta i nodi: diventano 2); passa a `GGML_TYPE_F16` per `a` (serve
    `ggml_fp32_to_fp16_row` per riempirla) e osserva che `ggml_mul_mat` accetta operandi di tipo diverso purché il
    secondo sia F32. Se aumenti il numero di tensori senza aggiornare la stima di `mem`, vedrai l'asserzione
    del contesto: è voluto.

## Verifica del risultato

- [ ] `./build/matmul` stampa `grafo: 1 nodi` e la matrice 3×4 con `60 55 50 110` nella prima riga.
- [ ] `./build/matmul-backend` stampa `backend scelto: CPU` e la stessa matrice.
- [ ] Con la build GPU, `matmul-backend` stampa il nome del backend GPU e gli stessi numeri.
- [ ] Sai spiegare perché il risultato ha `ne = [4, 3]` e non `[3, 4]`.

## Domande e varianti

1. Perché `matmul-backend.c` alloca l'arena con `ggml_tensor_overhead() * GGML_DEFAULT_GRAPH_SIZE` invece di
   `2 * ggml_tensor_overhead()`? (Suggerimento: guarda cosa fa `ggml_new_graph`.)
2. Cosa succederebbe passando un solo backend (`backend_cpu`) allo scheduler? E passando prima `backend_cpu`
   e poi `backend`?
3. Nel programma con i backend, in che momento esatto viene decisa la memoria in cui vivono `a` e `b`?
4. Variante: sostituisci `ggml_mul_mat` con `ggml_mul_mat(ctx, b, a)`: quali dimensioni ha il risultato e cosa rappresenta?
5. Variante (avanzata): apri `src/models/llama.cpp` in llama.cpp e trova le chiamate `ggml_mul_mat` con i pesi
   `wq`, `wk`, `wv`: riconosci la stessa convenzione `[n_embd, n_head*head_dim]`?

## Consegna

- L'output dei due programmi su CPU (e su GPU se disponibile), con il nome del backend scelto.
- Un `matmul.c` modificato con almeno un secondo nodo nel grafo e il nuovo output, più due righe di commento in
  italiano che spiegano la convenzione `Cᵀ = A·Bᵀ` con i tuoi numeri.
- Le risposte alle domande 1-3.
