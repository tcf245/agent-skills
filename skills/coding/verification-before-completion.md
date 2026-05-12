---
name: verification-before-completion
description: Use before claiming any work is complete, fixed, or passing — and before committing or creating PRs. Run the verification command, read the output, and only then make the success claim. Evidence before assertions, always.
type: behavior
triggers:
  - "is it done"
  - "claim complete"
  - "before committing"
  - "before PR"
  - "ready to merge"
platforms: [cc, codex, gemini]
---

# Verification Before Completion

A claim of "done" without evidence is a guess. Guess wrong and you waste the user's time chasing your phantom victory.

## The rule

Before you say "done", "fixed", "passing", "working", "should be ready", or any equivalent:

1. **Identify the verification command.** What concretely proves the claim? `npm test path/to/file`, `curl localhost:3000/health`, `python -m pytest -k new_feature`, `git status`, etc.
2. **Run the command.**
3. **Read the actual output.** Not the exit code alone. Failures sometimes return 0; warnings sometimes hide in stderr.
4. **Match output to claim.** If the test says `PASSED 12 failed 1`, you don't say "all green" — you investigate the one.
5. **Only then** make the claim, and **quote the evidence** in your response: "12 tests passed (output above)" or `tests/foo.test.ts — green`.

## What counts as evidence

- ✅ The test runner's PASS/FAIL summary you just produced.
- ✅ A `curl` response showing the expected status and body.
- ✅ A `git diff` showing the file actually changed.
- ❌ "It should work because the logic is correct."
- ❌ "The types pass" (when the task requires behavior, not types).
- ❌ "I made the change" (file existence ≠ correctness).

## Before committing

Always run, in order:
1. The relevant test/build command — proves correctness.
2. `git diff --staged` (or `git diff` if pre-add) — proves you're committing what you think.
3. `git status` — proves there are no surprise files or omissions.

If any of these surprises you, fix before committing.

## Before opening a PR

- Run the full test suite, not just the file you touched.
- Self-review the diff one more time as if you were the reviewer.
- Confirm the PR description matches the actual changes — not the changes you planned to make.

## Anti-patterns

- **"Tests should be passing"** (without running them) — guess, not evidence.
- **Running tests, getting a failure, claiming success anyway** because the failure "looks unrelated". It is rarely unrelated. Investigate.
- **Quoting only the exit code.** Some tools exit 0 on warnings. Some exit non-zero on noise. Read the body.
- **Skipping verification because the change is "trivial".** Trivial changes are exactly where reflexive confidence misleads.
