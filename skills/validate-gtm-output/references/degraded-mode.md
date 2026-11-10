# Missing inputs — degrade the task, never block it

Read this when a GetWhys call comes back empty, or when the org artifact a step depends on
isn't configured.

Empty-workspace responses ("No personas found…", "No brand voice characteristics configured…",
"No messaging frameworks configured…") are **answers, not errors** — the org simply hasn't
configured that artifact. They are not retryable, and they never cancel the work.

## Principles

1. **Degrade, don't block.** Deliver the largest useful subset. The gap is a caption on the
   work — one line before the analysis, an upgrade offer after it — never a substitute for the
   work and never a precondition.
2. **Every prohibition carries an affirmative fallback.** "Never guess a handle" has to be
   followed by "→ do this instead", or the guardrail becomes a dead end.
3. **A required parameter belongs to a tool, not to the task.** One unavailable tool removes
   one check, not the goal.
4. **Validation is a ladder, not one rung.** `score_content` is the strongest rung;
   `query_market_research` evidence-checking and brand-voice / framework hand-checks stand on
   their own. Use the highest rung available and say which one you used.
5. **An inferred substitute is a stated substitute.** When you proceed without a configured
   artifact, name what you used in its place — the audience you read the content as targeting,
   plain B2B clarity standing in for a configured voice — so the user can judge the
   substitution and act on it.

Never end a turn having delivered nothing, and never end on a question the user must answer
before anything ships.

## What still works

| Missing | What still works |
|---|---|
| **No relevant persona** — empty `list_personas`, *or* non-empty with nothing matching the content's audience | Everything except `get_persona` / `score_content`. See the response shape below |
| No brand voice | Frameworks, personas, research, scoring. Draft to plain B2B clarity and say that's the standard you applied |
| No messaging frameworks | Voice, personas, research, scoring. Draft from persona + research; flag any claim you couldn't check against approved positioning |
| Nothing configured | `query_market_research` alone grounds *and* validates content end to end — audience pains, the language buyers use, objections, proof points |

## Response shape when no persona is relevant

The case that matters most, because it's the one where stopping feels safest. Three beats:

1. **One line, first** — the audience the content reads as written for (role / seniority,
   function, segment, the problem they own), and that no configured persona covers it. One
   line. Not a paragraph, not an apology, not a question.
2. **The analysis** — mirror `score_content`'s shape (per-dimension verdicts → gaps →
   recommendations) so it reads as the same product, but keep the verdicts **qualitative**:
   strong / mixed / gap. **Never emit a 0–100 figure** unless `score_content` actually ran —
   the score is exactly what the upgrade buys, so faking one destroys the offer.
3. **One closing line** — adding that persona in the GetWhys app unlocks the persona-fit score
   and the scoring iteration loop. *"If you want more rigor"*, never *"this analysis is
   incomplete"*.

Never invent a `persona:<handle>`. A *close-enough* configured persona is a different case —
use it and say which one you picked. Only fall to the inferred read when nothing is relevant.

The full two-rung validation ladder — and the `query_market_research` calls that back the
analysis — are in `content-creation.md` step 5.
