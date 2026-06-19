import json
import os
from pathlib import Path
from typing import List, Dict
from skill.renderer.styles import build_carousel_html, build_single_infographic_html, build_card_html


def render_html_to_image(html: str, out_path: str, width: int = 1080, height: int = 1350):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise RuntimeError('Playwright is required. Run: pip install playwright && python -m playwright install') from e

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})
        page.set_content(html)
        page.screenshot(path=out_path, type='png', full_page=False)
        browser.close()


def _generate_slide_content(topic: str, post_content: str) -> List[Dict]:
    """Use AI to break a post into carousel slide content."""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model='gpt-4o',
            max_tokens=800,
            messages=[
                {'role': 'system', 'content': (
                    'You convert LinkedIn posts into carousel slide content. '
                    'Output valid JSON only. No markdown. No explanation.\n'
                    'Format: [{"type":"hook","title":"...","body":"..."},'
                    '{"type":"point","title":"...","body":"...","number":1},...,'
                    '{"type":"cta","title":"...","body":"..."}]\n'
                    'Rules:\n'
                    '- First slide: type "hook" with a bold 6-10 word title and short subtitle\n'
                    '- Middle slides: type "point" with numbered tips (title: 5-8 words, body: 15-25 words)\n'
                    '- Last slide: type "cta" with engagement prompt\n'
                    '- 6-8 slides total\n'
                    '- Each slide title must be punchy and standalone\n'
                    '- Keep body text under 25 words per slide'
                )},
                {'role': 'user', 'content': f'Topic: {topic}\n\nPost content:\n{post_content[:1500]}'},
            ],
        )
        text = response.choices[0].message.content.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        return json.loads(text)
    except Exception as e:
        print(f'  AI slide generation failed, using fallback: {e}')
        return _fallback_slides(topic, post_content)


def _fallback_slides(topic: str, post_content: str) -> List[Dict]:
    """Extract slides from post content without AI."""
    import re
    lines = [l.strip() for l in post_content.split('\n') if l.strip()]

    slides = [{'type': 'hook', 'title': topic, 'body': lines[0] if lines else 'Swipe to learn more →'}]

    points = []
    for line in lines:
        cleaned = re.sub(r'^→\s*\**|\**$|^\d+[\.\)]\s*', '', line).strip()
        if len(cleaned) > 20 and len(cleaned) < 200 and cleaned != lines[0]:
            parts = cleaned.split(':', 1) if ':' in cleaned else (cleaned, '')
            points.append({
                'type': 'point',
                'title': parts[0].strip()[:60],
                'body': parts[1].strip()[:100] if len(parts) > 1 and parts[1].strip() else '',
                'number': len(points) + 1,
            })
        if len(points) >= 5:
            break

    slides.extend(points)
    slides.append({'type': 'cta', 'title': 'Found this useful?', 'body': 'Save this post and share with your network.'})
    return slides


def render_carousel(
    topic: str,
    post_content: str,
    out_dir: str,
    style_index: int = 0,
    author_name: str = '',
) -> List[str]:
    """Render a full carousel (multiple slides) as individual PNGs."""
    slides_data = _generate_slide_content(topic, post_content)
    html_slides = build_carousel_html(
        slides=slides_data,
        style_index=style_index,
        author_name=author_name,
    )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for i, html in enumerate(html_slides):
        out_path = out_dir / f'slide_{i + 1:02d}.png'
        render_html_to_image(html, str(out_path), width=1080, height=1350)
        paths.append(str(out_path))

    return paths


def render_infographic(
    topic: str,
    post_content: str,
    out_path: str,
    style_index: int = 0,
    author_name: str = '',
) -> str:
    """Render a single infographic image with all points."""
    slides_data = _generate_slide_content(topic, post_content)
    points = [s for s in slides_data if s.get('type') == 'point']

    html = build_single_infographic_html(
        topic=topic,
        points=points,
        style_index=style_index,
        author_name=author_name,
    )
    render_html_to_image(html, out_path, width=1080, height=1350)
    return out_path


def render_card(
    quote: str,
    topic: str,
    out_path: str,
    style_index: int = 0,
    width: int = 1200,
    height: int = 630,
    author_name: str = '',
):
    html = build_card_html(
        quote=quote, topic=topic, style_index=style_index,
        width=width, height=height, author_name=author_name,
    )
    render_html_to_image(html, out_path, width=width, height=height)
    return out_path


def render_batch(items: list, out_dir: str, author_name: str = '') -> list:
    """Render carousel + infographic for each item."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, item in enumerate(items):
        topic = item.get('topic', f'Topic {i + 1}')
        post_content = item.get('post_content', '')
        safe_name = _safe_filename(topic)
        item_dir = out_dir / safe_name

        try:
            carousel_paths = render_carousel(
                topic=topic, post_content=post_content,
                out_dir=str(item_dir / 'carousel'),
                style_index=i, author_name=author_name,
            )
            infographic_path = render_infographic(
                topic=topic, post_content=post_content,
                out_path=str(item_dir / 'infographic.png'),
                style_index=i, author_name=author_name,
            )
            paths.append({
                'carousel': carousel_paths,
                'infographic': infographic_path,
            })
        except Exception as e:
            print(f'Image render failed for "{topic}": {e}')
            paths.append(None)

    return paths


def _safe_filename(text: str) -> str:
    safe = text.lower()
    safe = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in safe)
    return safe.replace(' ', '_')[:60]
