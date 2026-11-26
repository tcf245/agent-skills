#!/usr/bin/env python3
"""Check that SKILL.md bodies under skills/ are written in English (FB-078)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})")
STRIP_PATTERNS = (
    re.compile(r"`[^`]*`"),
    re.compile(r'"[^"]*"'),
    re.compile(r"“[^”]*”"),
    re.compile(r"「[^」]*」"),
    re.compile(r"『[^』]*』"),
    re.compile(r"（[^）]*）"),
)
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")

MIN_CJK_CHARS = 8
MAX_ASCII_WORDS_EXEMPT = 3
MIN_VIOLATING_LINES = 3


def check_text(text: str) -> tuple[int, int | None]:
    """Return (violating_line_count, first_violating_line_1_based) for a skill body."""
    lines = text.splitlines()
    idx = 0

    if lines and lines[0].strip() == "---":
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "---":
            idx += 1
        if idx < len(lines):
            idx += 1

    fence_char: str | None = None
    fence_len = 0
    violating_count = 0
    first_line: int | None = None

    for line_no in range(idx + 1, len(lines) + 1):
        line = lines[line_no - 1]
        if fence_char is not None:
            stripped = line.strip()
            if (
                len(stripped) >= fence_len
                and set(stripped) == {fence_char}
            ):
                fence_char = None
                fence_len = 0
            continue

        fence_match = FENCE_OPEN_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            fence_char = marker[0]
            fence_len = len(marker)
            continue

        if not line.strip():
            continue

        cleaned = line
        for pattern in STRIP_PATTERNS:
            cleaned = pattern.sub(" ", cleaned)

        cjk_count = len(CJK_RE.findall(cleaned))
        ascii_word_count = len(ASCII_WORD_RE.findall(cleaned))
        if cjk_count >= MIN_CJK_CHARS and ascii_word_count < MAX_ASCII_WORDS_EXEMPT:
            violating_count += 1
            if first_line is None:
                first_line = line_no

    return violating_count, first_line


def check_file(path: Path) -> tuple[int, int | None]:
    """Read a SKILL.md file and return (violating_line_count, first_line)."""
    return check_text(path.read_text(encoding="utf-8"))


def format_violation(display_path: str, count: int, first_line: int) -> str:
    """Format the actionable FB-078 lint error message."""
    return (
        f"{display_path}: {count} lines of Chinese/Japanese prose "
        f"(first: line {first_line}). Write skill bodies in English; keep "
        "non-English only for trigger phrases, verbatim quotes in quotes, "
        "and examples in backticks or code blocks. (FB-078)"
    )


def iter_skill_files(targets: list[str]) -> list[Path]:
    """Expand directory and file targets into SKILL.md paths."""
    files: list[Path] = []
    for raw in targets:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("SKILL.md")))
        elif path.is_file():
            files.append(path)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        default=["skills"],
        help="Skill files or directories to scan (default: skills)",
    )
    args = parser.parse_args(argv)

    failed = False
    for skill_path in iter_skill_files(args.paths):
        count, first_line = check_file(skill_path)
        if count >= MIN_VIOLATING_LINES and first_line is not None:
            print(format_violation(skill_path.as_posix(), count, first_line))
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
