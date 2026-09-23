# CMakeLists.txt del lab 10-01: compila matmul.c e matmul-backend.c contro i sorgenti di ggml.
#
# Struttura attesa:
#   lab-10-01-grafo-ggml/
#     CMakeLists.txt      (questo file)
#     matmul.c
#     matmul-backend.c
#     ggml/               (git clone https://github.com/ggml-org/ggml)
#
# Uso:
#   cmake -B build                       # CPU
#   cmake -B build -DGGML_CUDA=ON        # con GPU NVIDIA (o -DGGML_METAL=ON, -DGGML_VULKAN=ON)
#   cmake --build build -j
#   ./build/matmul && ./build/matmul-backend
cmake_minimum_required(VERSION 3.14)
project(lab-grafo-ggml C CXX)   # ggml e' C/C++: servono entrambi i compilatori

set(CMAKE_C_STANDARD 11)

# Non ci servono gli esempi e i test di ggml: risparmiamo tempo di compilazione.
set(GGML_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GGML_BUILD_TESTS    OFF CACHE BOOL "" FORCE)

add_subdirectory(ggml)   # crea il target "ggml" (e ggml-base, ggml-cpu, ggml-cuda...)

add_executable(matmul matmul.c)
target_link_libraries(matmul PRIVATE ggml)

add_executable(matmul-backend matmul-backend.c)
target_link_libraries(matmul-backend PRIVATE ggml)
