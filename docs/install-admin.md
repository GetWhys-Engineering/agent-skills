# Install GetWhys skills for your whole organization (no git required)

This page is for **workspace / org admins**. You'll download one file and upload
it in your admin settings — that's it. No command line, no git.

> **Prerequisite — connect the GetWhys MCP server first.**
> These skills guide your AI assistant in using the **GetWhys MCP server**, a
> paid GetWhys product connected through
> [GetWhys onboarding](https://www.getwhys.io). Skills are **inert without it**.
> The Claude Tag plugin declares the server endpoint, but its credential and
> allowed-host access still require separate Access bundle configuration.

## 1. Download the skill

Each skill is published as a `.zip` on this repo's
[Releases page](https://github.com/GetWhys-Engineering/agent-skills/releases).
Direct links (also in the [README skills table](../README.md#available-skills)):

```
https://github.com/GetWhys-Engineering/agent-skills/releases/latest/download/<skill>.zip   ← always the newest
https://github.com/GetWhys-Engineering/agent-skills/releases/download/vX.Y.Z/<skill>.zip   ← pinned version
```

The **same `<skill>.zip`** works for Claude and ChatGPT (§2a/§2b). Claude Tag
(§2d) and Microsoft 365 Copilot Cowork (§2c) each load a different package from
the same Releases page — **`getwhys-skills.zip`** and **`getwhys-cowork.zip`**
respectively.

## 2a. Claude.ai / Claude Desktop / Claude Cowork (Team & Enterprise)

One upload provisions **all three surfaces** — web, the Desktop Chat tab, and
Claude Cowork (where Cowork is enabled for your org — it's a separate org
toggle). Group targeting carries over.

1. Go to **Org settings → Skills**.
2. One-time setup: enable **Skills** and **Code execution & file creation**.
   > **Why code execution?** These skills are instruction-only — they guide
   > your assistant in calling the GetWhys MCP tools and run no code or file
   > creation on your machine. **Code execution & file creation** is a
   > platform-level prerequisite for Claude's Skills feature itself, not
   > something these skills use.
3. Under **Organization skills**, click **+ Add** and select the downloaded `.zip`.
4. Done — the skill is provisioned to **all users and enabled by default**.

## 2b. ChatGPT (Business / Enterprise / Edu / Teachers / Healthcare)

> Skills are in **beta** on these plans and **not available on Plus/Pro**.

1. Go to skills and choose **New skill → Upload from computer**, selecting the
   same `.zip`. ChatGPT scans the upload automatically.
2. **Share** the skill with your workspace. Admin permissions gate who can
   Enable / Upload / Share.

## 2c. Microsoft 365 Copilot Cowork (org-push)

> Copilot Cowork is currently a **Frontier preview** — your tenant must be
> enrolled in the Frontier program. (Note: this is Microsoft's Cowork,
> distinct from Claude Cowork above.)

Uses a different artifact: **`getwhys-cowork.zip`**, an M365 app package
bundling *all* GetWhys skills (same Releases page).

1. Download **`getwhys-cowork.zip`** from
   [Releases](https://github.com/GetWhys-Engineering/agent-skills/releases).
2. **M365 Admin Center → Manage Apps → Upload custom app** (sideload to test).
3. **Teams Admin Center → Copilot → Agents** → select the plugin →
   **Deploy to "Entire organization"**.
4. It's auto-acquired by all licensed Copilot users and shows
   *"Managed by your organization."*

Per-user alternative (no admin needed): drop a skill folder into OneDrive at
`/Documents/Cowork/skills/<name>/SKILL.md` — it's auto-discovered.

## 2d. Claude Tag (Claude in Slack)

> Claude Tag (Anthropic's Slack agent) is in **public beta** — this UI may change.

Claude Tag loads **plugins**, not skill zips, so it uses a different artifact:
**`getwhys-skills.zip`** (same Releases page). The plugin's root `.mcp.json`
declares `https://api.getwhys.io/mcp/org`, without credentials or headers. The
§2a skill zip is rejected by the plugin uploader, and a *public*-repo plugin
marketplace can't be registered org-wide — uploading the plugin package is the
supported path.

1. Download **`getwhys-skills.zip`** from
   [Releases](https://github.com/GetWhys-Engineering/agent-skills/releases).
2. **Org settings → Plugins → Add plugins → Upload plugin** → **Upload to a new
   marketplace**, give it a name (e.g. `getwhys`) → select the zip → **Upload**.
3. Enable **`getwhys-skills`** for the scope (workspace or channel) where Claude
   Tag should use it.
4. In that scope's Access bundle, open **Credentials**, click **Connect** next
   to **Custom tool**, and configure the GetWhys credential provided during
   onboarding.
5. Set the credential's **Allowed websites** host to `api.getwhys.io`. The
   plugin declaration alone does not grant network or authentication access.

See Anthropic's [custom MCP connection
guide](https://claude.com/docs/claude-tag/admins/connections/custom) for the
current Claude Tag flow.

## What "org-wide" actually means

Admin-provisioned skills are **on by default / shared with everyone**, but
individual members can still toggle a skill off for themselves. Neither Claude
nor ChatGPT currently offers a force-locked "always on" mode for skills.

## Updating

Re-download the `latest` zip and upload it again the same way. Pin a
`vX.Y.Z` URL instead if you want to control rollout timing.

---

*Using a CLI or IDE instead (Claude Code, Cursor, Codex, Gemini CLI, ...)?
See [install-platforms.md](install-platforms.md).*
