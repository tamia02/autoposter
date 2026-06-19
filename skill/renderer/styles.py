"""
Infographic-style carousel and visual templates.
Inspired by Nick Broekema, Daniel Korenblum, Jasmin Alic carousel designs.
"""

BRAND_COLORS = [
    {'bg': '#0A0A0A', 'accent': '#6C63FF', 'text': '#FFFFFF', 'muted': '#8B8B8B'},
    {'bg': '#0D1117', 'accent': '#58A6FF', 'text': '#F0F6FC', 'muted': '#8B949E'},
    {'bg': '#1A1A2E', 'accent': '#E94560', 'text': '#FFFFFF', 'muted': '#A0A0B0'},
    {'bg': '#FFFFFF', 'accent': '#6C63FF', 'text': '#1A1A1A', 'muted': '#6B7280'},
    {'bg': '#FFF8F0', 'accent': '#FF6B35', 'text': '#1A1A1A', 'muted': '#6B7280'},
    {'bg': '#F0FFF4', 'accent': '#22C55E', 'text': '#1A1A1A', 'muted': '#6B7280'},
    {'bg': '#0F172A', 'accent': '#FACC15', 'text': '#F8FAFC', 'muted': '#94A3B8'},
]


def _esc(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build_carousel_html(
    slides: list,
    style_index: int = 0,
    width: int = 1080,
    height: int = 1350,
    author_name: str = '',
) -> list:
    """
    Generate HTML for each carousel slide.
    Each slide dict: {type: 'hook'|'point'|'cta', title: str, body: str, number: int}
    Returns list of HTML strings, one per slide.
    """
    colors = BRAND_COLORS[style_index % len(BRAND_COLORS)]
    bg = colors['bg']
    accent = colors['accent']
    text = colors['text']
    muted = colors['muted']

    html_slides = []
    total = len(slides)

    for i, slide in enumerate(slides):
        slide_type = slide.get('type', 'point')
        title = _esc(slide.get('title', ''))
        body = _esc(slide.get('body', ''))
        number = slide.get('number', i + 1)

        progress_dots = ''.join(
            f'<span style="width:{"24px" if j == i else "8px"};height:8px;'
            f'border-radius:4px;background:{"" + accent if j == i else muted};'
            f'display:inline-block;margin:0 3px;transition:all 0.3s;"></span>'
            for j in range(total)
        )

        if slide_type == 'hook':
            content_html = f'''
                <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 80px;">
                    <div style="width:60px;height:4px;background:{accent};margin-bottom:40px;border-radius:2px;"></div>
                    <h1 style="font-size:64px;line-height:1.15;margin:0 0 30px 0;font-weight:800;color:{text};">
                        {title}
                    </h1>
                    <p style="font-size:28px;line-height:1.5;color:{muted};margin:0;">
                        {body}
                    </p>
                </div>
            '''
        elif slide_type == 'cta':
            author_html = f'<p style="font-size:24px;color:{muted};margin:20px 0 0;">— {_esc(author_name)}</p>' if author_name else ''
            content_html = f'''
                <div style="flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 80px;text-align:center;">
                    <div style="width:80px;height:80px;border-radius:50%;background:{accent};display:flex;align-items:center;justify-content:center;margin-bottom:40px;">
                        <span style="font-size:40px;color:{bg};">→</span>
                    </div>
                    <h2 style="font-size:52px;line-height:1.2;margin:0 0 20px;font-weight:700;color:{text};">
                        {title}
                    </h2>
                    <p style="font-size:28px;line-height:1.5;color:{muted};margin:0;">
                        {body}
                    </p>
                    {author_html}
                </div>
            '''
        else:
            content_html = f'''
                <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 80px;">
                    <div style="display:flex;align-items:center;margin-bottom:30px;">
                        <div style="width:64px;height:64px;border-radius:16px;background:{accent};display:flex;align-items:center;justify-content:center;margin-right:20px;flex-shrink:0;">
                            <span style="font-size:32px;font-weight:800;color:{bg};">{number}</span>
                        </div>
                        <h2 style="font-size:44px;line-height:1.2;margin:0;font-weight:700;color:{text};">
                            {title}
                        </h2>
                    </div>
                    <p style="font-size:30px;line-height:1.6;color:{muted};margin:0;padding-left:84px;">
                        {body}
                    </p>
                </div>
            '''

        html = f'''<!doctype html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;">
<div style="
    width:{width}px;height:{height}px;background:{bg};
    display:flex;flex-direction:column;
    font-family:'Segoe UI','Inter',Arial,sans-serif;
    box-sizing:border-box;
    position:relative;
">
    {content_html}
    <div style="padding:30px 80px 40px;text-align:center;">
        {progress_dots}
    </div>
</div>
</body></html>'''
        html_slides.append(html)

    return html_slides


def build_single_infographic_html(
    topic: str,
    points: list,
    style_index: int = 0,
    width: int = 1080,
    height: int = 1350,
    author_name: str = '',
) -> str:
    """
    Single-image infographic with all points visible.
    points: list of {title: str, body: str}
    """
    colors = BRAND_COLORS[style_index % len(BRAND_COLORS)]
    bg = colors['bg']
    accent = colors['accent']
    text = colors['text']
    muted = colors['muted']

    points_html = ''
    for i, p in enumerate(points):
        points_html += f'''
        <div style="display:flex;align-items:flex-start;margin-bottom:28px;">
            <div style="width:48px;height:48px;border-radius:12px;background:{accent};display:flex;align-items:center;justify-content:center;margin-right:20px;flex-shrink:0;">
                <span style="font-size:24px;font-weight:800;color:{bg};">{i+1}</span>
            </div>
            <div>
                <p style="font-size:28px;font-weight:700;color:{text};margin:0 0 6px;">{_esc(p.get("title",""))}</p>
                <p style="font-size:22px;color:{muted};margin:0;line-height:1.4;">{_esc(p.get("body",""))}</p>
            </div>
        </div>'''

    author_html = f'<p style="font-size:20px;color:{muted};margin:0;">— {_esc(author_name)}</p>' if author_name else ''

    return f'''<!doctype html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;">
<div style="
    width:{width}px;height:{height}px;background:{bg};
    display:flex;flex-direction:column;
    font-family:'Segoe UI','Inter',Arial,sans-serif;
    box-sizing:border-box;padding:60px 70px;
">
    <div style="width:50px;height:4px;background:{accent};margin-bottom:30px;border-radius:2px;"></div>
    <h1 style="font-size:48px;line-height:1.15;margin:0 0 40px;font-weight:800;color:{text};">
        {_esc(topic)}
    </h1>
    <div style="flex:1;">
        {points_html}
    </div>
    <div style="border-top:1px solid {muted}33;padding-top:20px;display:flex;justify-content:space-between;align-items:center;">
        {author_html}
        <p style="font-size:18px;color:{muted};margin:0;">Save this ♻️</p>
    </div>
</div>
</body></html>'''


def build_card_html(
    quote: str,
    topic: str,
    style_index: int = 0,
    width: int = 1200,
    height: int = 630,
    author_name: str = '',
) -> str:
    """Legacy simple card for X/Threads share images."""
    colors = BRAND_COLORS[style_index % len(BRAND_COLORS)]
    bg = colors['bg']
    accent = colors['accent']
    text = colors['text']
    muted = colors['muted']

    author_html = f'<p style="font-size:20px;margin-top:30px;color:{muted};">— {_esc(author_name)}</p>' if author_name else ''

    return f'''<!doctype html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;">
<div style="
    width:{width}px;height:{height}px;background:{bg};
    display:flex;flex-direction:column;justify-content:center;align-items:center;
    padding:60px;box-sizing:border-box;
    font-family:'Segoe UI','Inter',Arial,sans-serif;color:{text};text-align:center;
">
    <div style="width:50px;height:4px;background:{accent};margin-bottom:30px;border-radius:2px;"></div>
    <h1 style="font-size:48px;line-height:1.2;margin:0;font-weight:700;max-width:900px;">
        {_esc(quote)}
    </h1>
    {author_html}
</div>
</body></html>'''
