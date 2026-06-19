# LinkedIn App Review — Detailed Justification and Implementation Notes

Overview

This integration programmatically creates and publishes posts on behalf of a LinkedIn member or organization using the Community Management API ("Share on LinkedIn"). The routine is intended for scheduled and curated content publishing with an explicit human review option. Initial operation will be PR-only (drafts committed to the repo); publishing can be enabled later after verification.

Primary use cases

- Schedule and publish company updates, product announcements, and thought-leadership posts from a maintained editorial calendar.
- Publish short-form personal posts for a single account when authorized by the account owner.
- Upload and attach a generated share image to increase engagement.

Permissions and OAuth

- The app will request the minimum publish scopes required by LinkedIn's review: organization posting and/or member posting scopes (for example, the Community Management product and relevant w_* scopes). Scopes requested will be limited to posting and media upload; no broad-profile read scopes will be requested unless required for a feature.
- Authorization is performed via a one-time OAuth consent flow. The routine stores the issued refresh token in the routine environment (secure store). The token refresh cycle is managed outside the routine (manual refresh reminders or a separate maintenance process).

Data handling and privacy

- Stored data: OAuth tokens only (kept as environment variables in the routine runtime). The repo contains generated drafts and rendered images; these are not transmitted except when explicitly publishing.
- No long-term profile, connections, or messages are harvested. Only post text and optional media bytes are sent to LinkedIn at publish time.
- The app exposes a configurable `PUBLISH_MODE` (default `pr-only`) so initial runs create draft files and PRs rather than publishing live.

Safety and review process (demo expectations)

- Demonstration should show: (1) performing a one-time OAuth flow to obtain a token; (2) running the routine to generate platform-specific drafts; (3) rendering an image locally; (4) optionally executing a publish cycle using a test/org account.
- For review, provide a short screencast (1–2 minutes) showing the above steps and a sample token lifecycle management plan.

Implementation notes for reviewers

- The routine's publishing wrapper performs a REST `POST /rest/posts` call for organization/person posts and uses the documented media upload flow when attaching images.
- Token storage: tokens are stored only in the environment variables of the routine runtime; CI/Repo does not contain secrets.
- The project includes a human-review safe default (`PUBLISH_MODE=pr-only`) and clear instructions to enable live publishing only after review and confirmation by the account owner.

Contact & support

If LinkedIn reviewers need an in-person demo or temporary test credentials, we can supply a demo company page and a short recorded walkthrough showing the full OAuth and publish flow.
