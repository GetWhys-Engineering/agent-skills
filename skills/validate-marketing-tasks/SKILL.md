---
name: validate-marketing-tasks
description: Ground marketing tasks in real buyer interviews, personas, brand voice, and messaging frameworks (GetWhys). Use for ANY marketing, content, or GTM task or question, even if GetWhys is never mentioned. Covers writing or rewriting copy (blog posts, emails, landing pages, web copy, social posts, ads, white papers, campaign briefs, sales enablement), buyer and market research (pain points, objections, win/loss, why deals are lost, what customers think of vendors and competitors, pricing and discount norms, buying committees and buyer journeys), competitive analysis, battlecards and talk tracks, building buyer personas and ICPs, messaging and positioning, on-brand rewrites, and validating or scoring drafts (will this resonate?). Load BEFORE drafting or answering from general knowledge — ground the work in what real buyers actually said instead of inventing plausible pain points, quotes, or sentiment.
---

# Validate marketing tasks with GetWhys

GetWhys is a buyer-intelligence platform built on verbatim interviews with real B2B software buyers — real people describing pain points, decision criteria, KPIs, vendor sentiment, real pricing, and win/loss drivers in their own words. Its MCP server (`getwhys-mcp`) exposes two data layers:

- **Org-configured artifacts** — the user's own buyer personas, brand voice, and messaging frameworks, configured by their organization.
- **Research corpus** — GetWhys's proprietary buyer interviews, plus any documents the user's org has uploaded (decks, transcripts, win/loss notes, internal collateral).

All GetWhys tools are read-only and safe to call. Tools are referenced below by bare name (e.g. `get_persona`); your client may display namespaced variants (e.g. `getwhys-mcp:get_persona`). Some clients defer MCP tools behind a search step — if no GetWhys tools are visible, search the available-tool registry for `getwhys` before concluding the server is absent.

## Pick the playbook

| The user wants to… | Playbook | Tool sequence |
|---|---|---|
| Answer a buyer/market research question — pain points, objections, pricing, packaging, discounts, buying committees, buyer journeys, channels ("where do CROs get their information?") | Research question | One focused `query_market_research` call per sub-question, in parallel |
| Competitive work — "compare X vs Y", "why do we lose deals to X?", "what do customers think of vendor Y?", battlecards, talk tracks | Competitive intel & battlecards | 3–4 parallel `query_market_research` calls (competitor × angle) → synthesize. **No** voice/framework calls |
| Write or rewrite outward-facing copy — blog posts, emails, landing pages, web copy, social posts, ads, white papers, case studies, campaign briefs | Create outward-facing content | `get_brand_voice` + `get_all_messaging_frameworks` (parallel) → persona resolution → optional research grounding → draft → score loop |
| Validate a draft — "score this", "will this resonate with [audience]?", "how would [persona] react to this?" | Score existing content | `list_personas` → `score_content` → present scores table-first |
| See which personas exist, or load one persona's details | Explore personas | `list_personas` → `get_persona` |
| Build a buyer persona or ICP from research ("Develop a buyer persona for [role]…") | Build a persona from research | `list_personas` (check for a close match) → parallel research per dimension group → synthesize |
| Look up a messaging framework by name | Framework lookup | `get_messaging_framework({title})`, or `list_messaging_frameworks` → `get_messaging_framework({id})` |
| Check the connection or who is signed in | Connection sanity | `whoami` |

## Playbooks

### Research question

