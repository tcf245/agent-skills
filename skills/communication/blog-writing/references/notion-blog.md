# Notion blog database

Eric's blog (`~/workspace/blog`, Next.js) reads the Notion database **📝 Blog Articles** through `lib/notion.ts` and revalidates every 60 seconds, so a published page appears on the site within about a minute.

- Database: `https://app.notion.com/p/14b7bd4a70564a1a8644de0cf0a52eee`
- Data source (use as `parent.data_source_id`): `d18ace0c-f22e-4ba0-b955-e80fec4a3db6`
- MCP server: `plugin:engineering:notion` (official `mcp.notion.com`). If its tools are missing, run `/mcp` and sign in there; the Dia browser does not complete the localhost OAuth redirect.

## Fields

| Field | Type | Value |
|---|---|---|
| `Name` | title | Plain, descriptive title (hard rule 1) |
| `Slug` | text | kebab-case English phrase of 3–6 words that says what the post does, e.g. `build-agent-crew-on-discord`; never a bare keyword or project name such as `agent-crew` (Eric, 2026-11-21: keywords should stay free for later posts) |
| `Date` | date | `date:Date:start` = `YYYY-MM-DD`, `date:Date:is_datetime` = 0 |
| `Tags` | multi_select | JSON array string, existing options `Tech`, `Design` |
| `Lang` | select | `zh`, `en`, or `ja` |
| `Published` | checkbox | `__NO__` until Eric says to publish |

The site only lists pages with `Published` ticked; without a `Slug` a page has no URL.

Since 2026-11-21 (blog commit `55fd247`) the post body is read through the official API with the integration token (`notion-compat`), so **ticking `Published` is the only switch**; pages do not need Publish to web. After ticking it, wait up to a minute (ISR) and confirm `https://blog-inky-three-27.vercel.app/<slug>` returns 200. Image URLs are signed and expire after an hour; ISR refreshes them every 60 seconds.

Known quirk: notion-compat wraps image captions in an extra array; `fixImageCaptions` in `lib/notion.ts` flattens it. If a post with a new block type returns 500, render it locally with `keychain-secret run .env.keychain -- npx next dev` (outside the sandbox) to get a readable stack.

## Content

- Notion-flavored Markdown (`notion://docs/notion-flavored-markdown-spec`). Headings `##`/`###`, lists, `**bold**`, inline code, pipe tables.
- Images: `<image source="file-upload://<id>">caption</image>` on its own line with blank lines around it. Existing uploads read back as `notion-file-block://...`; keep those sources when editing.
- No raw HTML other than Notion's tags; it is saved as literal text.
- Fetch the page before editing; use `replace_content` for a full revision.
