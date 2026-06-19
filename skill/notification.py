import os
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Optional


def get_email_config():
    smtp_port_text = os.getenv('EMAIL_SMTP_PORT', '').strip()
    smtp_port = int(smtp_port_text) if smtp_port_text.isdigit() else 587
    return {
        'smtp_server': os.getenv('EMAIL_SMTP_SERVER', '').strip(),
        'smtp_port': smtp_port,
        'username': os.getenv('EMAIL_USERNAME', '').strip(),
        'password': os.getenv('EMAIL_PASSWORD', '').strip(),
        'recipients': [r.strip() for r in os.getenv('EMAIL_RECIPIENTS', '').split(',') if r.strip()],
        'use_tls': os.getenv('EMAIL_USE_TLS', 'true').strip().lower() != 'false',
    }


def _is_configured() -> bool:
    config = get_email_config()
    return bool(config['smtp_server'] and config['username'] and config['password'] and config['recipients'])


def _send(subject: str, body: str, html_body: str = None):
    config = get_email_config()
    if not _is_configured():
        raise RuntimeError('Email notification environment variables are incomplete.')

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = config['username']
    message['To'] = ', '.join(config['recipients'])
    message.set_content(body)

    if html_body:
        message.add_alternative(html_body, subtype='html')

    with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=20) as smtp:
        if config['use_tls']:
            smtp.starttls()
        smtp.login(config['username'], config['password'])
        smtp.send_message(message)

    return True


def send_email_notification(subject: str, body: str):
    return _send(subject, body)


def send_weekly_content_ready(
    topics: List[Dict],
    drafts_dir: str = '',
    week_label: str = '',
    approve_port: int = 8787,
):
    """
    Send a 'Your 7-day content is ready' email with:
    - Summary of all topics
    - One-click PUBLISH buttons per platform per day
    - One-click PUBLISH ALL button
    """
    if not _is_configured():
        print('Email not configured — skipping weekly notification.')
        return False

    import os
    approve_port = int(os.getenv('APPROVE_PORT', str(approve_port)))
    base_url = f'http://localhost:{approve_port}'

    subject = f'Your {len(topics)}-day content is ready!'
    if week_label:
        subject += f' ({week_label})'

    text_lines = [
        f'Your {len(topics)}-day content batch is ready for review.\n',
        f'Start the approval server: python -m skill.approve_server\n',
        f'Then open: {base_url}/dashboard\n',
        'Or click the approve links below:\n',
    ]
    html_rows = []

    for i, item in enumerate(topics, 1):
        topic = item.get('topic', 'Untitled')
        drafts = item.get('drafts', {})
        has_visuals = bool(item.get('image_path') or item.get('carousel_paths'))

        text_lines.append(f'Day {i}: {topic}')
        for plat, path in drafts.items():
            text_lines.append(f'  {plat}: {base_url}/approve?platform={plat}&path={path}&day={i}')
        text_lines.append('')

        approve_buttons = ''
        for plat, path in drafts.items():
            link = f'{base_url}/approve?platform={plat}&path={_esc(str(path))}&day={i}'
            color = {'linkedin': '#0A66C2', 'x': '#000000', 'threads': '#000000'}.get(plat, '#6C63FF')
            approve_buttons += (
                f'<a href="{link}" style="display:inline-block;padding:6px 14px;'
                f'background:{color};color:#fff;border-radius:6px;text-decoration:none;'
                f'font-size:13px;margin-right:6px;">{plat.upper()}</a>'
            )

        visuals_badge = (
            '<span style="color:#22C55E;font-size:12px;">Carousel + Infographic</span>'
            if has_visuals else
            '<span style="color:#EAB308;font-size:12px;">Text only</span>'
        )

        html_rows.append(
            f'<tr>'
            f'<td style="padding:12px;border-bottom:1px solid #eee;font-weight:600;">Day {i}</td>'
            f'<td style="padding:12px;border-bottom:1px solid #eee;">{_esc(topic)}<br>{visuals_badge}</td>'
            f'<td style="padding:12px;border-bottom:1px solid #eee;">{approve_buttons}</td>'
            f'</tr>'
        )

    text_lines.append(f'\nPublish ALL: {base_url}/approve-all?dir={drafts_dir}&platform=all')

    text_body = '\n'.join(text_lines)

    publish_all_link = f'{base_url}/approve-all?dir={_esc(drafts_dir)}&platform=all'

    html_body = f'''
    <html>
    <body style="font-family:'Segoe UI',Arial,sans-serif;color:#1f2937;max-width:700px;margin:0 auto;">
      <div style="background:#0A0A0A;padding:40px;border-radius:16px 16px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:28px;">Your {len(topics)}-Day Content is Ready</h1>
        <p style="color:#8B8B8B;margin:10px 0 20px;font-size:16px;">Review and publish with one click.</p>
        <a href="{publish_all_link}" style="display:inline-block;padding:12px 28px;background:#6C63FF;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
          Publish All →
        </a>
      </div>
      <div style="padding:20px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 16px 16px;">
        <p style="color:#6b7280;font-size:13px;margin-bottom:16px;">
          First run: <code>python -m skill.approve_server</code> — then click the buttons below.
        </p>
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#f9fafb;">
              <th style="padding:10px;text-align:left;font-size:13px;color:#6b7280;">Day</th>
              <th style="padding:10px;text-align:left;font-size:13px;color:#6b7280;">Topic</th>
              <th style="padding:10px;text-align:left;font-size:13px;color:#6b7280;">Publish</th>
            </tr>
          </thead>
          <tbody>
            {''.join(html_rows)}
          </tbody>
        </table>
      </div>
    </body>
    </html>
    '''

    return _send(subject, text_body, html_body)


def send_post_published(topic: str, platform: str, post_url: str = ''):
    """Notify that a post was published live."""
    if not _is_configured():
        return False

    subject = f'Published on {platform}: {topic[:50]}'
    body = (
        f'Your content was published live on {platform}.\n\n'
        f'Topic: {topic}\n'
    )
    if post_url:
        body += f'URL: {post_url}\n'

    return _send(subject, body)


def _esc(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


if __name__ == '__main__':
    print('Email configured:', _is_configured())
    print('Config:', get_email_config())
