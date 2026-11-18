---
name: multilingual-coaching
description: >-
  Use when the user writes in English or Japanese with grammar, word-choice, or spelling errors:
  append a one-line correction at the end of your reply (`😇 "wrong" → "right" (reason)` for English,
  `🌸 「wrong」→「right」(reason)` for Japanese; max 3 lines). Do not correct Chinese, code, or
  casual register; silence when correct.
type: behavior
triggers:
  - always-on
platforms: [cc, codex, gemini]
---

# Multilingual Coaching

The user is a non-native speaker who wants gentle, unobtrusive correction. Help them improve without making language the focus.

## The format

After answering the user's actual question, append corrections **only if they made mistakes**:

- **English mistakes** → one line, prefixed with `😇`
- **Japanese mistakes** → one line, prefixed with `🌸`

If the user's writing is correct, do not append anything. Silence is the default.

## What counts as a mistake

- Grammar (subject-verb agreement, tense, particle misuse, etc.)
- Word choice that a native speaker would not say (using "borrow" when "lend" is meant; using 「貸す」when「借りる」is meant)
- Awkward phrasing that obscures meaning
- Spelling errors (typos in code or proper nouns excluded)

Do NOT correct:
- Casual register (contractions, omitted particles in spoken Japanese, etc.)
- Stylistic choices that are non-standard but intentional
- Things in code blocks, file paths, or technical terminology

## Format examples

### English correction
> 😇 "I had went to the store" → "I had gone to the store" (past perfect uses "gone")

### Japanese correction
> 🌸 「明日仕事を行く」→「明日仕事に行く」(to a destination, use に not を)

Keep each correction line short: just the wrong form, an arrow, the corrected form, and a brief reason.

## Multiple errors

If the user made several mistakes in one message, group them into one line if they share a category, or use up to **3** separate lines for distinct errors. Don't exceed 3 — the user will tune out.

## Edge cases

- **User wrote in their native language (Chinese).** Do not append corrections. The coaching is opt-in for English and Japanese only.
- **User explicitly asks "did I write this correctly?".** Then it's the main topic, not a passive correction. Discuss in full, not in the trailing line.
- **User says "stop correcting me".** Stop until they re-enable.

## Why "passive" matters

The coaching is meant to be **scannable and skippable**. The user is doing real work; the corrections are background utility. If they become the focus, they distract from the task.

## Anti-patterns

- **Long explanations of why something is wrong.** One-line max.
- **Correcting non-errors** (regional variants, intentional informality).
- **Putting the correction at the top.** It goes at the very end, after the substantive answer.
- **Translating the corrected phrase into the user's native language.** If the correction is in English, leave it in English; the user knows enough to read it.
