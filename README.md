# llama.cpp Course: Run Local LLMs from Install to Production

🇬🇧 English · 🇮🇹 [Italiano](README.it.md)

**A free, hands-on llama.cpp course and tutorial for running local LLMs on your own machine**, in English and Italian:
install llama.cpp on Windows, macOS, Linux and Android, pick and quantize GGUF models, serve an OpenAI-compatible API,
tune CPU/GPU performance, get structured JSON output, build a local RAG chatbot in Python and C, and deploy to production.
Includes step-by-step labs and final projects.

**Live course:** https://corso-llamacpp.giuseppebosi.com/en/ (English) · https://corso-llamacpp.giuseppebosi.com/ (Italian) (free and open, also available as
[llms.txt](https://corso-llamacpp.giuseppebosi.com/llms.txt) for AI assistants)

## Structure

- `corso/`: all course content in Markdown (MkDocs `docs_dir`)
  - `moduli/`: lessons · `laboratori/`: labs with scripts · `progetti-finali/`: final projects · `risorse/`: glossary, models, links
  - `assets/img/`: SVG diagrams (Mermaid diagrams are inline in the pages)
- `overrides/`: theme override (Open Graph, JSON-LD)
- `scripts/`: build helpers (`pubblica.sh` publishes, `visibilita.py` writes robots.txt, llms.txt and per-page Markdown)
- `redazione/`, `templates/`: authoring notes and page templates (Italian)
- `mkdocs.yml`: site configuration (MkDocs Material, light theme by default with dark toggle)

Navigation is automatic (`awesome-nav`): page title = first `#` heading, order = file name.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=$PWD .venv/bin/mkdocs serve -a 127.0.0.1:8000
```

`PYTHONPATH` is needed by `scripts/mermaid_fence.py`. Build with `mkdocs build --strict`.

## License

Course text and diagrams: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Lab code: MIT.
llama.cpp is an MIT project by ggml-org; this course is not affiliated with it.

## Author

Giuseppe Bosi, Master's-level degree in Electronic Engineering (5-year Italian Laurea, pre-reform, EQF level 7),
Teacher of Computer Science and Technology (EQF 7) ·
[www.giuseppebosi.com](https://www.giuseppebosi.com) · [LinkedIn](https://www.linkedin.com/in/giuseppebosi)
