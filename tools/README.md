# Research Agenda → Diagram tool (tools)

This folder contains a small client-side demo and a Python CLI to convert a tagged research-agenda paragraph into a Mermaid diagram.

Files
- `diagram_demo.html` — browser demo: edit a tagged paragraph, see generated Mermaid and a live rendered diagram, download SVG/PNG.
- `agenda_to_mermaid.py` — Python CLI: parse input, emit Mermaid, optionally call `mmdc` to export SVG/PNG.

Quick demo

Open `tools/diagram_demo.html` in a browser (double-click or serve via a static file server). Edit the example paragraph and click Render. Use Download SVG/PNG to export.

Orientation

The demo and CLI support choosing diagram orientation:
- Vertical (top-down) — Mermaid uses `graph TD`, Graphviz uses `rankdir=TB`.
- Horizontal (left-right) — Mermaid uses `graph LR`, Graphviz uses `rankdir=LR`.

CLI option: `--orientation vertical|horizontal`.

Python CLI

Requirements:
- Python 3.8+
- Optional: `mmdc` (Mermaid CLI) for SVG/PNG export. Install with `npm install -g @mermaid-js/mermaid-cli` or use `npx`.

Usage examples:

Render Mermaid to stdout:

```bash
python tools/agenda_to_mermaid.py -i "[theme]Interactive Visualization[/theme] [component time=current]Model development[/component]"
```

Write Mermaid to a file:

```bash
python tools/agenda_to_mermaid.py -i input.txt -o output.mmd
```

Export SVG (requires `mmdc` or `npx`):

```bash
python tools/agenda_to_mermaid.py -i input.txt -o diagram.svg --format svg
```

If `mmdc` is not found, the script will try to run `npx -y @mermaid-js/mermaid-cli` as a fallback.

Tagging syntax

Supported tags (case-insensitive):
- `[theme]...[/theme]` — main theme (root node)
- `[component time=past|current|future]...[/component]` — components (time places them in swimlanes)
- `[subcomponent of=Parent]...[/subcomponent]` — subcomponent under `Parent`
- `[relation:TYPE]A->B[/relation:TYPE]` — labeled edge from A to B

If tags are not present, the script tries simple heuristics (first sentence as theme, comma-lists as components).

See the demo HTML for examples and test inputs.
