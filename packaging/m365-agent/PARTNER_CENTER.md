# Partner Center submission

Submit only after the complete test checklist passes in both the publisher
tenant and a separate customer-like tenant.

## Prerequisites

- Enroll the publisher in the Microsoft 365 and Copilot Partner Center program.
- Confirm the **Apps and agents for Microsoft 365 and Copilot** offer type
  accepts a declarative agent with an MCP action for public distribution.
- Preserve the production Microsoft app ID for every update after the first
  published version.
- Record the exact tested ZIP, SHA-256, version, DCR auth-configuration ID,
  supported Microsoft 365 experiences, and release owner.

## Listing assets and disclosures

Prepare outside the package:

- Listing name: **GetWhys Buyer Intelligence**.
- Summary and full description consistent with `manifest.json`.
- Store icons, screenshots of the agent, sign-in, evidence-backed results, and
  any required promotional images.
- Support URL, privacy policy, terms of use, publisher contact, regions, and
  supported languages.
- A clear disclosure that an active paid GetWhys account and organization
  access are required, including any additional-purchase selection required by
  Partner Center.
- Customer installation, user sign-in, consent, sign-out, and removal steps.
- Supported Microsoft 365 experiences and known limitations.

Do not put CTA hyperlinks such as **Sign up**, **Get started**, **Help**, or
**Contact us** inside the app manifest description. Put the required links in
Partner Center's designated support, privacy, terms, and listing fields.

## Reviewer accounts and test notes

Create dedicated, nonemployee reviewer accounts with stable access for the
entire certification window:

- A Microsoft 365 test user licensed for Copilot and permitted to install/use
  the submitted agent if Microsoft does not supply its own licensed context.
- A GetWhys reviewer user in a dedicated review organization containing safe,
  representative personas, messaging frameworks, documents, and buyer evidence.
- Optionally, a second GetWhys user/organization for isolation testing.

Enter credentials only in Partner Center's certification fields. Never commit
them or place them in the ZIP, README, screenshots, or public listing. Reviewers
cannot contact an employee to obtain missing credentials, so include complete
steps and all required values in the submission.

Certification notes should state:

1. Install and open **GetWhys Buyer Intelligence**.
2. Use a supplied starter that requires a GetWhys tool.
3. Select the sign-in prompt and use the dedicated GetWhys reviewer account.
4. Approve access and retry the prompt if Microsoft does not resume it.
5. Verify an evidence-backed response with tool-supplied citations.
6. Test persona, uploaded-document, and content-evaluation scenarios with the
   supplied safe sample data.
7. Sign out through Copilot Chat settings and verify that the next tool-backed
   request prompts for sign-in.
8. Note that DCR is pre-provisioned through Microsoft's Enterprise token store;
   no reviewer creates a client or enters a secret.

Also disclose the external MCP endpoint, OAuth/PKCE dependency, required
GetWhys account, data accessed, retention/support expectations, and the fact
that organization authorization comes from the user's GetWhys grant.

## Submission

1. Sign in to Partner Center and open **Marketplace offers**.
2. Select the **Microsoft 365 and Copilot** tab.
3. Create **Apps and agents for Microsoft 365 and Copilot**, or update the
   intended existing offer only if Microsoft confirms its identity and package
   migration path.
4. Complete product setup, including the additional-purchase disclosure.
5. Upload the exact tested `getwhys-m365-agent.zip`.
6. Complete properties, legal/support information, Marketplace listings,
   availability, certification notes, and optional detailed reviewer PDF.
7. Review and submit for certification. Record the offer ID, package version,
   submission date, status, and owner.

Submission does not publish the offer. Track certification findings, rerun all
affected tests after any package change, and publish only the approved version.
