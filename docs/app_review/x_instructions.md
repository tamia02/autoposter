# X (Twitter) Developer Setup, Consent, and Billing Instructions

Overview

X's platform now requires a developer account with billing enabled for write operations. This document explains the recommended steps to obtain credentials and safely store tokens for automated posting.

Required developer steps

1. Create an X developer account and enable billing for your project.
2. Create an application (project) and register an OAuth client configured for user-context OAuth (so posts are created on behalf of a user).
3. Request the `tweet.write` scope (and `tweet.read` or others only if needed for features).
4. Complete a one-time OAuth user-consent flow for the target account to obtain access and refresh tokens. Keep a copy of the token expiry and refresh process documentation.

Token handling and rotation

- Store tokens in the routine's secured environment variables. Do not commit tokens to the repo.
- Monitor token lifetimes and set calendar reminders or an automated maintenance job to refresh tokens before expiry. X tokens and policies evolve; plan for periodic rotation.

Billing and cost considerations

- Posting may incur small per-write costs; estimate approximate costs during scale testing (e.g., $0.01–$0.02 per tweet). Costs can vary based on media attachments and API tiering.
- Use a test account and billing project for initial validation to avoid unexpected charges on production billing.

Demo & review package

- For internal review, supply a short demo showing the OAuth consent flow and one successful test post created via the API. Provide the API request and response logs (redacting tokens) to demonstrate correct usage.
