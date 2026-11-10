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
- **Never add credential-bearing or platform-specific MCP config**
  (`gemini-extension.json` MCP bundles, tokens, secrets, client IDs, or request
  headers). There are two exceptions, and `validate-skills.sh` checks both:
  - `packaging/claude-tag/.mcp.json`: the package build copies this
    credential-free public endpoint declaration into the root of the built
    Claude plugin (`dist/getwhys-skills/`), which ships as the Claude Tag zip
    and as the `claude-directory` branch.
  - `packaging/m365/manifest.json`: the manifest of the "GetWhys MCP" app on
    Microsoft Marketplace. Its `agentConnectors` entry names the public
    endpoint and a connection Microsoft stores, by ID only (`type` and
    `referenceId`). Keep its `id` unchanged: Microsoft treats a new id as a
    different app.

  Never put `.mcp.json` at the repository root,
  where the Claude Code marketplace plugin would load it automatically.
  Authentication and allowed-host access are configured separately through
  GetWhys onboarding. Skills may reference MCP tools by name only.
- **Never commit to the `claude-directory` branch.** Claude's plugin directory
  lists our plugin from it, and CI rewrites it on every `v*` tag (and on a
  manual run of the "Publish Claude directory plugin" workflow from `main`).
  To change what the directory serves, change the skills,
  `.claude-plugin/plugin.json`, or `packaging/claude-directory/` (the listing's
  README and icon) on `main`. The listing icon is fixed once the listing is
  first saved; replacing the file later doesn't change it.
- **< 200 files** per skill directory (Claude upload limit).
- No `.DS_Store` / `__MACOSX` anywhere.

## Workflow before committing

1. `./scripts/validate-skills.sh` — must pass (frontmatter, file counts, hygiene).
2. Optionally preview the artifacts in `dist/` (git-ignored):
   `./scripts/package-skills.sh` (per-skill zips),
   `./scripts/package-cowork-plugin.sh` (M365 Cowork package),
   `./scripts/package-plugin.sh` (Claude plugin: the `getwhys-skills/` folder
   for Claude's directory and `getwhys-skills.zip` for Claude Tag; fails on
   anything the directory would hold or block),
   `./scripts/package-openai-plugin.sh` (ChatGPT plugin package, `getwhys-openai.zip`), and
   `./scripts/package-m365-app.sh` (Microsoft 365 Marketplace app, `getwhys-m365.zip`).
3. Releases are cut by pushing a `v*` tag — CI re-validates, builds all zips,
   and attaches them to a GitHub Release. A second workflow publishes the
   Claude plugin to the `claude-directory` branch, which Claude's plugin
   directory tracks. Stable download URLs:
   - `https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/<skill>.zip`
   - `https://github.com/GetWhys-Engineering/agent-skills/releases/download/<tag>/<skill>.zip`
