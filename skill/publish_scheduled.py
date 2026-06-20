"""
Publish posts that are scheduled for today.
Run daily by cloud routine or manually: python -m skill.publish_scheduled
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def get_todays_posts():
    schedule_file = ROOT / 'drafts' / 'schedule.json'
    if not schedule_file.exists():
        return []

    schedule = json.loads(schedule_file.read_text(encoding='utf-8'))
    today = datetime.now()
    today_str = today.strftime('%b %d').replace(' 0', ' ')  # "Jun 19" not "Jun 09"

    todays = [s for s in schedule if s.get('status') == 'scheduled' and s.get('date') == today_str]
    return todays


def publish_post(item):
    from skill.orchestrate import _publish_single

    fp = Path(item['file_path'])
    if not fp.exists():
        return {'error': f'File not found: {item["file_path"]}'}

    content = fp.read_text(encoding='utf-8')
    img = item.get('image_path', '')
    img = img if img and Path(img).exists() else None

    result = _publish_single(item['platform'], content, img)
    return {'success': True, 'result': str(result)}


def run():
    posts = get_todays_posts()
    if not posts:
        print('No posts scheduled for today.')
        return

    print(f'Found {len(posts)} posts scheduled for today.')

    schedule_file = ROOT / 'drafts' / 'schedule.json'
    schedule = json.loads(schedule_file.read_text(encoding='utf-8'))

    for item in posts:
        platform = item['platform']
        folder = item.get('folder', '')
        print(f'Publishing to {platform}: {folder}...')

        try:
            result = publish_post(item)
            print(f'  Result: {result}')
            for s in schedule:
                if s.get('file_path') == item['file_path'] and s.get('platform') == platform:
                    s['status'] = 'published'
                    s['published_at'] = datetime.now().isoformat()
        except Exception as e:
            print(f'  Failed: {e}')
            for s in schedule:
                if s.get('file_path') == item['file_path'] and s.get('platform') == platform:
                    s['status'] = 'failed'
                    s['error'] = str(e)

    schedule_file.write_text(json.dumps(schedule, indent=2), encoding='utf-8')
    print('Schedule updated.')


if __name__ == '__main__':
    run()
