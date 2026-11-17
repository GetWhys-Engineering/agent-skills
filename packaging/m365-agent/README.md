# GetWhys Buyer Intelligence for Microsoft 365 Copilot

This project builds an installable Microsoft 365 app containing a declarative
agent and an authenticated remote-MCP action. Customers install the published
app, open **GetWhys Buyer Intelligence**, sign in to GetWhys, and chat. They do
not create an agent or attach tools themselves.

This package is separate from `packaging/m365/`, the existing connector-only
Marketplace app that uses `agentConnectors` and `ConnectionVault`. Do not copy
`shared_getwhysmcp` into this project.

## Package architecture

```text
manifest.json (Microsoft 365 app manifest 1.30)
└── copilotAgents.declarativeAgents → declarativeAgent.json (v1.9)
    ├── actions → ai-plugin.json (v2.4)
    │   └── RemoteMCPServer → https://api.getwhys.io/mcp/org
    └── agent_skills → skills/validate-gtm-output/SKILL.md
```

The bundled agent skill is copied from the repository's canonical
`skills/validate-gtm-output/` directory at build time, including its reference
files. Do not maintain a second copy under `appPackage/`; the packaging script
and Agents Toolkit lifecycle both stage the canonical source automatically.

`ai-plugin.json` omits `mcp_tool_description`, has an empty `functions` array,
and dispatches `run_for_functions: ["*"]`. Microsoft therefore discovers tools
at runtime with MCP `tools/list`.

Authentication uses `OAuthPluginVault`. The `reference_id` is a Microsoft
authentication-configuration ID created by `dcr/register`; it is not an OAuth
client ID. The generated OAuth client ID and secret remain between Microsoft
and the GetWhys authorization server and must never be committed.

## Developer prerequisites

- VS Code and Microsoft 365 Agents Toolkit 6.12.0 or later.
- Node.js 20 or 22 (required by Agents Toolkit and the skill staging step).
- A work or school Microsoft 365 development account with a Microsoft 365
  Copilot license.
- Permission to upload custom apps and access Copilot in the development tenant.
- Permission to create Microsoft app registrations and Enterprise token-store
  authentication configurations through Agents Toolkit.
- `python3`, `zip`, `curl`, and `jq` for repository validation.
- `uv` or `pipx` for validation against Microsoft's live JSON schemas.
- For public release: a Partner Center publisher enrolled in the **Microsoft
  365 and Copilot** program and a separate customer-like tenant for the required
  cross-tenant test.

## Validate locally without provisioning

From the repository root:

```bash
./scripts/validate-m365-agent.sh
```

This uses non-live sentinel IDs in a temporary package, validates all three
official schemas, verifies the bundled skill byte-for-byte against its canonical
source, checks the ZIP layout, and performs read-only checks of GetWhys OAuth
discovery metadata. It never registers an OAuth client or modifies a Microsoft
tenant. Set `SKIP_REMOTE_DCR_CHECK=1` only for offline validation.

## Provision DCR in a development tenant

Provisioning changes Microsoft tenant state and dynamically registers an OAuth
client with GetWhys. Run it only after the tenant owner approves those changes.

1. Copy `env/.env.dev.example` to `env/.env.dev`. Keep the generated file local;
   `.gitignore` excludes it.
2. Open `packaging/m365-agent/` as the project folder in VS Code.
3. Sign in through Microsoft 365 Agents Toolkit. Confirm **Custom App Upload
   Enabled** and **Copilot Access Enabled**.
4. In the Toolkit Lifecycle panel, select **Provision** and approve the change.
5. The lifecycle creates a development Microsoft app, runs `dcr/register`,
   validates the package, updates the development app, and shares the agent to
   the configured development scope.
6. Confirm `env/.env.dev` now contains non-empty, different values for:
   `TEAMS_APP_ID` and `GETWHYS_DCR_AUTH_ID`. The second value is Microsoft's
   auth-configuration ID. It must not equal an OAuth client ID or
   `shared_getwhysmcp`.

The DCR lifecycle is intentionally configured with:

- `applicableToApps: AnyApp`
- `targetAudience: AnyTenant`
- `includePersonalMicrosoftAccounts: false`
- the complete MCP endpoint for both discovery and the allowed target

