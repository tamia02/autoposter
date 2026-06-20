"""
Auto-Poster Dashboard — Full web app for managing content.
Run: python -m app.server
Open: http://localhost:5000
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

APP_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(APP_DIR / 'templates'), static_folder=str(APP_DIR / 'static'))
app.secret_key = 'autoposter-dashboard-key'

CONTENT_DIR = ROOT / 'drafts' / 'content'
WEEKLY_DIR = ROOT / 'drafts' / 'weekly'
REPORTS_DIR = ROOT / 'reports'


def _get_days():
    """Get all content days sorted."""
    days = []
    content_dir = CONTENT_DIR if CONTENT_DIR.exists() else WEEKLY_DIR
    if not content_dir.exists():
        return days
    for d in sorted(content_dir.iterdir()):
        if not d.is_dir():
            continue
        drafts = {}
        for plat_file, plat in [('LinkedIn.md', 'linkedin'), ('linkedin_draft.md', 'linkedin'),
                                 ('X Thread.md', 'x'), ('x_draft.md', 'x'),
                                 ('Threads.md', 'threads'), ('threads_draft.md', 'threads')]:
            f = d / plat_file
            if f.exists():
                drafts[plat] = {'path': str(f), 'content': f.read_text(encoding='utf-8')}

        has_infographic = (d / 'Infographic.png').exists() or (d / 'infographic.png').exists()
        infographic_name = 'Infographic.png' if (d / 'Infographic.png').exists() else 'infographic.png'

        carousel_dir = d / 'Carousel Slides' if (d / 'Carousel Slides').exists() else d / 'carousel'
        carousel_count = len(list(carousel_dir.iterdir())) if carousel_dir.exists() else 0

        days.append({
            'name': d.name,
            'folder': str(d),
            'drafts': drafts,
            'has_infographic': has_infographic,
            'infographic_name': infographic_name,
            'carousel_count': carousel_count,
            'carousel_dir': str(carousel_dir) if carousel_dir.exists() else None,
        })
    return days


def _get_calendar():
    """Load calendar.yaml."""
    import yaml
    cal_path = ROOT / 'calendar.yaml'
    if cal_path.exists():
        return yaml.safe_load(cal_path.read_text()) or []
    return []


def _get_analytics():
    """Load engagement data."""
    try:
        from skill.analytics import EngagementTracker
        tracker = EngagementTracker()
        return {
            'summary': tracker.get_platform_summary(days=30),
            'top_topics': tracker.get_top_topics(days=30),
            'report': tracker.generate_report(days=30),
        }
    except Exception:
        return {'summary': {}, 'top_topics': [], 'report': 'No data yet.'}


def _publish(platform, content, image_path=None):
    """Publish to a platform."""
    from skill.orchestrate import _publish_single
    return _publish_single(platform, content, image_path)


# ── Routes ──

@app.route('/')
def dashboard():
    days = _get_days()
    calendar = _get_calendar()
    today = datetime.now().strftime('%Y-%m-%d')

    scheduled_today = [c for c in calendar if str(c.get('scheduled_date', '')) == today]
    total_drafts = sum(len(d['drafts']) for d in days)

    return render_template('dashboard.html',
        days=days,
        total_days=len(days),
        total_drafts=total_drafts,
        scheduled_today=scheduled_today,
        calendar=calendar[:7],
    )


@app.route('/drafts')
def drafts():
    days = _get_days()
    return render_template('drafts.html', days=days)


@app.route('/draft/<path:folder_name>')
def draft_detail(folder_name):
    days = _get_days()
    day = next((d for d in days if d['name'] == folder_name), None)
    if not day:
        return redirect(url_for('drafts'))
    return render_template('draft_detail.html', day=day)


@app.route('/edit/<path:file_path>', methods=['GET', 'POST'])
def edit_draft(file_path):
    full_path = Path(file_path.replace('/', os.sep))
    if not full_path.exists():
        return "File not found", 404

    if request.method == 'POST':
        content = request.form.get('content', '')
        full_path.write_text(content, encoding='utf-8')
        return redirect(request.referrer or url_for('drafts'))

    content = full_path.read_text(encoding='utf-8')
    return render_template('edit.html', path=str(full_path), content=content, filename=full_path.name)


@app.route('/publish', methods=['POST'])
def publish_post():
    try:
        platform = request.form.get('platform', '')
        file_path = request.form.get('file_path', '')
        image_path = request.form.get('image_path', '')

        if not platform or not file_path:
            return jsonify({'error': 'Missing platform or file_path'}), 400

        fp = Path(file_path.replace('/', os.sep))
        if not fp.exists():
            return jsonify({'error': f'File not found: {file_path}'}), 404

        content = fp.read_text(encoding='utf-8')
        img = image_path if image_path and Path(image_path).exists() else None

        result = _publish(platform, content, img)
        return jsonify({'success': True, 'result': str(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/schedule-post', methods=['POST'])
def schedule_post():
    """Schedule a post for its assigned date (from folder name)."""
    try:
        platform = request.form.get('platform', '')
        file_path = request.form.get('file_path', '')
        image_path = request.form.get('image_path', '')

        if not platform or not file_path:
            return jsonify({'error': 'Missing platform or file_path'}), 400

        fp = Path(file_path.replace('/', os.sep))
        if not fp.exists():
            return jsonify({'error': f'File not found: {file_path}'}), 404

        # Extract date from folder name (e.g. "Day 1 - Jun 19 - ...")
        import re
        folder_name = fp.parent.name
        date_match = re.search(r'(Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May)\s+(\d+)', folder_name)
        scheduled_date = folder_name
        if date_match:
            scheduled_date = f'{date_match.group(1)} {date_match.group(2)}'

        # Save to schedule file
        schedule_file = ROOT / 'drafts' / 'schedule.json'
        schedule = []
        if schedule_file.exists():
            schedule = json.loads(schedule_file.read_text(encoding='utf-8'))

        img_path = image_path.replace('/', os.sep) if image_path else ''
        schedule.append({
            'platform': platform,
            'file_path': str(fp),
            'image_path': img_path if img_path and Path(img_path).exists() else '',
            'date': scheduled_date,
            'folder': folder_name,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
        })

        schedule_file.write_text(json.dumps(schedule, indent=2), encoding='utf-8')
        return jsonify({'success': True, 'date': scheduled_date})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/schedule-all/<path:folder_name>', methods=['POST'])
def schedule_all(folder_name):
    """Schedule all platforms for a day."""
    try:
        days = _get_days()
        day = next((d for d in days if d['name'] == folder_name), None)
        if not day:
            return jsonify({'error': 'Day not found', 'success': False}), 404

        import re
        date_match = re.search(r'(Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May)\s+(\d+)', folder_name)
        scheduled_date = folder_name
        if date_match:
            scheduled_date = f'{date_match.group(1)} {date_match.group(2)}'

        schedule_file = ROOT / 'drafts' / 'schedule.json'
        schedule = []
        if schedule_file.exists():
            schedule = json.loads(schedule_file.read_text(encoding='utf-8'))

        folder = Path(day['folder'])
        img_path = ''
        for img_name in [day.get('infographic_name', ''), 'Infographic.png', 'infographic.png']:
            candidate = folder / img_name
            if candidate.exists():
                img_path = str(candidate)
                break

        for plat, info in day['drafts'].items():
            schedule.append({
                'platform': plat,
                'file_path': info['path'],
                'image_path': img_path,
                'date': scheduled_date,
                'folder': folder_name,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
            })

        schedule_file.write_text(json.dumps(schedule, indent=2), encoding='utf-8')
        return jsonify({'success': True, 'date': scheduled_date})

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/publish-all/<path:folder_name>', methods=['POST'])
def publish_all(folder_name):
    try:
        days = _get_days()
        day = next((d for d in days if d['name'] == folder_name), None)
        if not day:
            return jsonify({'error': 'Day not found'}), 404

        results = {}
        folder = Path(day['folder'])
        img_path = str(folder / day['infographic_name']) if day['has_infographic'] else None

        for plat, info in day['drafts'].items():
            try:
                result = _publish(plat, info['content'], img_path)
                results[plat] = {'success': True, 'result': str(result)}
            except Exception as e:
                results[plat] = {'success': False, 'error': str(e)}

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/calendar')
def calendar_view():
    calendar = _get_calendar()
    return render_template('calendar.html', calendar=calendar)


@app.route('/analytics')
def analytics():
    data = _get_analytics()
    return render_template('analytics.html', data=data)


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        mode = request.form.get('mode', 'weekly')
        competitors = request.form.get('competitors', '')
        topic = request.form.get('topic', '')

        import subprocess
        cmd = [str(ROOT / '.venv' / 'Scripts' / 'python.exe'), '-X', 'utf8', '-m', 'skill.orchestrate']

        if mode == 'weekly':
            cmd.append('--weekly')
        else:
            cmd.extend(['--topic', topic])

        cmd.append('--no-pr')
        if competitors:
            cmd.extend(['--competitors', competitors])

        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return render_template('generate.html', output=result.stdout + result.stderr, done=True)

    return render_template('generate.html', output=None, done=False)


@app.route('/image/<path:img_path>')
def serve_image(img_path):
    full = Path(img_path.replace('/', os.sep))
    if full.exists():
        return send_file(str(full), mimetype='image/png')
    return "Not found", 404


@app.route('/download/infographic/<path:folder_path>')
def download_infographic(folder_path):
    """Download infographic as JPG."""
    folder = Path(folder_path.replace('/', os.sep))
    for name in ['Infographic.png', 'infographic.png']:
        png_path = folder / name
        if png_path.exists():
            try:
                from PIL import Image
                jpg_path = folder / 'infographic_download.jpg'
                img = Image.open(png_path).convert('RGB')
                img.save(str(jpg_path), 'JPEG', quality=95)
                return send_file(str(jpg_path), as_attachment=True,
                    download_name=f'{folder.name} - Infographic.jpg', mimetype='image/jpeg')
            except ImportError:
                return send_file(str(png_path), as_attachment=True,
                    download_name=f'{folder.name} - Infographic.png', mimetype='image/png')
    return "Infographic not found", 404


@app.route('/download/carousel/<path:folder_path>')
def download_carousel(folder_path):
    """Download carousel slides as a single PDF."""
    folder = Path(folder_path.replace('/', os.sep))
    carousel_dir = folder / 'Carousel Slides' if (folder / 'Carousel Slides').exists() else folder / 'carousel'

    if not carousel_dir.exists():
        return "Carousel not found", 404

    slides = sorted(carousel_dir.glob('slide_*.png'))
    if not slides:
        return "No slides found", 404

    try:
        from PIL import Image
        images = []
        for slide_path in slides:
            img = Image.open(slide_path).convert('RGB')
            images.append(img)

        pdf_path = folder / 'carousel_download.pdf'
        images[0].save(str(pdf_path), 'PDF', save_all=True, append_images=images[1:], resolution=150)

        return send_file(str(pdf_path), as_attachment=True,
            download_name=f'{folder.name} - Carousel.pdf', mimetype='application/pdf')
    except ImportError:
        return "Pillow is required for PDF export. Run: pip install Pillow", 500


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    env_path = ROOT / '.env'
    if request.method == 'POST':
        for key in ['OPENAI_API_KEY', 'LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_AUTHOR_URN',
                     'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET',
                     'THREADS_ACCESS_TOKEN', 'THREADS_USER_ID',
                     'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENTS', 'PUBLISH_MODE']:
            val = request.form.get(key)
            if val is not None:
                os.environ[key] = val
        return redirect(url_for('settings'))

    config = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', '')[:10] + '...' if os.getenv('OPENAI_API_KEY') else '',
        'LINKEDIN_ACCESS_TOKEN': 'Connected' if os.getenv('LINKEDIN_ACCESS_TOKEN', '').startswith('AQ') else 'Not set',
        'X_ACCESS_TOKEN': 'Connected' if os.getenv('X_ACCESS_TOKEN') else 'Not set',
        'THREADS_ACCESS_TOKEN': 'Connected' if os.getenv('THREADS_ACCESS_TOKEN') else 'Not set',
        'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME', ''),
        'EMAIL_RECIPIENTS': os.getenv('EMAIL_RECIPIENTS', ''),
        'PUBLISH_MODE': os.getenv('PUBLISH_MODE', 'pr-only'),
    }
    return render_template('settings.html', config=config)


if __name__ == '__main__':
    print(f'\n  Auto-Poster Dashboard')
    print(f'  Open: http://localhost:8787\n')
    app.run(host='0.0.0.0', port=8787, debug=True)
