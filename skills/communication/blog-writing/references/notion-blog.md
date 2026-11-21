# Notion blog database

Eric's blog (`~/workspace/blog`, Next.js) reads the Notion database **📝 Blog Articles** through `lib/notion.ts` and revalidates every 60 seconds, so a published page appears on the site within about a minute.

- Database: `https://app.notion.com/p/14b7bd4a70564a1a8644de0cf0a52eee`
- Data source (use as `parent.data_source_id`): `d18ace0c-f22e-4ba0-b955-e80fec4a3db6`
- MCP server: `plugin:engineering:notion` (official `mcp.notion.com`). If its tools are missing, run `/mcp` and sign in there; the Dia browser does not complete the localhost OAuth redirect.

## Fields

| Field | Type | Value |
|---|---|---|
| `Name` | title | Plain, descriptive title (hard rule 1) |
| `Slug` | text | kebab-case English, unique; becomes the URL |
| `Date` | date | `date:Date:start` = `YYYY-MM-DD`, `date:Date:is_datetime` = 0 |
| `Tags` | multi_select | JSON array string, existing options `Tech`, `Design` |
| `Lang` | select | `zh`, `en`, or `ja` |
| `Published` | checkbox | Always `__NO__` from the agent |

The site only lists pages with `Published` ticked; without a `Slug` a page has no URL.

**The page must also be published to the web in Notion** (Share → Publish). The post body is read anonymously from the workspace's public `notion.site` domain (`getPageContent` in `lib/notion.ts`); a page that is not public lists fine on the home page but its URL returns 500 after about 15 seconds (`Notion page not found`). The MCP has no tool for this, so before ticking `Published`, ask Eric to publish the page to the web, then verify the live URL returns 200. Blog URL: `https://blog-inky-three-27.vercel.app/<slug>`.

Probe a page the way the blog does (run outside the sandbox, from `~/workspace/blog`, with the script at an explicit path, not `$TMPDIR`, which changes when the sandbox is off):

```js
import { NotionAPI } from "notion-client";
const api = new NotionAPI({ apiBaseUrl: "https://handsome-polyanthus-984.notion.site/api/v3" });
await api.getPage("<page-id>"); // throws "Notion page not found" if the page is not public
```

## Content

- Notion-flavored Markdown (`notion://docs/notion-flavored-markdown-spec`). Headings `##`/`###`, lists, `**bold**`, inline code, pipe tables.
- Images: `<image source="file-upload://<id>">caption</image>` on its own line with blank lines around it. Existing uploads read back as `notion-file-block://...`; keep those sources when editing.
- No raw HTML other than Notion's tags; it is saved as literal text.
- Fetch the page before editing; use `replace_content` for a full revision.