These settings are required for work/school users outside the publisher tenant.
They do not grant access to a GetWhys organization; organization access comes
from each user's GetWhys sign-in and authorization grant.

## Build the exact release ZIP

The two production IDs come from the approved Agents Toolkit **Provision**
lifecycle; they are not values GetWhys invents:

- `TEAMS_APP_ID` is the Microsoft 365 app GUID returned by `teamsApp/create`.
- `GETWHYS_DCR_AUTH_ID` is the Microsoft authentication-configuration ID
  returned by `dcr/register`. It is not the dynamically registered OAuth
  `client_id`, and it is not `shared_getwhysmcp`.

Provision them once for production:

1. Copy `env/.env.prod.example` to `env/.env.prod` and set the intended semantic
   `APP_VERSION`. Keep `APP_NAME_SUFFIX` empty.
2. Open `packaging/m365-agent/` in VS Code, select the `prod` environment, sign
   in to the publisher tenant, and run **Provision** after tenant-owner approval.
3. Agents Toolkit writes `TEAMS_APP_ID` and `GETWHYS_DCR_AUTH_ID` into
   `env/.env.prod`. Keep that generated file local.
4. In GitHub, open **Settings → Secrets and variables → Actions →
   Variables** and create repository variables named `TEAMS_APP_ID` and
   `GETWHYS_DCR_AUTH_ID` using those two values. They are identifiers rather
   than credentials, so do not store the generated OAuth client secret or any
   token in GitHub.

The tag-release workflow maps those repository variables into the packaging
process and derives `VERSION` from the `v*` tag. Defining a GitHub variable does
not inject it automatically; the explicit `env` mapping in
`.github/workflows/release.yml` performs that handoff. A missing value fails the
release instead of producing a package with an unresolved placeholder.

To build the same production package locally, load the provisioned environment:

```bash
set -a
. packaging/m365-agent/env/.env.prod
set +a
./scripts/package-m365-agent.sh
```

The output is `dist/getwhys-m365-agent.zip`. The build fails if either Microsoft
ID is absent, if the connector-only reference is reused, if static MCP tools are
introduced, or if credentials appear in a manifest.

If production provisioning is intentionally repeated and Microsoft returns a
new app or authentication-configuration ID, update the corresponding GitHub
variable before creating the release tag.

Do not submit a ZIP produced with the sentinel values used by the validation
script. Submit only the exact production ZIP that passed the full test checklist.

## Current Microsoft constraints and release gate

Microsoft currently requires DCR to return a `client_secret`. GetWhys supports
`client_secret_basic` and `client_secret_post`, returns a non-expiring secret
for secret-based registrations, and requires PKCE for authorization-code flows.

The live authorization-server metadata currently advertises authorization-code
and JWT-bearer grants but does not list `refresh_token` in
`grant_types_supported`. The backend is expected to accept refresh-token grants,
but the production checklist must prove refresh through Microsoft's actual DCR
configuration. If Microsoft relies on the metadata list, add `refresh_token` to
the advertised grants before release.

Microsoft's documented `AnyTenant`/`AnyApp` settings express public reach, but
schema validation and publisher-tenant testing do not prove that the auth
configuration resolves for another tenant. Before Partner Center submission,
install the exact package in a separate Microsoft 365 tenant and complete DCR,
sign-in, token refresh, sign-out, and organization-isolation tests. Treat any
cross-tenant failure as a release blocker and escalate it to Microsoft with the
auth-configuration ID and app ID (never with client secrets or tokens).

See also:

- [Customer installation and sign-in](CUSTOMER_INSTALL.md)
- [Release test checklist](TEST_CHECKLIST.md)
- [Partner Center submission](PARTNER_CENTER.md)

Official Microsoft references used for this implementation:

- [Build a declarative-agent MCP plugin](https://learn.microsoft.com/en-us/plugins/build-mcp-plugins)
- [Configure DCR](https://learn.microsoft.com/en-us/plugins/plugin-authentication-dynamic-client-registration)
- [Plugin manifest schema 2.4](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/plugin-manifest-2.4)
- [Declarative agent schema 1.9](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest)
- [Add skills to declarative agents](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/build-declarative-agents-add-custom-skills)
- [Publish publicly through Microsoft Marketplace](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/publish-plugin-publicly)
