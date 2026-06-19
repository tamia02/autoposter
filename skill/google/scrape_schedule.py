import os
from typing import List, Dict
from skill.google.connectors import read_sheet_rows


def load_sheet_schedule(sheet_id: str, range_name: str = 'Sheet1!A1:Z100') -> List[Dict]:
    rows = read_sheet_rows(sheet_id, range_name)
    schedule = []
    for i, row in enumerate(rows):
        item = {
            'id': int(row.get('id', i + 1)) if row.get('id') else (i + 1),
            'topic': row.get('topic', row.get('Topic', '')).strip(),
            'scheduled_date': row.get('scheduled_date', row.get('Scheduled Date', '')).strip(),
            'status': row.get('status', row.get('Status', 'draft')).strip() or 'draft',
            'linkedin': row.get('linkedin', row.get('LinkedIn', '')).strip(),
            'twitter': row.get('twitter', row.get('Twitter', '')).strip(),
            'threads': row.get('threads', row.get('Threads', '')).strip(),
            'doc_id': row.get('doc_id', row.get('Doc ID', row.get('google_doc_id', ''))).strip(),
        }
        schedule.append(item)
    return schedule
