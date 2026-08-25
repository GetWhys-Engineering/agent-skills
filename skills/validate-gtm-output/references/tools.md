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
| `list_messaging_frameworks` | Framework index (`id`, `title`, `description`) — no framework content | — | `get_messaging_framework({id})` |
| `get_messaging_framework` | One framework's full content (+ `description`) | `id` XOR `title` | Apply to the named-framework task |
| `get_all_messaging_frameworks` | Every framework, full content | — | Pair with `get_brand_voice` at content kickoff |
| `query_market_research` | Synthesized answer from buyer interviews + org docs | `query`, `explain`, `keywords`, `temporalRange` | Relay with Sources verbatim + link |
| `score_content` | Persona-informed content score (0–100) + recommendations | `content`, `persona_handle` | Capture returned `content_id`; revise → resubmit with it until threshold |

## Playbook — framework lookup

For "show me / use our [named] messaging framework" asks (NOT for content generation — that's
the kickoff pair, `get_brand_voice` + `get_all_messaging_frameworks`):

- User named the framework **verbatim** → `get_messaging_framework({title})` directly — one
  round trip.
- **Fuzzy or partial** reference → `list_messaging_frameworks` to disambiguate, then
  `get_messaging_framework({id})`. Each index entry carries a `description` — a short "when to
  apply this" note (its topic plus any channel / content type, product, or audience it targets;
  may be null) — use it to pick the framework the user means and to tell similarly-named
  frameworks apart.
- A `title` call returning a "multiple frameworks share that title" error → re-call with one
  of the returned ids.
- Pass exactly one of `id` or `title`, never both.

## Playbook — connection & identity sanity

- `whoami` reports who is authenticated (a user or an org-level key) and the organization.
  Use it when results look wrong (e.g. an unexpected workspace) or the user asks who's
  connected. It takes no inputs and is safe to call any time.

## Empty-workspace semantics

These responses mean the org hasn't configured that artifact yet — they are answers, not
errors, and not retryable. (The server may append its own guidance after the opening sentence;
match on the opening sentence.)

| Response opens with | Meaning |
|---|---|
| "No personas found in this workspace." | No personas configured |
| "No brand voice characteristics configured for this workspace." | No brand voice configured |
| "No messaging frameworks configured for this workspace." | No frameworks configured |

Don't retry, and don't let a missing artifact cancel the task — see `degraded-mode.md` for what
still works in each case and how to shape the response.
