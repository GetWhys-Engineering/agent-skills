# Tool quick reference, framework lookup, and workspace sanity

## Tool quick reference

The GetWhys MCP server is the source of truth for exact tool names and inputs; this table is a
sequencing cheat-sheet, not a schema.

| Tool | Purpose | Key input | Typical next step |
|---|---|---|---|
| `whoami` | Who is authenticated + which org | — | Sanity-check workspace |
| `list_personas` | Lightweight persona index (handle + name) | — | `get_persona` with the chosen handle |
| `get_persona` | Full attributes of one persona | `handle` (`persona:<handle>`) | Draft / score against it |
| `get_all_personas` | Every persona, full detail | — | Only when the full set is explicitly required |
| `get_brand_voice` | Org brand voice (do/don't rules) | — | Apply while drafting publishable copy |
| `list_messaging_frameworks` | Framework index over **all** frameworks (`id, title, summary, scope`) | — | `get_messaging_framework({id})` |
| `get_messaging_framework` | One framework's full content (+ `scope`, `summary`), any scope | `id` XOR `title` | Apply to the named / selected framework |
| `get_all_messaging_frameworks` | **Global (always-on)** frameworks, full content | — | Pair with `get_brand_voice` at content kickoff |
| `query_market_research` | Synthesized answer from buyer interviews + org docs | `query`, `explain`, `keywords`, `temporalRange` | Relay with Sources verbatim + link |
| `score_content` | Persona-informed content score (0–100) + recommendations | `content`, `persona_handle` | Revise → resubmit until threshold |

## Playbook — framework lookup & scope

Each `list_messaging_frameworks` entry carries a `scope`:

- **`global`** = org-wide guidance, *always* applied, already returned in full by
  `get_all_messaging_frameworks` — no need to fetch these again.
- **`use_case`** = situational; applies only to a specific product, channel, or audience. Read
  its `summary`, and call `get_messaging_framework({id})` for the full content only when that
  summary matches what you're creating.

Use this playbook both for "show me / use our [named] messaging framework" asks **and** for
selecting `use_case` frameworks during content generation (the content-gen kickoff itself is
still the pair `get_brand_voice` + `get_all_messaging_frameworks`, which supplies the globals):

- User named the framework **verbatim** → `get_messaging_framework({title})` directly — one
  round trip.
- **Fuzzy or partial** reference → `list_messaging_frameworks` to disambiguate, then
  `get_messaging_framework({id})`.
- A `title` call returning a "multiple frameworks share that title" error → re-call with one
  of the returned ids.
- Pass exactly one of `id` or `title`, never both.

## Playbook — connection & identity sanity

- `whoami` reports who is authenticated (a user or an org-level key) and the organization.
  Use it when results look wrong (e.g. an unexpected workspace) or the user asks who's
  connected. It takes no inputs and is safe to call any time.

## Empty-workspace semantics

These responses mean the org hasn't configured that artifact yet — they are not errors and
not retryable:

| Response | Meaning |
|---|---|
| "No personas found in this workspace." | No personas configured |
| "No brand voice characteristics configured for this workspace." | No brand voice configured |
| "No messaging frameworks configured for this workspace." (from `list_messaging_frameworks`) | No frameworks configured at all |
| "No global (always-on) messaging frameworks configured. Call list_messaging_frameworks to check for situational frameworks." (from `get_all_messaging_frameworks`) | No **global** frameworks; situational (`use_case`) frameworks may still exist |

Don't retry; proceed without that artifact (note its absence once if it affects quality) and
point the user to the GetWhys app to configure it. The one exception is the
`get_all_messaging_frameworks` row above: during content generation, follow its instruction and
call `list_messaging_frameworks` for `use_case` frameworks before proceeding without any.
