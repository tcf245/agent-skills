# Design Playbook

How to produce a design that holds up under questioning. Apply every section; the order below is also the order of the wiki page.

## 1. One-sentence version

Before anything else, write the whole design in one or two sentences that name the key mechanism of each hard problem. If you cannot, the design is not clear yet.

Example: "Quota uses incremental leases (each stream reserves only the next small slice and renews as it goes); recovery works because generation is decoupled from the connection through a replayable event log."

## 2. Requirements and estimation

- Functional scope, non-functional targets, and an explicit **out of scope** row.
- A derivation table: metric, how it was derived, result. Cover request rate (average and peak), concurrency, data volume per day and per year, and the operation rate on the hot-path component.
- End with one conclusion sentence: **where the bottleneck is and where it is not**. This decides where the design spends its effort.

## 3. Architecture and responsibilities

- A table with three columns: component, responsibility, **not responsible for**.
- Call out concepts that are commonly confused and must be kept apart (for example rate limit vs. quota vs. provider capacity; online enforcement vs. ledger; connection vs. job).
- Name the single writer of every piece of authoritative state.
- Storage table: store, contents, why this store.
- A deployment note: how few deployables this could be at the given scale. Service boundaries are about ownership, not process count.

## 4. Each hard problem: the required treatment

Do all eight steps for every hard problem.

1. **Define correctness as verifiable guarantees.** Split a vague goal ("accurate", "consistent", "reliable") into three to five statements that could each be a monitor or a test.
2. **Explain the root tension** in one sentence: what is unknown, or which two requirements conflict.
3. **Show the naive options fail.** A comparison table with the same example numbers for every option, including yours. Columns are the quantities that matter (overshoot bound, false-rejection bound, latency, complexity).
4. **Present the mechanism.** State layout (keys, tables), the operations, and pseudo-code for the atomic part. Then a numbered timeline of one request.
5. **Give the bounds.** Each guarantee from step 1 gets a formula or a number, with a worked example.
6. **Answer the user's stated difficulties one by one**, by name, each in its own paragraph.
7. **Failure table.** Crash of each participant, retry and duplicate delivery, loss of the fast store, total unavailability of the enforcing component (fail-open or fail-closed, and why), partial data from an external dependency.
8. **The defensible alternative.** The simpler design that would also work at this scale, and why you still chose yours. State it as a trade-off, not as a mistake.

## 5. Patterns to reach for

Use them when they fit; always explain the mechanism rather than citing the name.

| Situation | Pattern |
|---|---|
| Concurrent consumers of a shared budget, final cost unknown | Incremental lease: reserve a small slice, renew, settle; bound = concurrency × slice |
| Fast enforcement plus durable truth | Enforcement point in a fast store, append-only ledger as authority, periodic reconciliation |
| State change plus event publication | Same-transaction outbox, at-least-once delivery, idempotent consumer keyed by a stable ID |
| Retries of a reporting call | Report cumulative values instead of deltas |
| Holder may crash | Lease with TTL and heartbeat; on expiry charge conservatively, reconcile later |
| Long-running job with unreliable client connection | Decouple job from connection through a sequence-numbered replayable log; resume by last seen ID |
| Duplicate submission | Client-generated idempotency key with a unique constraint |
| At most one active job per entity | Partial unique index or conditional insert |
| Flapping near a threshold | Hysteresis: once in the limited state, stay until an explicit reset |
| Periodic reset for many users | Lazy reset on next access instead of a scheduled job |
| Hot shared key at the top of a hierarchy | Hierarchical leases: children borrow a block from the parent |
| Blast radius at large scale | Cell architecture: the current design becomes one cell |

## 6. Lifecycles and recovery

- Disambiguate overloaded words first ("session", "order", "transaction" usually mean three or four different objects with different lifetimes). A table of concept, lifetime, where it lives.
- Data model sketch with the constraints that enforce invariants (unique keys, partial indexes).
- API list, including why calls are split the way they are.
- A state machine for the main entity; every terminal state persists what was produced and triggers settlement; transitions are idempotent.
- A scenario table that walks every failure and user action one by one: refresh, duplicate click, cancel, crash of each component, dependency failure, loss of the transient store, return on another device.
- State plainly what **cannot** be recovered and why.

## 7. Follow-up question list

Ten to fifteen questions an interviewer would ask, each answered in two to four sentences. Must include:

- Why not the simplest approach?
- What does the extra mechanism cost in latency and dependencies?
- What happens in the race at the boundary?
- What if the fast store loses data or is down?
- How would you verify this in production (metrics tied to the guarantees, plus property tests of the invariant)?
- **What is the weakest part of this design?**

## 8. Extensions

Eight to ten bullets, one or two sentences each: adjacent features, hierarchy (team or organization level), multi-region, safety and compliance, observability, cost levers. Say which existing component absorbs each one.

## 9. Ten-times scale

- Recompute the estimation table at 10×.
- A table: aspect, now, at 10×. Mark the **first** bottleneck.
- State what does **not** need redesign and why (a bound that is independent of user count is the strongest answer).
- Give the order in which to tackle the changes.

## 10. Narration order

Close with a seven-step outline for telling this in the interview: clarify, estimate, draw, walk one request, deep dive one, deep dive two, weaknesses and scale.

## Final check before saving

- Every difficulty the user named has an explicit, labeled answer.
- Every bound has a formula and a worked number.
- Every number is derived or marked as an assumption.
- Every component has a "not responsible for".
- At least one simpler alternative is acknowledged as viable.
- Two or three weaknesses are stated by the design itself.
- No claim that this is how a real company's system works, unless sourced.
