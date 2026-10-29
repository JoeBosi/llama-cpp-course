# Lab 10-01 · A ggml graph by hand

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/10-approfondimenti/README.md">10: Deep dives: inside ggml and llama.cpp</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 60 minutes (+ building ggml)</span>
</div>

## Objective

Write (or rather: read line by line, build and run) two C programs that multiply two matrices with
ggml. The first, `matmul.c`, uses the "context" API and runs only on CPU; the second, `matmul-backend.c`, uses the
backend API and the scheduler, and runs on the GPU if the binary has one. By the end you can recognize in any
llama.cpp source the four ggml objects (context, tensor, graph, backend) and you know why the result of
`ggml_mul_mat` comes out "transposed".

## Prerequisites

- Module 10, sections 1 and 2.
- A C/C++ compiler and CMake ≥ 3.14 (the same as in [lab 01-02](../lab-01-02-build-sorgenti-cpu/README.md));
  `git`. For the GPU part: your backend's toolkit (CUDA, Vulkan SDK, Xcode on macOS).
- No model: here you multiply two matrices, 4×2 and 3×2.

## Materials

| What | Source | Size |
|---|---|---|
| ggml sources | `git clone https://github.com/ggml-org/ggml` (MIT license) | ~40 MB with git history (`--depth 1` to reduce it) |
| [`matmul.c`](matmul.c) | this folder: C translation of `examples/simple/simple-ctx.cpp` | |
| [`matmul-backend.c`](matmul-backend.c) | this folder: C translation of `examples/simple/simple-backend.cpp` | |
| [`CMakeLists.txt`](CMakeLists.txt) | this folder: builds the two programs against `ggml/` as a subproject | |

