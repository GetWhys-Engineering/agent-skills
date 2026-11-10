# Personas — deep guidance

Persona work runs in two directions: **using** the personas the org has configured, and
**building** new personas from buyer research. Keep them straight — and route "how would
[persona] react?" asks correctly (see Disambiguation).

## (a) Use org-configured personas

Selection rules:

- `list_personas` — the lightweight index (`handle` + `name`). Call it **first** whenever a
  workflow needs a target persona: content generation, scoring, persona-scoped research.
- `get_persona({handle})` — full attributes for the one persona you'll target. Handles come
  from the list output, format `persona:<handle>`; an unknown handle fails the call, so never
  guess one.
- `get_all_personas` — every persona in full detail, one response. **Only** when the user
  explicitly requires the full set ("show me all our personas", "compare our personas").
  Routine single-persona workflows use list → get.
- **No relevant persona** — the list came back empty, *or* it came back non-empty and nothing
  in it matches the audience at hand. Both resolve the same way. What's unavailable is the
  persona-*targeted* tooling (`get_persona`, `score_content`); nothing else is, and neither
  case is a question for the user. Continue with the stated audience read from
  `content-creation.md` step 2 — name the role / seniority, function, segment, and problem the
  work actually addresses, in one line, up front — then do the work. Offer workflow (b) below
  (build that persona from the corpus) as the rigor upgrade, not a precondition. This is the
  same instinct as the closing rule in (b): **refinement offers, not blocking questions**.

A full persona carries: name, job titles, description, challenges, motivations, business
needs, KPIs, key stakeholders, watering holes, and interests. Use them to calibrate work:

- **Drafting** — speak to the challenges and motivations; position value against the KPIs;
  match register to seniority.
- **Scoring** — `score_content` reads the same fields; a low Relevance score usually means the
  draft missed the persona's stated challenges/KPIs.
- **Research scoping** — the persona's titles and industry sharpen `query_market_research`
  questions ("What slows down [title]s in [industry] when …").

## (b) Build a new persona from research

The classic shape: "Develop a buyer persona for [role]" — often with a section checklist
(Titles / Description / Challenges / Motivations / KPIs / …).

1. **Check `list_personas` first.** If a close match already exists, `get_persona` it and
   **enrich** it with fresh research — don't build a duplicate from scratch. Tell the user
   you're extending their configured persona.
2. **Decompose the dimensions into 2–4 parallel `query_market_research` calls**, grouping
   related dimensions per call (one focused question each — see `market-research.md`). The
   standard dimension set and a workable grouping:

   | Call | Dimensions covered | Example query |
   |---|---|---|
   | 1 | Job titles; description/responsibilities | "What are the responsibilities and typical titles of [role] at [segment] companies?" |
   | 2 | Challenges/pain points; motivations | "What challenges and goals do [role]s describe in their work?" |
   | 3 | Watering holes/information sources; key stakeholders/buying committee | "Where do [role]s get information, and who do they involve in purchase decisions?" |
   | 4 | Business priorities; KPIs; interests/trends | "What metrics and priorities do [role]s say they are measured on?" |

   Fold the grouping to fewer calls when the user's template is shorter.
3. **Synthesize into the user's template** — or, if they gave none, the default section set
   above. Preserve † markers and include each call's "GetWhys Sources" paragraph (grouped at
   the end is fine) plus `view_in_getwhys` links.
4. **Close with refinement offers, not blocking questions**: offer to segment by industry,
   company size, or GTM motion — don't interrogate the user before doing the first pass.

A persona document is an **internal analytical artifact** — don't style it with
`get_brand_voice`. Messaging frameworks, by contrast, are an optional input: pull one in when
the org's positioning or value props should shape the persona; otherwise skip it (research is
the backbone here).

## Disambiguation

- "How would [persona] react to **this draft** / will **this** resonate?" — a draft is
  attached → resolve the handle via `list_personas`, then `score_content`. Not research.
- "What does [audience] care about / struggle with?" — a question *about* an audience with no
  draft attached → `query_market_research` (persona fields via `get_persona` can sharpen the
  question, when a matching persona exists).
- "Show me our [role] persona" — org artifact lookup → `list_personas` → `get_persona`.
- "Build/update a persona for [role]" — research workflow (b), starting from `list_personas`.
