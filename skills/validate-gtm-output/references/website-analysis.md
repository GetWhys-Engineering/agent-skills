# Website analysis — auditing a live site against buyer evidence

The route for "go through [site] and critique it", homepage and messaging teardowns, "why
isn't this page converting?", and pre-call or pre-proposal research on someone else's site.

**The failure this file exists to prevent:** a website critique assembled entirely from web
search and general UX/SEO heuristics — page titles, meta descriptions, CTA counts, typos —
with no buyer evidence behind a single claim about what the audience cares about. Those
observations are legitimate and worth keeping (step 5), but they are the *secondary* layer.
A site's job is to say the right thing to the right buyer; whether it does is a question
GetWhys answers rather than guesses.

## Why this isn't draft scoring

Three differences from the pasted-draft route in `content-creation.md`:

- **The content has to be fetched.** Nothing is pasted — page copy is an input you go get.
- **It's multi-page.** A homepage and a pricing page address different moments for different
  reasons; scoring one concatenated blob of the whole site scores nothing.
- **Cross-page consistency is a finding that only exists at site scale.** Whether the pages
  tell one story is invisible when you look at any one of them, and it's usually the most
  valuable thing an audit surfaces.

## Step 0 — get the pages

Fetch the actual copy with whatever web fetch or browse capability the client has. Cover the
pages that carry positioning:

- the homepage;
- the main product / platform / solution page(s);
- pricing, if it exists;
- proof — customers, case studies, testimonials;
- the primary conversion page (demo request, trial signup, contact).

Say which pages you covered. An audit of three pages presented as an audit of "the site" is a
coverage claim you can't support.

**No web access, or the fetch is blocked?** Ask the user to paste the copy. Never critique a
site from general knowledge of the brand, and never let search-result snippets stand in for
page text — a summary of a page is not the page.

This step makes no GetWhys calls.

## Step 1 — whose site is it?

The whole sequence branches here. Getting this wrong is how a competitor teardown ends up
styled against your own brand voice.

| Whose site | Sequence |
|---|---|
| **Ours** | Full stack: kickoff pair `get_brand_voice` + `get_all_messaging_frameworks` (parallel) → persona resolution → per-page `score_content` → research grounding → cross-page checks |
| **A competitor's** | Competitive-intel shape (`market-research.md`): 3–4 parallel `query_market_research` — what buyers say about them, why buyers pick or reject them, their pricing and packaging — read against the claims their pages make. **No `get_brand_voice`, no `score_content`** |
| **A prospect's or customer's** | Account research: 2–3 parallel `query_market_research` on that segment's pains, priorities, and buying committee, read against what their site says they care about. **No `get_brand_voice`**; score against our personas only when the question is explicitly "do we fit them?" |

**On brand voice.** SKILL.md restricts `get_brand_voice` to outward-facing publishable
content. A live website *is* exactly that, so for **our** site it's the right call. For anyone
else's site the deliverable is an internal analysis and voice never applies. Messaging
frameworks follow the usual rule: required for our site, an optional input elsewhere when the
org's positioning should shape the comparison.

## Step 2 — persona resolution

Per `content-creation.md` step 2: `list_personas` → best-matching handle → `get_persona`.
Handles come from the list output, never guessed.

A site usually has one primary buyer and one or two secondary ones. Resolve the primary
persona and say which you used. When the site clearly speaks to more than one, score each
page against the persona that owns it rather than everything against one handle.

No relevant persona — empty list, *or* nothing in it matching — takes the `degraded-mode.md`
path: name the audience the site reads as written for in one line up front, run the cross-page
checks on research alone, keep every verdict qualitative, and never report a 0–100 figure that
`score_content` didn't produce.

## Step 3 — score page by page (our site only)

One `score_content` call per page:

- `content` — that page's copy.
- `persona_handle` — from step 2.
- `content_type` — `"homepage"`, `"landing page"`, `"pricing page"`, `"web copy"`.
- optional framework by `id` **or** `title` (never both) when a specific framework governs.

**Present table-first**: a pages × dimensions table carrying each page's `overall_score`,
before any prose. The spread across pages is itself the finding — a strong homepage with a
weak conversion page is a different problem from a site that's uniformly mid.

## Step 4 — the four cross-page checks

These are what a heuristics-only critique reaches for and has to guess at. Run all four.

1. **One story, or several?** Extract each page's core positioning claim, then read the set
   against `get_all_messaging_frameworks`. Pages that each sound fine alone but make a visitor
   re-learn what the company is are the classic finding — and the frameworks let you
   adjudicate it on approved positioning instead of taste. Flag any page claim that
   contradicts a framework or has no basis in one.
2. **Does the site name its buyer?** Compare the hero and subhead against the persona's role,
   seniority, function, and the problem they own. "The reader can't self-identify in two
   seconds" is a persona-fit gap, not a copywriting opinion.
3. **Pain match.** One `query_market_research` call on the pains and priorities that audience
   reports in this category, compared with the pains the site leads with. Ranking matters: a
   site leading with the buyer's third-most-urgent pain is a fixable problem you can only see
   with the evidence in hand.
4. **Objection coverage.** One `query_market_research` call on the objections that audience
   raises and the proof that moves them, then mark each *answered*, *answered weakly*, or
   **never addressed**. The never-addressed column is usually the highest-value output of the
   whole audit.

Issue the step-4 research calls **in parallel**, one focused question each, per
`market-research.md`.

## Step 5 — deliver

Order matters — lead with what only GetWhys could tell them:

1. **Per-page scores** — the step-3 table, first, before prose.
2. **Cross-page findings** — the four checks, each with the evidence behind it.
3. **Prioritized fixes** — ranked by impact on the buyer, not by ease of editing.
4. **Hygiene and UX** — a clearly secondary section for the generic layer: page titles and
   meta descriptions, CTA paths, broken or mislabeled links, typos, SEO and brand-confusion
   risks. Keep it — it's useful and the user asked for a critique. It just never substitutes
   for the evidence layer above it.

State what you didn't assess (visual design, mobile, pages you couldn't reach) rather than
letting the scope pass as complete.

Relay rules apply to every research answer you cite: the "GetWhys Sources" paragraph verbatim,
the `view_in_getwhys` link when present, † markers preserved.

## Worked example — "Go through our website and critique it"

1. **Fetch** the homepage, platform page, data page, and demo-request page; note those four as
   the covered set.
2. **Whose site:** ours → full stack.
3. **Parallel:** `get_brand_voice` + `get_all_messaging_frameworks`.
4. `list_personas` → primary buyer is a GTM / product-marketing leader →
   `get_persona({handle: "persona:pmm-leader"})` *(handle from the list output)*.
5. **Parallel** `score_content`, one per page: homepage (`content_type: "homepage"`), platform
   (`"landing page"`), data page (`"web copy"`), demo request (`"landing page"`).
6. **Parallel** `query_market_research`:
   - query "What problems do product marketing leaders report when validating messaging before
     launch?" — `keywords: { allOfAny: [["product marketing", "PMM"]] }`
   - query "What objections do GTM leaders raise when evaluating buyer research tools?" —
     `keywords: { allOfAny: [["buyer research", "customer research", "voice of customer"]] }`
7. **Cross-page checks:** each page's positioning claim vs. the frameworks; hero vs. persona;
   the site's lead pain vs. the researched pain ranking; objections vs. what the pages answer.
8. **Deliver** in step-5 order: score table → cross-page findings → prioritized fixes →
   hygiene notes.
