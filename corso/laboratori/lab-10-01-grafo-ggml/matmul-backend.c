// matmul-backend.c: la stessa moltiplicazione, ma con l'API dei backend e lo scheduler.
//
// Ricalca examples/simple/simple-backend.cpp del repository ggml, in C puro.
// Differenze rispetto a matmul.c:
//   - il contesto e' creato con no_alloc = true: descrive solo i tensori, non ha i dati;
//   - i buffer vengono allocati dallo scheduler (ggml_backend_sched_alloc_graph) sul backend migliore
//     disponibile (CUDA, Metal, Vulkan... oppure CPU se non c'e' altro);
//   - i dati entrano ed escono con ggml_backend_tensor_set / ggml_backend_tensor_get.

#include "ggml.h"
#include "ggml-backend.h"

#include <stdio.h>
#include <stdlib.h>

static void log_su_stderr(enum ggml_log_level livello, const char * testo, void * dati) {
    (void) livello; (void) dati;
    fputs(testo, stderr);
}

int main(void) {
    ggml_time_init();
    ggml_log_set(log_su_stderr, NULL);

    const int righe_A = 4, colonne_A = 2;
    float dati_A[4 * 2] = { 2, 8,  5, 1,  4, 2,  8, 6 };
    const int righe_B = 3, colonne_B = 2;
    float dati_B[3 * 2] = { 10, 5,  9, 9,  5, 4 };

    // 1. Backend: carica le librerie dei backend (libggml-cuda.so, libggml-cpu-*.so, ...) e sceglie il migliore.
    ggml_backend_load_all();
    ggml_backend_t backend     = ggml_backend_init_best();
    ggml_backend_t backend_cpu = ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_CPU, NULL);
    printf("backend scelto: %s\n", ggml_backend_name(backend));

    // 2. Scheduler con due backend: il migliore e la CPU come riserva per le op non supportate.
    ggml_backend_t backends[2] = { backend, backend_cpu };
    ggml_backend_sched_t sched = ggml_backend_sched_new(backends, NULL, 2, GGML_DEFAULT_GRAPH_SIZE, false, true);

    // 3. Contesto senza dati (no_alloc = true): serve solo per i metadati dei tensori e il grafo.
    size_t mem = ggml_tensor_overhead() * GGML_DEFAULT_GRAPH_SIZE + ggml_graph_overhead();
    void * arena = malloc(mem);
    struct ggml_init_params params = {
        /*.mem_size   =*/ mem,
        /*.mem_buffer =*/ arena,
        /*.no_alloc   =*/ true,
    };
    struct ggml_context * ctx = ggml_init(params);

    struct ggml_tensor * a = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_A, righe_A);
    struct ggml_tensor * b = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_B, righe_B);

    struct ggml_cgraph * gf        = ggml_new_graph(ctx);
    struct ggml_tensor * risultato = ggml_mul_mat(ctx, a, b);
    ggml_build_forward_expand(gf, risultato);

    // 4. Lo scheduler alloca i buffer per tutti i tensori del grafo sul backend che li eseguira'.
    ggml_backend_sched_reset(sched);
    ggml_backend_sched_alloc_graph(sched, gf);

    // 5. Copia dei dati dalla RAM del programma al buffer del backend (VRAM se e' una GPU).
    ggml_backend_tensor_set(a, dati_A, 0, ggml_nbytes(a));
    ggml_backend_tensor_set(b, dati_B, 0, ggml_nbytes(b));

    // 6. Esecuzione: lo scheduler divide il grafo tra i backend e lancia il calcolo.
    ggml_backend_sched_graph_compute(sched, gf);

    // 7. Lettura del risultato dal buffer del backend.
    struct ggml_tensor * out = ggml_graph_node(gf, -1);
    float * dati_out = malloc(ggml_nbytes(out));
    ggml_backend_tensor_get(out, dati_out, 0, ggml_nbytes(out));

    printf("mul_mat (%d x %d), risultato trasposto:\n", (int) out->ne[0], (int) out->ne[1]);
    for (int j = 0; j < out->ne[1]; j++) {
        for (int i = 0; i < out->ne[0]; i++) {
            printf(" %6.2f", dati_out[j * out->ne[0] + i]);
        }
        printf("\n");
    }

    free(dati_out);
    ggml_free(ctx);
    free(arena);
    ggml_backend_sched_free(sched);
    ggml_backend_free(backend);
    ggml_backend_free(backend_cpu);
    return 0;
}
