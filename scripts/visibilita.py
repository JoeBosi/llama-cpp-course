"""Hook MkDocs per la visibilità: description per pagina, robots.txt, llms.txt, llms-full.txt e .md delle pagine."""
import os
import re

_pagine = []


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
    _pagine.append((page, markdown))
    return markdown


def on_pre_build(config):
    _pagine.clear()


def on_post_build(config):
    sito = config["site_url"].rstrip("/") + "/"
    out = config["site_dir"]
    pagine = sorted(_pagine, key=lambda p: p[0].file.src_uri)
    with open(os.path.join(out, "robots.txt"), "w") as f:
        f.write("# Tutti i motori di ricerca e i crawler IA sono benvenuti\n")
        for bot in ("*", "GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"):
            f.write(f"User-agent: {bot}\nAllow: /\n\n")
        f.write(f"Sitemap: {sito}sitemap.xml\n")
    righe = [f"# {config['site_name']}", "", f"> {config['site_description']}", "",
             "Corso in italiano del Prof. Giuseppe Bosi (https://www.giuseppebosi.com). "
             "Ogni pagina è disponibile anche in Markdown: aggiungere `index.md` all'indirizzo.", "",
             "## Pagine", ""]
    completo = [f"# {config['site_name']}", "", config["site_description"], ""]
    for page, md in pagine:
        righe.append(f"- [{page.title}]({sito}{page.url}): {page.meta['description']}")
        completo += ["", "---", "", f"Fonte: {sito}{page.url}", "", md.strip(), ""]
        dest = os.path.join(out, page.url, "index.md") if page.url.endswith("/") or not page.url else None
        if dest:
            with open(dest, "w") as f:
                f.write(md)
    righe += ["", "## Altri corsi dello stesso autore", "",
              "- [Corso JSON & API](https://corso-api-json.giuseppebosi.com/)",
              "- [Costruisci la tua memoria AI (corso RAG)](https://corso-rag.giuseppebosi.com/)", ""]
    with open(os.path.join(out, "llms.txt"), "w") as f:
        f.write("\n".join(righe))
    with open(os.path.join(out, "llms-full.txt"), "w") as f:
        f.write("\n".join(completo))
