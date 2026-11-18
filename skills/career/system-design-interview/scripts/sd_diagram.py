#!/usr/bin/env python3
"""
Small SVG helper for system design diagrams (warm cream "Claude Official" style).

Usage:

    import sys; sys.path.insert(0, "<skill_dir>/scripts")
    from sd_diagram import Diagram

    d = Diagram(1400, 930, "Title", "subtitle on the right")
    d.layer_label(365, "Services")
    d.box(580, 325, 240, 80, "teal", "Chat Orchestrator", ("line 1", "line 2"))
    d.arrow([(645, 405), (645, 505)]); d.badge(645, 455, 3)
    d.steps_panel(40, 770, 1320, ["step one", "step two"], columns=2)
    d.save("out.svg", png=True)

Text that does not fit its box is reported on stderr as OVERFLOW; fix it
before saving. PNG export needs `rsvg-convert` on PATH.
"""
from __future__ import annotations

import subprocess
import sys
from xml.sax.saxutils import escape

FONT = "-apple-system, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif"

COLORS = {
    "bg": "#f8f6f3",
    "blue": "#a8c5e6",    # clients, external systems, entry points
    "teal": "#9dd4c7",    # services / processing steps
    "beige": "#f4e4c1",   # infrastructure: gateways, queues
    "gray": "#e8e6e3",    # storage / state
    "red": "#f0b8a8",     # rejection / failure outcomes
    "white": "#ffffff",
    "stroke": "#4a4a4a",
    "text": "#1a1a1a",
    "muted": "#6a6a6a",
    "arrow": "#5a5a5a",
}


def text_width(s: str, size: float) -> float:
    """Rough rendered width: CJK glyphs are square, Latin about 0.56 em."""
    return sum(size if ord(c) > 0x2E80 else size * 0.56 for c in s)


