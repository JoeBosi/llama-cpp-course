# Lab 05-04 · RPC cluster

<div class="meta" markdown>
<span class="meta-item">:material-book-open-page-variant:{ .meta-icon } Module <a href="../../moduli/05-prestazioni/README.md">05: Performance and optimization</a></span>
<span class="meta-item">:material-clock-outline:{ .meta-icon } 45 minutes</span>
</div>

## Objective

Run a model using the memory (and, if present, the GPU) of **another machine** through the ggml RPC backend:
start `ggml-rpc-server` on the remote host, connect to it with `--rpc`, check how the weights are distributed and measure the
price you pay in speed. The same exercise works on a single machine with two terminals (or two containers):
that is the setup used in the examples below.

## Prerequisites

- Two machines on the same trusted local network (A = main, B = remote), **or** a single machine with two terminals.
- On both, the **release tarball binaries** (e.g. `llama-b11046-bin-ubuntu-x64.tar.gz`, module 01) or a build
  with `-DGGML_RPC=ON`. The installer's `llama` binary does **not** have the RPC backend: its `--help` does not show `--rpc`.
- The model downloaded **on machine A** (B receives the tensors over the network, it does not read the file).

## Materials

| What | Source | Size |
|---|---|---|
| Test model | `ggml-org/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q8_0.gguf` (Apache 2.0) | 795 MB |
| Model "that does not fit" (variant) | `ggml-org/gemma-3-12b-it-GGUF:Q4_K_M` | 6.96 GB |
| Binaries | release tarball in `~/llama-lab/rel/llama-b11046/` (contains `ggml-rpc-server`, `llama-cli`, `llama-server`, `llama-bench` and `libggml-rpc.so`) | 16 MB |

```bash
R=~/llama-lab/rel/llama-b11046
$R/ggml-rpc-server --help
```

Expected output:

```
load_backend: loaded RPC backend from …/libggml-rpc.so
load_backend: loaded CPU backend from …/libggml-cpu-haswell.so
Usage: ggml-rpc-server [options]
  -t, --threads N                  number of threads for the CPU device (default: 3)
  -d, --device <dev1,dev2,...>     comma-separated list of devices
  -H, --host HOST                  host to bind to (default: 127.0.0.1)
  -p, --port PORT                  port to bind to (default: 50052)
  -c, --cache                      enable local file cache
```

## Steps

1. **On machine B (or in terminal 1): start the server.** Locally use `127.0.0.1`; on two machines use
    B's LAN address (`-H 192.168.1.20`) and **only** on a trusted network:

    ```bash
    $R/ggml-rpc-server -H 127.0.0.1 -p 50052 -t 3
    ```

    Expected output:

    ```
    Starting RPC server v7.0.0
      endpoint       : 127.0.0.1:50052
      local cache    : n/a
    Devices:
      CPU: AMD EPYC Processor (with IBPB) (11960 MiB, 11960 MiB free)
      transport      : TCP
    ```

    On a machine with a GPU you see `CUDA0: NVIDIA … (32109 MiB, 31588 MiB free)` instead; with `-d CUDA0` or
    `CUDA_VISIBLE_DEVICES` you choose which devices to expose.

2. **On machine A (terminal 2): is the remote device visible?**

    ```bash
    $R/llama-cli --rpc 127.0.0.1:50052 --list-devices
    ```

    ```
    Available devices:
      RPC0: 127.0.0.1:50052 (11960 MiB, 11960 MiB free)
    ```

    The device is called `RPC0` (then `RPC1`… for other servers, in list order). On the server you see
    `Accepted client connection` / `Client connection closed`.

3. **Generate across the network.**

    ```bash
    M=$(ls ~/.cache/huggingface/hub/models--ggml-org--Qwen3.5-0.8B-GGUF/snapshots/*/Qwen3.5-0.8B-Q8_0.gguf)
    $R/llama-cli --rpc 127.0.0.1:50052 -m "$M" -st -p "ciao" -n 20 -t 3 -rea off
    ```

    Output on a 6 vCPU machine without GPU:

    ```
    > ciao
    Ciao! Come posso aiutarti oggi?

    [ Prompt: 1.4 t/s | Generation: 0.6 t/s ]
    ```

    Loading is slower than usual: the weights are **sent** to the RPC server (785 MB over loopback in a few
    seconds; on a 1 Gbit/s LAN about 8 seconds, for a 7 GB model over a minute).