1. **One focused question per call.** A multi-part ask ("compare mid-market vs enterprise CRM buying") decomposes into one `query_market_research` call per sub-question, issued in parallel. You synthesize across the answers; the tool will not.
2. Per call: `query` = the semantic intent as a natural-language question (no retrieval verbs like "find" or "show me"); `explain` = a one-line rationale for this specific call; distinctive entities and their variants go in `keywords.allOfAny`; time windows go in `temporalRange` (YYYY-MM-DD), never in keywords.
3. Relay the answer per the [relay rules](#cross-cutting-rules): "GetWhys Sources" paragraph verbatim, `view_in_getwhys` link, inline † markers preserved.

Recurring shapes: win/loss ("why do we lose deals to [competitor]?"), vendor/competitor sentiment ("what do customers think of [vendor]?"), pricing/packaging/discount norms, buying-committee and buyer-journey mapping, channels/watering holes.

*Deep dive — query, keyword, and date-range crafting: read `references/market-research.md`.*

### Competitive intel & battlecards

1. Decompose into 3–4 parallel focused `query_market_research` calls, one per competitor × angle: their customers' pain points; win/loss reasons against them; what buyers say about them; their pricing/packaging.
2. Synthesize the answers into the user's template (battlecard sections, comparison table, talk track) — keep each section traceable to its † markers and include every call's "GetWhys Sources" paragraph.
3. Battlecards, talk tracks, and competitive teardowns are **internal analytical artifacts** — do NOT call `get_brand_voice` or any messaging-framework tool for them.

*Worked battlecard decomposition: read `references/market-research.md`.*

### Create outward-facing content

For anything the user will publish or send — net-new drafts AND rewrites ("improve this page for [audience]", "make this more relevant to [title]"):

1. **Kickoff pair, every time**: call `get_brand_voice` and `get_all_messaging_frameworks` in parallel before drafting. Never `list_messaging_frameworks` here — fetching one framework under-applies the org's voice.
2. **Persona resolution**: `list_personas` → pick the handle matching the target audience → `get_persona` for full attributes.
3. **Optional research grounding**: focused `query_market_research` calls for the pain points, proof points, or buyer language the piece should use.
4. Draft, applying the brand-voice do/don't rules, the messaging frameworks, and the persona's challenges/motivations/KPIs.
5. **Score loop**: `score_content` → render the dimensional scores as a table or chart first → revise per the recommendations → resubmit until the score meets the user's threshold (default ~80 if they don't set one).

*Deep dive — drafting with voice + frameworks, scoring parameters, worked examples: read `references/content-creation.md`.*

### Score existing content

The route for "score this draft", "will this resonate with [audience]?", and "how would [persona] react to this?" when a draft is attached.

1. Resolve the persona: `list_personas` → match the audience to a handle. Never guess `persona:<handle>` IDs.
2. Call `score_content` with `content`, `persona_handle`, and optionally `content_type` (e.g. "email subject line", "blog post"). To score against a messaging framework, pass `messaging_framework_id` OR `messaging_framework_title` — exactly one, never both.
3. **Present table-first**: render the dimensional scores as a table or bar chart before any written summary, then the recommendations.

### Explore personas

- `list_personas` returns the lightweight index (handle + name). Call it first whenever a workflow needs a target persona.
- `get_persona({handle})` loads one persona's full attributes. Handles come from `list_personas` output — never invented.
- `get_all_personas` only when the user explicitly needs every persona in detail ("show me all our personas").

### Build a persona from research

For "develop/build a buyer persona for [role]" asks, usually arriving with a section template (Titles / Challenges / Motivations / KPIs / …):

1. `list_personas` first — if a close org-configured match exists, `get_persona` it and **enrich** it rather than building a duplicate.
2. Decompose the requested dimensions into 2–4 parallel `query_market_research` calls grouped by related dimensions (e.g. titles + responsibilities; challenges + motivations; watering holes + buying committee; KPIs + priorities).
3. Synthesize into the user's template, relaying † markers and each call's "GetWhys Sources" paragraph.
4. Close by offering segmentation refinements (industry, company size, GTM motion) — don't front-load blocking questions.

*Deep dive — dimension grouping, enrich-vs-duplicate, disambiguation: read `references/buyer-personas.md`.*

### Framework lookup

- User named the framework verbatim → `get_messaging_framework({title})` directly — one round trip.
- Fuzzy or partial reference → `list_messaging_frameworks` to disambiguate, then `get_messaging_framework({id})`.
- A `title` call returning a "multiple frameworks share that title" error → re-call with one of the returned ids.
- Pass exactly one of `id` or `title`, never both.

### Connection sanity