class Diagram:
    def __init__(self, width: int, height: int, title: str, subtitle: str = ""):
        self.w, self.h = width, height
        self.out: list[str] = []
        a = self.out.append
        a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
          f'width="{width}" height="{height}">')
        a(f"<style>text{{font-family:{FONT};}}</style>")
        a('<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" '
          f'orient="auto"><polygon points="0 0, 8 4, 0 8" fill="{COLORS["arrow"]}"/>'
          "</marker></defs>")
        a(f'<rect width="{width}" height="{height}" fill="{COLORS["bg"]}"/>')
        self.text(40, 40, title, 22, weight=700, anchor="start")
        if subtitle:
            self.text(width - 40, 40, subtitle, 13, COLORS["muted"], anchor="end")

    # --- primitives ---------------------------------------------------------

    def raw(self, svg: str) -> None:
        self.out.append(svg)

    def text(self, x, y, s, size=13, fill=None, weight=400, anchor="middle") -> None:
        self.out.append(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill or COLORS["text"]}">{escape(s)}</text>'
        )

    def _check(self, s: str, size: float, limit: float) -> None:
        if text_width(s, size) > limit:
            print(f"OVERFLOW: {s!r} needs {text_width(s, size):.0f}px, has {limit:.0f}px",
                  file=sys.stderr)

    def box(self, x, y, w, h, fill, title, subs=(), size=15) -> None:
        """Rounded node: bold title plus up to three muted sub-lines."""
        self.out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" ry="12" '
            f'fill="{COLORS[fill]}" stroke="{COLORS["stroke"]}" stroke-width="2"/>'
        )
        line_h = 17
        y0 = y + (h - (size + len(subs) * line_h)) / 2 + size - 2
        self._check(title, size, w - 12)
        self.text(x + w / 2, y0, title, size, weight=600)
        for i, s in enumerate(subs):
            self._check(s, 12, w - 12)
            self.text(x + w / 2, y0 + (i + 1) * line_h, s, 12, COLORS["muted"])

    def diamond(self, cx, cy, w, h, lines, size=13) -> None:
        """Decision node centred on (cx, cy). Keep text within the middle half."""
        self.out.append(
            f'<polygon points="{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} '
            f'{cx - w / 2},{cy}" fill="{COLORS["white"]}" stroke="{COLORS["stroke"]}" '
            'stroke-width="2"/>'
        )
        n = len(lines)
        for i, s in enumerate(lines):
            self._check(s, size, w * 0.62)
            self.text(cx, cy + 5 + (i - (n - 1) / 2) * 17, s, size, weight=600)

    def arrow(self, points, dash: str | None = None, head: bool = True) -> None:
        """Orthogonal polyline through `points`. Start and end on box edges."""
        d = "M " + " L ".join(f"{x},{y}" for x, y in points)
        self.out.append(
            f'<path d="{d}" fill="none" stroke="{COLORS["arrow"]}" stroke-width="2"'
            + (f' stroke-dasharray="{dash}"' if dash else "")
            + (' marker-end="url(#ar)"' if head else "")
            + "/>"
        )

    def badge(self, x, y, n) -> None:
        """Numbered step marker placed on an arrow."""
        self.out.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{COLORS["text"]}"/>')
        self.text(x, y + 4.5, str(n), 12, COLORS["white"], 700)

    def label(self, x, y, s, size=12) -> None:
        """Arrow label with a background so the line does not strike through it."""
        w = text_width(s, size) + 10
        self.out.append(
            f'<rect x="{x - w / 2}" y="{y - size}" width="{w}" height="{size + 6}" rx="3" '
            f'fill="{COLORS["bg"]}" opacity="0.96"/>'
        )
        self.text(x, y, s, size, COLORS["arrow"], 600)

    # --- composites ---------------------------------------------------------

    def layer_label(self, y, name, x=22) -> None:
        self.text(x, y, name, 12, COLORS["muted"], 600, "start")

    def panel(self, x, y, w, h) -> None:
        self.out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{COLORS["white"]}" stroke="{COLORS["stroke"]}" stroke-width="1.5"/>'
        )

    def steps_panel(self, x, y, w, steps, columns=2, row_h=27) -> None:
        """White panel listing numbered steps that match the badges."""
        rows = -(-len(steps) // columns)
        self.panel(x, y, w, rows * row_h + 27)
        col_w = (w - 60) / columns
        for i, s in enumerate(steps):
            col, row = divmod(i, rows)
            bx, by = x + 30 + col * col_w, y + 30 + row * row_h
            self._check(s, 13.5, col_w - 40)
            self.badge(bx, by - 4, i + 1)
            self.text(bx + 22, by, s, 13.5, anchor="start")

    def text_panel(self, x, y, w, rows, size=12.5) -> None:
        """White panel of lines. `rows` is a list of (text, is_heading); '' adds a gap."""
        height = 28 + sum(20 if t else 8 for t, _ in rows) + 10
        self.panel(x, y, w, height)
        cy = y + 28
        for t, heading in rows:
            if t:
                self._check(t, size, w - 30)
                self.text(x + 18, cy, t, size, COLORS["text"] if heading else COLORS["muted"],
                          700 if heading else 400, "start")
            cy += 20 if t else 8

    def legend(self, x, y, items) -> None:
        """`items` is a list of (label, dash-or-None)."""
        for i, (name, dash) in enumerate(items):
            ly = y + i * 23
            self.out.append(
                f'<line x1="{x}" y1="{ly}" x2="{x + 40}" y2="{ly}" stroke="{COLORS["arrow"]}" '
                'stroke-width="2"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
            )
            self.text(x + 50, ly + 4, name, 12, COLORS["muted"], anchor="start")

    # --- output -------------------------------------------------------------

    def save(self, path: str, png: bool = False, png_width: int = 1920) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.out + ["</svg>"]))
        if png:
            target = path.rsplit(".", 1)[0] + ".png"
            subprocess.run(["rsvg-convert", "-w", str(png_width), path, "-o", target], check=True)
