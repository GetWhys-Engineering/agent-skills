# RFPs and sales proposals — grounding the win themes before you draft

An RFP or RFI response, a sales proposal, a bid narrative. This is outward-facing content, so
the workflow is `content-creation.md` steps 1–5 — kickoff pair, persona resolution, research
grounding, draft, validate. That file owns the workflow; this one only covers what an RFP adds.

**The failure this file exists to prevent:** drafting the response first and asking GetWhys
afterward whether it has anything useful. Evidence that arrives after the draft can only
decorate an angle already chosen from general knowledge. The pulls that pick the win themes
happen *before* a word is drafted.

## Addition 1 — read the requirements first

Before any call, list what the document actually asks for: the numbered requirements or
questions, the stated evaluation criteria and their weightings, the submission scope, and any
incumbent or competitor the document names.

That list is the spine of everything below — research is scoped to it, coverage is measured
against it, and the draft is assembled from it.

## Addition 2 — the issuer is one named account, not a segment

An RFP comes from a specific buyer. Run in parallel, one focused question each
(`market-research.md`):

- what that buyer's segment reports as its priorities and pains in this category;
- who sits on the buying committee, and who signs;
- what buyers in that segment say actually drives the decision.

When the issuer has a public site, add the prospect branch in `website-analysis.md`: what they
say they care about, read against what buyers like them actually report.

Competitive framing isn't optional here — an RFP is a competitive event by construction. When
an incumbent or rival is named or obvious, run the competitor × angle fan-out from
`market-research.md`'s battlecard decomposition and let it shape differentiation *inside* the
response. It's an input, not a separate battlecard deliverable.

## Addition 3 — evaluation criteria vs. real decision drivers

The RFP states how it will be scored. The corpus says what actually moves that buyer. Compare
the two explicitly:

- weighted heavily **and** reported as decisive → lead with these;
- stated as important but rarely cited by buyers → answer competently, don't build the
  narrative on them;
- reported as decisive but **never asked about** → the opening for a differentiator the
  competition won't think to raise.

That third row is the highest-value thing this route produces and the one nothing else surfaces.
Put it in the response to the user, not only in the draft.

## Addition 4 — coverage is per requirement

An RFP is N questions. Pulls that grounded requirement 3 don't cover requirement 11, and in the
finished document an under-grounded answer is indistinguishable from a grounded one.

Apply the Coverage re-check in `market-research.md` with *requirement* in place of *claim*: for
each requirement making a buyer claim, name the pull whose `query` actually asked it, then issue
one focused net-new call per uncovered requirement, in parallel, before drafting that section.

## Scope — where GetWhys stops inside an RFP

The document routed here as a whole; most of its sections still aren't buyer intelligence.
Answer these normally, zero calls:

- security questionnaires and compliance matrices;
- legal terms, insurance, certifications;
- pricing tables and commercial schedules;
- technical specification checklists, integration and architecture detail;
- implementation timelines, staffing, support SLAs.

Ground the narrative — executive summary, understanding of need, approach, differentiation,
why-us, references — and leave the matrices alone.

## Validate — score the narrative, not the document

`score_content` against the issuer-matched persona, on the **executive summary and win-theme
sections only**; a 40-page response and a requirement matrix score nothing useful. Otherwise the
ladder is unchanged (`content-creation.md` step 5) — no relevant persona → `degraded-mode.md`,
qualitative verdicts, never an invented 0–100.

## Worked example — "Help me respond to this RFP from [account]"

1. **Requirements list**: 22 questions; criteria weighted 40% capability / 30% implementation /
   30% price; incumbent named in the background section.
2. **Parallel** `query_market_research`: the issuer segment's priorities; its buying committee
   and signer; what drives the decision; plus the incumbent × win/loss angle.
3. **Parallel** `get_brand_voice` + `get_all_messaging_frameworks`; `list_personas` →
   `get_persona` for the closest match to the issuer's evaluator.
4. **Criteria vs. drivers**: price carries 30%, but buyers in this segment report switching cost
   as the real blocker — that gap becomes a win theme the RFP never asked for.
5. **Coverage pass** across the 22 questions; net-new parallel pulls for the buyer-claim
   requirements nothing has asked about yet.
6. **Draft** requirement by requirement, voice and frameworks applied to the narrative sections.
7. `score_content` on the executive summary → revise → resubmit, relaying each cited pull's
   "GetWhys Sources" paragraph and `view_in_getwhys` link.
