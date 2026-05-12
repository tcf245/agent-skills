---
name: tdd-workflow
description: Use when implementing any feature or bugfix. Tests first as the acceptance criterion; one git commit per step; do not claim done until the test runs green.
type: workflow
triggers:
  - "implement"
  - "add a feature"
  - "fix a bug"
  - "write code"
  - "build this"
platforms: [cc, codex, gemini]
---

# TDD Workflow

Tests come first. They are the contract for what "done" means.

## The cycle

1. **Write the failing test.** It should fail for the *right reason* — the symptom of the missing behavior, not a syntax error. Show the failure output before moving on.
2. **Write the minimum code to pass.** No extras. No "while I'm here" cleanup. Single concern per step.
3. **Run the test.** It must go green. If it doesn't, stay in step 2 — do not write more tests.
4. **Commit.** One step, one commit. Message names the behavior added, not the code touched.
5. **Refactor (optional).** Only if the green test now lets you simplify. Re-run after.
6. **Next test.** Go back to step 1 for the next behavior.

## When to skip TDD

Skip the test-first cycle only when:

- The task has no testable output (UI demo, manual perf tuning, infra migration).
- You're spiking to learn an API — but mark the code as throwaway and rewrite under TDD before merging.
- The codebase has no test harness yet — then the first commit is "add test harness," not the feature.

## Defaults

- **One commit per step.** If two changes would be reverted independently, they belong in two commits.
- **No mocks for code paths you don't own.** Mock external services (HTTP, time, RNG); do not mock your own functions across module boundaries — the test then proves nothing about real behavior.
- **Pair with `verification-before-completion`.** Green test in your terminal counts. "Tests should pass" without running them does not.

## Anti-patterns

- **Writing the implementation, then the test.** The test passes the first time you run it, which means it would have passed without your change. You've tested nothing.
- **One mega-commit at the end.** No revert handle; git bisect is useless; review is unreviewable.
- **Asserting on incidental output.** Test the contract, not the implementation. `assertEqual(result.status, "ok")` survives refactors; `assertEqual(result.internal_cache_key, "user:42")` does not.

## Anchor in the plan

When operating under `plan-mode`, the Verification section IS the test plan. List the test commands there explicitly; they are the acceptance criteria.
