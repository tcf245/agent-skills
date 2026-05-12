---
name: plan-mode
description: Use when the user asks for a plan, invokes /plan, or any time you need to design a multi-step change before touching code. Produces a plan with six required sections.
type: workflow
triggers:
  - "/plan"
  - "make a plan"
  - "design a plan"
  - "plan this out"
  - "before implementing"
platforms: [cc, codex, gemini]
---

# Plan Mode

When designing a multi-step change, the plan must contain all six sections below. Do not wait for the user to ask — these are the default.

## The six sections

1. **Context / Why** — The problem being solved and why now. Without this, future readers (and you in the next session) can't tell whether the plan is still load-bearing.

2. **Target State** — What the system looks like after the change. Prefer a structure diagram or a before/after table. Specific files and entities, not abstract goals.

3. **Steps** — Ordered, each independently revertible. For non-trivial multi-step work, **default to one git commit per step** so the user can rebase, drop, or reorder cleanly.

4. **Files Touched** — A table of `path × action` (create / edit / delete / read-only). Catches scope creep before it starts.

5. **Verification** — Concrete, runnable commands with expected outputs. NOT abstract ("tests should pass") but copy-pasteable ("`pytest tests/test_foo.py::test_bar` exits 0"). For coding work, default to TDD: write the failing test first as the acceptance criterion.

6. **Risks & Mitigations** — A table. For each risk, name a strategy in order of preference: **Prevention > Detection > Recovery**.

## How to apply

- Always include all six sections, even if a section is short. A one-line Risks table is fine; an absent one is not.
- Verification commands must be copy-pasteable. "Run the tests" is aspirational; `cd foo && npm test -- --grep auth` is verifiable.
- For multi-step plans on a git-tracked repo, propose per-step commits explicitly and note that the user can rebase to squash if they prefer.
- For non-code work (UI demo, infra migration, perf tuning), skip the TDD default but keep the Verification section — describe how the user can manually confirm the change.

## Risks table format

| Risk | Probability | Impact | Prevention | Detection | Recovery |
|------|-------------|--------|------------|-----------|----------|

Use Probability ∈ {Low, Medium, High}. Impact ∈ {Low, Medium, High, Critical}. Empty cells are OK if the strategy is "n/a" — just don't omit the column.

## Anti-patterns

- **Vague verification.** "Make sure it works" is not verification.
- **Skipping Risks because the task feels safe.** The risks for safe tasks are short — write them anyway. The act of listing forces you to think about what could go wrong.
- **Combining steps that should be separate commits.** If two changes would be reverted independently, they're two steps.
- **Adding scope inside Steps that wasn't in Target State.** If a step changes something not in Target State, update Target State first.

## Claude Code specifics

- After the plan is complete and approved, delete the plan file (`rm ~/.claude/plans/<file>`) so the UI badge clears. Do not wait for the user to ask.
- In Plan Mode, only the plan file is editable; other tools are read-only. Don't try to execute steps until ExitPlanMode is called.
