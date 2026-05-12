---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior — before proposing or applying a fix. Reproduce, narrow, hypothesize, verify, then change one thing.
type: workflow
triggers:
  - "this is broken"
  - "test failure"
  - "unexpected behavior"
  - "bug"
  - "why doesn't it work"
platforms: [cc, codex, gemini]
---

# Systematic Debugging

The fastest path to the fix is also the slowest-feeling: do not skip a step.

## The four-step cycle

### 1. Reproduce
- Find the smallest invocation that triggers the bug. If you can't reproduce, you can't fix it — anything else is guessing.
- Capture: command, input, environment, exact error/output. Paste it verbatim into your scratchpad.
- If the bug is intermittent, run the repro 10 times and record hit rate.

### 2. Narrow
- Bisect the surface area. Comment out half the code path, half the input, half the config; see which half still reproduces. Repeat.
- Or use `git bisect` if the bug is regression-shaped (worked, now doesn't).
- Stop narrowing when one more cut would lose the repro entirely.

### 3. Hypothesize
- State ONE specific hypothesis: "`fn_x` returns `null` when `arg` is empty because the guard at line N is reversed."
- It must be falsifiable. "Something with caching" is not a hypothesis; "the cache returns stale value when key length > 64" is.
- If you have multiple hypotheses, pick the cheapest one to test first.

### 4. Verify
- Run an experiment that distinguishes the hypothesis from its alternatives. Print, assert, breakpoint, or add a one-line log.
- If verified → apply the fix → re-run repro to confirm it's gone → also run an *unrelated* test to confirm no regression.
- If falsified → go back to step 3 with what you learned. Do NOT skip back to step 1 unless you discover the repro itself was wrong.

## Anti-patterns

- **Shotgun debugging.** Changing three things at once. When the bug stops, you don't know which fix worked; the other two are mysteries that will haunt the codebase.
- **Skipping reproduce.** "I think I know what it is" → apply fix → commit. Tomorrow the bug returns because you fixed a different bug.
- **Fixing the symptom.** The exception trace shows a `NullPointerException`. You add a null check. The bug is gone — but the *reason* something was null is still there, waiting to explode somewhere harder to debug.
- **Believing transient bugs are unimportant.** "Re-running fixed it" is a postponement, not a resolution. Capture and fix.
- **Treating logs/error messages as ground truth.** They tell you what the program *thinks* happened, which can be misleading. Verify against actual state (database, filesystem, network capture).

## When to escalate

If after one cycle through 1–4 you still have no hypothesis, stop. State explicitly what you've ruled out, what you observed, and ask the user. Pretending to know is worse than admitting you're stuck.

## Pair with other skills

- After reproducing, if the fix turns out to be non-trivial → switch to `plan-mode` to design it.
- Once a fix is applied → run `verification-before-completion` before claiming done.
