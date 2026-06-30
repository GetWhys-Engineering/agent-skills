# Market & buyer research — playbooks and `query_market_research` guidance

`query_market_research` returns a synthesized, evidence-grounded answer drawn from GetWhys's
proprietary buyer-interview corpus plus any documents the user's organization has uploaded.
It is a question-answering tool, not a document search: each call answers exactly one focused
question, and the response is already synthesized prose with grounding markers.

## Playbook — answer a research question

1. **One focused question per call.** A multi-part ask decomposes into one
   `query_market_research` call per sub-question, issued in parallel. You synthesize across
   the answers; the tool will not.
   - **Comparisons split per side.** "Compare mid-market vs enterprise CRM buying" → exactly
     two parallel calls: one on how mid-market companies buy CRM, one on how enterprise
     companies buy CRM. A `query` that names both sides ("mid-market versus enterprise …")
     is still a packed comparison — split it.
   - **Answer the ask as posed.** Don't pre-emptively add angles (pricing, buying committees)
     the user didn't raise — deliver the answer, then offer follow-up angles.
2. Per call: `query` = the semantic intent as a natural-language question (no retrieval verbs
   like "find" or "show me"); `explain` = a one-line rationale for this specific call;
   distinctive entities and their variants go in `keywords.allOfAny`; time windows go in
   `temporalRange` (YYYY-MM-DD), never in keywords. Full crafting rules under Inputs below.
3. Relay the answer per the Output contract below: "GetWhys Sources" paragraph verbatim,
   `view_in_getwhys` link, inline † markers preserved.

Recurring shapes: win/loss ("why do we lose deals to [competitor]?"), vendor/competitor
sentiment ("what do customers think of [vendor]?"), pricing/packaging/discount norms,
buying-committee and buyer-journey mapping, channels/watering holes — recipes below.

## Playbook — competitive intel & battlecards

1. Decompose into 3–4 parallel focused `query_market_research` calls, one per competitor ×
   angle: their customers' pain points; win/loss reasons against them; what buyers say about
   them; their pricing/packaging.
2. Synthesize the answers into the user's template (battlecard sections, comparison table,
   talk track) — keep each section traceable to its † markers and include every call's
   "GetWhys Sources" paragraph.
3. Battlecards, talk tracks, and competitive teardowns are **internal analytical artifacts** —
   do NOT call `get_brand_voice` for them. A messaging framework is an optional input: pull one
   in when the org's positioning or approved claims should shape the output; otherwise skip it.

A full worked decomposition follows below.

## Inputs

### `explain` (required)

A one-line rationale for **this specific call**: the single question it answers and why that's
the right scope. Be specific to the current task — don't restate the tool's generic purpose.

> `explain: "Isolating win/loss reasons against Competitor X to fill the battlecard's 'why we win' section."`

### `query`

A single, focused, natural-language question capturing the **semantic intent** — the topic,
concept, or question to retrieve, not an action to perform.

- **One question per call.** If your `query` contains multiple `?`, conjoined sub-questions, or
  a list of distinct asks, split into separate parallel calls — one per question.
- **No retrieval verbs.** Never "find", "search for", "look up", "retrieve", or "show me
  documents" — describe the meaning to retrieve instead.
- Entities and their variants belong in `keywords`, not piled into the query.
- Temporal constraints belong in `temporalRange`, not in the query text. For "ACME customer
  calls dated March 25", the query is "ACME customer call" and the date goes in `temporalRange`.

### `keywords.allOfAny`

Short terms/phrases likely to appear **verbatim** in the underlying documents.

- **Outer array is AND across groups; inner array is OR within a group.** A document must
  contain at least one term from EVERY outer group. Each AND group narrows results
  multiplicatively — aim for **1–2 groups per call**; needing 3+ groups almost always means
  you're conflating distinct questions and should split into separate calls.
- Include distinctive content-bearing terms: companies, products, competitors, people,
  campaigns, acronyms, named pain points, feature names, technical terms.
- **Do NOT add low-signal source/document/workflow words** just because they appear in the ask:
  "call", "sales", "customer", "discovery", "interview", "meeting", "transcript", "document",
  "research", "feedback", "notes" — unless that exact term is itself the distinctive entity.
- Variants handled automatically: standard dictionary plurals and verb forms.
- **Manual variants required** for everything else:
  - synonyms — `["vs", "versus"]`
  - abbreviations — `["artificial intelligence", "AI"]`
  - hyphenation/spacing — `["mid-market", "midmarket", "mid market"]`
  - proper-noun variants — `["Salesforce", "SFDC"]`, `["Kubernetes", "K8s", "Kube"]`
  - non-dictionary plurals — `["OKR", "OKRs"]`
