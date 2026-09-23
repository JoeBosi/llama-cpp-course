// main.cpp - generatore di testo minimo con la C API di libllama.
// Basato su examples/simple/simple.cpp del repository ufficiale (b11046),
// con i commenti in italiano e una catena di campionamento "vera"
// (top-k, top-p, temperatura) al posto del semplice greedy.
//
// Uso:  ./generatore modello.gguf ["prompt"] [n_predict] [n_threads]

#include "llama.h"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// Filtro dei log: libllama stampa decine di righe INFO al caricamento.
// Qui lasciamo passare solo avvisi ed errori.
static void log_silenzioso(ggml_log_level livello, const char * testo, void * /*dati*/) {
    if (livello == GGML_LOG_LEVEL_WARN || livello == GGML_LOG_LEVEL_ERROR) {
        fputs(testo, stderr);
    }
}

int main(int argc, char ** argv) {
    if (argc < 2) {
        fprintf(stderr, "uso: %s modello.gguf [\"prompt\"] [n_predict] [n_threads]\n", argv[0]);
        return 1;
    }
    const std::string percorso_modello = argv[1];
    const std::string prompt    = argc > 2 ? argv[2] : "La capitale d'Italia è";
    const int         n_predict = argc > 3 ? std::atoi(argv[3]) : 32;   // token da generare
    const int         n_threads = argc > 4 ? std::atoi(argv[4]) : 4;    // thread CPU

    // 1. Inizializzazione di ggml/llama e caricamento dei backend dinamici
    //    (libggml-cpu-*.so, libggml-cuda.so ... se presenti accanto alla libreria).
    llama_log_set(log_silenzioso, nullptr);
    llama_backend_init();
    ggml_backend_load_all();

    // 2. Il modello: pesi + vocabolario. n_gpu_layers = 0 -> tutto su CPU
    //    (99 per mandare tutti i layer sulla GPU, se c'è un backend GPU).
    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;

    llama_model * model = llama_model_load_from_file(percorso_modello.c_str(), mparams);
    if (model == nullptr) {
        fprintf(stderr, "errore: impossibile caricare %s\n", percorso_modello.c_str());
        return 1;
    }
    const llama_vocab * vocab = llama_model_get_vocab(model);

    // 3. Tokenizzazione del prompt. Chiamata due volte: la prima (buffer NULL)
    //    restituisce -N, cioè quanti token servono; la seconda li scrive davvero.
    const int n_prompt = -llama_tokenize(vocab, prompt.c_str(), prompt.size(), nullptr, 0, true, true);
    std::vector<llama_token> token_prompt(n_prompt);
    if (llama_tokenize(vocab, prompt.c_str(), prompt.size(), token_prompt.data(), token_prompt.size(), true, true) < 0) {
        fprintf(stderr, "errore: tokenizzazione fallita\n");
        return 1;
    }

    // 4. Il contesto: KV cache, thread, dimensione del batch.
    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx           = n_prompt + n_predict;  // giusto lo spazio che serve
    cparams.n_batch         = n_prompt;              // tutto il prompt in una chiamata a llama_decode
    cparams.n_threads       = n_threads;
    cparams.n_threads_batch = n_threads;
    cparams.no_perf         = false;                 // abilita i contatori di prestazioni

    llama_context * ctx = llama_init_from_model(model, cparams);
    if (ctx == nullptr) {
        fprintf(stderr, "errore: impossibile creare il contesto\n");
        return 1;
    }

    // 5. La catena di campionamento: stessi valori di default di `llama cli`
    //    (top-k 40, top-p 0.95, temp 0.8) e infine l'estrazione casuale.
    llama_sampler_chain_params sparams = llama_sampler_chain_default_params();
    sparams.no_perf = false;   // altrimenti llama_perf_sampler_print stampa zeri
    llama_sampler * smpl = llama_sampler_chain_init(sparams);
    llama_sampler_chain_add(smpl, llama_sampler_init_top_k(40));
    llama_sampler_chain_add(smpl, llama_sampler_init_top_p(0.95f, 1));
    llama_sampler_chain_add(smpl, llama_sampler_init_temp(0.8f));
    llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    // Stampa il prompt, token per token, per vedere come è stato spezzato.
    for (llama_token id : token_prompt) {
        char buf[256];
        const int n = llama_token_to_piece(vocab, id, buf, sizeof(buf), 0, true);
        if (n < 0) { fprintf(stderr, "errore: token_to_piece\n"); return 1; }
        fwrite(buf, 1, n, stdout);
    }

    // 6. Il ciclo di generazione: decode del batch -> campiona -> nuovo batch da 1 token.
    llama_batch batch = llama_batch_get_one(token_prompt.data(), token_prompt.size());
    llama_token nuovo_token = LLAMA_TOKEN_NULL;
    int n_generati = 0;

    for (int n_pos = 0; n_pos + batch.n_tokens < n_prompt + n_predict; ) {
        if (llama_decode(ctx, batch) != 0) {
            fprintf(stderr, "errore: llama_decode fallita\n");
            return 1;
        }
        n_pos += batch.n_tokens;

        // campiona dal logit dell'ultimo token del batch (indice -1)
        nuovo_token = llama_sampler_sample(smpl, ctx, -1);

        if (llama_vocab_is_eog(vocab, nuovo_token)) {   // fine generazione (EOS o simili)
            break;
        }

        char buf[256];
        const int n = llama_token_to_piece(vocab, nuovo_token, buf, sizeof(buf), 0, true);
        if (n < 0) { fprintf(stderr, "errore: token_to_piece\n"); return 1; }
        fwrite(buf, 1, n, stdout);
        fflush(stdout);

        // il prossimo batch contiene solo il token appena generato
        batch = llama_batch_get_one(&nuovo_token, 1);
        n_generati++;
    }
    printf("\n");

    // 7. Statistiche e pulizia (ordine inverso rispetto alla creazione).
    //    Le statistiche passano dal logger a livello INFO: riattiviamo quello di default.
    fprintf(stderr, "\ngenerati %d token\n", n_generati);
    llama_log_set(nullptr, nullptr);
    llama_perf_sampler_print(smpl);
    llama_perf_context_print(ctx);

    llama_sampler_free(smpl);
    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();
    return 0;
}
