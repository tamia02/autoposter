import argparse
from skill.research.fetcher import combine_research
from skill.research.summarize import research_to_snippet
from skill.generator.generate import generate_all


def main():
    p = argparse.ArgumentParser(description='Research + Generate content drafts for a topic.')
    p.add_argument('--topic', required=True, help='Topic to research.')
    p.add_argument('--hashtags', default='AI,automation', help='Comma-separated hashtags.')
    p.add_argument('--competitors', default='', help='Comma-separated competitor names.')
    p.add_argument('--competitor-urls', default='', help='Comma-separated competitor URLs.')
    p.add_argument('--outdir', default=None, help='Output directory for drafts.')
    args = p.parse_args()

    competitor_names = [c.strip() for c in args.competitors.split(',') if c.strip()]
    competitor_urls = [u.strip() for u in args.competitor_urls.split(',') if u.strip()]

    print(f'Researching: {args.topic}...')
    research_text = combine_research(
        args.topic,
        competitor_names=competitor_names or None,
        competitor_urls=competitor_urls or None,
    )
    print(research_text)

    snippet = research_to_snippet(research_text)
    print(f'\nResearch snippet: {snippet}\n')

    hashtags = [h.strip() for h in args.hashtags.split(',')]
    print('Generating drafts...')
    res = generate_all(
        topic=args.topic,
        research=snippet,
        hashtags=hashtags,
        source_link='',
        out_dir=args.outdir,
    )

    print(f'\nDrafts written:')
    print(f"  LinkedIn: {res['linkedin']}")
    print(f"  X Thread: {res['x']}")
    print(f"  Threads: {res['threads']}")


if __name__ == '__main__':
    main()
