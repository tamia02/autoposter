# Threads / Meta App Review — Detailed Justification and Implementation Notes

Overview

This integration publishes Threads content for an Instagram Business or Creator account via the Meta Graph API. Posting requires that the Instagram account be linked to the Threads profile and that the app has been granted the `threads_content_publish` capability during app review.

Primary use cases

- Schedule short-form posts and attach a generated image rendered by the routine's headless renderer.
- Enable cross-posting workflows where content is drafted once and adapted to each platform's style.

Permissions and OAuth

- The app will request only the `threads_content_publish` scope (and any minimal user identity scopes Meta requires for the chosen flow). App Review will be accompanied by a clear description of the business or creator account in use and confirmation that the account is eligible (Business/Creator and linked to Threads).
- Authorization is done via OAuth; tokens are stored in the routine environment variables. Token refresh/rotation is handled externally and noted in the submission.

Data handling and privacy

- Stored data: OAuth tokens in the routine runtime environment and generated media files in the cloned repo working directory. No additional profile or follower data is stored or analyzed.
- Only post text and media bytes are sent to Meta when publishing.

Safety and review process (demo expectations)

- Provide a short demo video or screencast showing: (1) performing the OAuth flow for the Instagram Business/Creator account; (2) running the routine to create a draft, render the image, upload to the container endpoint, and publish a test post.
- Explain that the default configuration is `pr-only` (no automatic live publishing) and that live publishing will be enabled only after manual verification.

Implementation notes for reviewers

- The routine implements the two-step container-then-publish flow: upload media to the container endpoint, then call the publish endpoint with the container ID.
- Tokens are never checked into source control and live only in the routine environment variables.

Contact & support

We can provide a demo company/creator account and a short recorded walkthrough for the review team showing the full token flow and a successful test publish.