- `whoami` reports who is authenticated (a user or an org-level key) and the organization. Use it when results look wrong (e.g. unexpected workspace) or the user asks who's connected.
- Empty-workspace responses — "No personas found in this workspace.", "No brand voice characteristics configured for this workspace.", "No messaging frameworks configured for this workspace." — mean the org hasn't configured that artifact yet. Don't retry; proceed without it and point the user to the GetWhys app to set it up.

## When NOT to call GetWhys

- **General definitions** ("what's a messaging framework?", "what does ICP mean?") → answer directly, zero calls.
- **Technical product documentation** → not buyer intelligence.
- **Tasks with no buyer / persona / brand / org-document angle** → this skill triggers on a wide net by design; when the loaded task turns out to have no such angle, just do the task normally — zero GetWhys calls, no mention of the detour.
- **Voice/framework tools on internal artifacts** — `get_brand_voice` and the messaging-framework tools are guardrails for outward-facing publishable copy ONLY. Never call them for PRDs, product specs, battlecards, competitive teardowns, persona documents, or other internal analytical prose. (Research-grounding an internal PRD with `query_market_research` is fine; styling it with brand voice is not.)

## Cross-cutting rules

- **Handle discipline**: persona handles (`persona:<handle>`) always come from `list_personas` output. Unknown handles fail the call.
- **`id` XOR `title`**: `get_messaging_framework` and `score_content`'s framework parameters take exactly one identifier, never both.
- **Parallelize independent calls**: research decompositions, the content kickoff pair, persona-dimension groups.
- **Relay rules** for every `query_market_research` answer:
  - Include the trailing **"GetWhys Sources" paragraph verbatim** — never paraphrase, abridge, or omit it; it's how the user gauges credibility.
  - Surface the **`view_in_getwhys` link** when present so the user can explore the underlying sources.
  - Preserve the **inline † grounding markers** in the answer text.
- **`no_data: true`** means no buyer interviews or uploaded documents matched — do NOT fabricate an answer from general knowledge. Rephrase and retry once at most (different angle, fewer/different keywords), then tell the user plainly what the corpus didn't cover.

## Tool quick reference

| Tool | Purpose | Key input | Typical next step |
|---|---|---|---|
| `whoami` | Who is authenticated + which org | — | Sanity-check workspace |
| `list_personas` | Lightweight persona index (handle + name) | — | `get_persona` with the chosen handle |
| `get_persona` | Full attributes of one persona | `handle` (`persona:<handle>`) | Draft / score against it |
| `get_all_personas` | Every persona, full detail | — | Only when the full set is explicitly required |
| `get_brand_voice` | Org brand voice (do/don't rules) | — | Apply while drafting publishable copy |
| `list_messaging_frameworks` | Framework index (id + title) | — | `get_messaging_framework({id})` |
| `get_messaging_framework` | One framework's full content | `id` XOR `title` | Apply to the named-framework task |
| `get_all_messaging_frameworks` | Every framework, full content | — | Pair with `get_brand_voice` at content kickoff |
| `query_market_research` | Synthesized answer from buyer interviews + org docs | `query`, `explain`, `keywords`, `temporalRange` | Relay with Sources verbatim + link |
| `score_content` | Persona-informed content score (0–100) + recommendations | `content`, `persona_handle` | Revise → resubmit until threshold |

## Anti-patterns

- ❌ Guessing or inventing `persona:<handle>` IDs instead of calling `list_personas`.
- ❌ Packing multiple questions, comparisons, or "and what about X" clauses into one `query_market_research` call.
- ❌ Putting dates or temporal phrases ("recent", "2026", "last quarter") in `keywords` instead of `temporalRange`.
- ❌ Calling `list_messaging_frameworks` for content generation — that's `get_all_messaging_frameworks`.
- ❌ Fetching a single framework for general "make it on-brand" copy — that under-applies the org's voice.
- ❌ Skipping `get_brand_voice` on publishable content, or calling it on internal artifacts.
- ❌ Paraphrasing or dropping the "GetWhys Sources" paragraph, the `view_in_getwhys` link, or the † markers.
- ❌ Answering from general knowledge after `no_data: true` instead of saying what the corpus didn't cover.
