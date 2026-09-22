# Glossario

| Termine | Significato |
|---|---|
| GGUF | Formato di file di llama.cpp: pesi del modello + metadati (architettura, tokenizer, chat template) |
| ggml | Libreria tensoriale su cui si basa llama.cpp |
| Quantizzazione | Rappresentare i pesi con meno bit (es. 4 invece di 16) per ridurre memoria e aumentare la velocità |
| KV cache | Memoria che conserva chiavi/valori dell'attenzione dei token già elaborati; cresce con il contesto |
| Offload (`-ngl`) | Numero di layer del modello spostati sulla GPU |
| pp / tg | Prompt processing / token generation: le due velocità misurate da `llama-bench` |
| mmproj | Proiettore multimodale: file separato che collega un encoder di immagini/audio al modello linguistico |
| _(da ampliare)_ | |
