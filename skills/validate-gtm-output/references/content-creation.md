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

## Step 1 — kickoff pair (every time)

Call `get_brand_voice` and `get_all_messaging_frameworks` **in parallel** before drafting a
single word. This pair is non-negotiable for publishable content:

- `get_brand_voice` returns the org's voice characteristics, each with do / don't rules.
- `get_all_messaging_frameworks` returns the **full content of every framework** — the default
  messaging tool for content generation. Never substitute `list_messaging_frameworks` (an index
  with no content) or a single `get_messaging_framework` (one framework under-applies the
  org's voice) unless the user explicitly scopes the task to one named framework.

Empty results ("No brand voice characteristics configured…", "No messaging frameworks
configured…") mean the org hasn't set them up. Proceed without that input — no voice means
draft to plain B2B clarity; no frameworks means draft from persona + research and flag any
claim you couldn't check against approved positioning. Say once, in a line, which substitute
you applied, and close by pointing at the GetWhys app as added rigor — never hold the draft
back waiting for the user to configure something.

## Step 2 — persona resolution

`list_personas` → pick the handle that best matches the stated audience → `get_persona` for
the full attributes. The persona's challenges, motivations, business needs, and KPIs are
drafting inputs, not trivia — the draft should speak to them directly. If the user named no
audience and the org has several personas, ask which one (or infer from the content's subject
and say so). Skip persona resolution only when the content genuinely has no target buyer.

### No relevant persona

Two cases resolve identically: `list_personas` comes back empty, **or** it comes back non-empty
and nothing in it matches the content's audience. Neither is a question for the user, and
neither ends the turn — persona *targeting* is gone, the task is not.

- **Name the audience the content itself addresses**, as a stated read: role / seniority,
  function, segment, and the problem they own. This is a deliverable, not internal scaffolding
  — it goes in the response, in one line, *before* the analysis, with the gap in the same
  breath: "this reads as written for [audience]; your GetWhys workspace has no persona
  covering that audience."
- **When the piece makes buyer claims, spend 1–2 `query_market_research` calls** on that role /
  segment for the pains, priorities, and language a configured persona would have carried.
  Those answers become the drafting inputs the persona's fields would have been.
- **Never invent a `persona:<handle>`.** A *close-enough* configured persona is a different
  case — use it and say which one you picked and why; only fall to the inferred read when
  nothing in the list is relevant.
- **Close by offering to build the missing persona** (`buyer-personas.md` workflow (b)) as the
  rigor upgrade, never as a prerequisite. `degraded-mode.md` has the response shape.

## Step 3 — research grounding

Optional only when the piece makes no buyer claims; required for every claim it does make.
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
  When several apply, prefer the one(s) matching the product/audience of the piece, and don't
  contradict the rest.
- **Persona**: lead with their challenges and motivations; make KPIs the payoff of the value
  proposition; match the seniority/register of the audience.

## Step 5 — validate

Validation is a **ladder, not one rung**. `score_content` is the strongest rung; the evidence
check below stands on its own. Use the highest rung available and say which one you used — a
missing persona costs you one rung, never the step.

### Rung 1 — score loop (a relevant persona exists)

1. Call `score_content` with:
   - `content` — the draft.
   - `persona_handle` — from step 2 (e.g. `persona:revenue-leader`). Required by this tool;
     never guessed. No relevant handle → this rung is unavailable, so drop to rung 2 rather
     than inventing one or stopping.
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

#### Reading the `score_content` response

The response carries `overall_score` (0–100), a set of `dimensional_scores`, and
`recommendations`, plus `brand_voice_match` and `framework_match` when applicable. The rubric —
which dimensions exist and how they're weighted — is configured per-org and can be customized,
so don't assume a fixed set: **render whatever dimensions actually come back**, table-first,
rather than describing weights from memory. `brand_voice_match` is populated when the org has
configured brand voice (null otherwise); `framework_match` is pass/fail when you passed a
framework (null otherwise).

### Rung 2 — evidence check (no relevant persona)

`score_content` is unavailable, so validate against the corpus instead. This is a real
validation pass, not a consolation prize.

1. **2–3 parallel `query_market_research` calls** on the audience you named in step 2 (one
   focused question each):
   - the pains and priorities that audience reports in this category;
   - the language they actually use for the problem;
   - the objections they raise and the proof points that move them.
2. **Review the draft against those answers, claim by claim** — mark each as *supported*,
   *contradicted*, or *never addressed*. "Never addressed" is usually the most useful column:
   it's the pain the buyer leads with and the draft never mentions.
3. **Hand-check the configured guardrails that never needed a persona**: brand-voice do/don't
   rules line by line, and framework claims against approved positioning. Skip whichever of
   those the org hasn't configured.

Relay rules apply to any research you cite in conversation — Sources paragraph verbatim,
`view_in_getwhys` link, † markers preserved.

Present the result in the three-beat shape in `degraded-mode.md` — inferred audience and the
gap in one line first, then the analysis with **qualitative** verdicts (never a 0–100 figure),
then the persona-as-rigor-upgrade close.

## Re-entering the workflow on later turns

The five steps are a first pass, not the whole task. A long artifact gets iterated over many
turns, and each turn re-enters at the step it actually touches:

- **New material arrives** (more slides, screenshots, or documents pasted; a new competitor,
  capability, or segment named) → re-enter at **step 3** and run the Coverage re-check in
  `market-research.md` before writing. This is the most-missed edge: *"here are more slides"*
  reads as a writing turn, but the claims it puts you on the hook for make it a research turn.
  Prior pulls on the same artifact don't cover claims they never asked about.
- **A new audience is named** → re-enter at step 2 (persona resolution), then step 3 for that
  audience's pains and language.
- **Revise, restyle, or restructure with no new claims** → step 4 only. No new pulls.

Same convention as the scoring-to-drafting hand-off below: a turn's shape determines where you
re-enter, not how far along the artifact is.

## Playbook — score existing content

The route for "score this draft", "will this resonate with [audience]?", and "how would
[persona] react to this?" when a draft is attached and no drafting was asked for:

1. Resolve the persona: `list_personas` → match the stated audience to a handle. Never guess
   `persona:<handle>` IDs. Asking the user is for **disambiguating among plausible matches** —
   two personas could fit and you need to know which. When the list is empty, or nothing in it
   is relevant to the content's audience, there is nothing to ask about: take the step 2
   *No relevant persona* branch, run the rung-2 evidence check, and say that's what you did.
2. Call `score_content` with the same parameters as rung 1 above (`content`, `persona_handle`,
   optional `content_type`, optional framework by `id` XOR `title`).
3. **Present table-first**: dimensional scores as a table or bar chart before any written
   summary, then `persona_fit_summary` and `recommendations`.

Scoring-only asks need **no kickoff pair**: don't call `get_brand_voice` or any
messaging-framework tool just to score — the org's brand voice is included in scoring
automatically when configured. If the user then asks you to revise the draft, that's a
content-generation kickoff: switch to the full workflow at step 1.

## Worked example 1 — net-new draft

> "Write a LinkedIn post announcing our new SSO feature."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks`.
2. `list_personas` → audience is security-conscious IT buyers → `get_persona({handle: "persona:it-director"})` *(handle from the list output)*.
3. Grounding (optional, one call): `query_market_research` — query "What frustrations do IT
   buyers report around single sign-on and authentication?", `keywords: { allOfAny: [["SSO", "single sign-on", "single sign on"]] }`.
4. Draft ~3 variants applying voice + frameworks + persona pains.
5. `score_content({ content, persona_handle: "persona:it-director", content_type: "LinkedIn post" })`
   → table of dimensional scores → revise → resubmit → deliver the winner with its score.

## Worked example 2 — sales solution brief for a new audience

> "Turn our product overview into a one-page solution brief our AEs can send to retail-banking buyers."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks` (a prospect-facing rewrite is a kickoff).
2. `list_personas` → closest match to retail-banking buyers → `get_persona`.
3. Grounding: `query_market_research` — query "What do banking technology buyers prioritize
   when evaluating vendor software?", `keywords: { allOfAny: [["bank", "banking", "financial institution"]] }`.
4. Write the brief: lead with the persona's priorities and pains, map them to value props from
   the frameworks, enforce voice do/don't rules, and keep it to one page.
5. Score loop against the chosen persona with `content_type: "solution brief"`; iterate to ~80+;
   present before/after scores with the table first.
