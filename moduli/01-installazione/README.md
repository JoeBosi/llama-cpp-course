# Modulo 01: Installazione su varie piattaforme

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Via rapida: llama.app e gestori di pacchetti (Homebrew, winget, Nix, …)
2. Binari precompilati dalla pagina release: quale archivio scegliere per CPU/GPU
3. Docker: immagini ufficiali `ghcr.io/ggml-org/llama.cpp` (varianti cpu/cuda/vulkan/…)
4. Compilare dai sorgenti con CMake: Linux, macOS, Windows (MSVC/clang)
5. Backend GPU: CUDA (NVIDIA), Metal (Apple), HIP (AMD), Vulkan, SYCL (Intel), OpenCL (Adreno)
6. Piattaforme edge: Raspberry Pi / ARM64, Android (Termux e NDK)
7. Verificare l'installazione: `--version`, backend rilevati, primo modello
8. Aggiornare e fissare una versione

## Laboratori
- [Installazione da binari/pacchetti](../../laboratori/lab-01-01-binari-precompilati/README.md): Installare llama.cpp senza compilare sulla propria piattaforma e verificare backend e versione.
- [Build dai sorgenti (CPU)](../../laboratori/lab-01-02-build-sorgenti-cpu/README.md): Clonare, fissare la versione del corso, compilare con CMake/Ninja e ccache; confrontare i tempi.
- [Build con backend GPU](../../laboratori/lab-01-03-build-gpu/README.md): Compilare con il backend della propria GPU (CUDA/Metal/Vulkan/HIP) e verificarne l'uso. Laboratorio a percorsi alternativi.
- [llama.cpp in Docker](../../laboratori/lab-01-04-docker/README.md): Eseguire cli e server dalle immagini ufficiali, con volume per la cache dei modelli ed eventuale GPU passthrough.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
