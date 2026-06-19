# LinkedIn/X/Threads Auto-Poster

Automated social media content pipeline powered by Claude AI:

1. **Research** competitors and trending topics (DuckDuckGo + direct URL scraping)
2. **Generate** platform-specific drafts using AI in your voice (Claude API)
3. **Render** unique branded share images per post (Playwright)
4. **Notify** you by email when your 7-day content batch is ready
5. **Publish** to LinkedIn, X (threads), and Threads with image uploads

## Quick Start

```bash
# Install
pip install -r requirements.txt
python -m playwright install

# Set your API key
cp .env.example .env
# Edit .env with your OPENAI_API_KEY (minimum) + platform tokens

# Generate a single topic
python -m skill.orchestrate --topic "Your topic" --no-pr

# Generate a full 7-day batch
python -m skill.orchestrate --weekly

# With competitor research
python -m skill.orchestrate --weekly --competitors "Gary Vee,Alex Hormozi"
```

## Commands

| Command | What it does |
|---------|-------------|
| `python -m skill.orchestrate --topic "..."` | Single topic: research + AI draft + image + PR |
| `python -m skill.orchestrate --weekly` | 7-day batch: per-topic research + AI + images + email |
| `python -m skill.routine daily` | Run today's scheduled calendar topic |
| `python -m skill.routine weekly` | Full weekly batch + email notification |
| `python -m skill.routine publish` | Publish existing drafts live |
| `python -m skill.routine report` | Engagement analytics report |
| `python -m skill.voice.cli audio.mp3` | Ingest your voice/tone from audio |
| `python -m skill.research.cli --topic "..."` | Research-only mode |

## Architecture

```
skill/
  ai/           Claude API integration (content generation + image quotes)
  research/     Web search + competitor scraping + summarization
  generator/    AI-powered draft generation + template fallback + weekly batch
  renderer/     Playwright image rendering with 7 gradient styles
  posting/      LinkedIn (image upload) + X (OAuth threads) + Threads (2-step publish)
  voice/        Whisper audio transcription + voice profiling
  google/       Google Sheets/Docs connectors
  orchestrate.py   Main pipeline (single + weekly modes)
  routine.py       Routine scheduler CLI (daily/weekly/publish/report)
  scheduler.py     Calendar management + execution logging
  notification.py  Email notifications (per-topic + weekly batch summary)
  analytics.py     Engagement tracking + insights feedback loop
  dashboard.py     HTML dashboard generator
  git_helper.py    Git commit + branch + PR automation
```

## See Also

- **[Full Setup Guide](docs/SETUP_AND_USAGE.md)** — environment, tokens, scheduling
- **[Quick Reference](QUICK_REFERENCE.md)** — one-liner commands
- **[App Review Guides](docs/app_review/)** — LinkedIn, Threads, X developer setup
