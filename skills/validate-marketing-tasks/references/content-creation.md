# Creating outward-facing content — deep guidance

The end-to-end workflow for anything the user will publish or send: blog posts, emails,
landing pages, web copy, social/LinkedIn posts, ad copy, white papers, case studies,
one-pagers, campaign briefs, content calendars, sales pitches, customer stories, scripts.
It covers three ask shapes equally:

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
configured…") mean the org hasn't set them up — proceed without that input, mention it once,
and point the user to the GetWhys app.

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
  When several apply, prefer the one(s) matching the product/audience of the piece, and don't
  contradict the rest.
- **Persona**: lead with their challenges and motivations; make KPIs the payoff of the value
  proposition; match the seniority/register of the audience.

## Step 5 — score loop

1. Call `score_content` with:
   - `content` — the draft.
   - `persona_handle` — from step 2 (e.g. `persona:vp-marketing`). Required; never guessed.
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

### The default rubric

Unless the org has configured custom scoring criteria, `overall_score` (0–100) is the weighted
composite of five dimensions:

| Dimension | Weight |
|---|---|
| Relevance (pain points, motivations, KPIs addressed) | 40% |
| CTA / Persuasion | 30% |
| Clarity & Messaging | 10% |
| Brand Recall & Identity | 10% |
| Emotional Engagement | 10% |

Alongside the dimensions: `brand_voice_match` (the org's brand voice is automatically included
when configured; null otherwise) and `framework_match` (pass/fail when you passed a framework;
null otherwise).

**Custom-rubric caveat**: orgs can override the rubric, so the dimensions and weights in a
response may differ from the table above. Always render whatever dimensions actually come back
rather than assuming the default five.

## Worked example 1 — net-new draft

> "Write a LinkedIn post announcing our new SSO feature."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks`.
2. `list_personas` → audience is security-conscious IT buyers → `get_persona({handle: "persona:it-director"})` *(handle from the list output)*.
3. Grounding (optional, one call): `query_market_research` — query "What frustrations do IT
   buyers report around single sign-on and authentication?", `keywords: { allOfAny: [["SSO", "single sign-on", "single sign on"]] }`.
4. Draft ~3 variants applying voice + frameworks + persona pains.
5. `score_content({ content, persona_handle: "persona:it-director", content_type: "LinkedIn post" })`
   → table of dimensional scores → revise → resubmit → deliver the winner with its score.

## Worked example 2 — rewrite for a new audience

> "Improve this homepage section for retail banking buyers."

1. Parallel: `get_brand_voice` + `get_all_messaging_frameworks` (a rewrite is a kickoff).
2. `list_personas` → closest match to retail-banking buyers → `get_persona`.
3. Grounding: `query_market_research` — query "What do banking technology buyers prioritize
   when evaluating vendor software?", `keywords: { allOfAny: [["bank", "banking", "financial institution"]] }`.
4. Rewrite the section: keep the user's structure, swap generic claims for persona-relevant
   pains/KPIs, enforce voice do/don't rules.
5. Score loop against the chosen persona with `content_type: "web copy"`; iterate to ~80+;
   present before/after scores with the table first.
