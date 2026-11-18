---
name: brainstorm-spec-plan-implement
description: Use when starting any non-trivial work — feature, refactor, system design, new tool. The default pipeline is Brainstorm -> Spec -> Plan -> Implement -> Verify. Each stage has an owner skill; do not skip stages.
type: workflow
triggers:
  - "let's build"
  - "let's design"
  - "new feature"
  - "non-trivial work"
  - "start a project"
platforms: [cc, codex, gemini]
---

# Brainstorm → Spec → Plan → Implement → Verify

Most rework comes from skipping the front of the pipeline. The stages are short; the cost of skipping them is high.

## Stages

### 1. Brainstorm
- Goal: align on **intent and requirements** before any structure. One question at a time. Surface assumptions.
- Owner skill: this skill. Keep the discussion lightweight, but do not move into implementation until intent, constraints, and the chosen approach are clear.
- Output: a shared understanding of *what success looks like* and *which approach* (out of 2–3 alternatives) the user picked.

### 2. Spec
- Goal: write the design decisions down so they survive across sessions.
- Output: a design doc, typically at `docs/specs/YYYY-MM-DD-<topic>-design.md`.
- Self-review the spec for placeholders, contradictions, and ambiguity before handing it to the user.

### 3. Plan
- Goal: turn the spec into ordered, verifiable steps.
- Owner skill: `plan-mode` (this repo). Six required sections — Context, Target, Steps, Files, Verification, Risks.
- Output: a plan file the user reviews and approves before any code is touched.

### 4. Implement
- Goal: execute the plan one step at a time.
- Owner skill: `tdd-workflow` (this repo) for code work; for non-code execution, follow the approved plan step by step and verify each checkpoint.
- Default: one git commit per step. After each step, the plan should still be the source of truth — if you discover the plan is wrong, update the plan before continuing.

### 5. Verify
- Goal: confirm the work matches the spec before claiming done.
- Owner skill: `verification-before-completion` (this repo).
- Evidence before assertions. Quote the verification output when reporting completion.

## When to skip stages

- **Trivial change** (typo, single-line tweak): skip Brainstorm and Spec. Still write a one-paragraph mental plan and verify.
- **Bug fix with known root cause**: start at Plan (or just Implement + Verify if the fix is one line). Use `systematic-debugging` if the root cause is unclear.
- **Exploration / research**: Brainstorm only; no Spec or Plan until intent settles.

Do NOT skip Verify. Ever.

## Anti-patterns

- **"Let me just start coding."** Without a spec, every dead-end is wasted work that could have been a 5-minute conversation.
- **Plan without Brainstorm.** Plans are concrete; if the concrete is wrong, you waste the plan. Spend cheap brainstorming tokens before expensive plan tokens.
- **Implement without Plan on multi-step work.** No revert handle; review impossible; user can't course-correct mid-flight.
- **Verify by reading the diff.** Diffs prove the code changed, not that it behaves correctly. Run the verification command.
