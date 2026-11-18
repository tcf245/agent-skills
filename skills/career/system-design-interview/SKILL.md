---
name: system-design-interview
description: Use when Eric gives a one-line system design prompt ("设计一个股票交易系统", "design a rate limiter", "SD 课题") and wants a complete interview-grade design. Produces a design that survives follow-up questions, two polished diagrams, and saves it to the LLM Wiki as a concept page plus a dated record. Trigger on 系统设计, System Design, SD 课题, 设计一个…系统, 如何设计, 面试设计题, or "design a ... system".
type: workflow
triggers:
  - "system design"
  - "系统设计"
  - "SD 课题"
  - "设计一个.*系统"
  - "如何设计"
  - "design a .* system"
  - "system design interview"
platforms: [cc, codex, gemini]
---

# System Design Interview

Turn a one-line prompt into a design Eric can defend in a 60-minute interview, then archive it in the wiki for his review. The input is deliberately small; the depth comes from you.

The output is judged on one thing: **can it survive an interviewer who keeps asking "why" and "what if"**. A broad list of components is not a design. Depth on the two or three hard problems is.

## Input Handling

- Accept a single line. Do not open with clarifying questions. Choose the scope a strong candidate would choose, write the assumptions down in the page, and proceed.
- Ask only when two readings of the prompt lead to different systems (for example "trading system" could mean a broker's order app or an exchange matching engine). Ask one question, then proceed.
- If Eric names hard problems, constraints, or scale, those override your own choices and must each be answered explicitly in the page.
- If no scale is given, pick one that makes the hard problems real, and say it is an assumption.

## Route The Request

- **New design**: a prompt for a system that has no page yet. Run the full workflow below.
- **Review or continue**: Eric comes back with a question, an objection, or "继续 … 的讨论" about a design that already exists. Do not redesign. Follow "Continuing A Design" at the end.

Decide by searching `index.md` for the topic before doing anything else.

## Workflow

### 1. Load context

1. Resolve the wiki path from `config.example.yml` (`/Users/eric/Library/Mobile Documents/iCloud~md~obsidian/Documents/LLM-Wiki`) or the local override, and follow the `llm-wiki` skill for schema, index, and log rules.
2. Read `index.md`. Find earlier pages on the same or a neighboring problem: prior interview records, earlier attempts, related concept pages.
3. Read those pages. An earlier attempt by Eric is important input: the new design must say what changed and why.
4. Read `wiki/concepts/System Design Interview Framework.md` if present, for his narration conventions.

### 2. Establish domain facts

Some domains have real-world rules that an interviewer will expect (matching priority in exchanges, settlement cycles, double-entry in ledgers, delivery semantics of a named message broker). When the design depends on such a fact:

- Verify it against a primary source if you are not certain, and link the source.
- If you cannot verify it, write it as an assumption, not as a fact.
- Never describe the design as how a named company actually built its system unless a source says so.

### 3. Pick the hard problems

Choose two or three. A hard problem is one where the obvious solution is wrong in a way that can be shown with numbers, or where two requirements pull against each other. Everything else gets a table row, not a section.

### 4. Design

Follow [references/design-playbook.md](references/design-playbook.md). It defines the required treatment of each hard problem and the quality bar. Read it every time; do not work from memory.

### 5. Draw

Two polished diagrams, plus inline Mermaid where it helps:

| Diagram | Content |
|---|---|
| Architecture | Layered components with the single-request path numbered ①–⑧ and a step legend |
| Core mechanism | A flowchart of the hardest problem's mechanism, with a side panel stating the invariant and the bounds |
| Mermaid (inline) | State machines and sequence diagrams for lifecycles and recovery |

Use [scripts/sd_diagram.py](scripts/sd_diagram.py). See [references/diagrams.md](references/diagrams.md) for the API, layout rules, and the mistakes to check for. Render to PNG and **look at the image** before saving; fix any arrow that crosses a box or a badge.

### 6. Write to the wiki

Use [references/page-template.md](references/page-template.md). Write the pages in the language Eric used, keeping technical terms in English.

- **Concept page** `wiki/concepts/<Topic> System Design.md`: the timeless design. `status: refined`. Never links to records.
- **Record page** `wiki/records/YYYY-MM-DD <Topic> System Design.md`: Eric's stated constraints, the design judgments in one line each, a table of the key conclusions (invariants, bounds, example numbers), what changed from any earlier attempt, the points he should challenge in review, an entry point for continuing the discussion, and an empty review log. `status: active`. Mark it as awaiting his review.
- The record page is the handoff. A later session with no memory of this one must be able to resume from it alone, so it names which sections of the concept page cover what, and lists what was left undone or unverified.
- Diagrams go to `attachments/diagrams/<topic-slug>-*.svg` and `.png`.
- Update `index.md` (both the concept list and the System Design record list) and append a `CAPTURE` entry to `log.md`.
- Confirm that every `[[wikilink]]` in the new pages resolves to an existing file.

Do not run the snapshot script.

### 7. Report

Reply in chat with a short summary, not a copy of the page:

1. The core idea of each hard problem in two or three sentences.
2. The trade-offs you made that Eric might reject.
3. What you assumed and what you did not verify (include any diagram type you could not render-check).
4. File paths.

## Continuing A Design

Used when Eric reviews an existing design and wants to pick the conversation back up.

1. Read the record page first: constraints, key conclusions, open challenge points, review log, and the "继续讨论的入口" section.
2. Read only the sections of the concept page that the question touches, plus any earlier-attempt record it points to.
3. Engage with the objection on its merits. If Eric is right, say so and change the design; if the design holds, show the bound or the scenario that answers it. Do not defend a choice just because it is already written down.
4. When the point is settled:
   - edit the affected sections of the concept page (and its Q&A list if a new follow-up question emerged);
   - add a dated row to the record's review log: the challenge, the conclusion, what changed;
   - move resolved items out of the "points to challenge" list;
   - regenerate a diagram only if it is now wrong;
   - append an `UPDATE` entry to `log.md`.
5. If the discussion is left unresolved, record the open question in the record page so the next session starts from it.

## Rules

- **Numbers are assumptions unless sourced.** Label them once, clearly.
- **State bounds, not adjectives.** "Idle reservation ≤ N × S" instead of "minimal over-reservation".
- **Show the naive solutions fail before presenting yours.** Same example numbers across all options.
- **Say what each component does not own.** Boundaries are what interviewers probe.
- **Name the design's weakest points yourself.** Two or three, each with its bound and why it is accepted.
- **Offer the simpler alternative honestly.** If one database would do at this scale, say so.
- **The design is a proposal.** The record page says it is awaiting review; do not write as if Eric agreed.

## Anti-patterns

- Opening with five clarifying questions for a one-line prompt.
- A component list with one sentence each and no deep dive.
- Technology name-dropping without the reason that technology is needed here.
- "Use Kafka for exactly-once" style claims that hide the real mechanism (idempotent consumer, unique key).
- Scaling section that says "add more servers" without naming the first bottleneck.
- Saving only one page, or forgetting `index.md` and `log.md`.
- Pasting the whole design into chat.

## Claude Code specifics

- The vault may sit outside the command sandbox. Generate diagrams in the temp directory, view the PNGs, then copy them into the vault; write Markdown with the file tools.
- Write the diagrams yourself. You hold the design context; a subagent would start cold.
