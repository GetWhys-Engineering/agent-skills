# Contributing to agent-skills

This file is for **contributor agents** (and humans) authoring skills in this repo.
Consumer-facing install docs live in [README.md](README.md) and [docs/](docs/).

This is a **public** repo of GetWhys Agent Skills built on the open `SKILL.md`
standard. Everything under `skills/` is distributed verbatim to every
SKILL.md-compatible client (Claude, ChatGPT, Claude Code, Codex, Cursor,
Gemini CLI, Copilot, and more), so portability and hygiene rules below are hard
requirements, not style preferences.

## How to add a skill

1. Create `skills/<name>/SKILL.md`. Start from [template/SKILL.md](template/SKILL.md).
2. `<name>` is kebab-case and **must match the directory name exactly**.
3. Supporting files are allowed alongside `SKILL.md` (e.g. `scripts/`,
   `references/`, `assets/`) and ship inside the skill's zip.
4. Run `./scripts/validate-skills.sh` before committing (see Workflow below).
5. Register the skill where consumers find it:
   - add a row to the "Available skills" table in [README.md](README.md).

   No `.claude-plugin/` edit is needed: the plugin manifest
   ([.claude-plugin/plugin.json](.claude-plugin/plugin.json)) and the
   marketplace entry both auto-discover every `skills/<name>/` directory, so a
   new skill ships in the per-skill zip, the Cowork package, and the Claude Tag
   plugin package automatically.

## Frontmatter constraints

These are enforced by `scripts/validate-skills.sh` and by the upload UIs
(Claude.ai, ChatGPT, etc.) — violations block both CI releases and admin uploads.

- Frontmatter is **valid YAML** and the **first thing in the file** (`---` on line 1).
- `name`: required; max **64** chars; matches `^[a-z0-9-]+$` (lowercase letters,
  numbers, hyphens); **equals the directory name**; no XML tags.
- `description`: required; non-empty; max **1024** chars; no XML tags.
  Lead with the use case and the trigger phrases a user would say — this is
  the only text clients use to decide when to load the skill.

## Portability rule

Only the two standard keys — `name` and `description` — are allowed in
`SKILL.md` frontmatter. No vendor-specific keys (e.g. Claude Code's
`allowed-tools`): the same file must work across all platforms. Claude-Code-only
niceties belong in the plugin wrapper (`.claude-plugin/`), not in the skill.

## Hard guardrails

- **Public repo.** No secrets, credentials, internal endpoints, or
  internal-only details — in skills, docs, or commit history.
- **Never add MCP config** (`.mcp.json`, `mcpServers` blocks,
  `gemini-extension.json` MCP bundles). The GetWhys MCP is a paid product;
  connecting it is handled by GetWhys onboarding, not this repo. Skills may
  reference MCP tools by name only.
- **< 200 files** per skill directory (Claude upload limit).
- No `.DS_Store` / `__MACOSX` anywhere.

## Workflow before committing

1. `./scripts/validate-skills.sh` — must pass (frontmatter, file counts, hygiene).
2. Optionally preview the artifacts in `dist/` (git-ignored):
   `./scripts/package-skills.sh` (per-skill zips),
   `./scripts/package-cowork-plugin.sh` (M365 Cowork package), and
   `./scripts/package-plugin.sh` (Claude Tag plugin package, `getwhys-skills.zip`).
3. Releases are cut by pushing a `v*` tag — CI re-validates, builds all zips,
   and attaches them to a GitHub Release. Stable download URLs:
   - `https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/<skill>.zip`
   - `https://github.com/GetWhys-Engineering/agent-skills/releases/download/<tag>/<skill>.zip`
