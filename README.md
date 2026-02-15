# DrawAgenda

Developer: Jae Yeon Kim and Codex (2026)

This repository provides a small toolchain to turn a tagged research-agenda paragraph into a diagram.

## What is included

- `tools/diagram_demo.html`: client-side interactive demo to edit text, preview Mermaid, and export SVG/PNG.
- `tools/agenda_to_mermaid.py`: Python CLI to parse tagged text and output Mermaid or Graphviz DOT; can also render SVG/PNG.
- `.github/workflows/pages.yml`: GitHub Actions workflow to deploy the browser demo to GitHub Pages.

## Input format (recommended)

Use explicit tags for the most predictable output:

```text
[theme]Interactive Visualization[/theme]
[component time=past]Data collection[/component]
[component time=current]Model development[/component]
[component time=future]Deployment[/component]
[subcomponent of=Model development]Evaluation[/subcomponent]
[relation:enables]Model development->Deployment[/relation:enables]
```

Supported tags:

- `[theme]...[/theme]`: main theme/root node.
- `[component time=past|current|future]...[/component]`: top-level components; `time` places items in lanes.
- `[subcomponent of=Parent]...[/subcomponent]`: nested component under `Parent`.
- `[relation:TYPE]A->B[/relation:TYPE]`: labeled edge from `A` to `B`.

If tags are missing, the parser falls back to simple heuristics (for example, first sentence as theme and comma-separated lists as components). It can also use optional spaCy noun-chunk extraction when available.

## Quick start

Open `tools/diagram_demo.html` in a browser, edit the sample text, then click `Render`.

CLI examples (Python 3.8+):

```bash
python tools/agenda_to_mermaid.py -i input.txt
python tools/agenda_to_mermaid.py -i input.txt -o out.mmd
python tools/agenda_to_mermaid.py -i input.txt -o out.svg --format svg
python tools/agenda_to_mermaid.py -i input.txt -o out.png --format png --engine graphviz
```

Useful options:

- `--format`: `mermaid` (default), `dot`, `svg`, `png`.
- `--engine`: `mermaid` (`mmdc` or `npx`) or `graphviz` (`dot`).
- `--orientation`: `vertical` (`TD` / `TB`) or `horizontal` (`LR`).

## Dependencies

- Required: Python 3.8+.
- Optional for image rendering:
  - Mermaid CLI (`mmdc`) or `npx -y @mermaid-js/mermaid-cli`.
  - Graphviz (`dot`) when using `--engine graphviz`.

## Testing

```bash
python -m unittest tools/tests/test_agenda.py
```

## GitHub Pages

The Pages workflow publishes `tools/diagram_demo.html` as a static site. Static Pages cannot run server-side rendering (`mmdc`/`dot`) on demand.

## Live Demo URL

- Project Pages URL format: `https://<username>.github.io/draw_research_agenda/`
- Example: `https://jaeyeonkim.github.io/draw_research_agenda/`
