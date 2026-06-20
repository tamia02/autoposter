import re
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]


def load_voice_text(path: str = None) -> str:
    if path is None:
        path = ROOT / 'knowledge' / 'voice.md'
    p = Path(path)
    if p.exists():
        return p.read_text(encoding='utf-8')
    return ''


def _ai_available() -> bool:
    import os
    return bool(os.getenv('OPENAI_API_KEY'))


def _clean_markdown(text: str) -> str:
    """Strip markdown formatting for clean LinkedIn/X/Threads paste."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-•]\s+', '→ ', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_ai(
    topic: str,
    platform: str,
    research: str = '',
    competitor_signals: str = '',
    hashtags: List[str] = None,
) -> str:
    from skill.ai.client import generate_post
    content = generate_post(
        topic=topic,
        platform=platform,
        research=research,
        competitor_signals=competitor_signals,
    )
    return _clean_markdown(content)


def extract_competitor_signals(research: str) -> str:
    match = re.search(r'Competitor signals:\s*(.*)', research, flags=re.I | re.S)
    if not match:
        return ''
    lines = []
    for line in match.group(1).splitlines():
        text = line.strip()
        if text.startswith('-'):
            text = text[1:].strip()
        if text:
            lines.append(text)
        if len(lines) >= 4:
            break
    return '\n'.join(lines)


# --- Fallback template generation (no API key needed) ---

def _make_hook(topic: str, research: str = '') -> str:
    if research and 'competitor signals:' in research.lower():
        return f"I checked what others are doing on {topic} — here's what still feels true."
    return f"I started building around {topic} — here's a simple idea."


def _make_body(topic: str, research: str, voice_text: str) -> str:
    research_line = research.strip()[:200]
    lines = [f"Why this matters: {research_line}"]

    comp_sig = extract_competitor_signals(research)
    if comp_sig:
        lines.append(f"I saw a pattern in competitor posts: {comp_sig[:120]}")

    lines.extend([
        "What I try: small experiments every day — build the smallest version that proves the idea.",
        "What I avoid: too much tool complexity before the problem or customer is clear.",
        "If you can write it down, you can automate it.",
    ])

    if 'informal' in voice_text.lower():
        lines.append("I say it like I would to someone building beside me.")

    return '\n\n'.join(lines)


def _make_cta() -> str:
    return "Try this and tell me what you learn."


def _segment_thread(text: str, max_len: int = 270) -> List[str]:
    sents = re.split(r'(?<=[\.\?!])\s+', text)
    parts, cur = [], ''
    for s in sents:
        if len(cur) + len(s) + 1 <= max_len:
            cur = (cur + ' ' + s).strip()
        else:
            if cur:
                parts.append(cur)
            if len(s) <= max_len:
                cur = s
            else:
                for i in range(0, len(s), max_len):
                    parts.append(s[i:i + max_len])
                cur = ''
    if cur:
        parts.append(cur)
    return parts


def generate_template(
    topic: str,
    platform: str,
    research: str = '',
    hashtags: List[str] = None,
    source_link: str = '',
) -> str:
    voice = load_voice_text()
    hook = _make_hook(topic, research)
    body = _make_body(topic, research, voice)
    cta = _make_cta()

    if platform == 'linkedin':
        tags = ' '.join(f'#{h.strip().lstrip("#")}' for h in (hashtags or []))
        return f"{hook}\n\n{body}\n\n{cta}\n\nHashtags: {tags}"

    elif platform == 'x':
        parts = _segment_thread(f"{hook}\n\n{body}")
        thread = '\n\n'.join(f"{i + 1}/ {p}" for i, p in enumerate(parts))
        footer = f"\n\n—\nSource: {source_link}" if source_link else ''
        return thread + footer

    elif platform == 'threads':
        return f"{hook}\n\n{body}\n\n{cta}"

    return f"{hook}\n\n{body}\n\n{cta}"


# --- Main API ---

def generate_for_platform(
    topic: str,
    platform: str,
    research: str = '',
    competitor_signals: str = '',
    hashtags: List[str] = None,
    source_link: str = '',
) -> str:
    if _ai_available():
        try:
            return generate_ai(topic, platform, research, competitor_signals, hashtags)
        except Exception as e:
            print(f'AI generation failed for {platform}, falling back to template: {e}')

    return generate_template(topic, platform, research, hashtags, source_link)


def write_draft(platform: str, content: str, out_dir: str = None) -> str:
    if out_dir is None:
        out_dir = ROOT / 'drafts'
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{platform}_draft.md"
    f.write_text(content, encoding='utf-8')
    return str(f)


def generate_all(
    topic: str,
    research: str = '',
    hashtags: List[str] = None,
    source_link: str = '',
    out_dir: str = None,
    competitor_signals: str = '',
) -> dict:
    competitor_sig = competitor_signals or extract_competitor_signals(research)

    results = {}
    for platform in ('linkedin', 'x', 'threads'):
        content = generate_for_platform(
            topic=topic,
            platform=platform,
            research=research,
            competitor_signals=competitor_sig,
            hashtags=hashtags,
            source_link=source_link,
        )
        path = write_draft(platform, content, out_dir=out_dir)
        results[platform] = path

    return results


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--topic', required=True)
    p.add_argument('--research', default='')
    p.add_argument('--hashtags', default='design,branding')
    p.add_argument('--source', default='')
    args = p.parse_args()

    res = generate_all(
        args.topic,
        args.research,
        hashtags=[h.strip() for h in args.hashtags.split(',')],
        source_link=args.source,
    )
    print('Wrote drafts:', res)
