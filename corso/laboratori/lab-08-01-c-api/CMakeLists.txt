# CMakeLists.txt - lab 08-01: un programma C++ che usa libllama.
#
# Due modi per trovare la libreria, scelti in automatico:
#   A) sorgenti di llama.cpp in una sottocartella `llama.cpp/` (git clone o submodule):
#      vengono compilati insieme al programma con add_subdirectory().
#   B) llama.cpp gia' installata sul sistema (cmake --install, brew, conda...):
#      find_package(llama) legge il file llama-config.cmake e importa il target `llama`.
#
# Configura e compila:
#   cmake -B build -DCMAKE_BUILD_TYPE=Release      # (+ -DGGML_CUDA=ON ecc. nel caso A)
#   cmake --build build -j
#   ./build/generatore modello.gguf "La capitale d'Italia è" 32

cmake_minimum_required(VERSION 3.14)
project(lab-08-01-c-api LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/llama.cpp/CMakeLists.txt")
    message(STATUS "libllama: compilo dai sorgenti in llama.cpp/")
    # non servono gli strumenti (llama-cli, llama-server...) ne' i test: solo la libreria
    set(LLAMA_BUILD_TOOLS    OFF CACHE BOOL "" FORCE)
    set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(LLAMA_BUILD_TESTS    OFF CACHE BOOL "" FORCE)
    set(LLAMA_BUILD_SERVER   OFF CACHE BOOL "" FORCE)
    add_subdirectory(llama.cpp)
else()
    message(STATUS "libllama: cerco un'installazione con find_package(llama)")
    find_package(llama REQUIRED)   # es. -DCMAKE_PREFIX_PATH=/percorso/di/install
endif()

add_executable(generatore main.cpp)
# il target `llama` porta con se' include (llama.h, ggml.h) e librerie (libllama, libggml)
target_link_libraries(generatore PRIVATE llama)
