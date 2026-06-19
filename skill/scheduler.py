"""
Scheduling module: APScheduler for local testing, plus Claude Code routine integration guide.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent


def load_calendar(path: str = None) -> List[Dict]:
    """Load calendar items from YAML."""
    # If a Google Sheet ID is provided, prefer reading schedule from the sheet
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    sheet_range = os.getenv('GOOGLE_SHEET_RANGE', 'Sheet1!A1:Z100')
    if sheet_id:
        try:
            from skill.google.connectors import read_sheet_rows
            rows = read_sheet_rows(sheet_id, sheet_range)
            # Normalize rows to calendar-style dicts
            calendar = []
            for i, r in enumerate(rows):
                item = {}
                item['id'] = int(r.get('id', i + 1)) if r.get('id') else (i + 1)
                item['topic'] = r.get('topic', r.get('Topic', '')).strip()
                item['scheduled_date'] = r.get('scheduled_date', r.get('Scheduled Date', '')).strip()
                item['status'] = r.get('status', r.get('Status', '')) or ''
                item['linkedin'] = r.get('linkedin', r.get('LinkedIn', ''))
                item['twitter'] = r.get('twitter', r.get('Twitter', ''))
                item['threads'] = r.get('threads', r.get('Threads', ''))
                item['doc_id'] = r.get('doc_id', r.get('Doc ID', r.get('google_doc_id', '')))
                calendar.append(item)
            return calendar
        except Exception as e:
            print(f'⚠ Failed to read calendar from Google Sheet: {e} — falling back to calendar.yaml')

    if path is None:
        path = ROOT / 'calendar.yaml'
    if not Path(path).exists():
        return []
    import yaml
    return yaml.safe_load(Path(path).read_text()) or []


def update_calendar_item(item_id: int, status: str, path: str = None):
    """Update a calendar item's status."""
    if path is None:
        path = ROOT / 'calendar.yaml'
    
    import yaml
    calendar = yaml.safe_load(Path(path).read_text()) or []
    for item in calendar:
        if item.get('id') == item_id:
            item['status'] = status
            break
    
    with open(path, 'w') as f:
        yaml.dump(calendar, f)


def advance_calendar_item_schedule(item: Dict, path: str = None):
    """Advance schedule for a topic if repeat interval is configured."""
    if path is None:
        path = ROOT / 'calendar.yaml'
    import yaml

    if not item:
        return

    repeat_days = item.get('repeat_interval_days')
    if repeat_days is None:
        # no repeat defined -> mark as published
        update_calendar_item(item.get('id'), 'published', path=path)
        return

    try:
        repeat_days = int(repeat_days)
    except (ValueError, TypeError):
        update_calendar_item(item.get('id'), 'published', path=path)
        return

    calendar = yaml.safe_load(Path(path).read_text()) or []
    for entry in calendar:
        if entry.get('id') == item.get('id'):
            try:
                current_date = datetime.strptime(entry.get('scheduled_date', ''), '%Y-%m-%d').date()
                next_date = current_date + timedelta(days=repeat_days)
                entry['scheduled_date'] = next_date.strftime('%Y-%m-%d')
                entry['status'] = 'scheduled'
            except Exception:
                entry['status'] = 'published'
            break

    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(calendar, f)


def get_scheduled_topics(date_range_days: int = 7) -> List[Dict]:
    """Get topics scheduled within the next N days."""
    calendar = load_calendar()
    today = datetime.now().date()
    end_date = today + timedelta(days=date_range_days)
    
    scheduled = []
    for item in calendar:
        if item.get('status') not in ['published', 'archived']:
            try:
                raw = item.get('scheduled_date', '')
                if hasattr(raw, 'year'):
                    sched_date = raw
                else:
                    sched_date = datetime.strptime(str(raw), '%Y-%m-%d').date()
                if today <= sched_date <= end_date:
                    scheduled.append(item)
            except Exception:
                pass

    return sorted(scheduled, key=lambda x: str(x.get('scheduled_date', '')))


def log_execution(topic: str, status: str, details: Dict = None, log_path: str = None):
    """Log a routine execution."""
    if log_path is None:
        log_path = ROOT / 'reports' / 'execution_log.json'
    
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'topic': topic,
        'status': status,
        'details': details or {}
    }
    
    logs = []
    if log_path.exists():
        with open(log_path) as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)


class RoutineScheduler:
    """
    Simple scheduler for Claude Code routine integration.
    Claude Code handles the actual scheduling; this manages the loop.
    """
    
    def __init__(self, max_runs: int = 1):
        self.max_runs = max_runs
        self.run_count = 0
    
    def should_run_topic(self, topic: Dict) -> bool:
        """Check if a topic should run today."""
        raw = topic.get('scheduled_date', '')
        if not raw:
            return False

        try:
            if hasattr(raw, 'year'):
                sched = raw
            else:
                sched = datetime.strptime(str(raw), '%Y-%m-%d').date()
            return sched == datetime.now().date()
        except Exception:
            return False
    
    def run_if_scheduled(self) -> List[Dict]:
        """Check calendar and run for any topics scheduled today."""
        scheduled = get_scheduled_topics(date_range_days=1)
        results = []
        
        for topic_item in scheduled:
            if self.run_count >= self.max_runs:
                break
            
            if self.should_run_topic(topic_item):
                result = {
                    'id': topic_item.get('id'),
                    'topic': topic_item.get('topic'),
                    'status': 'ready',
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
                log_execution(topic_item.get('topic'), 'scheduled', result)
                self.run_count += 1
        
        return results


def get_next_scheduled_run() -> Dict:
    """Get the next scheduled topic."""
    scheduled = get_scheduled_topics()
    if scheduled:
        return scheduled[0]
    return {}
