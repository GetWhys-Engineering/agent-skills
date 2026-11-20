# Microsoft 365 agent release test checklist

Record the package SHA-256, app ID, auth-configuration ID, package version,
Microsoft tenant IDs, test date, and tester. Never record tokens, authorization
codes, client secrets, or customer data.

## Static validation

- [ ] `./scripts/validate-m365-agent.sh` passes.
- [ ] The exact production ZIP passes `./scripts/package-m365-agent.sh` and
      Microsoft `teamsApp/validateAppPackage` validation.
- [ ] The ZIP contains the five root package files plus only the canonical
      `skills/validate-gtm-output/` skill and its reference files.
- [ ] `manifest.json` uses numbered schema 1.30 and references the declarative
      agent through `copilotAgents.declarativeAgents`.
- [ ] The agent references `ai-plugin.json` through `actions`.
- [ ] The agent references `skills/validate-gtm-output` (no leading `./`) through
      `agent_skills`, and its packaged files match the canonical repository
      skill byte-for-byte.
- [ ] The plugin uses `RemoteMCPServer`, the exact GetWhys URL,
      `OAuthPluginVault`, the provisioned DCR auth-configuration ID, wildcard
      dispatch, and no `mcp_tool_description`.
- [ ] No client ID, client secret, token, authorization code, or
      `shared_getwhysmcp` appears in source, environment-independent artifacts,
      logs, or review materials.

## DCR and PKCE

- [ ] Provisioning creates a new Microsoft DCR auth configuration and writes
      its ID to `GETWHYS_DCR_AUTH_ID`.
- [ ] The auth configuration is `AnyTenant`, `AnyApp`, and work/school accounts.
- [ ] The protected-resource metadata identifies the exact MCP resource and
      `mcp:tools` scope.
- [ ] Authorization-server metadata advertises an RFC 7591 registration
      endpoint, authorization and token endpoints, `S256`, and a supported
      secret-based token authentication method.
- [ ] Registration returns a distinct OAuth `client_id`, a `client_secret`,
      `client_secret_expires_at: 0`, and the selected token authentication
      method. Verify server-side telemetry without copying these values into
      test records.
- [ ] Authorization uses PKCE S256; a missing or incorrect verifier fails.
- [ ] Code exchange succeeds only with the registered authentication method and
      correct secret; wrong or missing client authentication fails.

## User flows

- [ ] A clean user sees the GetWhys sign-in prompt on the first tool-backed turn.
- [ ] Successful sign-in returns to Copilot and the original tool-backed task
      completes.
- [ ] Dynamic `tools/list` discovery exposes the expected GetWhys tools without
      a bundled static catalog.
- [ ] A buyer-research answer retrieves evidence and preserves tool-supplied
      sources; the agent invents no interviews, quotations, or citations.
- [ ] Persona, messaging-framework, brand-voice, and uploaded-document workflows
      preserve the identifiers required by later tool calls.
- [ ] An account without GetWhys organization access receives a clear access
      explanation rather than a fabricated answer.
- [ ] A refresh after the initial access token expires succeeds with the same
      registered client authentication method.
- [ ] Signing out through Copilot Chat settings clears the connection; the next
      tool-backed request requires sign-in again.

## Cross-tenant and organization isolation

- [ ] Install the exact package in a second Microsoft 365 tenant unrelated to
      the publisher tenant; app acquisition and auth-configuration resolution
      both succeed.
- [ ] A user in GetWhys organization A can retrieve A's permitted personas,
      frameworks, and documents but none belonging only to organization B.
- [ ] After sign-out, a user in GetWhys organization B can retrieve B's
      permitted data but none belonging only to organization A.
- [ ] Reusing prompts, Copilot conversations, session IDs, document IDs, persona
      handles, or content IDs across those users does not cross organization
      boundaries.
- [ ] Server telemetry shows grants and tool calls scoped to the signed-in
      GetWhys user/organization, not the Microsoft publisher tenant.

Any failed cross-tenant, PKCE, token-refresh, or organization-isolation check is
a release blocker.
