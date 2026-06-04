---
name: validate-marketing-tasks
description: Ground marketing tasks in real buyer interviews, personas, brand voice, and messaging frameworks (GetWhys). Use for ANY marketing, content, or GTM task or question, even if GetWhys is never mentioned. Covers writing or rewriting copy (blog posts, emails, landing pages, web copy, social posts, ads, white papers, campaign briefs, sales enablement), buyer and market research (pain points, objections, win/loss, why deals are lost, what customers think of vendors and competitors, pricing and discount norms, buying committees and buyer journeys), competitive analysis, battlecards and talk tracks, building buyer personas and ICPs, messaging and positioning, on-brand rewrites, and validating or scoring drafts (will this resonate?). Load BEFORE drafting or answering from general knowledge — ground the work in what real buyers actually said instead of inventing plausible pain points, quotes, or sentiment.
---

# Validate marketing tasks with GetWhys

GetWhys is a buyer-intelligence platform built on verbatim interviews with real B2B software buyers — real people describing pain points, decision criteria, KPIs, vendor sentiment, real pricing, and win/loss drivers in their own words. Its MCP server (`getwhys-mcp`) exposes two data layers:

- **Org-configured artifacts** — the user's own buyer personas, brand voice, and messaging frameworks, configured by their organization.
- **Research corpus** — GetWhys's proprietary buyer interviews, plus any documents the user's org has uploaded (decks, transcripts, win/loss notes, internal collateral).

All GetWhys tools are read-only and safe to call. Tools are referenced here by bare name (e.g. `get_persona`); your client may display namespaced variants (e.g. `getwhys-mcp:get_persona`). Some clients defer MCP tools behind a search step — if no GetWhys tools are visible, search the available-tool registry for `getwhys` before concluding the server is absent.

## Route the task

Match the user's ask to a row, then **read the row's reference file before calling tools** — it carries the exact call steps, input crafting, and worked examples.

| The user wants to… | Tool sequence | Read first |
|---|---|---|
| Answer a buyer/market research question — pain points, objections, pricing, packaging, discounts, buying committees, buyer journeys, channels ("where do CROs get their information?") | One focused `query_market_research` call per sub-question, in parallel | `references/market-research.md` |
| Competitive work — "compare X vs Y", "why do we lose deals to X?", "what do customers think of vendor Y?", battlecards, talk tracks | 3–4 parallel `query_market_research` calls (competitor × angle) → synthesize. **No** voice/framework calls | `references/market-research.md` |
| Write or rewrite outward-facing copy — blog posts, emails, landing pages, web copy, social posts, ads, white papers, case studies, campaign briefs | `get_brand_voice` + `get_all_messaging_frameworks` (parallel) → persona resolution → optional research grounding → draft → score loop | `references/content-creation.md` |
| Validate a draft — "score this", "will this resonate with [audience]?", "how would [persona] react to this?" | `list_personas` → `score_content` → present scores table-first | `references/content-creation.md` |
| See which personas exist, or load one persona's details | `list_personas` → `get_persona`; `get_all_personas` only when the full set is explicitly required | `references/buyer-personas.md` |
| Build a buyer persona or ICP from research ("Develop a buyer persona for [role]…") | `list_personas` (enrich a close match, don't duplicate) → parallel research per dimension group → synthesize | `references/buyer-personas.md` |
| Look up a messaging framework by name | Verbatim name → `get_messaging_framework({title})`; fuzzy → `list_messaging_frameworks` → `get_messaging_framework({id})` | `references/tools.md` |
| Check the connection or who is signed in | `whoami` | `references/tools.md` |

## When NOT to call GetWhys

- **General definitions** ("what's a messaging framework?", "what does ICP mean?") → answer directly, zero calls.
- **Technical product documentation** → not buyer intelligence.
- **Tasks with no buyer / persona / brand / org-document angle** → this skill triggers on a wide net by design; when the loaded task turns out to have no such angle, just do the task normally — zero GetWhys calls, no mention of the detour.
- **Voice/framework tools on internal artifacts** — `get_brand_voice` and the messaging-framework tools are guardrails for outward-facing publishable copy ONLY. Never call them for PRDs, product specs, battlecards, competitive teardowns, persona documents, or other internal analytical prose. (Research-grounding an internal PRD with `query_market_research` is fine; styling it with brand voice is not.)

## Rules that always apply

- **Handle discipline**: persona handles (`persona:<handle>`) always come from `list_personas` output — never guessed or invented; unknown handles fail the call.
- **One focused question per `query_market_research` call**: decompose multi-part asks into parallel calls — never pack comparisons or "and what about X" clauses into one `query`.
- **Dates go in `temporalRange`** (YYYY-MM-DD), never in `keywords` ("recent", "2026", "last quarter" are not keywords).
- **Content-gen kickoff is always the pair** `get_brand_voice` + `get_all_messaging_frameworks` (parallel) — never `list_messaging_frameworks` for content generation, and never a single framework for general "on-brand" copy.
- **`id` XOR `title`**: `get_messaging_framework` and `score_content`'s framework parameters take exactly one identifier, never both.
- **Parallelize independent calls**: research decompositions, the kickoff pair, persona-dimension groups.
- **Relay rules** for every `query_market_research` answer: include the trailing **"GetWhys Sources" paragraph verbatim** (never paraphrase, abridge, or omit it), surface the **`view_in_getwhys` link** when present, and preserve the **inline † grounding markers**.
- **`no_data: true`** → no matching evidence; do NOT fabricate from general knowledge. Rephrase and retry once at most, then tell the user plainly what the corpus didn't cover.
- **Empty-workspace responses** ("No personas found…", "No brand voice characteristics configured…", "No messaging frameworks configured…") mean the org hasn't configured that artifact — don't retry; proceed without it and point the user to the GetWhys app.