- **Never express temporal filtering in keywords.** No "recent", "last month", "2026",
  "Q1 2026", "April 24" — these don't match document text reliably and waste a keyword slot.

### `temporalRange` (optional)

Inclusive `startDate`/`endDate` bounds in **YYYY-MM-DD**. The field is optional: when the user
implied no time window, **omit it entirely or set the whole object to null — the two are
equivalent**. Either way, **never invent a default broad range**.

- Resolve relative phrases against the current date: "this week" → start-of-week → today;
  "since January 1, 2026" → `{ startDate: "2026-01-01", endDate: "<today>" }`.
- Partial date mentions are temporal constraints, not keywords. A document "dated September 25"
  with no year resolves to the **most recent past occurrence** of that month/day (current year
  if already passed, otherwise the previous year) — unless the conversation is clearly about an
  upcoming event, in which case pick the next future occurrence. For a single day, set
  `startDate` = `endDate`.
- Example: "ACME call dated March" asked on 2026-04-30 → query "ACME call",
  `keywords: { allOfAny: [["ACME"]] }`, `temporalRange: { startDate: "2026-03-01", endDate: "2026-03-31" }`.

## Recipes — the highest-volume research shapes

One focused call each unless noted. Examples are illustrative; substitute the user's entities.

| Shape | Example `query` | Example `keywords.allOfAny` |
|---|---|---|
| Win/loss | "Why do buyers choose competitors over us in [category] deals?" | `[["Competitor X"]]` |
| Vendor/competitor sentiment | "What do customers say about their experience with Vendor Y?" | `[["Vendor Y"]]` |
| Pricing/packaging/discounts | "What discount levels do buyers negotiate on enterprise CRM deals?" | `[["CRM"], ["discount", "discounting", "pricing"]]` |
| Buying committee / buyer journey | "Who is involved in evaluating and approving a data-platform purchase?" | `[["buying committee", "stakeholders", "approval"]]` |
| Channels / watering holes | "Where do revenue leaders get information when evaluating new tools?" | `[["CRO", "chief revenue officer", "revenue leader"]]` |

## Worked decomposition — battlecard vs Competitor X

The most common templated ask. "Build a battlecard against Competitor X" decomposes into 3–4
**parallel** calls, one angle each:

1. `query`: "What pain points do Competitor X's customers experience with the product?" —
   `keywords: { allOfAny: [["Competitor X"]] }`
2. `query`: "Why do buyers pick or reject Competitor X in competitive evaluations?" —
   `keywords: { allOfAny: [["Competitor X"]] }`
3. `query`: "How do buyers describe Competitor X's strengths and reputation?" —
   `keywords: { allOfAny: [["Competitor X"]] }`
4. `query`: "What do buyers report about Competitor X's pricing and packaging?" —
   `keywords: { allOfAny: [["Competitor X"], ["pricing", "price", "packaging", "discount"]] }`

Then synthesize the four answers into the user's battlecard template (or a standard
overview / strengths / weaknesses / why-we-win / objection-handling layout). A battlecard is an
internal artifact: **no `get_brand_voice` styling**; a messaging framework is an optional input
when the org's positioning should shape it. Include each call's
"GetWhys Sources" paragraph (grouped at the end is fine) and every `view_in_getwhys` link.

## Output contract

Each call returns:

- **`answer`** — synthesized prose. Substantive claims carry inline **†** grounding markers,
  and the answer ends with an anonymized **"GetWhys Sources"** paragraph describing the
  underlying interviews and documents. Relay that paragraph **verbatim** — never paraphrase,
  abridge, or omit it — and preserve the † markers in any text you quote.
- **`no_data`** — `true` when nothing in the corpus matched (the answer will say so).
- **`view_in_getwhys`** — deep link to the citation-clickable version of the answer in the
  GetWhys app; null when no citations were emitted. Surface it whenever present.

Raw transcripts and verbatim quotes are intentionally not exposed across this boundary —
don't ask for them or imply they're retrievable.

## Retry etiquette

- `no_data: true` → rephrase **once at most**: broaden the angle, drop an over-narrow AND
  group, or fix a likely keyword mismatch (missing variant, misspelled entity). If the retry
  also returns no data, tell the user plainly what the corpus didn't cover — never fabricate.
- An answer that's on-topic but thin is a result, not an error — relay it; don't re-query the
  same question hoping for more.
- Don't re-issue the identical call after a transport error without checking whether the first
  call already returned.