4. **Where did the weights go?** Repeat with `-v` (full log) and look for the buffers:

    ```bash
    $R/llama-cli --rpc 127.0.0.1:50052 -m "$M" -st -p "ciao" -n 5 -rea off -v 2>&1 | grep -E "RPC0|CPU_Mapped|offloaded|buffer size"
    ```

    By default llama.cpp distributes weights and KV cache between local and remote devices **in proportion to free
    memory**; `-ngl` also counts the RPC device as a "GPU". With `-ts` you set the proportions: `-ts 1,0` (everything on the
    first device), `-ts 1,1` (half and half). Try `-ngl all -ts 0,1` to send everything to the remote server and compare
    the `Generation:` line with step 3.

5. **The HTTP server with a remote backend.** Everything that applies to `llama-cli` applies to `llama-server`:

    ```bash
    $R/llama-server --rpc 127.0.0.1:50052 -m "$M" --port 18104 -c 4096
    curl -s localhost:18104/health
    ```

    Stop it with ++ctrl+c++ and read `llama_memory_breakdown_print`: there is a line for `RPC0`.

6. **Local cache (variant).** On B restart with `-c`: on the second run the large tensors are read from
    `~/.cache/llama.cpp/rpc` instead of being received over the network. Time the loading before and after.

7. **Shut everything down.** ++ctrl+c++ on the RPC server, or:

    ```bash
    pkill -f "ggml-rpc-server"
    ```

    An RPC server left running is a risk (see below).

## Check the result

- [ ] `--list-devices` shows `RPC0` with the server's memory.
- [ ] The model answered through RPC and you noted pp/tg.
- [ ] You compared the speed with the same command **without** `--rpc`: the difference is the cost of the network (small
      locally, large on a LAN).
- [ ] You shut down the RPC server and checked with `pgrep -af rpc-server` that it is gone.

!!! danger "No authentication: trusted network only"
    `ggml-rpc-server` has no password, token or TLS; the official README calls it a *proof of concept, fragile and
    insecure* and says to **never run it on an open network**. Anyone who reaches the port can use your GPU and your RAM
    at will. Rules: `-H 127.0.0.1` or an isolated LAN address, a firewall that accepts only machine A, or an
    SSH tunnel (`ssh -L 50052:localhost:50052 utente@B`) or a VPN; shut the server down when you do not need it.

## Questions and variants

- Why is generation over RPC slower even when the server has a fast GPU? Think about what crosses the network at every token (activations between layers) and with what latency.
- With two machines: `-ts 3,1` (A keeps 75 %) against `-ts 1,3`. Which order is better if A has the faster GPU?
- Two RPC servers: `--rpc B:50052,C:50052`. In what order do they appear in `--list-devices`?
- `GGML_RPC_DEBUG=1 ggml-rpc-server …` shows every command received: count how many messages it takes to generate 5 tokens.
- Two containers on the same machine: create a network (`docker network create rpc`), start two Ubuntu containers with the
  tarball mounted in `/opt/llama` and use the container names as hosts (`--rpc rpc-b:50052`). Same security rules:
  the network is internal to Docker, do not publish the port with `-p`.
- With a GPU on B and a model that does not fit in A's VRAM (gemma-3-12b), compare: everything on A with partial `-ngl`
  against A+B via RPC. The winner depends on the network: with 1 Gbit/s almost always the local hybrid, with 10 Gbit/s or
  Thunderbolt/RDMA the cluster.

## Deliverable

The server startup log (the `Devices:` lines), the `--list-devices` output, the `[ Prompt … | Generation … ]` line
with and without `--rpc`, and five lines of conclusions: when you would use RPC and which security measures you would adopt.
