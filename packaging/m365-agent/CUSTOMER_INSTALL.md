# Customer installation and sign-in

## Administrator installation

1. In Microsoft Marketplace, find **GetWhys Buyer Intelligence**.
2. Acquire the app for the organization.
3. In the Microsoft 365 admin center, review and allow the GetWhys publisher
   and app, then assign or make it available to the intended licensed users.
4. Confirm those users have Microsoft 365 Copilot and are allowed to use agents
   and third-party plugins under the organization's policies.

No administrator or user should create a declarative agent, attach an MCP tool,
register an OAuth client, or enter a client secret.

## User sign-in

1. Open Microsoft 365 Copilot and select **GetWhys Buyer Intelligence** from
   the agent list or Agent Store.
2. Start a conversation or select a starter.
3. When Microsoft displays **Sign in to GetWhys Buyer Intelligence**, select it.
4. Sign in to GetWhys and authorize access. Use an account that belongs to the
   GetWhys organization whose personas, frameworks, documents, and research
   should be available.
5. Return to Copilot. Retry the original prompt if it did not resume
   automatically.

The Microsoft app and OAuth registration are not bound to one customer
organization. GetWhys determines organization access from the signed-in user
and the authorization grant.

## Troubleshooting

- **No sign-in prompt:** Ask the Microsoft 365 administrator to confirm that
  the app is installed, assigned, and allowed by agent/plugin policy.
- **Sign-in repeats:** Sign out from **Microsoft 365 Copilot → Chat settings →
  Agents**, reopen the agent, and sign in again. If it persists, contact GetWhys
  support with the time of failure; never send tokens or secrets.
- **Signed in but access denied:** Confirm that the same GetWhys account has
  access to the intended GetWhys organization. A Microsoft administrator cannot
  grant GetWhys organization membership.
- **Expected personas or documents are absent:** Verify the selected GetWhys
  organization and its configured artifacts.
- **Remove access:** Sign out from the agent in Copilot Chat settings. An
  administrator can also unassign or remove the app.
