---
name: parallel-tasks
description: Use when facing 2+ independent tasks that have no shared state or sequential dependency, especially when each task is slow (long render, deep search) or low-context (a clear spec is enough). Spawn parallel workers; do not serialize.
type: behavior
triggers:
  - "multiple independent tasks"
  - "in parallel"
  - "batch of"
  - "iterate on diagrams"
  - "search across"
platforms: [cc, codex, gemini]
---

# Parallel Tasks

Serial execution wastes wall-clock time and burns the main session's context on work that doesn't need it. When tasks are independent, parallelize.

## Decision criteria

A task is a parallelization candidate if **all three** hold:

1. **Independent.** No shared state, no ordering dependency with the other parallel tasks. Result-dependence is a no-go.
2. **Low context.** A short brief is enough — the worker doesn't need the full conversation history to succeed.
3. **Worth offloading.** Either slow (multi-second renders, large file scans) or context-heavy (would clutter the main session with intermediate output).

If even one fails, do it inline.

## How to parallelize per platform

### Claude Code
- Use the `Agent` tool with `subagent_type` matching the work (Explore for searches, general-purpose for arbitrary, specialized agents where available).
- Issue all independent agent calls in a **single message** with multiple tool blocks — they run truly in parallel. Sequential calls don't.

### Codex / Gemini CLI
- Open additional sessions in separate terminals; brief each with a self-contained prompt.
- Coordinate by file artifacts (each worker writes to its own path; main session reads when ready).
- Do not assume sessions can pass state to each other — they can't.

## High-value cases

- **Diagram batches.** Rendering 3 polished diagrams serially = 3× the wait. Parallel = ~1×. Diagrams have low context dependency (a node/edge spec is all the worker needs).
- **Independent searches across the codebase.** "Find usages of A" and "find usages of B" — two Explore agents, one message.
- **Independent file processing.** Linting 5 unrelated directories, generating fixtures for unrelated tests.
- **Read-heavy exploration.** Three angles of investigation that don't inform each other yet.

## Anti-patterns

- **Spawning a subagent for a 30-second task.** Subagents have overhead — cold start, context briefing. Worth it for slow or noisy work; not for a quick `grep`.
- **Treating sequential work as "in parallel" by issuing multiple calls.** If task B needs task A's result, B must wait for A. Multiple calls in one message ≠ correctness.
- **Briefing parallel workers in a way that requires them to coordinate.** They can't. Either give each worker independence, or accept serialization.
- **Doing the work inline in the main thread because it "feels productive".** Many small inline iterations of a slow renderer burn main-thread tokens for no reason.

## Concrete recipe (CC, Tier C diagrams)

Five hero diagrams to produce for a README:
1. Single Agent call message with 5 tool blocks, each spawning a subagent with `fireworks-tech-graph` skill.
2. Each prompt: node list + edge list + style choice + output path. ~10 lines is plenty.
3. Main thread continues writing prose while diagrams render.
4. Collect results, embed images, done.
