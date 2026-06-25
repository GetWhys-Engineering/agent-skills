# Install GetWhys skills — full platform matrix

Every platform below reads the **same** `skills/<name>/SKILL.md` artifact (the
open Agent Skills standard); only the install location or command differs.
Platforms are grouped by *how* you install.

> **Prerequisite (all platforms):** the **GetWhys MCP server** must be
> connected, or the skills are inert. It's a paid GetWhys product onboarded
> separately — see [GetWhys onboarding](https://www.getwhys.io). No MCP config
> ships from this repo.

## Tier 1 — chat clients (upload a zip, no CLI)

These consume the per-skill `.zip` release assets. **Org admins: see
[install-admin.md](install-admin.md)** for the full org-wide flows (the primary
GetWhys targets are Claude + ChatGPT, plus MS Copilot Cowork org-push).

| Platform | Install |
|---|---|
| **Claude** (.ai / Desktop / Cowork) | Settings → Skills → upload `<skill>.zip`. Org admins: Org settings → Skills → **+ Add** (provisions all users on all three surfaces). |
| **ChatGPT** (Business / Enterprise / Edu — beta, not Plus/Pro) | *New skill → Upload from computer* → **Share** with the workspace. |
| **Microsoft 365 Copilot Cowork** (Frontier preview) | Personal: drop the skill folder in OneDrive `/Documents/Cowork/skills/<name>/`. Org: deploy `getwhys-cowork.zip` — see [install-admin.md](install-admin.md). |
| **Claude Tag** (Claude in Slack — beta) | Org admins only: upload the **plugin** package `getwhys-skills.zip` via Org settings → Plugins → Upload plugin — see [install-admin.md](install-admin.md). |
| **Amazon Q Business** | *MY SKILLS → Upload* → select the `SKILL.md` (+ supporting files). |
| **Perplexity** (Perplexity Computer) | Skills sidebar → *+ Create skill → Upload* → drag in the skill files (≤10 MB). |

## Tier 2 — git-installable straight from this repo

One-liner per tool; installs/updates come from git, no zips involved.

| Platform | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add GetWhys-Engineering/agent-skills` then `/plugin install getwhys-skills@agent-skills` |
| **Gemini CLI** | `gemini skills install https://github.com/GetWhys-Engineering/agent-skills --path skills/<name>` |
| **OpenAI Codex CLI** | `$skill-installer install https://github.com/GetWhys-Engineering/agent-skills/tree/main/skills/<name>` (in-session) |

## Tier 3 — copy the folder into a skills directory

Clone (or download + unzip) and copy `skills/<name>/` into your tool's skills
dir. **Shortcut:** copying into **`.agents/skills/`** (project) or
**`~/.agents/skills/`** (global) — the vendor-neutral convention — covers
Cursor, Gemini CLI, GitHub Copilot, and Google Antigravity in one drop.

```bash
git clone https://github.com/GetWhys-Engineering/agent-skills.git
mkdir -p .agents/skills
cp -R agent-skills/skills/<name> .agents/skills/
```

Per-tool directories:

| Platform | Project dir | Global dir |
|---|---|---|
| **Cursor** | `.cursor/skills/`, `.agents/skills/` (also reads `.claude/`, `.codex/`) | — |
| **GitHub Copilot** (VS Code / Visual Studio / CLI / coding agent) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/` (`~/.config/github-copilot/skills/`; Windows `%APPDATA%\github-copilot\skills\`) |
| **JetBrains Junie** (IntelliJ / PyCharm / WebStorm / ...) | `.junie/skills/` | via **Skill Manager** (IDE-wide or per-project) |
| **AWS Kiro / Amazon Q Developer** | `.kiro/skills/<name>/SKILL.md` | `~/.kiro/skills/` (`skill://` URIs) |
| **Google Antigravity** | `.agents/skills/` (default), `.agent/skills/` (legacy) | `~/.agents/skills/` |
| **Claude Code** (manual alternative to Tier 2) | `.claude/skills/` | `~/.claude/skills/` |
| **Gemini CLI** (manual alternative to Tier 2) | `.gemini/skills/`, `.agents/skills/` | `~/.gemini/skills/` |
| **OpenAI Codex CLI** (manual alternative to Tier 2) | `.codex/skills/` | `~/.codex/skills/` |
| **Block Goose** | reads `SKILL.md` (open-standard compatible) | — |

## Updating

- **Tier 1:** re-download the `latest` zip and re-upload.
- **Tier 2:** each tool's own update command (e.g. Claude Code
  `/plugin marketplace update agent-skills`).
- **Tier 3:** `git pull` and re-copy the folder.

Release tags (`vX.Y.Z`) map to versioned download URLs — see
[README → Updating / versioning](../README.md#updating--versioning).
