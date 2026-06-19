import json
import os
from pathlib import Path
from typing import Dict, List

from skill.analytics import EngagementTracker
from skill.scheduler import get_next_scheduled_run, load_calendar

ROOT = Path(__file__).resolve().parents[2]


def _load_execution_log(path: str = None) -> List[Dict]:
    if path is None:
        path = ROOT / 'reports' / 'execution_log.json'
    path = Path(path)
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _render_table(headers: List[str], rows: List[List[str]]) -> str:
    header_html = ''.join(f'<th>{h}</th>' for h in headers)
    body_html = ''.join(
        '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
        for row in rows
    )
    return f'<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>'


def _sanitize(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def generate_dashboard(output_path: str = None) -> str:
    calendar = load_calendar()
    engagement = EngagementTracker()
    platform_summary = engagement.get_platform_summary(days=30)
    top_topics = engagement.get_top_topics(days=30)
    execution_log = _load_execution_log()
    next_run = get_next_scheduled_run()

    if output_path is None:
        output_path = ROOT / 'reports' / 'dashboard.html'
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    calendar_rows = []
    for item in calendar:
        calendar_rows.append([
            str(item.get('id', '')),
            _sanitize(str(item.get('topic', ''))),
            str(item.get('scheduled_date', '')),
            str(item.get('repeat_interval_days', '')),
            str(item.get('status', '')),
        ])

    log_rows = []
    for entry in execution_log[-10:]:
        log_rows.append([
            entry.get('timestamp', ''),
            _sanitize(entry.get('topic', '')),
            entry.get('status', ''),
            _sanitize(json.dumps(entry.get('details', {}), ensure_ascii=False))
        ])

    summary_rows = []
    for platform, stats in platform_summary.items():
        summary_rows.append([
            _sanitize(platform),
            str(stats.get('count', 0)),
            f"{stats.get('avg_engagement', 0):.1f}",
            str(stats.get('total_likes', 0)),
            str(stats.get('total_comments', 0)),
        ])

    top_topic_rows = []
    for topic in top_topics:
        top_topic_rows.append([
            _sanitize(topic.get('topic', '')),
            f"{topic.get('avg_score', 0):.1f}",
            str(topic.get('posts', 0)),
        ])

    next_topic_html = '<p>No upcoming scheduled topics.</p>'
    if next_run:
        next_topic_html = (
            '<p><strong>Next Scheduled:</strong> ' + _sanitize(str(next_run.get('topic', ''))) +
            ' on ' + _sanitize(str(next_run.get('scheduled_date', ''))) + '</p>'
        )

    html = f'''
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Content Automation Dashboard</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f6f7fb; color: #111; }}
        h1,h2,h3 {{ color: #1f2937; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
        th, td {{ border: 1px solid #d1d5db; padding: 10px; text-align: left; }}
        th {{ background: #eef2ff; }}
        tr:nth-child(even) {{ background: #ffffff; }}
        tr:nth-child(odd) {{ background: #f8fafc; }}
        .section {{ margin-bottom: 40px; }}
        .panel {{ background: white; border: 1px solid #d1d5db; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
        .small {{ font-size: 0.95rem; color: #4b5563; }}
      </style>
    </head>
    <body>
      <h1>Content Automation Dashboard</h1>
      <div class="panel">
        <h2>Overview</h2>
        {next_topic_html}
        <p class="small">Generated on {Path(output_path).name}</p>
      </div>

      <div class="section panel">
        <h2>Calendar</h2>
        {_render_table(['ID', 'Topic', 'Scheduled Date', 'Repeat Days', 'Status'], calendar_rows)}
      </div>

      <div class="section panel">
        <h2>Recent Routine Runs</h2>
        {_render_table(['Timestamp', 'Topic', 'Status', 'Details'], log_rows)}
      </div>

      <div class="section panel">
        <h2>Engagement Summary (30 days)</h2>
        {_render_table(['Platform', 'Posts', 'Avg Engagement', 'Likes', 'Comments'], summary_rows)}
      </div>

      <div class="section panel">
        <h2>Top Topics</h2>
        {_render_table(['Topic', 'Avg Score', 'Posts'], top_topic_rows)}
      </div>
    </body>
    </html>
    '''

    output_path.write_text(html, encoding='utf-8')
    return str(output_path)


if __name__ == '__main__':
    print('Dashboard created:', generate_dashboard())
