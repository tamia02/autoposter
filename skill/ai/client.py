import os
from pathlib import Path
from typing import Dict, List, Optional

from skill.ai.prompts import build_system_prompt, build_user_prompt, build_image_prompt

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = 'gpt-4o'


def _get_client():
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError('openai package is required. Run: pip install openai')

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is required for AI generation.')
    return OpenAI(api_key=api_key)


def _load_voice_profile() -> str:
    voice_path = ROOT / 'knowledge' / 'voice.md'
    if voice_path.exists():
        return voice_path.read_text(encoding='utf-8')
    return (
        "Tone: informal and direct. "
        "Speaks from first person. "
        "Short sentences. "
        "Practical, no fluff."
    )


def generate_post(
    topic: str,
    platform: str,
    research: str = '',
    competitor_signals: str = '',
    voice_profile: str = None,
    model: str = None,
) -> str:
    client = _get_client()
    if voice_profile is None:
        voice_profile = _load_voice_profile()

    system = build_system_prompt(platform, voice_profile)
    user_msg = build_user_prompt(topic, research, competitor_signals, platform)

    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        max_tokens=1200,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_msg},
        ],
    )
    return response.choices[0].message.content.strip()


def generate_image_quote(topic: str, platform: str = 'linkedin', model: str = None) -> str:
    client = _get_client()
    prompt = build_image_prompt(topic, platform)

    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        max_tokens=60,
        messages=[
            {'role': 'user', 'content': prompt},
        ],
    )
    return response.choices[0].message.content.strip().strip('"').strip("'")


def generate_post_batch(
    topics: List[Dict],
    research_per_topic: Dict[str, str] = None,
    competitor_signals: str = '',
    voice_profile: str = None,
) -> List[Dict]:
    if voice_profile is None:
        voice_profile = _load_voice_profile()
    if research_per_topic is None:
        research_per_topic = {}

    results = []
    for item in topics:
        topic = item['topic']
        hashtags = item.get('hashtags', [])
        research = research_per_topic.get(topic, '')

        drafts = {}
        for platform in ('linkedin', 'x', 'threads'):
            content = generate_post(
                topic=topic,
                platform=platform,
                research=research,
                competitor_signals=competitor_signals,
                voice_profile=voice_profile,
            )
            drafts[platform] = content

        quote = generate_image_quote(topic)
        results.append({
            'topic': topic,
            'hashtags': hashtags,
            'drafts': drafts,
            'image_quote': quote,
        })

    return results
