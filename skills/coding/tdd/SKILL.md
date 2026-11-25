---
name: tdd
description: Use when fixing a bug or changing behavior, to decide whether to write a failing test first and what evidence the final reply must show.
type: workflow
platforms: [cc, codex, gemini]
---

# Pragmatic TDD

Decide when to write a failing test before fixing a bug (replaces "always write a failing test first", Eric 2026-11-25, FB-066). Write one first **only** when the user explicitly asks for TDD, a failing test, or a regression test, OR when the bug has an obvious, cheap local test target. Skip when the test path is unclear, expensive, integration-heavy, or not requested, and use the closest useful verification instead.

## Workflow

1. Understand the bug.
2. Pick the narrowest executable check.
3. Write the failing test.
4. Run it before the fix to confirm it fails for the expected reason.
5. Make the minimal fix.
6. Rerun the check.

## When to skip & bad tests

Do not force a test when it would require broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, vague reproduction steps, or large unrelated fixture churn; use the closest useful verification instead.

Prefer no new test over a bad test. A bad test is one that:
- mostly tests mocks,
- encodes current implementation details,
- depends on timing or unrelated global state,
- needs expensive infrastructure for a small fix, or
- would be deleted immediately after proving the fix.

## Guardrails & evidence

- Never alter a test to fit a wrong implementation, and never weaken existing assertions.
- Keep the test focused on this bug; for a class of similar failures, land a focused regression first before considering broader coverage.
- **Final reply must show evidence:** the failing test and failure output before the fix, plus the passing run after; if a pre-fix failure could not be shown, explain why and what substitute check ran.

## Repo-specific notes

When a project defines its own test rules (e.g., `agent-crew` requires feedback IDs like `FB-NNN` in regression test docstrings and reruns live tests only by dependency fingerprint), follow the project's rules. This skill only decides whether to write a failing test first and what evidence the final reply must show.

## Source

Adapted from the [Cursor pstack `tdd` skill](https://github.com/cursor/plugins/tree/main/pstack/skills/tdd) by Lauren Tan (@poteto), MIT License.
