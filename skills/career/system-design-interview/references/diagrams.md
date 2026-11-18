# Diagrams

Two polished diagrams per design, built with `scripts/sd_diagram.py`, plus inline Mermaid for state machines and sequences. The style is the warm cream palette Eric uses for human-facing diagrams.

## Procedure

1. Write a short Python script in the temp directory that imports `Diagram` and builds both diagrams.
2. Run it. Fix every `OVERFLOW` line printed on stderr (shorten the text or widen the box).
3. Open each PNG and look at it. Check the list under "Mistakes to look for".
4. Copy the `.svg` and `.png` files to `attachments/diagrams/` in the vault.

## API

```python
from sd_diagram import Diagram

d = Diagram(width, height, "Title", "subtitle")
d.layer_label(y, "Services")                         # muted label at the left edge
d.box(x, y, w, h, fill, "Title", ("sub 1", "sub 2")) # fill: blue teal beige gray red white
d.diamond(cx, cy, w, h, ["line 1", "line 2"])        # decision node
d.arrow([(x1, y1), (x2, y2), ...], dash="5,3")       # orthogonal polyline, arrowhead at the end
d.badge(x, y, 3)                                     # numbered marker on an arrow
d.label(x, y, "outbox")                              # arrow label with background
d.steps_panel(x, y, w, ["step 1", ...], columns=2)   # legend for the badges
d.text_panel(x, y, w, [("Heading", True), ("line", False), ("", False)])
d.legend(x, y, [("同步调用", None), ("异步修正", "5,3")])
d.save("name.svg", png=True)
```

Colour meaning: `blue` clients and external systems, `teal` services and processing steps, `beige` gateways and queues, `gray` storage, `red` rejection and failure outcomes.

## Architecture diagram

Canvas about 1400 × 930. Rows from top to bottom, about 160 px apart:

| Row | Contents | Typical box |
|---|---|---|
| Client | browser or caller | 200 × 56 |
| Edge | gateways | 300 × 66 |
| Services | one box per service; the orchestrating one in the middle | 180–240 × 80 |
| State | the store each service owns, directly below it | 180–220 × 80 |
| Async | queue, consumers, ledger | 200–240 × 70 |

- Put each store under the service that owns it so ownership reads as a vertical line.
- Mark the single-request path with badges ①–⑧ and explain them in a `steps_panel` across the bottom. Prefer badges over text labels on short arrows.
- Each box: a name plus one or two lines of concrete detail (technology, key rule), not a restatement of the name.
- Use a dashed arrow for asynchronous correction paths, and add a `legend`.

## Core mechanism diagram

Canvas about 1280 × 1040. A top-to-bottom flow in the left column (boxes 360 wide, about 100 px pitch), outcome boxes in a second column to the right, and a `text_panel` on the far right that states:

- the quantity being tracked, drawn as a segmented bar if it is a budget;
- the invariant;
- the bounds, each as a formula;
- a worked example with numbers.

Loops go out to the right column and return to the box they re-enter.

## Mermaid

Use fenced `mermaid` blocks in the page for:

- `stateDiagram-v2` for entity lifecycles;
- `sequenceDiagram` for the reconnect or recovery path.

Mermaid cannot be render-checked from the command line here. Keep the syntax plain, and say in the final report that these were not visually verified.

## Mistakes to look for

- A vertical arrow that passes through a box or a badge in another row. Reroute it around the outside of the row, or move the target box.
- Two arrows crossing. Rearrange boxes first; crossings are almost always avoidable.
- An arrow ending at a box corner or floating short of the edge.
- A label sitting on top of a line junction.
- Text touching the box border.
- A badge number that has no entry in the steps panel, or the reverse.
