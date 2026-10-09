# GetWhys Agent Skills

A provider-agnostic collection of **GetWhys Agent Skills** (and future agent
resources), built on the open [`SKILL.md`](https://agentskills.io) standard.
The same skills work in:

- **Chat clients:** Claude (.ai / Desktop / Cowork), ChatGPT (Business /
  Enterprise), Microsoft 365 Copilot Cowork, Amazon Q Business, Perplexity
- **Dev tools:** Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot,
  JetBrains Junie, AWS Kiro, Google Antigravity, Block Goose

> ## Prerequisite: the GetWhys MCP server
>
> These skills are companions to the **GetWhys MCP server, a paid GetWhys
> product**. They guide your AI assistant in using its tools — and are **inert
> without it**. Connect the MCP through
> [GetWhys onboarding](https://www.getwhys.io). The portable plugin and Claude
> Tag plugin declare the public server endpoint. Authentication is configured
> separately; Claude Tag also requires allowed-host access in its Access bundle.
> Per-skill and M365 Cowork packages contain no MCP configuration.

## Available skills

| Skill | What it does | Download |
|---|---|---|
| [`validate-gtm-output`](skills/validate-gtm-output/SKILL.md) | Grounds marketing, content, and GTM work in real buyer evidence via the GetWhys MCP tools — research questions, competitive intel and battlecards, outward-facing content with brand voice and messaging frameworks, persona building, and draft scoring. | [zip](https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/validate-gtm-output.zip) |

## Install — pick your platform

### Portable Agent Plugins clients

This repository is an [Agent Plugins 1.0](https://agent-plugins.org/specification)
plugin directory. Use your compatible client's local-directory or Git install
flow to load it. The root [`plugin.json`](plugin.json) identifies the `getwhys`
plugin, clients discover skills under `skills/`, and [`mcp.json`](mcp.json)
declares the credential-free GetWhys Streamable HTTP endpoint. Configure
authentication through GetWhys onboarding before using the tools.

Client-specific metadata belongs under `extensions` in the root manifest.
The existing `.claude-plugin/` manifests and release packages support their
respective client install flows.

Build the OpenAI upload ZIP with `./scripts/package-openai-plugin.sh` (Python
3.9+). It writes `dist/getwhys-openai.zip` with a single `getwhys/` directory
containing the portable manifests, all skills and their supporting files,
LICENSE, and any referenced icons/screenshots. It excludes repository files
and client-specific manifests. The version defaults to root `plugin.json`;
override it with `VERSION=vX.Y.Z ./scripts/package-openai-plugin.sh`.
The manifest's release notes default to the subjects of commits that touched
packaged files since the previous `v*` tag; set `RELEASE_NOTES` to override
them. Every release attaches this ZIP. The script reports missing review
materials; a draft ZIP does not establish public submission readiness.

### No CLI? Org admin? (Claude.ai / Desktop / Cowork, ChatGPT Business/Enterprise)

Download the skill's `.zip` above, then upload it in settings:

- **Claude (Team/Enterprise admin):** Org settings → Skills → **+ Add** → select
  the zip. On by default for every user, across web, the Desktop Chat tab, and
  Claude Cowork (where Cowork is enabled for your org).
- **ChatGPT (Business/Enterprise — beta):** *New skill → Upload from computer*
  → **Share** with the workspace.
- **Claude Tag (Claude in Slack — beta):** Org settings → **Plugins** → **Upload
  plugin** → upload the plugin package
  [`getwhys-skills.zip`](https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/getwhys-skills.zip)
  — a *plugin* zip, distinct from the skill zip above. It declares the GetWhys
  server, but an admin must separately add the credential and allow
  `api.getwhys.io` in the scope's Access bundle.

Full org-wide flows (including **Microsoft 365 Copilot Cowork** org-push and
**Claude Tag**): **[docs/install-admin.md](docs/install-admin.md)**.

### Git install one-liners

| Tool | Command |
|---|---|
| **Claude Code** | `/plugin marketplace add GetWhys-Engineering/agent-skills` → `/plugin install getwhys-skills@agent-skills` |
| **Gemini CLI** | `gemini skills install https://github.com/GetWhys-Engineering/agent-skills --path skills/<name>` |
| **OpenAI Codex** | `$skill-installer install https://github.com/GetWhys-Engineering/agent-skills/tree/main/skills/<name>` |

### Copy a folder (Cursor, Copilot, Junie, Kiro, Antigravity, ...)

Copy `skills/<name>/` into **`.agents/skills/`** in your project (or
`~/.agents/skills/` globally) — this vendor-neutral location covers Cursor,
Gemini CLI, GitHub Copilot, and Google Antigravity at once:

```bash
git clone https://github.com/GetWhys-Engineering/agent-skills.git
mkdir -p .agents/skills && cp -R agent-skills/skills/<name> .agents/skills/
```

Complete per-tool directory matrix:
**[docs/install-platforms.md](docs/install-platforms.md)**.

## Updating / versioning

Releases are cut as `vX.Y.Z` tags; each release attaches one zip per skill, the
M365 Cowork package (`getwhys-cowork.zip`), the Claude Tag plugin package
(`getwhys-skills.zip`), and the OpenAI plugin upload (`getwhys-openai.zip`).
Two URL shapes:

```
https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/<skill>.zip   # always the newest
https://github.com/GetWhys-Engineering/agent-skills/releases/download/vX.Y.Z/<skill>.zip   # pinned
```

Git-based installs (Claude Code, Gemini, Codex) track the repo and update via
each tool's own update command.

## Authoring / contributing

Authoring rules live in [AGENTS.md](AGENTS.md) (frontmatter constraints,
portability rules, validation workflow); start new skills from
[template/SKILL.md](template/SKILL.md). Run `./scripts/validate-skills.sh`
before committing.

## License

[MIT](LICENSE)
