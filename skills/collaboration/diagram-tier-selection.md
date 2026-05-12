---
name: diagram-tier-selection
description: Use whenever you need to produce a diagram. Three tiers — Obsidian JSON Canvas / inline Mermaid / polished renderer — chosen by audience and purpose.
type: behavior
triggers:
  - "draw a diagram"
  - "visualize this"
  - "make an architecture diagram"
  - "show me a flowchart"
  - "diagram"
platforms: [cc, codex, gemini]
---

# Diagram Tier Selection

Pick the tool by purpose, not habit. Three tiers cover almost everything.

## Tier A — JSON Canvas (Obsidian-native)

**Use when**: the diagram lives inside an Obsidian vault and maps the vault's own concept graph or structure — things that evolve with the knowledge base.

- Format: hand-written `.canvas` JSON
- Examples: `knowledge-network.canvas` (top-level domain map), per-domain concept clusters, exploration boards
- **Why**: Canvas is editable in Obsidian (drag/drop, recolor); every node can embed a real wiki page (clickable preview); diff-friendly JSON
- **Path**: `attachments/diagrams/*.canvas` inside the vault

**Layout rule**: keep ≥ 150px between node boxes that share a labeled edge. Shorter gaps clip the edge label text — found by trial after several illegible canvases.

## Tier B — Mermaid (inline default)

**Use when**: simple structural diagram (3–4 components), or the primary audience is the agent itself (helping you understand a sequence, workflow, dependency, state machine).

- Format: ` ```mermaid ... ``` ` fenced block inline in markdown
- Examples: quick flowcharts, sequence diagrams, simple architecture sketches, decision trees
- **Why**: zero overhead — pure text, GitHub & Obsidian both render natively, no file artifact to maintain
- **No file artifact** — lives inline in the doc

## Tier C — Polished renderer (human-facing)

**Use when**: diagram is for **human consumption with high visual quality** — README hero diagrams, presentation slides, complex production architecture, or the user asks for "a nice diagram".

- On Claude Code: prefer `fireworks-tech-graph` skill (default style: "Style 6 — Claude Official", warm cream `#f8f6f3`)
- On Codex / Gemini / wherever fireworks is unavailable: fall back to `graphviz` (`dot` CLI) emitting SVG, then `rsvg-convert` to PNG for embedding
- Output: SVG + PNG
- **Cost**: slow to generate. Use the `parallel-tasks` skill — spawn a subagent (CC) or a parallel session if you have 2+ diagrams to produce

## Cheatsheet

| Use case | Tier |
|---|---|
| Obsidian wiki concept map / domain overview | A — Canvas |
| Sequence/workflow/state to help the agent understand | B — Mermaid |
| 3–4 boxes, quick flowchart, no need for polish | B — Mermaid |
| README hero diagram, slide export, polished production diagram | C — fireworks (CC) / graphviz (elsewhere) |
| User says "draw it as X" | Honor the explicit request |

## Anti-patterns

- **Using Tier C for a 3-box flowchart.** Wastes time; Mermaid is faster and looks fine.
- **Using Tier B for an Obsidian knowledge map.** Loses the live, navigable Canvas affordances.
- **Hand-tuning Canvas coordinates pixel-by-pixel.** Lay it out roughly, then move on; perfectionism here doesn't pay.
