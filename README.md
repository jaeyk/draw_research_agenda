Input: prefer keywords/tags
Input format (preferred — use tags)
----------------------------------
For the most reliable and predictable results prefer annotating your paragraph using the supported tags/keywords. Tags are explicit, easy to read, and make the generated diagram predictable.

Example (preferred — use these tags in your paragraph):

```
[theme]Interactive Visualization[/theme]
[component time=past]Data collection[/component] [component time=current]Model development[/component] [component time=future]Deployment[/component]
[subcomponent of=Model development]Evaluation[/subcomponent]
[relation:enables]Model development->Deployment[/relation:enables]
```

# draw_research_agenda

Overview
--------
This repository contains a small research-agenda -> diagram toolchain:

- `tools/diagram_demo.html` — client-side interactive demo (edit tagged paragraph, preview Mermaid diagram, download SVG/PNG).
- `tools/agenda_to_mermaid.py` — Python CLI to parse tagged paragraphs and emit Mermaid or DOT, and optionally render SVG/PNG via Mermaid CLI (`mmdc`) or Graphviz (`dot`).
- `.github/workflows/pages.yml` — GitHub Actions workflow that deploys the demo to GitHub Pages.

Design choices
--------------
- Input format: flexible tagged paragraphs. Tags supported: `[theme]`, `[component time=...]`, `[subcomponent of=..]`, `[relation:TYPE]`.
- Parser: simple deterministic tag parsing with heuristics fallback. When explicit tags are missing the tool attempts heuristics:
	- Look for "components:" lists and comma-separated items.
	- Optional spaCy noun-chunk extraction (if `spacy` and `en_core_web_sm` are available) for better component suggestions.
- Graph model: `theme` becomes root node; `component` nodes attach to the theme; `subcomponent` can set a parent; `relation` creates labeled edges.
- Output formats: Mermaid (text) and Graphviz DOT. Mermaid is the recommended default for ease of use; Graphviz (DOT) is available for alternative layouts and server-side rendering.
- Orientation/timeline: support for horizontal/vertical orientation and time lanes (past/current/future). Mermaid uses `graph TD`/`graph LR` and DOT uses `rankdir=TB`/`LR` with clusters for time lanes.

Why these choices
-----------------
- Mermaid is simple to read and embed (README, GitHub). It enables quick iteration and client-side rendering in modern browsers.
- DOT/Graphviz provides stronger layout control when you need more precise rendering or server-side export to raster formats.
- Tags keep user control simple and avoid brittle NLP-only parsing; heuristics + optional spaCy provide helpful defaults.

Quick start
-----------
1. Open the demo: open `tools/diagram_demo.html` in a browser (double-click or serve the repository). Edit the example paragraph and click Render. Use Download SVG/PNG to export.
2. CLI (Python 3.8+):

```bash
python tools/agenda_to_mermaid.py -i input.txt            # prints Mermaid to stdout
python tools/agenda_to_mermaid.py -i input.txt -o out.mmd # writes Mermaid file
python tools/agenda_to_mermaid.py -i input.txt -o out.svg --format svg # uses mmdc or npx
python tools/agenda_to_mermaid.py -i input.txt -o out.png --format png --engine graphviz # uses dot
```

Options of note:
- `--format`: `mermaid` (default), `dot`, `svg`, `png`.
- `--engine`: `mermaid` (uses `mmdc` / `npx`) or `graphviz` (uses `dot` for rendering DOT).
- `--orientation`: `vertical` (top-down) or `horizontal` (left-right).

Build & deploy (GitHub Pages)
-----------------------------
This repository includes a workflow at `.github/workflows/pages.yml` that copies `tools/diagram_demo.html` into a `site/` directory and deploys it to GitHub Pages on pushes to `main`.

To manually test the site build locally:

```bash
mkdir -p site
cp tools/diagram_demo.html site/index.html
# Then serve `site/` with a static server (e.g., `python -m http.server 8000` in the `site` folder)
```

Notes about Pages and server-side features
- GitHub Pages hosts static assets only; server-side rendering (running `mmdc` or `dot`) requires a server and cannot run on Pages.
- If you want a hosted Python-backed demo (able to run `mmdc` or Graphviz on-demand), consider deploying a Streamlit/Gradio app on Hugging Face Spaces or a small cloud VM/container.

Testing
-------
Unit tests are included in `tools/tests/test_agenda.py`. Run them with:

```bash
python -m unittest tools/tests/test_agenda.py
```

Contributing / Next steps
-------------------------
- Improve parser with better NLP heuristics or optional LLM parsing for ambiguous inputs.
- Add UI to edit parsed nodes before rendering (client or server-side) for corrective feedback.
- Add CI integration to run `mmdc` or `dot` if needed for artifacts (note: CI runners may need `npm`/Graphviz installed).

Contact
-------
If you'd like help deploying to Hugging Face Spaces or adding server-side rendering, tell me which option and I will scaffold it.