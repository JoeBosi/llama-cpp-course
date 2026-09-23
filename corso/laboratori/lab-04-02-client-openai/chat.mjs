// Client JavaScript senza dipendenze: `fetch` nativo di Node.js 18+ (o del browser).
// Uso:  node chat.mjs            -> risposta intera
//       node chat.mjs --stream   -> streaming SSE riga per riga
const BASE = process.env.LLAMA_URL ?? "http://127.0.0.1:8080";
const stream = process.argv.includes("--stream");

const body = {
  model: "local",
  messages: [
    { role: "system", content: "Rispondi in italiano, in modo conciso." },
    { role: "user", content: "Elenca tre usi di un server LLM locale." },
  ],
  max_tokens: 80,
  temperature: 0.2,
  stream,
  chat_template_kwargs: { enable_thinking: false }, // parametro extra di llama.cpp
};

const res = await fetch(`${BASE}/v1/chat/completions`, {
  method: "POST",
  headers: { "Content-Type": "application/json" /* , Authorization: "Bearer LA-TUA-CHIAVE" */ },
  body: JSON.stringify(body),
});
if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

if (!stream) {
  const data = await res.json();
  console.log(data.choices[0].message.content);
  console.log(`[${data.usage.completion_tokens} token, ${data.timings.predicted_per_second.toFixed(1)} t/s]`);
} else {
  // Il corpo è un flusso di eventi SSE: righe "data: {...}" separate da righe vuote, chiuse da "data: [DONE]".
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    const righe = buffer.split("\n");
    buffer = righe.pop(); // l'ultima riga può essere incompleta: la teniamo per il prossimo giro
    for (const riga of righe) {
      if (!riga.startsWith("data: ")) continue; // salta righe vuote e commenti ": ping"
      const payload = riga.slice(6);
      if (payload === "[DONE]") { process.stdout.write("\n[fine]\n"); continue; }
      const chunk = JSON.parse(payload);
      const delta = chunk.choices?.[0]?.delta?.content;
      if (delta) process.stdout.write(delta);
      if (chunk.timings) console.log(`\n[${chunk.timings.predicted_n} token, ${chunk.timings.predicted_per_second.toFixed(1)} t/s]`);
    }
  }
}
