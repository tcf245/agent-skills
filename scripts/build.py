#!/usr/bin/env python3
"""
Build dist/AGENTS.md and dist/GEMINI.md from skills/ and vendored/.

Scans every .md file with a YAML frontmatter block (delimited by ---),
extracts name/description/type/triggers/platforms, and emits an index
that downstream agents (Codex / Gemini CLI) can read.

Always-on behaviors (triggers includes "always-on") are inlined into
the index, not listed as read-on-demand.

Output is deterministic — same inputs produce byte-identical output so
`git diff dist/` is meaningful in CI.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- File discovery ---------------------------------------------------------

SKILL_FILE_RULES = [
    # (glob, skip-if-name-matches)
    ("skills/**/*.md", {"_schema.md", "README.md", "config.example.yml"}),
    ("vendored/*.md", {"README.md"}),
]

# Multi-file skills use SKILL.md at the top of their dir. The above glob
# already matches `**/SKILL.md`, so no special-casing needed.


def discover_files() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pattern, skips in SKILL_FILE_RULES:
        for f in sorted(REPO_ROOT.glob(pattern)):
            if f.name in skips:
                continue
            if "references" in f.relative_to(REPO_ROOT).parts:
                continue
            if f in seen:
                continue
            seen.add(f)
            out.append(f)
    return out


# --- Frontmatter parser -----------------------------------------------------

FRONTMATTER_RE = re.compile(
    r"^(?:\s*<!--.*?-->\s*\n+)*---\s*\n(.*?)\n---\s*\n", re.DOTALL
)


def parse_frontmatter(content: str) -> dict | None:
    """Tiny YAML subset parser. Supports:
       - key: value
       - key: | or >- (multi-line block scalar)
       - key: [a, b, c]
       - key:\n  - a\n  - b
    """
    m = FRONTMATTER_RE.match(content)
    if not m:
        return None
    body = m.group(1)
    result: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        # Top-level key
        m_kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m_kv:
            i += 1
            continue
        key, raw = m_kv.group(1), m_kv.group(2).strip()
        # Block scalars: `|` preserves newlines, `>` / `>-` folds to spaces.
        if raw in {"|", "|-", ">", ">-"}:
            block_lines = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                block_lines.append(lines[i][2:] if lines[i].startswith("  ") else "")
                i += 1
            if raw.startswith(">"):
                result[key] = " ".join(line.strip() for line in block_lines).strip()
            else:
                result[key] = "\n".join(block_lines).strip()
            continue
        # Inline list `[a, b]`
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            result[key] = [s.strip().strip("\"'") for s in inner.split(",") if s.strip()] if inner else []
            i += 1
            continue
        # Empty -> following block list
        if raw == "":
            items = []
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("-"):
                item = lines[i].strip()[1:].strip().strip("\"'")
                items.append(item)
                i += 1
            result[key] = items
            continue
        # Scalar value (strip surrounding quotes)
        result[key] = raw.strip("\"'")
        i += 1
    return result


# --- Skill record -----------------------------------------------------------

class Skill:
    def __init__(self, path: Path, fm: dict):
        self.path = path
        self.rel_path = path.relative_to(REPO_ROOT).as_posix()
        self.name = fm.get("name") or path.stem
        self.description = (fm.get("description") or "").replace("\n", " ").strip()
        self.type = fm.get("type", "workflow")
        triggers = fm.get("triggers") or []
        if isinstance(triggers, str):
            triggers = [triggers]
        self.triggers = triggers
        platforms = fm.get("platforms") or ["cc", "codex", "gemini"]
        if isinstance(platforms, str):
            platforms = [platforms]
        self.platforms = platforms
        self.is_vendored = self.rel_path.startswith("vendored/")
        self.always_on = "always-on" in [t.lower() for t in self.triggers]

    @property
    def category(self) -> str:
        parts = self.rel_path.split("/")
        if self.is_vendored:
            return "vendored"
        # skills/<category>/...
        return parts[1] if len(parts) >= 3 else "misc"

    @property
    def short_triggers(self) -> str:
        if not self.triggers:
            return "(see description)"
        non_always = [t for t in self.triggers if t.lower() != "always-on"]
        if not non_always:
            return "always-on"
        return ", ".join(f'"{t}"' for t in non_always)


def load_all_skills() -> list[Skill]:
    skills: list[Skill] = []
    for f in discover_files():
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[skip] {f}: {e}", file=sys.stderr)
            continue
        fm = parse_frontmatter(content)
        if fm is None:
            print(f"[skip] {f}: no frontmatter", file=sys.stderr)
            continue
        skills.append(Skill(f, fm))
    return skills


# --- Output generation ------------------------------------------------------

CATEGORY_ORDER = [
    "coding",
    "collaboration",
    "communication",
    "context",
    "language",
    "wiki",
    "obsidian-llm-wiki",
    "diagram",
    "media",
    "vendored",
]
CATEGORY_TITLES = {
    "coding": "Coding workflows",
    "collaboration": "Collaboration patterns",
    "communication": "Communication habits",
    "context": "Personal context",
    "language": "Language learning",
    "wiki": "LLM Wiki",
    "obsidian-llm-wiki": "Obsidian LLM Wiki",
    "diagram": "Diagrams",
    "media": "Media",
    "vendored": "Vendored third-party (non-CC platforms only)",
}


PLATFORM_FILENAMES = {
    "cc": "CLAUDE.md",
    "codex": "AGENTS.md",
    "gemini": "GEMINI.md",
}


def render_index(skills: list[Skill], platform: str, *, repo_url: str) -> str:
    """Build the per-platform index content.

    `platform` is one of: cc, codex, gemini.
    """
    out: list[str] = []
    title = PLATFORM_FILENAMES[platform]
    out.append(f"# Eric's Agent Skills — {title}")
    out.append("")
    out.append("> This file is auto-generated by `scripts/build.py`. Do not edit by hand.")
    out.append(f"> Source: {repo_url}")
    out.append(f"> Generated for platform: `{platform}`")
    out.append("")
    out.append("## How to use this file")
    out.append("")
    out.append("Behaviors below are split into two layers:")
    out.append("")
    out.append("1. **Always-on rules** — these apply to every response. Read once and internalize.")
    out.append("2. **Triggered skills** — when you see a trigger condition (a slash command, a phrase, a task type), **read the listed skill file with your file-read tool BEFORE responding**, then follow it.")
    out.append("")
    out.append("Do not paraphrase the rules from memory. Read the skill file fresh each time — they may have been updated.")
    out.append("")

    # Filter to platform
    visible = [s for s in skills if platform in s.platforms]
    if platform == "cc":
        # Vendored snapshots are for non-CC platforms only: Claude Code installs the upstream plugin instead,
        # and listing both gives the model two copies of the same rules.
        visible = [s for s in visible if s.category != "vendored"]

    # Always-on rules
    always_on = [s for s in visible if s.always_on]
    if always_on:
        out.append("## Always-on rules")
        out.append("")
        for s in always_on:
            out.append(f"- **{s.name}** — {s.description}")
            out.append(f"  Full content: `{s.rel_path}`")
        out.append("")

    # Triggered skills, grouped by category
    triggered = [s for s in visible if not s.always_on]
    by_cat: dict[str, list[Skill]] = {}
    for s in triggered:
        by_cat.setdefault(s.category, []).append(s)

    out.append("## Triggered skills")
    out.append("")
    cats_seen = []
    for cat in CATEGORY_ORDER:
        if cat not in by_cat:
            continue
        cats_seen.append(cat)
        out.append(f"### {CATEGORY_TITLES.get(cat, cat.title())}")
        out.append("")
        for s in sorted(by_cat[cat], key=lambda x: x.name):
            out.append(f"- `{s.rel_path}`")
            out.append(f"  - **name**: {s.name}")
            out.append(f"  - **triggers**: {s.short_triggers}")
            out.append(f"  - **summary**: {s.description}")
        out.append("")
    # Any leftover categories not in CATEGORY_ORDER
    for cat in sorted(by_cat):
        if cat in cats_seen:
            continue
        out.append(f"### {cat.title()}")
        out.append("")
        for s in sorted(by_cat[cat], key=lambda x: x.name):
            out.append(f"- `{s.rel_path}`")
            out.append(f"  - **name**: {s.name}")
            out.append(f"  - **triggers**: {s.short_triggers}")
            out.append(f"  - **summary**: {s.description}")
        out.append("")

    out.append("## Maintenance")
    out.append("")
    out.append("If a trigger seems to apply but the corresponding skill file is missing, report the broken pointer to the user — do not silently skip it.")
    out.append("")
    return "\n".join(out)


# --- Main -------------------------------------------------------------------

def main() -> int:
    repo_url = "https://github.com/tcf245/agent-skills"
    dist = REPO_ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    skills = load_all_skills()
    print(f"[build] discovered {len(skills)} skill(s)")

    claude_md = render_index(skills, "cc", repo_url=repo_url)
    agents_md = render_index(skills, "codex", repo_url=repo_url)
    gemini_md = render_index(skills, "gemini", repo_url=repo_url)

    (dist / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
    (dist / "AGENTS.md").write_text(agents_md, encoding="utf-8")
    (dist / "GEMINI.md").write_text(gemini_md, encoding="utf-8")
    print(f"[build] wrote dist/CLAUDE.md ({len(claude_md)} bytes)")
    print(f"[build] wrote dist/AGENTS.md ({len(agents_md)} bytes)")
    print(f"[build] wrote dist/GEMINI.md ({len(gemini_md)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
