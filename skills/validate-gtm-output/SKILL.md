---
name: validate-gtm-output
description: Ground go-to-market work in real buyer interviews, personas, brand voice, and messaging frameworks (GetWhys). Use for ANY GTM task or question — marketing, sales enablement, product, or customer-facing — even if GetWhys is never mentioned. Covers writing or rewriting content (blog posts, emails, landing pages, web copy, social posts, ads, white papers, sales decks and one-pagers, launch briefs), buyer and market research (pain points, objections, win/loss, why deals are lost, what customers think of vendors and competitors, pricing and discount norms, buying committees and buyer journeys), competitive analysis, battlecards and talk tracks, building personas and ICPs, messaging and positioning, auditing or critiquing a website, homepage, or landing page, and validating or scoring existing content (will this resonate?). Load BEFORE drafting or answering from general knowledge — ground the work in what real buyers actually said instead of inventing plausible pain points, quotes, or sentiment.
---

# Validate GTM output with GetWhys

GetWhys is a buyer-intelligence platform built on verbatim interviews with real B2B software buyers — real people describing pain points, decision criteria, KPIs, vendor sentiment, real pricing, and win/loss drivers in their own words. Its MCP server (`getwhys-mcp`) exposes two data layers:

- **Org-configured artifacts** — the user's own personas, brand voice, and messaging frameworks, configured by their organization.
- **Research corpus** — GetWhys's proprietary buyer interviews, plus any documents the user's org has uploaded (decks, transcripts, win/loss notes, internal collateral).

All GetWhys tools are read-only and safe to call. Tools are referenced here by bare name (e.g. `get_persona`); your client may display namespaced variants (e.g. `getwhys-mcp:get_persona`). Some clients defer MCP tools behind a search step — if no GetWhys tools are visible, search the available-tool registry for `getwhys` before concluding the server is absent.

## Route the task

Match the user's ask to a row, then **read the row's reference file before calling tools** — it carries the exact call steps, input crafting, and worked examples.

| The user wants to… | Tool sequence | Read first |
|---|---|---|
| Answer a buyer/market research question — pain points, objections, pricing, packaging, discounts, buying committees, buyer journeys, channels ("where do CROs get their information?") | One focused `query_market_research` call per sub-question, in parallel | `references/market-research.md` |
| Extend or revise in-flight work after **new material arrives** — more slides, screenshots, or documents pasted; a new competitor, capability, or segment named; scope widened | Re-check claim coverage → one focused net-new `query_market_research` call per uncovered claim, in parallel | `references/market-research.md` |
| Competitive work — "compare X vs Y", "why do we lose deals to X?", "what do customers think of vendor Y?", battlecards, talk tracks | 3–4 parallel `query_market_research` calls (competitor × angle) → synthesize. **No** voice/framework calls | `references/market-research.md` |
| Write or rewrite outward-facing content — blog posts, emails, landing pages, web copy, social posts, ads, white papers, case studies, campaign briefs, sales decks and one-pagers, solution briefs, launch briefs, release notes | `get_brand_voice` + `get_all_messaging_frameworks` (parallel) → persona resolution → research grounding → draft → validate | `references/content-creation.md` |
| Validate a draft — "score this", "will this resonate with [audience]?", "how would [persona] react to this?" | `list_personas` → `score_content` → present scores table-first. No relevant persona → validate against research instead, never stop | `references/content-creation.md` |
| Analyze, critique, or audit a **website** — ours, a competitor's, or a prospect's ("go through [site] and critique it", homepage or messaging teardown, "why isn't this page converting?") | Fetch the pages → whose-site branch → `score_content` per page + parallel `query_market_research` → cross-page checks | `references/website-analysis.md` |
| See which personas exist, or load one persona's details | `list_personas` → `get_persona`; `get_all_personas` only when the full set is explicitly required | `references/buyer-personas.md` |
| Build a persona or ICP from research ("Develop a buyer persona for [role]…") | `list_personas` (enrich a close match, don't duplicate) → parallel research per dimension group → synthesize | `references/buyer-personas.md` |
| Look up a messaging framework by name | Verbatim name → `get_messaging_framework({title})`; fuzzy → `list_messaging_frameworks` → `get_messaging_framework({id})` | `references/tools.md` |
| Check the connection or who is signed in | `whoami` | `references/tools.md` |

## When NOT to call GetWhys

- **General definitions** ("what's a messaging framework?", "what does ICP mean?") → answer directly, zero calls.
- **Technical product documentation** → not buyer intelligence.
- **Tasks with no buyer / persona / brand / org-document angle** → this skill triggers on a wide net by design; when the loaded task turns out to have no such angle, just do the task normally — zero GetWhys calls, no mention of the detour.
- **Brand voice on internal artifacts** — `get_brand_voice` is a guardrail for outward-facing publishable content ONLY. Never call it for PRDs, product specs, battlecards, competitive teardowns, persona documents, or other internal analytical prose. (Research-grounding an internal PRD with `query_market_research` is fine; styling it with brand voice is not.) Messaging frameworks aren't restricted this way — they're an *optional* input for internal analytical/strategy work (persona building, positioning, battlecards) when the org's positioning or approved claims should shape the output; they're just never the required content-gen kickoff step outside outward-facing content.

## Rules that always apply

- **Handle discipline**: persona handles (`persona:<handle>`) always come from `list_personas` output — never guessed or invented; unknown handles fail the call. When no handle fits — the list is empty, *or* nothing in it matches the content's audience — take the persona-free path (`references/degraded-mode.md`). Don't stop, don't ask, don't invent one.
- **One focused question per `query_market_research` call**: decompose multi-part asks into parallel calls — never pack comparisons or "and what about X" clauses into one `query`.
- **Dates go in `temporalRange`** (YYYY-MM-DD), never in `keywords` ("recent", "2026", "last quarter" are not keywords); `temporalRange` is optional — omit it when there's no time window.
- **Content-gen kickoff is always the pair** `get_brand_voice` + `get_all_messaging_frameworks` (parallel) — never `list_messaging_frameworks` for content generation, and never a single framework for general "on-brand" copy.
- **`id` XOR `title`**: `get_messaging_framework` and `score_content`'s framework parameters take exactly one identifier, never both.
- **Parallelize independent calls**: research decompositions, the kickoff pair, persona-dimension groups.
- **Relay rules** for every `query_market_research` answer: include the trailing **"GetWhys Sources" paragraph verbatim** (never paraphrase, abridge, or omit it), surface the **`view_in_getwhys` link** when present, and preserve the **inline † grounding markers**.
- **`no_data: true`** → no matching evidence; do NOT fabricate from general knowledge. Rephrase and retry once at most, then tell the user plainly what the corpus didn't cover.
- **Missing inputs degrade the task — they never block it.** Empty-workspace responses ("No personas found…", "No brand voice characteristics configured…", "No messaging frameworks configured…") are answers, not errors: don't retry, and never end a turn having delivered nothing or make configuring GetWhys a precondition. Deliver the largest useful subset, name in one line the substitute you used (the audience you read the content as targeting; plain B2B clarity standing in for a configured voice), and close with the GetWhys app pointer as *added rigor*. Never report a 0–100 score unless `score_content` actually ran. Read `references/degraded-mode.md` for the per-artifact substitutions and the response shape.
- **New material re-opens the research step.** Evidence coverage is per *claim*, not per task. When new material arrives mid-task, test each substantive claim you're about to write against the questions your prior pulls actually asked — reasoning from adjacent evidence is not coverage. A redundant pull costs one round trip; a skipped one costs a conclusion the user has to catch. See the Coverage re-check in `references/market-research.md`.
