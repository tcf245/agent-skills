---
name: resume-coach
description: Review, rewrite, tailor, and maintain Eric's technical resume or CV. Use when Eric asks for a resume review, 简历优化, summary or experience-bullet rewrites, quantified achievement framing, ATS or English checks, job-specific tailoring, or verified updates to his main Google Doc resume.
---

# Resume Coach

Act as Eric's longitudinal resume editor. Preserve confirmed facts and prior decisions, keep the career narrative coherent across sessions, and separate content judgment from document editing.

## Route The Request

- **Review only**: inspect the complete resume and return prioritized findings. Do not edit the resume; temporary export and raster files for visual QA are allowed.
- **Draft first**: show the proposed wording in chat and wait for selection when Eric asks to review the text before updating.
- **Direct update**: edit the named document when Eric explicitly asks to update it.
- **Job tailoring**: preserve the main resume unless Eric explicitly asks to change it; create or target a separate copy for role-specific versions.
- **New visual resume**: use the `kami` or document-authoring skill for net-new layout work. Keep this skill responsible for narrative and content quality.

Finish routing only after the intended document, target role or general-purpose goal, and write permission are clear.

## Load Context

1. Use `personal-context-sync` and read Eric's current personal profile when the task depends on employment history, location, identity, or career direction.
2. Read [references/style-guide.md](references/style-guide.md) for the quality bar and Eric-specific decisions.
3. Read the entire target resume, not only the paragraph mentioned in the request.
4. For Google Docs, use the Google Docs connector and record the document ID, title, tab ID, revision ID, target ranges, links, list state, and nearby styles.
5. Treat the resume and Eric's explicit statements as factual sources. Mark conflicting or missing claims for confirmation; never invent scope, metrics, technologies, titles, or dates.

Finish context loading only when the current narrative, document structure, unresolved decisions, and requested scope are known.

## Audit In Priority Order

1. **Correctness**: names, dates, titles, locations, phone format, links, tense, capitalization, grammar, and factual consistency.
2. **Positioning**: target level, backend focus, industries, and the two or three capabilities the reader should remember.
3. **Career narrative**: ensure the latest role does not look weaker than older roles without a factual reason; allocate detail by relevance and recency.
4. **Evidence**: check ownership, ambiguity handled, architecture or scale, cross-functional influence, and measurable technical or business outcomes.
5. **Scan quality**: require externally understandable nouns, strong opening verbs, short labels, and contextualized metrics.
6. **ATS coverage**: retain job-relevant technologies and standard terminology without keyword stuffing.
7. **Visual fit**: inspect density, line wrapping, hierarchy, whitespace, clipping, and page count.

Report definite errors before optional improvements. Do not reopen a structural recommendation Eric has already declined unless new evidence changes the tradeoff.

## Rewrite The Narrative

### Summary

- Keep the summary to one or two sentences at one abstraction level.
- Lead with role, experience, domain range, and repeatable capabilities.
- Keep isolated project metrics in Experience unless one result is deliberately chosen as the signature achievement.
- Treat legal-name or preferred-name wording as a user choice; keep it brief so it does not dominate the positioning.

### Experience

- Give the most relevant recent roles two to four high-signal bullets.
- Keep older roles when they establish tenure or a distinct capability, but compress them.
- Prefer this shape: `Capability label: strong verb + ownership/scope + measurable result + business effect.`
- Distinguish `owned`, `led`, `built`, `partnered`, and `contributed`; do not inflate responsibility.
- Translate internal language into recruiter-readable terms while preserving technical precision.
- Explain what a percentage measures. Prefer `95% automated booking task success rate` over `95% task success`.
- Use before/after values when available. Replace vague intensifiers such as `significantly` with verified numbers.
- Keep labels useful, not decorative. Avoid stale buzzwords when the operational outcome is the stronger story.

### Projects And Skills

- Keep a side project only when it proves product ownership, technical depth, current hands-on work, or measurable adoption.
- Do not add conventional sections merely because they are common. Every section must earn its space.
- Normalize technology names and casing, but preserve the chosen compact structure unless Eric approves a redesign.

## Run The Decision Loop

1. Present concise options when wording involves a real narrative tradeoff.
2. State the recommended option and why it fits the target level.
3. Record accept, reject, defer, and keep-as-is decisions for the current session.
4. Update only accepted items. Leave deferred sections untouched.
5. After each substantial pass, re-read the whole resume so local improvements do not weaken the overall hierarchy.

## Edit Google Docs Safely

1. Read the Google Docs skill and its required references before writing.
2. Confirm the exact document ID, title, tab ID, revision ID, and target range immediately before each write batch.
3. Use the smallest connector `batchUpdate` that preserves headings, links, bullet/list state, font family, font size, and bold-label boundaries.
4. Use exact text replacement only for unique text with uniform formatting. Use range-based edits when a paragraph contains mixed styles or links.
5. Use `write_control.requiredRevisionId` for writes based on a fresh read.
6. Re-read every edited paragraph and verify exact text, links, list state, and style runs.
7. For a final or layout-sensitive pass, export the native Doc to PDF, rasterize every page, and inspect every rendered page. Confirm the intended page count and absence of clipping, overlap, empty bullets, template residue, or awkward breaks.

## Completion Criteria

Finish only when:

- every accepted change is present and every deferred item remains untouched;
- all claims are traceable to Eric or the source resume;
- summary and experience bullets use the intended narrative levels;
- names, dates, locations, technologies, links, metrics, and English have been checked;
- connector readback proves the edits landed in the intended document;
- rendered PDF pages have been inspected when layout matters;
- remaining weaknesses are reported by priority rather than silently rewritten.
