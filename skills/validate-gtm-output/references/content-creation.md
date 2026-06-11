# Creating and scoring content — deep guidance

Two entry points share this file:

- **Creating outward-facing content** (steps 1–5 below) — anything the user will publish or
  send, across any GTM function: blog posts, emails, landing pages, web copy, social/LinkedIn
  posts, ad copy, white papers, case studies, one-pagers, campaign briefs, content calendars,
  sales pitches and decks, solution briefs, customer stories, product launch briefs, release
  notes and feature announcements, scripts.
- **Scoring an existing draft** with no drafting asked for — jump straight to the
  "Playbook — score existing content" section below.

The creation workflow covers three ask shapes equally:

- **Net-new drafts** — "write a launch email for…", "draft a blog post about…"
- **Rewrites / optimizations** — "improve this page for [audience]", "make this more relevant
  to [title]", "adapt this for LinkedIn" — a rewrite is a content-generation kickoff, not an edit.
- **Longer-form artifacts** — white papers, case studies, thought-leadership posts, content
  calendars: same workflow, with research grounding doing more of the work.

## Step 1 — kickoff pair + framework selection (every time)

Call `get_brand_voice` and `get_all_messaging_frameworks` **in parallel** before drafting a
single word. This pair is non-negotiable for publishable content:

- `get_brand_voice` returns the org's voice characteristics, each with do / don't rules.
- `get_all_messaging_frameworks` returns the full content of the org's **global (always-on)**
  messaging frameworks — the org-wide guardrails that apply to every piece. These are the
  baseline; never reduce the org's voice to a single framework.

Then **select the situational frameworks**: call `list_messaging_frameworks` — an index where
each entry carries an applicability `summary` and a `scope` — and for any **`use_case`** framework
whose `summary` matches the product / channel / audience of this piece, pull its full content with
`get_messaging_framework({id})`. `global` frameworks are already covered by `get_all`; don't
re-fetch them.

Empty results ("No brand voice characteristics configured…") mean the org hasn't set that up —
proceed without it, mention it once, and point the user to the GetWhys app. If
`get_all_messaging_frameworks` returns "No global (always-on) messaging frameworks configured…",
that only rules out *global* frameworks — still call `list_messaging_frameworks` for `use_case`
ones before drafting without any.

## Step 2 — persona resolution

`list_personas` → pick the handle that best matches the stated audience → `get_persona` for
the full attributes. The persona's challenges, motivations, business needs, and KPIs are
drafting inputs, not trivia — the draft should speak to them directly. If the user named no
audience and the org has several personas, ask which one (or infer from the content's subject
and say so). Skip persona resolution only when the content genuinely has no target buyer.

## Step 3 — optional research grounding

When the piece makes claims about buyer pain, market reality, or competitor behavior, ground
them with focused `query_market_research` calls (one question per call, in parallel — see
`market-research.md`). Typical grounding asks: the target persona's top pain points in this
product category; the language buyers use about the problem; proof points/objections to
pre-empt. Relay rules apply when you cite the research in conversation; in the draft itself,
use the findings as inputs, not as quoted output.

## Step 4 — draft

Combine the three inputs:

- **Brand voice**: apply every characteristic's "do" rules; treat "don't" rules as hard
  constraints to check the draft against line-by-line.
- **Messaging frameworks**: frameworks supply positioning, value props, and approved claims.
  The **global** frameworks (from `get_all`) always apply; the **`use_case`** frameworks you
  selected by relevance in step 1 layer on top for this specific piece. Don't contradict the
  globals.
- **Persona**: lead with their challenges and motivations; make KPIs the payoff of the value
  proposition; match the seniority/register of the audience.

## Step 5 — score loop

