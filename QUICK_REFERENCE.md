# Quick Reference

## One-Line Commands

### Generate a single topic (AI-powered)
```bash
python -m skill.orchestrate --topic "Your topic" --no-pr
```

### Generate a full 7-day content batch
```bash
python -m skill.orchestrate --weekly
```

### With competitor research
```bash
python -m skill.orchestrate --weekly --competitors "Gary Vee,Alex Hormozi" --competitor-urls "https://example.com/blog"
```

### Single topic with competitors + live publish
```bash
python -m skill.orchestrate --topic "AI automation tips" --competitors "Gary Vee" --publish-mode live
```

### Ingest your voice from audio
```bash
python -m skill.voice.cli your_voice.mp3
```

### Research only
```bash
python -m skill.research.cli --topic "LinkedIn personal branding" --competitors "Alex Hormozi"
```

### Run today's scheduled topic
```bash
python -m skill.routine daily
```

### Generate weekly batch + email notification
```bash
python -m skill.routine weekly
```

### Publish existing drafts live
```bash
python -m skill.routine publish --dir drafts/weekly/day1_topic
```

### Engagement report
```bash
python -m skill.routine report
```

## Environment Variables

```bash
# Required for AI generation
OPENAI_API_KEY=your_key

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_AUTHOR_URN=urn:li:person:YOUR_ID

# X (Twitter) — OAuth 1.0a for write access
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_secret

# Threads
THREADS_ACCESS_TOKEN=your_token
THREADS_USER_ID=your_user_id

# Email notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=you@example.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=you@example.com

# Control
PUBLISH_MODE=pr-only  # or "live"
```

## File Locations

| File | Purpose |
|------|---------|
| `knowledge/voice.md` | Your voice profile & tone |
| `calendar.yaml` | Topic calendar & scheduling |
| `drafts/` | Single-topic drafts |
| `drafts/weekly/` | 7-day batch drafts |
| `skill/orchestrate.py` | Main pipeline (single + weekly) |
| `skill/routine.py` | Routine scheduler CLI |
| `skill/ai/client.py` | Claude AI content generation |
| `skill/research/fetcher.py` | Web + competitor research |
| `skill/renderer/styles.py` | Image card styles |

## Workflow

1. **Set up** `.env` with your API keys
2. **Ingest voice** from audio (`python -m skill.voice.cli audio.mp3`)
3. **Generate weekly batch** (`python -m skill.orchestrate --weekly`)
4. **Review drafts** in `drafts/weekly/`
5. **Get email** "Your 7-day content is ready"
6. **Publish** when ready (`python -m skill.routine publish`)

## Status

- AI content generation (Claude API)
- Web research (DuckDuckGo + Bing)
- Competitor scraping & analysis
- Per-topic unique research
- Unique branded images per post
- 7-day batch generation
- Email notification ("content ready")
- LinkedIn posting with image upload
- X/Twitter thread posting with media
- Threads publishing flow
- Voice profiling from audio
- Content calendar + scheduling
- Analytics & engagement tracking
- Dashboard (HTML report)
- Git + PR automation
