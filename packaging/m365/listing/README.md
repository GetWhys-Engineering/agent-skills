# Microsoft 365 Marketplace listing

The store listing for the **GetWhys MCP** app
([WA200012755](https://marketplace.microsoft.com/en-us/product/wa200012755)).
None of these files goes into `getwhys-m365.zip`. They exist so the listing is
reviewed in a pull request and checked on every build like the app's manifest is.
Partner Center has no upload for them, so someone copies each field in by hand.

| File | Partner Center field |
|---|---|
| `listing.json` `summary` | Marketplace listings → English → **Summary** |
| `description.html` | Marketplace listings → English → **Description** (simple HTML) |
| `listing.json` `screenshots` | Marketplace listings → English → **Screenshots**, in order, each with its caption |
| `listing.json` `videoUrl` | Marketplace listings → English → **Video link** |
| `listing.json` `eulaUrl` | Properties → **End User License Agreement (EULA) link** |
| `listing.json` `privacyUrl` | Properties → **Privacy policy link** |
| `listing.json` `supportUrl` | Properties → **Support document link** |

A listing change goes through Microsoft certification like a package change,
even when the package stays the same.

## Screenshots

This is a public repository, and a committed image stays in its history even
after it's replaced. Commit only screenshots made for publication:

- Use a demo organization: demo personas, brand voice and messaging frameworks,
  never a real customer's or GetWhys's own.
- Show no real people's names, avatars or email addresses.
- Show no conversation, run, workflow or content IDs.

Put them in `screenshots/` and list each one, with its caption, in
`listing.json`. While the list is empty, the live screenshots stay in Partner
Center and this folder doesn't track them.

## Checks

`scripts/package-m365-app.sh` runs `artifact-json.py verify-m365-listing` and
fails the build if the listing breaks one of these rules:

- The summary is one line of at most 100 characters (Partner Center's limit).
  The description is at most 10,000 characters.
- There are at most 5 screenshots. Each is a PNG of exactly 1366 x 768 pixels,
  no larger than 1,024 KB, with a caption and no text or EXIF metadata. Every
  file in `screenshots/` is listed.
- The EULA link equals the manifest's `developer.termsOfUseUrl`, and the privacy
  link equals `developer.privacyUrl`. The support link is an https URL, because
  Partner Center won't take an email address.
- The video link is on YouTube or Vimeo.
- In the order a reader sees them (summary, description, captions), the first
  mention of Copilot reads "Microsoft Copilot" or "Microsoft 365 Copilot". The
  first mention of Teams reads "Microsoft Teams". Later mentions can be short.
  Microsoft is never abbreviated "MS" or "MSFT". The manifest's names and
  descriptions get the same check.

Microsoft also checks rules that a script can't:

- Screenshots show the app working inside Microsoft 365 Copilot.
- Captions are part of each image, not only in the caption field.
- There is as little Teams UI around the app as possible.

See
[Teams Store validation guidelines: Screenshots](https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/deploy-and-publish/appsource/prepare/teams-store-validation-guidelines#screenshots).
