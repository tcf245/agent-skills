---
name: obsidian-llm-wiki-graph
description: Use when the user asks for a diagram of wiki structure, a domain overview, or wants to visualize relationships in the knowledge base. Honors the three-layer view convention from the methodology skill.
type: workflow
triggers:
  - "GRAPH"
  - "draw the wiki"
  - "show me the structure"
  - "visualize relationships"
  - "domain map"
platforms: [cc, codex, gemini]
---

# GRAPH Operation

Produce or refresh diagrams of the wiki structure. Choose the right view layer.

## Three view layers — never confuse them

The methodology skill defines three:

1. **Obsidian Graph View** (built-in, `Cmd+G`) — live, complete, zero maintenance. Do NOT replicate this.
2. **Architecture canvas** (`attachments/diagrams/knowledge-network.canvas`) — curated high-level domain map with entry-point wikilinks. Regenerate when top-level domains change.
3. **Static graph snapshot** (`attachments/diagrams/knowledge-network.png` or `.svg`) — for slide export.

**Default choice**: regenerate the architecture canvas. Static snapshots only when the user explicitly asks for an exportable image.

## Procedure (architecture canvas)

### 1. Read current state
- Read `index.md` to learn the current page set.
- Read the current `knowledge-network.canvas` to understand the existing domain partitioning.

### 2. Decide whether regeneration is needed
- If a top-level domain has been added/removed/renamed since the last canvas update, regenerate.
- If only individual concepts/entities changed within existing domains, do NOT regenerate — Obsidian Graph View handles that layer already.

### 3. Generate
- Use the `diagram-tier-selection` skill — Tier A (JSON Canvas).
- Each domain gets one card: short description plus a few entry-point `[[wikilinks]]` to the most important pages.
- Apply the layout rule: ≥ 150px between any two node boxes that share a labeled edge, or the edge label will clip.

### 4. Save and log
- Write the canvas to `attachments/diagrams/knowledge-network.canvas`.
- Append a `GRAPH` entry to `log.md` noting what changed.

## Static snapshot (only when asked)

- Use Tier C of `diagram-tier-selection` — fireworks-tech-graph on CC, graphviz elsewhere.
- Output both SVG (preferred for clarity) and PNG (for paste-into-slides).
- Save to `attachments/diagrams/knowledge-network.png` / `.svg`.
- For slow rendering, use the `parallel-tasks` skill to spawn a subagent.

## Anti-patterns

- **Enumerating every concept page in the canvas.** That's what Graph View is for. The canvas is for domains.
- **Hand-tuning every node coordinate.** Lay out roughly; the value is in the curation, not the pixel placement.
- **Regenerating on every INGEST.** Wastes time; the domain layer rarely changes per-INGEST.
