// matmul.c: moltiplicazione di matrici con ggml, API "a contesto" (solo CPU).
//
// Ricalca examples/simple/simple-ctx.cpp del repository ggml, tradotto in C puro.
// Passi: 1) contesto con memoria pre-allocata; 2) tensori a e b; 3) grafo con un nodo MUL_MAT;
//        4) esecuzione su CPU; 5) lettura del risultato.
//
// Compilazione: vedi CMakeLists.txt in questa cartella (cmake -B build && cmake --build build).

#include "ggml.h"
#include "ggml-cpu.h"   // ggml_graph_compute_with_ctx

#include <stdio.h>
#include <string.h>

int main(void) {
    ggml_time_init();

    // Matrice A: 4 righe x 2 colonne (in ggml ne[0] = colonne, ne[1] = righe).
    const int righe_A = 4, colonne_A = 2;
    float dati_A[4 * 2] = {
        2, 8,
        5, 1,
        4, 2,
        8, 6,
    };

    // Matrice B: 3 righe x 2 colonne. ggml_mul_mat calcola A * B^T, quindi B va data "trasposta":
    // qui B^T e' la matrice 2x3 [[10, 9, 5], [5, 9, 4]].
    const int righe_B = 3, colonne_B = 2;
    float dati_B[3 * 2] = {
        10, 5,
         9, 9,
         5, 4,
    };

    // 1. Stima della memoria del contesto: i due tensori, gli oggetti tensore, il grafo e un margine.
    size_t mem = 0;
    mem += righe_A * colonne_A * ggml_type_size(GGML_TYPE_F32);
    mem += righe_B * colonne_B * ggml_type_size(GGML_TYPE_F32);
    mem += 2 * ggml_tensor_overhead();   // metadati dei tensori
    mem += ggml_graph_overhead();        // struttura del grafo
    mem += 1024;                         // margine

    struct ggml_init_params params = {
        /*.mem_size   =*/ mem,
        /*.mem_buffer =*/ NULL,          // NULL: ggml alloca l'arena da solo
        /*.no_alloc   =*/ false,         // false: i tensori hanno subito la loro memoria (API legacy)
    };
    struct ggml_context * ctx = ggml_init(params);
    if (ctx == NULL) {
        fprintf(stderr, "ggml_init fallita\n");
        return 1;
    }

    // 2. Tensori: ggml_new_tensor_2d(ctx, tipo, ne0 = colonne, ne1 = righe).
    struct ggml_tensor * a = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_A, righe_A);
    struct ggml_tensor * b = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, colonne_B, righe_B);
    memcpy(a->data, dati_A, ggml_nbytes(a));
    memcpy(b->data, dati_B, ggml_nbytes(b));

    // 3. Grafo: un solo nodo, risultato = a * b^T. Nessun calcolo avviene qui.
    struct ggml_cgraph  * gf        = ggml_new_graph(ctx);
    struct ggml_tensor  * risultato = ggml_mul_mat(ctx, a, b);
    ggml_build_forward_expand(gf, risultato);

    printf("grafo: %d nodi, risultato %s con ne = [%d, %d]\n",
           ggml_graph_n_nodes(gf), ggml_op_name(risultato->op),
           (int) risultato->ne[0], (int) risultato->ne[1]);

    // 4. Esecuzione su CPU con n thread.
    const int n_thread = 2;
    ggml_graph_compute_with_ctx(ctx, gf, n_thread);

    // 5. L'ultimo nodo del grafo e' il risultato: ne[0] = 4 colonne (righe di A), ne[1] = 3 righe (righe di B).
    struct ggml_tensor * out = ggml_graph_node(gf, -1);
    const float * dati_out = (const float *) out->data;

    // Atteso (come in simple-ctx.cpp):
    // [ 60 55 50 110
    //   90 54 54 126
    //   42 29 28  64 ]
    printf("mul_mat (%d x %d), risultato trasposto:\n", (int) out->ne[0], (int) out->ne[1]);
    for (int j = 0; j < out->ne[1]; j++) {
        for (int i = 0; i < out->ne[0]; i++) {
            printf(" %6.2f", dati_out[j * out->ne[0] + i]);
        }
        printf("\n");
    }

    ggml_free(ctx);
    return 0;
}
