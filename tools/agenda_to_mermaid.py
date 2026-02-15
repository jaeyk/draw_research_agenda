#!/usr/bin/env python3
"""Convert a tagged research-agenda paragraph into Mermaid (and optionally SVG/PNG).

Usage:
  python tools/agenda_to_mermaid.py -i input.txt -o out.mmd --format mermaid
  python tools/agenda_to_mermaid.py -i input.txt -o out.svg --format svg

If --format is svg/png the script will try to call `mmdc` (Mermaid CLI) or fall back to `npx`.
"""
from __future__ import annotations
import re
import argparse
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path


def parse(text: str):
    data = {"theme": None, "components": [], "relations": []}

    theme_match = re.search(r"\[theme(?:\s+[^\]]*)?\]([\s\S]*?)\[/theme\]", text, flags=re.I)
    if theme_match:
        data["theme"] = theme_match.group(1).strip()

    comp_re = re.compile(r"\[component(?:\s+time=(past|current|future))?\]([\s\S]*?)\[/component\]", flags=re.I)
    for m in comp_re.finditer(text):
        time = (m.group(1) or "current").lower()
        data["components"].append({"name": m.group(2).strip(), "time": time})

    sub_re = re.compile(r"\[subcomponent(?:\s+of=([^\]]+))?\]([\s\S]*?)\[/subcomponent\]", flags=re.I)
    for m in sub_re.finditer(text):
        parent = (m.group(1) or None)
        data["components"].append({"name": m.group(2).strip(), "time": "current", "parent": parent})

    rel_re = re.compile(r"\[relation:([^\]]+)\]([\s\S]*?)\[/relation:[^\]]+\]", flags=re.I)
    for m in rel_re.finditer(text):
        typ = m.group(1).strip()
        pair = m.group(2).strip()
        parts = re.split(r"->|→", pair)
        if len(parts) == 2:
            data["relations"].append({"from": parts[0].strip(), "to": parts[1].strip(), "type": typ})

    if not data["theme"]:
        first_sentence = re.split(r"[\.\n]", text, maxsplit=1)[0].strip()
        if first_sentence:
            data["theme"] = first_sentence

    if not data["components"]:
        comp_list = re.search(r"components?:\s*([^\n]*)", text, flags=re.I)
        if comp_list:
            parts = re.split(r"[;,] *", comp_list.group(1))
            for p in parts:
                p = p.strip()
                if p:
                    data["components"].append({"name": p, "time": "current"})
        else:
            # Try spaCy noun-chunk extraction when available for better heuristics
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                doc = nlp(text)
                seen = set()
                for chunk in doc.noun_chunks:
                    name = chunk.text.strip()
                    if len(name) > 1 and name.lower() != (data.get("theme") or "").lower() and name.lower() not in seen:
                        seen.add(name.lower())
                        data["components"].append({"name": name, "time": "current"})
                # keep only a few
                data["components"] = data["components"][:8]
            except Exception:
                remainder = re.sub(r"\[.*?\]", "", text)
                remainder = remainder.replace(data.get("theme") or "", "")
                parts = re.split(r"[;,] ", remainder)
                for p in parts:
                    p = p.strip()
                    if p and len(p) < 60:
                        data["components"].append({"name": p, "time": "current"})

    return data


def id_for(name: str) -> str:
    return "N" + re.sub(r"[^a-z0-9]+", "_", name, flags=re.I)


def to_mermaid(model: dict, orientation: str = "vertical") -> str:
    # orientation: 'vertical' -> TD (top-down), 'horizontal' -> LR (left-right)
    dir_code = "TD" if orientation == "vertical" else "LR"
    lines = [f"graph {dir_code}"]
    lanes = {"past": [], "current": [], "future": []}
    nodes = {}

    for c in model.get("components", []):
        nid = id_for(c["name"]) if "name" in c else id_for(str(c))
        nodes[c["name"]] = nid
        lanes[c.get("time", "current")] .append(f"{nid}[{c['name']}]")

    root = model.get("theme") or "Theme"
    root_id = id_for(root)
    lines.append(f"{root_id}[{root}]")

    if lanes["past"]:
        lines.append("  subgraph Past")
        for l in lanes["past"]:
            lines.append("    " + l)
        lines.append("  end")
    if lanes["current"]:
        lines.append("  subgraph Current")
        for l in lanes["current"]:
            lines.append("    " + l)
        lines.append("  end")
    if lanes["future"]:
        lines.append("  subgraph Future")
        for l in lanes["future"]:
            lines.append("    " + l)
        lines.append("  end")

    for c in model.get("components", []):
        nid = nodes.get(c["name"]) or id_for(c["name"])
        lines.append(f"{root_id} --> {nid}")
        if c.get("parent"):
            pid = nodes.get(c["parent"]) or id_for(c["parent"])
            lines.append(f"{pid} --> {nid}")

    for r in model.get("relations", []):
        frm = nodes.get(r["from"]) or id_for(r["from"])
        to = nodes.get(r["to"]) or id_for(r["to"])
        typ = r.get("type", "")
        lines.append(f"{frm} --|{typ}| {to}")

    return "\n".join(lines)


