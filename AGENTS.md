# Engineering Conventions

This file is the single source of engineering conventions for every agent working in this repository (Claude Code, Codex, agy/Gemini).

## Language
- Skill bodies and descriptions, code, comments, docs, commit messages, and PR text are in English.
- Non-English is allowed only for trigger phrases the user types, verbatim quotes, and output examples (see `skills/_schema.md`).
- A task instruction that asks for something else does not override this rule — follow this file and note the conflict in your summary.

## Layout and Skill Format
- Follow `skills/_schema.md` for skill directory structure, frontmatter, and naming rules.

## Before Calling Work Done
- Run `./scripts/lint.sh`.
- If you changed any skill, run `python3 ./scripts/build.py`, then verify with `python3 ./scripts/build.py --check`.
- Run the `pytest` files under `scripts/` and `tools/` that cover what you touched.

## Workflow
- Work on a feature branch -> open a PR -> pass CI -> merge.
- Write commit messages in English.
