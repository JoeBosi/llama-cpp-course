"""Hook MkDocs per la visibilità: description per pagina, robots.txt, llms.txt, llms-full.txt e .md delle pagine."""
import os
import re

_pagine = {}  # url -> (pagina, markdown); i18n costruisce una lingua alla volta, quindi si accumula


def _riassunto(markdown):
    """Primo paragrafo di testo vero della pagina, senza markup, ~160 caratteri."""
    testo = re.sub(r"^---.*?---\n", "", markdown, flags=re.S)
    for blocco in re.split(r"\n\s*\n", testo):
        b = blocco.strip()
        if not b or b[0] in "#!<|`-*>:=[{" or b.startswith(("???", "===", "```")):
            continue
        b = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
        b = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", b)
        b = re.sub(r"\{[^}]*\}|[*_`]|:[a-z0-9-]+:", "", b)
        b = re.sub(r"\s+", " ", b).strip()
        if len(b) < 40:
            continue
        return b if len(b) <= 160 else b[:157].rsplit(" ", 1)[0] + "…"
    return None


def on_page_markdown(markdown, page, config, files):
    if not page.meta.get("description"):
        page.meta["description"] = _riassunto(markdown) or config["site_description"]
    _pagine[page.url] = (page, markdown)
    return markdown


def on_post_build(config):
    sito = config["site_url"].rstrip("/") + "/"
    out = config["site_dir"]
    tutte = sorted(_pagine.values(), key=lambda p: p[0].url)
    it = [p for p in tutte if not p[0].url.startswith("en/")]
    en = [p for p in tutte if p[0].url.startswith("en/")]
    with open(os.path.join(out, "robots.txt"), "w") as f:
        f.write("# Tutti i motori di ricerca e i crawler IA sono benvenuti\n")
        for bot in ("*", "GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"):
            f.write(f"User-agent: {bot}\nAllow: /\n\n")
        f.write(f"Sitemap: {sito}sitemap.xml\n")
    for page, md in tutte:
        if page.url.endswith("/") or not page.url:
            with open(os.path.join(out, page.url, "index.md"), "w") as f:
                f.write(md)
    elenco = lambda pagine: [f"- [{p.title}]({sito}{p.url}): {p.meta['description']}" for p, _ in pagine]
    righe = ["# Corso pratico di llama.cpp / llama.cpp Practical Course", "",
             "> Corso pratico su llama.cpp, dall'installazione alla produzione, in italiano e in inglese. "
             "A hands-on llama.cpp course, from installation to production, in Italian and English.", "",
             "Autore / author: Prof. Giuseppe Bosi (https://www.giuseppebosi.com, LinkedIn https://www.linkedin.com/in/giuseppebosi). "
             "Ogni pagina è disponibile anche in Markdown aggiungendo `index.md` all'indirizzo "
             "(every page is also available as Markdown by appending `index.md` to its URL).", "",
             "## Pagine (italiano)", "", *elenco(it), "",
             "## Pages (English)", "", *elenco(en), "",
             "## Altri corsi dello stesso autore / Other courses by the same author", "",
             "- [Corso JSON & API](https://corso-api-json.giuseppebosi.com/)",
             "- [Costruisci la tua memoria AI (corso RAG)](https://corso-rag.giuseppebosi.com/)", ""]
    with open(os.path.join(out, "llms.txt"), "w") as f:
        f.write("\n".join(righe))
    completo = [righe[0], "", righe[2][2:], ""]
    for page, md in it + en:
        completo += ["", "---", "", f"Fonte / source: {sito}{page.url}", "", md.strip(), ""]
    with open(os.path.join(out, "llms-full.txt"), "w") as f:
        f.write("\n".join(completo))