The two original `.cpp` files are in [examples/simple](https://github.com/ggml-org/ggml/tree/master/examples/simple)
of the ggml repository: keep them open next to the `.c` files to compare (same data, same expected result).

## Steps

1. **Prepare the folder.** Copy the three lab files into a working folder and clone ggml **inside** it
    (the `CMakeLists.txt` expects `./ggml`):

    ```bash
    mkdir -p ~/lab-ggml && cd ~/lab-ggml
    cp /percorso/del/corso/laboratori/lab-10-01-grafo-ggml/{matmul.c,matmul-backend.c,CMakeLists.txt} .
    git clone --depth 1 https://github.com/ggml-org/ggml
    ls
    ```
    ```
    CMakeLists.txt  ggml  matmul-backend.c  matmul.c
    ```

2. **Read `matmul.c`** before building. There are five steps, the same as in `simple-ctx.cpp`:

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

    1. `ggml.h` is the tensor and operation API; `ggml-cpu.h` adds `ggml_graph_compute_with_ctx`, which
       exists only for the CPU backend.
    2. `A` is 4 rows × 2 columns, written row by row (ggml is *row-major*).
    3. `B` is given **already transposed** (3×2): `ggml_mul_mat` computes `A·Bᵀ`, so by passing `Bᵀ` we get the classic `A·B` with `B` = `[[10, 9, 5], [5, 9, 4]]`.
    4. The memory estimate: the data bytes, the metadata of 2 tensors, the graph, a margin. If you underestimate, `ggml_new_tensor_2d` fails with an assertion.
    5. `mem_buffer = NULL` lets ggml allocate the arena; `no_alloc = false` because with the legacy API tensors must hold their data in the context.
    6. **`ne[0]` = columns, `ne[1]` = rows**: `a` has `ne = [2, 4]`, `b` has `ne = [2, 3]`. It is the reverse of PyTorch's order.
    7. With `no_alloc = false` the pointer `a->data` is valid memory: you copy into it directly.
    8. No computation: `risultato` is a tensor with `op = GGML_OP_MUL_MAT`, `src[0] = a`, `src[1] = b`, `ne = [4, 3]`.
    9. The graph is filled starting from the result and walking back through the dependencies: 1 node (the following `printf` prints it).
    10. Execution on CPU with 2 threads. This is where the multiplication happens.
    11. The last node of the graph is the result; with the legacy API `out->data` is directly readable.

3. **Read `matmul-backend.c`.** Same data, same `ggml_mul_mat`, but the data no longer lives in the context:

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
    /* ... a, b, gf, risultato as before ... */

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

    1. Instead of `ggml-cpu.h`: the backend API is device-independent.
    2. Dynamically loads the backend libraries found next to the executable (`libggml-cuda.so`, `libggml-cpu-*.so`…) and registers them.
    3. The "best" of the registered backends (GPU if there is one, otherwise CPU). The CPU is initialized anyway as a fallback.
    4. The scheduler: list of backends in priority order, no forced buffer type (`NULL`), 2 backends, maximum graph size, no parallel execution, automatic allocation.
    5. `no_alloc = true`: the context holds only metadata; the arena is small (overhead only) and we provide it ourselves with `malloc`.
    6. The scheduler assigns each node to a backend and allocates buffers for **all** tensors in the graph, `a` and `b` included, on the device of the backend that will use them.
    7. The data must be copied into the backend's buffer: if it is a GPU, this is a host→device copy. A `memcpy` on `a->data` here would be a bug.
    8. Execution: the scheduler launches the splits in the right order.
    9. Device→host copy of the result into our own array.
    10. Freeing in reverse order: scheduler, then backends.

4. **Build on CPU.** The `CMakeLists.txt` includes `ggml/` with `add_subdirectory` and disables ggml's examples and tests:

    ```bash
    cmake -B build
    cmake --build build -j
    ```

    The first ggml build takes a few minutes (CPU kernels for all SIMD variants). The binaries
    end up in `build/` (or `build/bin/` depending on the CMake version and generator; `find build -name matmul`).

5. **Run and compare with the expected result.** The expected output is the one written in the comments of `simple-ctx.cpp`:

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

    Check one element by hand: row 0 of the result is `B[0]·A[i]` for i = 0..3: `10·2 + 5·8 = 60`,
    `10·5 + 5·1 = 55`, `10·4 + 5·2 = 50`, `10·8 + 5·6 = 110`. The "true" matrix `A·B` (4×3) is the transpose of
    what you see: that is the meaning of `Cᵀ = A·Bᵀ`.

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

6. **Rebuild with a GPU backend** (only if you have one; the CPU part does not change):

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
    === "Vulkan (any GPU)"
        ```bash
        cmake -B build-gpu -DGGML_VULKAN=ON
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```
    === "macOS (Metal)"
        ```bash
        cmake -B build-gpu          # Metal is the default on Apple Silicon macOS
        cmake --build build-gpu -j
        ./build-gpu/matmul-backend
        ```

    Expected: the first line becomes `backend scelto: CUDA0` (or `Vulkan0`, `Metal`, `ROCm0`), the numbers are
    identical. `matmul` instead prints the same as before: it uses `ggml_graph_compute_with_ctx`, which is CPU only.
    These are the same CMake options as in [module 01](../../moduli/01-installazione/README.md): llama.cpp builds
    ggml exactly this way.

7. **Experiment.** Change `n_thread` in `matmul.c`; add a second node (`ggml_add(ctx, risultato, risultato)`
    before `ggml_build_forward_expand` and count the nodes: they become 2); switch `a` to `GGML_TYPE_F16` (you need
    `ggml_fp32_to_fp16_row` to fill it) and observe that `ggml_mul_mat` accepts operands of different types as long as the
    second is F32. If you increase the number of tensors without updating the `mem` estimate, you will see the context
    assertion: that is intended.

## Check the result

- [ ] `./build/matmul` prints `grafo: 1 nodi` and the 3×4 matrix with `60 55 50 110` in the first row.
- [ ] `./build/matmul-backend` prints `backend scelto: CPU` and the same matrix.
- [ ] With the GPU build, `matmul-backend` prints the GPU backend's name and the same numbers.
- [ ] You can explain why the result has `ne = [4, 3]` and not `[3, 4]`.

## Questions and variations

1. Why does `matmul-backend.c` allocate the arena with `ggml_tensor_overhead() * GGML_DEFAULT_GRAPH_SIZE` instead of
   `2 * ggml_tensor_overhead()`? (Tip: look at what `ggml_new_graph` does.)
2. What would happen if you passed only one backend (`backend_cpu`) to the scheduler? And if you passed `backend_cpu` first
   and then `backend`?
3. In the backend program, at exactly what moment is the memory where `a` and `b` live decided?
4. Variation: replace `ggml_mul_mat` with `ggml_mul_mat(ctx, b, a)`: what dimensions does the result have and what does it represent?
5. Variation (advanced): open `src/models/llama.cpp` in llama.cpp and find the `ggml_mul_mat` calls with the weights
   `wq`, `wk`, `wv`: do you recognize the same `[n_embd, n_head*head_dim]` convention?

## Deliverable

- The output of both programs on CPU (and on GPU if available), with the name of the chosen backend.
- A modified `matmul.c` with at least a second node in the graph and the new output, plus two comment lines
  that explain the `Cᵀ = A·Bᵀ` convention with your numbers.
- The answers to questions 1-3.
