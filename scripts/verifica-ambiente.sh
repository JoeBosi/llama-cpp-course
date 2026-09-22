#!/usr/bin/env bash
# Verifica rapida dell'ambiente per il corso llama.cpp (Linux/macOS; su Windows usare WSL o Git Bash).
# Solo lettura: non installa nulla.

ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
no()   { printf '  \033[33m✘\033[0m %s\n' "$1"; }
cmd()  { command -v "$1" >/dev/null 2>&1; }

echo "== Sistema"
echo "  $(uname -s) $(uname -m)"
if [ "$(uname -s)" = "Darwin" ]; then
  echo "  CPU: $(sysctl -n machdep.cpu.brand_string 2>/dev/null) ($(sysctl -n hw.ncpu) core)"
  echo "  RAM: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 )) GB"
else
  echo "  CPU: $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs) ($(nproc) core)"
  echo "  RAM: $(free -g | awk '/Mem:/{print $2}') GB totali, $(free -g | awk '/Mem:/{print $7}') GB disponibili"
  flags=$(grep -m1 '^flags' /proc/cpuinfo 2>/dev/null)
  for f in avx2 avx512f amx_tile; do [[ $flags == *" $f"* ]] && ok "CPU supporta $f" || no "CPU senza $f"; done
fi
echo "  Disco libero qui: $(df -h . | awk 'NR==2{print $4}')"

echo "== GPU"
cmd nvidia-smi && ok "NVIDIA: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)" || no "nessuna GPU NVIDIA (nvidia-smi assente)"
cmd rocminfo   && ok "AMD ROCm presente" || no "ROCm assente"
cmd vulkaninfo && ok "Vulkan presente" || no "vulkaninfo assente"
[ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ] && ok "Apple Silicon: backend Metal disponibile"

echo "== Strumenti"
for t in git cmake ninja ccache gcc clang python3 docker curl; do
  cmd "$t" && ok "$t" || no "$t non trovato"
done

echo "== llama.cpp"
if cmd llama; then ok "llama: $(llama --version 2>&1 | head -1)"
elif cmd llama-cli; then ok "llama-cli (nomi vecchi): $(llama-cli --version 2>&1 | head -1)"
else no "llama.cpp non installato (vedi modulo 01)"; fi
