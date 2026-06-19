# Setup & Usage Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install
```

## 2. Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

**Minimum required:** `OPENAI_API_KEY` (for AI content generation).

Everything else is optional and enables specific features:

| Variable | Feature |
|----------|---------|
| `OPENAI_API_KEY` | AI-powered content writing (falls back to templates without it) |
| `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_AUTHOR_URN` | LinkedIn posting + image upload |
| `X_API_KEY` + `X_API_SECRET` + `X_ACCESS_TOKEN` + `X_ACCESS_TOKEN_SECRET` | X/Twitter posting (OAuth 1.0a for write access) |
| `THREADS_ACCESS_TOKEN` + `THREADS_USER_ID` | Threads publishing |
| `EMAIL_*` variables | Email notifications ("your content is ready") |
| `GOOGLE_*` variables | Google Sheets/Docs as research sources |

## 3. Single Topic Pipeline

```bash
python -m skill.orchestrate --topic "Why founders should automate early" --no-pr
```

This runs: Research → AI Generate → Render Image → Save Drafts.

With competitors:
```bash
python -m skill.orchestrate \
  --topic "AI automation tips" \
  --competitors "Gary Vee,Alex Hormozi" \
  --hashtags "AI,automation,founder" \
  --no-pr
```

With PR creation:
```bash
python -m skill.orchestrate \
  --topic "AI automation tips" \
  --publish-mode pr-only
```

With live publishing:
```bash
python -m skill.orchestrate \
  --topic "AI automation tips" \
  --publish-mode live
```

## 4. Weekly 7-Day Batch

Generate all 7 days at once with per-topic research, AI generation, unique images, and email notification:

```bash
python -m skill.orchestrate --weekly
```

With competitor research:
```bash
python -m skill.orchestrate --weekly \
  --competitors "Gary Vee,Alex Hormozi" \
  --competitor-urls "https://competitor.com/blog"
```

Output structure:
```
drafts/weekly/
  day1_topic_name/
    linkedin_draft.md
    x_draft.md
    threads_draft.md
    share_image.png
  day2_topic_name/
    ...
```

Topics are pulled from `calendar.yaml` (next 7 days) or built-in defaults.

## 5. Voice Profiling

Record yourself talking about your work (2-5 minutes). Then:

```bash
python -m skill.voice.cli your_audio.mp3
```

This creates `knowledge/voice.md` with your tone, vocabulary, and speaking patterns. The AI generator uses this to write content that sounds like you.

## 6. Scheduling

### Calendar (`calendar.yaml`)

```yaml
- id: 1
  topic: "Why AI automation is the growth secret founders still ignore"
  status: scheduled
  scheduled_date: 2026-06-19
```

### Daily Routine

```bash
python -m skill.routine daily
```

Checks the calendar, runs today's topic through the full pipeline, sends email on completion.

### Weekly Routine

```bash
python -m skill.routine weekly
```

Generates all content for the next 7 days, sends a batch summary email.

### Publishing Existing Drafts

```bash
python -m skill.routine publish --dir drafts/weekly/day1_topic
```

Publishes to all platforms (requires `PUBLISH_MODE=live`).

## 7. Platform Setup

### LinkedIn
1. Create an app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Request `w_member_social` scope
3. Get an OAuth access token
4. Set `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_AUTHOR_URN` in `.env`
5. See `docs/app_review/linkedin_app_review.md` for details

### X (Twitter)
1. Apply for developer access at [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a project + app with Read & Write permissions
3. Generate OAuth 1.0a keys (API Key, API Secret, Access Token, Access Token Secret)
4. Set all four `X_*` variables in `.env`
5. See `docs/app_review/x_instructions.md` for details

### Threads (Meta)
1. Create a Meta developer app
2. Request `threads_basic` and `threads_content_publish` permissions
3. Get access token and user ID
4. Set `THREADS_ACCESS_TOKEN` and `THREADS_USER_ID` in `.env`
5. See `docs/app_review/threads_app_review.md` for details

## 8. Email Notifications

Configure Gmail SMTP (or any SMTP provider):

```
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=you@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=you@gmail.com
EMAIL_USE_TLS=true
```

For Gmail, use an [App Password](https://myaccount.google.com/apppasswords) (not your regular password).

You'll receive:
- **Weekly batch summary**: "Your 7-day content is ready" with topic list
- **Per-topic notifications**: success/failure for scheduled runs
- **Publish confirmations**: when posts go live

## 9. Analytics & Dashboard

```bash
# View engagement report
python -m skill.routine report

# Generate HTML dashboard
python -c "from skill.dashboard import generate_dashboard; print(generate_dashboard())"
```

Update engagement metrics after posts are live:
```python
from skill.analytics import EngagementTracker
tracker = EngagementTracker()
tracker.update_metrics('post_id', {'likes': 42, 'comments': 8, 'shares': 3})
```

## 10. Google Sheets/Docs Integration

Use a Google Sheet as your content calendar or a Google Doc as research input:

```bash
python -m skill.orchestrate \
  --topic "Your topic" \
  --google-sheet-id YOUR_SHEET_ID \
  --google-doc-id YOUR_DOC_ID
```

Requires a Google service account. Set `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` in `.env`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No AI generation | Set `OPENAI_API_KEY` in `.env` |
| Playwright fails | `python -m playwright install` |
| Web search empty | Rate limited — wait 1-2 min and retry |
| X posting fails | Ensure OAuth 1.0a keys (not just Bearer token) |
| Email not sending | Use Gmail App Password, not regular password |
| Calendar topics not found | Check date format in `calendar.yaml` (`YYYY-MM-DD`) |
