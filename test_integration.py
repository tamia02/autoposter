#!/usr/bin/env python
"""Integration test: research + generate without API keys (template fallback)."""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

# Ensure voice.md exists for template generation
voice_path = REPO_ROOT / 'knowledge' / 'voice.md'
if not voice_path.exists():
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    voice_path.write_text(
        '# Voice Profile\n\n## Summary\n- Tone: informal\n- Average sentence length: 12\n- Uses first-person: True\n',
        encoding='utf-8',
    )


def test_research():
    print('=== Test: Research ===\n')
    from skill.research.fetcher import combine_research, search_web
    results = search_web('AI automation tips', limit=3)
    print(f'Web search returned {len(results)} results')
    for r in results:
        print(f"  - {r.get('title', '')[:60]}: {r.get('snippet', '')[:80]}")

    research_text = combine_research('AI automation for founders')
    print(f'\nCombined research ({len(research_text)} chars):\n{research_text[:300]}...\n')
    return research_text


def test_generate(research_text: str):
    print('=== Test: Generate (Template Fallback) ===\n')
    from skill.research.summarize import research_to_snippet
    from skill.generator.generate import generate_all

    snippet = research_to_snippet(research_text)
    print(f'Snippet: {snippet[:100]}...\n')

    res = generate_all(
        topic='AI automation for founders',
        research=snippet,
        hashtags=['AI', 'automation', 'founder'],
        source_link='',
        out_dir=str(REPO_ROOT / 'drafts'),
    )

    print('Drafts written:')
    for platform, path in res.items():
        with open(path, 'r') as f:
            content = f.read()
        print(f"  {platform}: {path} ({len(content)} chars)")
    print()
    return res


def test_ai_generate():
    print('=== Test: AI Generation ===\n')
    if not os.getenv('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set — skipping AI test.\n')
        return

    from skill.ai.client import generate_post, generate_image_quote

    content = generate_post(
        topic='Why founders should automate before they scale',
        platform='linkedin',
        research='Automation helps founders focus on high-value work instead of repetitive tasks.',
    )
    print(f'AI LinkedIn post ({len(content)} chars):')
    print(content[:300])
    print()

    quote = generate_image_quote('AI automation for founders')
    print(f'Image quote: {quote}\n')


def test_notification():
    print('=== Test: Notification (Config Check) ===\n')
    from skill.notification import _is_configured
    print(f'Email configured: {_is_configured()}\n')


def test_scheduler():
    print('=== Test: Scheduler ===\n')
    from skill.scheduler import get_scheduled_topics, get_next_scheduled_run

    scheduled = get_scheduled_topics(date_range_days=14)
    print(f'Topics scheduled in next 14 days: {len(scheduled)}')
    for item in scheduled:
        print(f"  - {item.get('topic', '')} on {item.get('scheduled_date', '')}")

    next_run = get_next_scheduled_run()
    if next_run:
        print(f"\nNext run: {next_run.get('topic')} on {next_run.get('scheduled_date')}")
    print()


if __name__ == '__main__':
    research = test_research()
    test_generate(research)
    test_ai_generate()
    test_notification()
    test_scheduler()
    print('=== All tests passed ===')