1. Call `score_content` with:
   - `content` — the draft.
   - `persona_handle` — from step 2 (e.g. `persona:revenue-leader`). Required; never guessed.
   - `content_type` — optional but useful: "email subject line", "ad copy", "blog post",
     "landing page", "LinkedIn post".
   - `messaging_framework_id` **or** `messaging_framework_title` — optional, exactly one, to
     additionally score against a specific framework. Use `list_messaging_frameworks` to find
     ids; a title-collision error means re-call with one of the returned ids.
2. **Present table-first**: render `dimensional_scores` as a table or bar chart *before* any
   written summary — never a wall of text. Then `persona_fit_summary`, then `recommendations`.
3. Revise the draft applying the recommendations, resubmit, and repeat until `overall_score`
   meets the user's threshold — default **~80** if they didn't set one. Report the
   before/after scores so the user sees the trajectory.

### Reading the `score_content` response

The response carries `overall_score` (0–100), a set of `dimensional_scores`, and
`recommendations`, plus `brand_voice_match` and `framework_match` when applicable. The rubric —
which dimensions exist and how they're weighted — is configured per-org and can be customized,
so don't assume a fixed set: **render whatever dimensions actually come back**, table-first,
rather than describing weights from memory. `brand_voice_match` is populated when the org has
configured brand voice (null otherwise); `framework_match` is pass/fail when you passed a
framework (null otherwise).

## Playbook — score existing content

The route for "score this draft", "will this resonate with [audience]?", and "how would
[persona] react to this?" when a draft is attached and no drafting was asked for:

1. Resolve the persona: `list_personas` → match the stated audience to a handle. Never guess
   `persona:<handle>` IDs; if no persona matches, ask the user which to use rather than
   inventing one.
2. Call `score_content` with the same parameters as step 5 above (`content`, `persona_handle`,
   optional `content_type`, optional framework by `id` XOR `title`).
3. **Present table-first**: dimensional scores as a table or bar chart before any written
   summary, then `persona_fit_summary` and `recommendations`.

Scoring-only asks need **no kickoff pair**: don't call `get_brand_voice` or any
messaging-framework tool just to score — the org's brand voice is included in scoring
automatically when configured. If the user then asks you to revise the draft, that's a
content-generation kickoff: switch to the full workflow at step 1.

## Worked example 1 — net-new draft

> "Write a LinkedIn post announcing our new SSO feature."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks` (global guardrails).
2. `list_messaging_frameworks` → scan summaries + scope → if a `use_case` framework matches (e.g. a security or product-launch framework), `get_messaging_framework({id})` for its full content.
3. `list_personas` → audience is security-conscious IT buyers → `get_persona({handle: "persona:it-director"})` *(handle from the list output)*.
4. Grounding (optional, one call): `query_market_research` — query "What frustrations do IT
   buyers report around single sign-on and authentication?", `keywords: { allOfAny: [["SSO", "single sign-on", "single sign on"]] }`.
5. Draft ~3 variants applying voice + frameworks + persona pains.
6. `score_content({ content, persona_handle: "persona:it-director", content_type: "LinkedIn post" })`
   → table of dimensional scores → revise → resubmit → deliver the winner with its score.

## Worked example 2 — sales solution brief for a new audience

> "Turn our product overview into a one-page solution brief our AEs can send to retail-banking buyers."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks` (a prospect-facing rewrite is a kickoff; `get_all` = global guardrails).
2. `list_messaging_frameworks` → pull any `use_case` framework whose `summary` fits banking / financial-services buyers via `get_messaging_framework({id})`.
3. `list_personas` → closest match to retail-banking buyers → `get_persona`.
4. Grounding: `query_market_research` — query "What do banking technology buyers prioritize
   when evaluating vendor software?", `keywords: { allOfAny: [["bank", "banking", "financial institution"]] }`.
5. Write the brief: lead with the persona's priorities and pains, map them to value props from
   the frameworks, enforce voice do/don't rules, and keep it to one page.
6. Score loop against the chosen persona with `content_type: "solution brief"`; iterate to ~80+;
   present before/after scores with the table first.
