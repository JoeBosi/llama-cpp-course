# llama.cpp Practical Course (Italian)

🇬🇧 English · 🇮🇹 [Italiano](README.it.md)

A hands-on course, written in Italian, on [llama.cpp](https://github.com/ggml-org/llama.cpp): installation on every
platform, everyday use, models and quantization, server and OpenAI-compatible API, performance, structured output,
multimodal models, embedding into C and Python programs, and production deployment, with labs and final projects.

**Live site:** https://corso-llamacpp.giuseppebosi.com/ (free and open, also available as
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

Course text and diagrams: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Lab code: MIT.
llama.cpp is an MIT project by ggml-org; this course is not affiliated with it.

## Author

Giuseppe Bosi, Teacher of Computer Science and Technology (EQF 7) ·
[www.giuseppebosi.com](https://www.giuseppebosi.com) · [LinkedIn](https://www.linkedin.com/in/giuseppebosi)
