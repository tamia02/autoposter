# Scheduling & Analytics Guide

## Scheduling Options

### Option 1: Claude Code Routine (Recommended)

Claude Code routines handle scheduling automatically. Set up your routine to run daily:

**Routine Prompt:**
```
python -m skill.routine daily
```

**Schedule:** Daily at 8 AM (or your preferred time)

This will:
1. Check `calendar.yaml` for today's topics
2. Run the orchestrator for any scheduled items
3. Create PRs for review
4. Log execution status

### Option 2: Local APScheduler (for testing)

```bash
pip install apscheduler

python -c "
from apscheduler.schedulers.background import BackgroundScheduler
from skill.routine import routine_daily_check
import time

scheduler = BackgroundScheduler()
scheduler.add_job(routine_daily_check, 'cron', hour=8, minute=0)
scheduler.start()

print('Scheduler running... Press Ctrl+C to stop.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
"
```

### Option 3: System Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line (8 AM daily):
0 8 * * * cd /path/to/repo && python -m skill.routine daily
```

### Option 4: Windows Task Scheduler

```powershell
# Create a scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m skill.routine daily" -WorkingDirectory "C:\path\to\repo"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "LinkedInAutoPost" -Description "Daily content posting"
```

---

## Calendar Format

Add `repeat_interval_days` to keep a topic on a recurring cadence. The scheduler will advance the date after a successful run.

```yaml
- id: 2
  topic: "How to structure a weekly newsletter"
  status: scheduled
  scheduled_date: 2026-07-01
  repeat_interval_days: 7
```

---

## Dashboard

Generate a simple HTML dashboard of your schedule, recent runs, and engagement summary:

```bash
python -m skill.dashboard
```

Then open `reports/dashboard.html` in your browser.

---

Edit `calendar.yaml`:

```yaml
- id: 1
  topic: "Productivity tips for remote teams"
  status: draft
  scheduled_date: 2026-06-25
- id: 2
  topic: "How to structure a weekly newsletter"
  status: scheduled
  scheduled_date: 2026-07-01
```

**Statuses:**
- `draft` — not ready to publish
- `scheduled` — ready, will run on scheduled_date
- `published` — already posted
- `archived` — skip this topic

---

## Analytics & Reporting

### View Engagement Metrics

```bash
python -m skill.routine report
```

Output example:
```
=== Engagement Report (30 days) ===

Platform Summary:

LinkedIn:
  Posts: 5
  Avg Engagement: 24.2
  Total Likes: 85
  Total Comments: 12

X:
  Posts: 8
  Avg Engagement: 18.5
  Total Likes: 120
  Total Comments: 32

Top Topics:
1. Design thinking for startups (avg score: 45.3)
2. Personal branding (avg score: 38.1)
3. Remote work culture (avg score: 32.7)
```

### Logged Files

- `reports/execution_log.json` — Each routine run
- `reports/engagement.json` — Post metrics (manual update required)
- `reports/engagement_report_*.txt` — Generated reports

### Manual Metrics Update

Track engagement by editing `reports/engagement.json`:

```json
{
  "post_id": "linkedin_topic_123",
  "platform": "linkedin",
  "topic": "Design for startups",
  "created_at": "2026-06-17T10:00:00",
  "metrics": {
    "likes": 85,
    "comments": 12,
    "shares": 3,
    "views": 1200,
    "engagement_rate": 8.1
  }
}
```

Then generate a report:

```bash
python -m skill.routine report --days 30
```

---

## Integration Checklist

- [ ] Add 3–5 topics to `calendar.yaml` with dates
- [ ] Set `status: scheduled` for topics you want to run
- [ ] Create Claude Code routine with prompt: `python -m skill.routine daily`
- [ ] Set routine to run at your preferred time
- [ ] Add platform tokens to routine environment variables
- [ ] Monitor execution logs in `reports/execution_log.json`
- [ ] After posts publish, manually update engagement metrics
- [ ] Run `python -m skill.routine report` weekly to track performance

---

## Feedback Loop

1. **Post:** Routine creates PR → you review & merge
2. **Monitor:** Track likes, comments, shares for 3–7 days
3. **Analyze:** Run `python -m skill.routine report`
4. **Iterate:** Update `knowledge/voice.md` or `calendar.yaml` based on top topics
5. **Repeat:** Schedule next set of posts

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Routine doesn't run at scheduled time | Check Claude Code routine scheduler settings; verify time zone |
| No topics in calendar | Add items to `calendar.yaml` with `scheduled_date` today or future |
| Engagement metrics empty | Manually update `reports/engagement.json` after posts go live |
| Report shows 0 posts | Ensure execution_log.json has entries; check dates match report range |
