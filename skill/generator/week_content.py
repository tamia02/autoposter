from pathlib import Path
from typing import List, Dict, Optional

from skill.generator.generate import generate_for_platform, write_draft
from skill.research.fetcher import combine_research
from skill.research.summarize import research_to_snippet

ROOT = Path(__file__).resolve().parents[2]


def sanitize_filename(text: str) -> str:
    safe = text.lower()
    safe = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in safe)
    return safe.replace(' ', '_')[:80]


def generate_week(
    topics: List[Dict] = None,
    out_dir: str = None,
    competitor_names: List[str] = None,
    competitor_urls: List[str] = None,
    render_images: bool = True,
    author_name: str = '',
) -> List[Dict]:
    """
    Generate a full week of content:
    1. Research each topic individually
    2. Generate AI-powered drafts for all 3 platforms
    3. Render a unique image per topic
    4. Return structured results for email notification
    """
    if topics is None:
        topics = _default_topics()
    if out_dir is None:
        out_dir = str(ROOT / 'drafts' / 'weekly')

    results = []
    base_dir = Path(out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    competitor_signals_text = ''
    if competitor_names or competitor_urls:
        from skill.research.fetcher import fetch_competitor_content
        comp_data = fetch_competitor_content(
            competitor_names=competitor_names,
            competitor_urls=competitor_urls,
            limit=5,
        )
        competitor_signals_text = '\n'.join(
            f"- {c['source']}: {c['snippet'][:150]}" for c in comp_data
        )

    for i, item in enumerate(topics):
        topic = item['topic']
        hashtags = item.get('hashtags', [])
        prefix = sanitize_filename(topic)
        topic_dir = base_dir / f'day{i + 1}_{prefix}'
        topic_dir.mkdir(parents=True, exist_ok=True)

        print(f'\n--- Day {i + 1}: {topic} ---')

        # 1. Research this specific topic
        print(f'  Researching...')
        research_text = combine_research(
            topic,
            competitor_names=competitor_names,
            competitor_urls=competitor_urls,
        )
        snippet = research_to_snippet(research_text)

        # 2. Generate drafts for each platform
        drafts = {}
        for platform in ('linkedin', 'x', 'threads'):
            print(f'  Generating {platform} draft...')
            content = generate_for_platform(
                topic=topic,
                platform=platform,
                research=snippet,
                competitor_signals=competitor_signals_text,
                hashtags=hashtags,
            )
            path = write_draft(platform, content, out_dir=str(topic_dir))
            drafts[platform] = path

        # 3. Render visuals (carousel + infographic)
        image_path = None
        carousel_paths = []
        if render_images:
            try:
                linkedin_content = Path(drafts['linkedin']).read_text(encoding='utf-8')

                from skill.renderer.render_image import render_carousel, render_infographic
                print(f'  Rendering carousel + infographic...')

                carousel_paths = render_carousel(
                    topic=topic, post_content=linkedin_content,
                    out_dir=str(topic_dir / 'carousel'),
                    style_index=i, author_name=author_name,
                )
                print(f'  Carousel: {len(carousel_paths)} slides')

                infographic_out = str(topic_dir / 'infographic.png')
                render_infographic(
                    topic=topic, post_content=linkedin_content,
                    out_path=infographic_out,
                    style_index=i, author_name=author_name,
                )
                image_path = infographic_out
                print(f'  Infographic: {infographic_out}')
            except Exception as e:
                print(f'  Visual render skipped: {e}')

        results.append({
            'day': i + 1,
            'topic': topic,
            'hashtags': hashtags,
            'drafts': drafts,
            'image_path': image_path,
            'carousel_paths': carousel_paths,
            'research_snippet': snippet[:200],
            'status': 'draft',
        })

    return results


def _default_topics() -> List[Dict]:
    """Load topics from calendar.yaml or use built-in defaults."""
    try:
        from skill.scheduler import get_scheduled_topics
        scheduled = get_scheduled_topics(date_range_days=7)
        if scheduled:
            return [
                {
                    'topic': item['topic'],
                    'hashtags': item.get('hashtags', ['AI', 'automation']),
                }
                for item in scheduled
            ]
    except Exception:
        pass

    return [
        {'topic': 'Why AI automation is the growth secret founders still ignore', 'hashtags': ['AI', 'automation', 'founder']},
        {'topic': 'The one common mistake every agency makes with WhatsApp automation', 'hashtags': ['WhatsApp', 'automation', 'agency']},
        {'topic': 'How automation can make your business feel smaller and more human', 'hashtags': ['automation', 'human', 'business']},
        {'topic': '3 AI trends every founder should use before the market catches up', 'hashtags': ['AI', 'trends', 'founder']},
        {'topic': 'The hidden cost of bad automation: burnout disguised as efficiency', 'hashtags': ['automation', 'burnout', 'efficiency']},
        {'topic': 'How to use AI to automate the work, not the customer', 'hashtags': ['AI', 'automation', 'customer']},
        {'topic': 'Why your automation playbook should start with client problems, not tools', 'hashtags': ['automation', 'playbook', 'product']},
    ]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a full week of content with per-topic research + AI.')
    parser.add_argument('--out-dir', default=None, help='Output directory')
    parser.add_argument('--competitors', default='', help='Comma-separated competitor names')
    parser.add_argument('--competitor-urls', default='', help='Comma-separated competitor URLs')
    parser.add_argument('--no-images', action='store_true', help='Skip image rendering')
    parser.add_argument('--author', default='', help='Author name for image cards')
    args = parser.parse_args()

    comp_names = [c.strip() for c in args.competitors.split(',') if c.strip()]
    comp_urls = [u.strip() for u in args.competitor_urls.split(',') if u.strip()]

    results = generate_week(
        out_dir=args.out_dir,
        competitor_names=comp_names or None,
        competitor_urls=comp_urls or None,
        render_images=not args.no_images,
        author_name=args.author,
    )

    print(f'\n=== Generated {len(results)} days of content ===')
    for r in results:
        print(f"  Day {r['day']}: {r['topic']}")
        for plat, path in r['drafts'].items():
            print(f"    {plat}: {path}")
        if r.get('image_path'):
            print(f"    image: {r['image_path']}")
