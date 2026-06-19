"""
Lightweight approval server for one-click publishing from email.
Run: python -m skill.approve_server
Then click the approve links in your email to publish posts.
"""

import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv('APPROVE_PORT', '8787'))


class ApproveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == '/approve':
            platform = params.get('platform', [''])[0]
            draft_path = params.get('path', [''])[0]
            day = params.get('day', [''])[0]

            if not platform or not draft_path:
                self._respond(400, 'Missing platform or path parameter.')
                return

            draft_file = Path(draft_path)
            if not draft_file.exists():
                self._respond(404, f'Draft not found: {draft_path}')
                return

            content = draft_file.read_text(encoding='utf-8')
            image_dir = draft_file.parent
            image_path = None
            for img_name in ['infographic.png', 'share_image.png']:
                candidate = image_dir / img_name
                if candidate.exists():
                    image_path = str(candidate)
                    break

            try:
                result = self._publish(platform, content, image_path)
                self._respond(200,
                    f'<h1>Published to {platform}!</h1>'
                    f'<p>Day {day}: {draft_file.parent.name}</p>'
                    f'<p>Result: {result}</p>'
                    f'<p><a href="/dashboard">View Dashboard</a></p>'
                )
            except Exception as e:
                self._respond(500, f'<h1>Publish failed</h1><p>{e}</p>')

        elif parsed.path == '/approve-all':
            batch_dir = params.get('dir', [''])[0]
            platform = params.get('platform', ['all'])[0]

            if not batch_dir:
                self._respond(400, 'Missing dir parameter.')
                return

            results = self._publish_batch(batch_dir, platform)
            results_html = ''.join(f'<li>{r}</li>' for r in results)
            self._respond(200,
                f'<h1>Batch Published!</h1>'
                f'<ul>{results_html}</ul>'
            )

        elif parsed.path == '/dashboard':
            self._respond(200, self._dashboard_html())

        else:
            self._respond(200,
                '<h1>Content Approval Server</h1>'
                '<p>Use the links from your email to approve and publish posts.</p>'
                f'<p><a href="/dashboard">View Dashboard</a></p>'
            )

    def _publish(self, platform, content, image_path=None):
        from skill.orchestrate import _publish_single
        return _publish_single(platform, content, image_path)

    def _publish_batch(self, batch_dir, platform='all'):
        batch_path = Path(batch_dir)
        results = []
        platforms = ['linkedin', 'x', 'threads'] if platform == 'all' else [platform]

        for day_dir in sorted(batch_path.iterdir()):
            if not day_dir.is_dir():
                continue
            for plat in platforms:
                draft = day_dir / f'{plat}_draft.md'
                if draft.exists():
                    content = draft.read_text(encoding='utf-8')
                    image_path = None
                    for img_name in ['infographic.png', 'share_image.png']:
                        candidate = day_dir / img_name
                        if candidate.exists():
                            image_path = str(candidate)
                            break
                    try:
                        self._publish(plat, content, image_path)
                        results.append(f'{day_dir.name} → {plat}: Published')
                    except Exception as e:
                        results.append(f'{day_dir.name} → {plat}: FAILED ({e})')

        return results

    def _dashboard_html(self):
        weekly_dir = ROOT / 'drafts' / 'weekly'
        rows = ''
        if weekly_dir.exists():
            for day_dir in sorted(weekly_dir.iterdir()):
                if not day_dir.is_dir():
                    continue
                for plat in ['linkedin', 'x', 'threads']:
                    draft = day_dir / f'{plat}_draft.md'
                    if draft.exists():
                        link = f'/approve?platform={plat}&path={draft}&day={day_dir.name}'
                        rows += f'<tr><td>{day_dir.name}</td><td>{plat}</td><td><a href="{link}" style="color:#6C63FF;">Publish →</a></td></tr>'

        return f'''
        <html><head><title>Content Approval Dashboard</title></head>
        <body style="font-family:Inter,Arial,sans-serif;max-width:800px;margin:40px auto;padding:20px;">
            <h1>Content Approval Dashboard</h1>
            <table style="width:100%;border-collapse:collapse;">
                <tr style="background:#f3f4f6;"><th style="padding:10px;text-align:left;">Day</th><th>Platform</th><th>Action</th></tr>
                {rows}
            </table>
        </body></html>
        '''

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        html = f'<html><body style="font-family:Inter,Arial,sans-serif;max-width:700px;margin:40px auto;padding:20px;">{body}</body></html>'
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        print(f'[Approve] {args[0]}')


def main():
    print(f'Starting approval server on http://localhost:{PORT}')
    print(f'Open http://localhost:{PORT}/dashboard to see all pending posts.')
    print('Click approve links from your email to publish.')
    server = HTTPServer(('0.0.0.0', PORT), ApproveHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()
