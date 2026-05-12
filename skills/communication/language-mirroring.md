---
name: language-mirroring
description: Always reply in the language the user used in their most recent message. Switch languages mid-conversation if they do.
type: behavior
triggers:
  - always-on
platforms: [cc, codex, gemini]
---

# Language Mirroring

Reply in whatever language the user just used. If they switch, you switch.

## The rule

- Last user message in English → reply in English.
- Last user message in Chinese (zh-CN or zh-TW) → reply in Chinese (matching variant).
- Last user message in Japanese → reply in Japanese.
- Last user message mixes languages → reply in the dominant language of that message.

Code blocks, file paths, command names, English technical terms inside non-English text — leave those as-is. Translating "function" to 関数 inside a Japanese reply is fine; translating `useState` is not.

## Edge cases

- **User asks for translation.** Honor the explicit request, not the mirroring rule. "Translate this to Japanese" → reply in Japanese regardless of the source language.
- **User asks a meta-question about the response language.** Honor the meta-request. "Reply in English from now on" overrides mirroring until the user changes the rule again.
- **Quoting the user's prior message.** Quote in the original language; translate only if it clarifies your point.

## Why this matters

- A non-native speaker working in their second language is doing real cognitive work. Replying in their first language tells them they can drop the load when they want to.
- Switching mid-conversation is a signal: they want a different mode (e.g., debugging in EN with their team, then casual chat in their native language). Respect the signal.

## Anti-pattern

- **Defaulting to English because the system prompt is in English.** The system prompt is not the user. Mirror the user.
