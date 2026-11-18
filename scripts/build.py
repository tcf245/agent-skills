#!/usr/bin/env python3
"""
Build minimal dist/CLAUDE.md, dist/AGENTS.md, and dist/GEMINI.md blocks from skills/.

Scans every native skill directory (`skills/<category>/<name>/SKILL.md`),
validates frontmatter (`name` and `description`), and emits a minimal block
containing only always-on rules (`triggers` includes "always-on") plus a
one-line pointer to native skill discovery under `~/.agents/skills`.

Output is deterministic — pass `--check` to verify `dist/` is in sync.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def discover_files() -> list[Path]:
    return sorted(REPO_ROOT.glob("skills/*/*/SKILL.md"))


FRONTMATTER_RE = re.compile(
    r"^(?:\s*<!--.*?-->\s*\n+)*---\s*\n(.*?)\n---\s*\n", re.DOTALL
)


def parse_frontmatter(content: str) -> dict | None:
    """Tiny YAML subset parser."""
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
        m_kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m_kv:
            i += 1
            continue
        key, raw = m_kv.group(1), m_kv.group(2).strip()
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
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            result[key] = [s.strip().strip("\"'") for s in inner.split(",") if s.strip()] if inner else []
            i += 1
            continue
        if raw == "":
            items = []
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("-"):
                item = lines[i].strip()[1:].strip().strip("\"'")
                items.append(item)
                i += 1
            result[key] = items
            continue
        result[key] = raw.strip("\"'")
        i += 1
    return result


class Skill:
    def __init__(self, path: Path, fm: dict):
        self.path = path
        self.rel_path = path.relative_to(REPO_ROOT).as_posix()
        self.name = fm.get("name") or path.parent.name
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
        self.always_on = "always-on" in [t.lower() for t in self.triggers]


def load_all_skills() -> list[Skill]:
    skills: list[Skill] = []
    for f in discover_files():
        content = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if fm is None:
            raise ValueError(f"{f}: missing YAML frontmatter")
        if not fm.get("name") or not fm.get("description"):
            raise ValueError(f"{f}: frontmatter must include 'name' and 'description'")
        if fm["name"] != f.parent.name:
            raise ValueError(f"{f}: frontmatter name '{fm['name']}' does not match dir '{f.parent.name}'")
        skills.append(Skill(f, fm))
    return skills


PLATFORM_FILENAMES = {
    "cc": "CLAUDE.md",
    "codex": "AGENTS.md",
    "gemini": "GEMINI.md",
}


def render_block(skills: list[Skill], platform: str) -> str:
    """Build the minimal always-on block for a platform."""
    visible = [s for s in skills if platform in s.platforms and s.always_on]
    out: list[str] = []
    for s in visible:
        out.append(f"- **{s.name}** — {s.description}")
        out.append(f"  Full rules: `~/.agents/skills/{s.name}/SKILL.md`")
    if out:
        out.append("")
    out.append("Skills are installed natively from ~/workspace/agent-skills (see ~/.agents/skills); no index here.")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    dist = REPO_ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    skills = load_all_skills()
    print(f"[build] discovered {len(skills)} skill(s)")

    for platform, filename in PLATFORM_FILENAMES.items():
        rendered = render_block(skills, platform)
        target = dist / filename
        if check_only:
            if not target.exists() or target.read_text(encoding="utf-8") != rendered:
                print(f"[build] ERROR: dist/{filename} is out of sync", file=sys.stderr)
                return 1
        else:
            target.write_text(rendered, encoding="utf-8")
            print(f"[build] wrote dist/{filename} ({len(rendered)} bytes)")

    if check_only:
        print("[build] dist/ is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