def to_dot(model: dict, orientation: str = "horizontal") -> str:
    # orientation: 'horizontal'-> rankdir=LR, 'vertical'-> rankdir=TB
    rankdir = "LR" if orientation == "horizontal" else "TB"
    lines = ["digraph G {", f"  rankdir={rankdir};", "  node [shape=box];"]
    lanes = {"past": [], "current": [], "future": []}
    nodes = {}

    for c in model.get("components", []):
        nid = id_for(c["name"]) if "name" in c else id_for(str(c))
        nodes[c["name"]] = nid
        lanes[c.get("time", "current")].append((nid, c["name"]))

    root = model.get("theme") or "Theme"
    root_id = id_for(root)
    lines.append(f'  {root_id} [label="{root}"];')

    def add_cluster(name, items):
        if not items:
            return
        lines.append(f'  subgraph cluster_{name} {{')
        lines.append(f'    label = "{name.title()}";')
        for nid, label in items:
            lines.append(f'    {nid} [label="{label}"];')
        lines.append('  }')

    add_cluster('past', lanes['past'])
    add_cluster('current', lanes['current'])
    add_cluster('future', lanes['future'])

    for c in model.get("components", []):
        nid = nodes.get(c["name"]) or id_for(c["name"])
        lines.append(f'  {root_id} -> {nid};')
        if c.get("parent"):
            pid = nodes.get(c["parent"]) or id_for(c["parent"])
            lines.append(f'  {pid} -> {nid};')

    for r in model.get("relations", []):
        frm = nodes.get(r["from"]) or id_for(r["from"])
        to = nodes.get(r["to"]) or id_for(r["to"])
        typ = r.get("type", "")
        if typ:
            lines.append(f'  {frm} -> {to} [label="{typ}"];')
        else:
            lines.append(f'  {frm} -> {to};')

    lines.append('}')
    return "\n".join(lines)


def find_mmdc() -> tuple[str, list[str]] | None:
    """Return (cmd, base_args) to run mmdc or npx fallback."""
    if shutil.which("mmdc"):
        return ("mmdc", [])
    # try npx fallback
    if shutil.which("npx"):
        return ("npx", ["-y", "@mermaid-js/mermaid-cli", "mmdc"])
    return None


def run_mmdc(input_path: Path, output_path: Path) -> int:
    found = find_mmdc()
    if not found:
        raise RuntimeError("mmdc not found; install @mermaid-js/mermaid-cli or ensure npx is available")
    cmd, pre = found
    if cmd == "mmdc":
        args = [cmd, "-i", str(input_path), "-o", str(output_path)]
    else:
        # npx wrapper: pre + ["-i", input, "-o", output]
        args = [cmd] + pre + ["-i", str(input_path), "-o", str(output_path)]
    print("Running:", " ".join(args), file=sys.stderr)
    res = subprocess.run(args)
    return res.returncode


def find_dot() -> str | None:
    return shutil.which("dot")


def run_dot(input_path: Path, output_path: Path, fmt: str) -> int:
    dot = find_dot()
    if not dot:
        raise RuntimeError("Graphviz 'dot' not found; install graphviz to render DOT to images")
    args = [dot, f"-T{fmt}", str(input_path), "-o", str(output_path)]
    print("Running:", " ".join(args), file=sys.stderr)
    return subprocess.run(args).returncode


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse tagged research agenda and emit Mermaid (or export via mmdc)")
    p.add_argument("-i", "--input", default="-", help="Input file (default stdin)")
    p.add_argument("-o", "--output", default="-", help="Output file (default stdout). For svg/png must be a filename.")
    p.add_argument("--format", choices=["mermaid", "dot", "svg", "png"], default="mermaid")
    p.add_argument("--engine", choices=["mermaid", "graphviz"], default="mermaid", help="Renderer to use for svg/png: 'mermaid' uses mmdc, 'graphviz' uses dot on DOT output")
    p.add_argument("--orientation", choices=["vertical", "horizontal"], default="vertical", help="Diagram orientation: vertical (top-down) or horizontal (left-right)")
    args = p.parse_args(argv)

    if args.input == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.input).read_text(encoding="utf-8")

    model = parse(text)
    mermaid = to_mermaid(model)

    if args.format == "mermaid":
        # respect orientation
        mermaid_text = to_mermaid(model, orientation=args.orientation)
        if args.output == "-":
            sys.stdout.write(mermaid_text + "\n")
        else:
            Path(args.output).write_text(mermaid_text, encoding="utf-8")
        return 0

    if args.format == "dot":
        dot = to_dot(model, orientation=args.orientation if args.engine == 'graphviz' else 'horizontal')
        if args.output == "-":
            sys.stdout.write(dot + "\n")
        else:
            Path(args.output).write_text(dot, encoding="utf-8")
        return 0

    # format is svg or png — require output path
    if args.output == "-":
        print("Error: for svg/png an output filename is required", file=sys.stderr)
        return 2

    # if using graphviz engine, convert to DOT and use dot
    if args.engine == 'graphviz':
        dot_text = to_dot(model, orientation=args.orientation)
        with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False, encoding="utf-8") as tf:
            tf.write(dot_text)
            tmp_name = Path(tf.name)
        try:
            rc = run_dot(tmp_name, Path(args.output), 'svg' if args.format=='svg' else 'png')
            return rc
        finally:
            try:
                tmp_name.unlink()
            except Exception:
                pass

    # default: use mermaid CLI (mmdc / npx)
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8") as tf:
        tf.write(mermaid)
        tmp_name = tf.name

    try:
        rc = run_mmdc(Path(tmp_name), Path(args.output))
        return rc
    finally:
        try:
            Path(tmp_name).unlink()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
