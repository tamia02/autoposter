"""
Main orchestrator: Research → AI Generate → Image → Draft → Commit → PR → Notify
Supports single-topic and full 7-day batch modes.
"""

import os
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from skill.research.fetcher import combine_research
from skill.research.summarize import research_to_snippet
from skill.generator.generate import generate_all
from skill.git_helper import git_init_if_needed, git_commit_drafts, git_create_branch, git_push_branch, git_create_pr
from skill.renderer.render_image import render_card

try:
    from skill.google import read_sheet, read_doc
except ImportError:
    read_sheet = None
    read_doc = None

ROOT = Path(__file__).resolve().parent.parent


def load_google_research(sheet_id: str = None, sheet_range: str = 'Sheet1!A1:C10', doc_id: str = None) -> str:
    sources = []
    if sheet_id and read_sheet:
        try:
            print(f'  Loading Google Sheet: {sheet_id}')
            sources.append(read_sheet(sheet_id, sheet_range))
        except Exception as e:
            print(f'  Google Sheet failed: {e}')
    if doc_id and read_doc:
        try:
            print(f'  Loading Google Doc: {doc_id}')
            sources.append(read_doc(doc_id))
        except Exception as e:
            print(f'  Google Doc failed: {e}')
    return '\n\n'.join([s for s in sources if s.strip()])


def _publish_single(platform: str, content: str, image_path: str = None):
    """Publish a single post to a platform."""
    if platform == 'linkedin':
        from skill.posting.linkedin import post, post_with_image
        if image_path and os.path.exists(image_path):
            return post_with_image(content, image_path)
        return post(content)

    elif platform == 'x':
        from skill.posting.x_api import post as x_post, upload_media, post_thread, parse_thread_text
        media_id = None
        if image_path and os.path.exists(image_path):
            media_id = upload_media(image_path)
        tweets = parse_thread_text(content)
        if len(tweets) > 1:
            return post_thread(tweets, media_id=media_id)
        return x_post(content, media_ids=[media_id] if media_id else None)

    elif platform == 'threads':
        from skill.posting.threads import publish
        return publish(content)


def run_single_topic(args):
    """Run the pipeline for a single topic."""
    print(f'\n=== Content Creation Pipeline ===\n')
    print(f'Topic: {args.topic}')
    print(f'Mode: {args.publish_mode}')
    print(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Voice (optional)
    if getattr(args, 'audio', None):
        print('Step 1: Ingesting voice profile...')
        try:
            from skill.voice.ingest import create_profile_from_audio
            result = create_profile_from_audio(args.audio, model='small')
            print(f'  Voice profile: {result["path"]}\n')
        except Exception as e:
            print(f'  Voice ingestion failed: {e}\n')

    # Research
    print('Step 2: Researching topic...')
    google_text = load_google_research(
        sheet_id=getattr(args, 'google_sheet_id', None) or os.getenv('GOOGLE_SHEET_ID'),
        sheet_range=getattr(args, 'google_sheet_range', None) or os.getenv('GOOGLE_SHEET_RANGE', 'Sheet1!A1:C10'),
        doc_id=getattr(args, 'google_doc_id', None) or os.getenv('GOOGLE_DOC_ID'),
    )

    competitor_names = [c.strip() for c in getattr(args, 'competitors', '').split(',') if c.strip()]
    competitor_urls = [u.strip() for u in getattr(args, 'competitor_urls', '').split(',') if u.strip()]

    research_text = combine_research(
        args.topic,
        competitor_names=competitor_names or None,
        competitor_urls=competitor_urls or None,
    )
    if google_text:
        research_text += '\n\nGoogle Research:\n' + google_text

    snippet = research_to_snippet(research_text)
    print(f'  Research ready ({len(snippet)} chars)\n')

    # Generate drafts (AI or template fallback)
    print('Step 3: Generating platform drafts...')
    from skill.generator.generate import extract_competitor_signals
    comp_sig = extract_competitor_signals(research_text)

    drafts_dir = ROOT / 'drafts'
    hashtags = [h.strip() for h in getattr(args, 'hashtags', 'AI,automation').split(',')]
    res = generate_all(
        topic=args.topic,
        research=snippet,
        hashtags=hashtags,
        source_link='',
        out_dir=str(drafts_dir),
        competitor_signals=comp_sig,
    )
    for platform, path in res.items():
        with open(path, encoding='utf-8') as f:
            length = len(f.read())
        print(f'  {platform}: {path} ({length} chars)')
    print()

    # Render image
    image_path = None
    if getattr(args, 'no_images', False):
        print('Step 4: Skipping image (--no-images)\n')
    else:
        print('Step 4: Rendering share image...')
        try:
            image_quote = args.topic
            try:
                from skill.ai.client import generate_image_quote
                image_quote = generate_image_quote(args.topic)
            except Exception:
                pass

            img_out = str(drafts_dir / 'share_image.png')
            render_card(quote=image_quote, topic=args.topic, out_path=img_out)
            image_path = img_out
            print(f'  Image: {img_out}\n')
        except Exception as e:
            print(f'  Image render skipped: {e}\n')

    # Git + PR
    if args.publish_mode == 'pr-only' and not getattr(args, 'no_pr', False):
        print('Step 5: Creating PR...')
        try:
            git_init_if_needed(str(ROOT))
            branch = git_create_branch(str(ROOT), f"drafts/{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            print(f'  Branch: {branch}')

            message = f"Auto-draft: {args.topic}"
            git_commit_drafts(str(ROOT), args.topic, message)
            print(f'  Committed: {message}')

            pr_info = git_create_pr(
                str(ROOT),
                title=f'Drafts: {args.topic}',
                body=f'Auto-generated drafts for: {args.topic}',
                branch=branch,
            )
            print(f'  PR: {pr_info["status"]}\n')
        except Exception as e:
            print(f'  Git/PR failed: {e}\n')

    # Live publish
    elif args.publish_mode == 'live':
        print('Step 5: Publishing live...')
        for platform, path in res.items():
            try:
                with open(path, encoding='utf-8') as f:
                    content = f.read()
                result = _publish_single(platform, content, image_path)
                print(f'  Published to {platform}: {result}')

                try:
                    from skill.notification import send_post_published
                    send_post_published(args.topic, platform)
                except Exception:
                    pass
            except Exception as e:
                print(f'  {platform} publish failed: {e}')
        print()
    else:
        print('Step 5: Skipping PR/publish (--no-pr or draft mode)\n')

    print(f'=== Pipeline Complete ===\n')
    return res


def run_weekly_batch(args):
    """Run the full 7-day content generation pipeline."""
    from skill.generator.week_content import generate_week
    from skill.notification import send_weekly_content_ready

    print(f'\n=== 7-Day Content Batch ===\n')
    print(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    competitor_names = [c.strip() for c in getattr(args, 'competitors', '').split(',') if c.strip()]
    competitor_urls = [u.strip() for u in getattr(args, 'competitor_urls', '').split(',') if u.strip()]

    out_dir = str(ROOT / 'drafts' / 'weekly')

    results = generate_week(
        out_dir=out_dir,
        competitor_names=competitor_names or None,
        competitor_urls=competitor_urls or None,
        render_images=not getattr(args, 'no_images', False),
        author_name=getattr(args, 'author', ''),
    )

    print(f'\n=== Generated {len(results)} days of content ===\n')
    for r in results:
        print(f"Day {r['day']}: {r['topic']}")
        for plat, path in r['drafts'].items():
            print(f"  {plat}: {path}")
        if r.get('image_path'):
            print(f"  image: {r['image_path']}")
        print()

    # Git + PR for the batch
    if getattr(args, 'publish_mode', 'pr-only') == 'pr-only' and not getattr(args, 'no_pr', False):
        try:
            git_init_if_needed(str(ROOT))
            branch = git_create_branch(str(ROOT), f"weekly/{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            git_commit_drafts(str(ROOT), 'Weekly batch', f"Auto-draft: Weekly content batch")
            pr_info = git_create_pr(
                str(ROOT),
                title=f'Weekly Content Batch ({datetime.now().strftime("%Y-%m-%d")})',
                body=f'Auto-generated {len(results)}-day content batch.',
                branch=branch,
            )
            print(f'PR: {pr_info["status"]}')
        except Exception as e:
            print(f'Git/PR failed: {e}')

    # Email notification
    try:
        week_label = datetime.now().strftime('%b %d - ') + (
            datetime.now().strftime('%b %d')
        )
        send_weekly_content_ready(
            topics=results,
            drafts_dir=out_dir,
            week_label=week_label,
        )
        print('Email notification sent!')
    except Exception as e:
        print(f'Email notification skipped: {e}')

    print(f'\n=== Weekly Batch Complete ===\n')
    return results


def main():
    parser = argparse.ArgumentParser(description='Content creation pipeline: research + AI generate + image + PR')
    parser.add_argument('--topic', default=None, help='Single topic to create content for')
    parser.add_argument('--weekly', action='store_true', help='Generate a full 7-day content batch')
    parser.add_argument('--audio', default=None, help='Path to audio file for voice ingestion')
    parser.add_argument('--hashtags', default='AI,automation', help='Comma-separated hashtags')
    parser.add_argument('--competitors', default='', help='Comma-separated competitor names')
    parser.add_argument('--competitor-urls', default='', help='Comma-separated competitor URLs')
    parser.add_argument('--google-sheet-id', default=None, help='Google Sheet ID')
    parser.add_argument('--google-sheet-range', default='Sheet1!A1:C10', help='Google Sheet range')
    parser.add_argument('--google-doc-id', default=None, help='Google Doc ID')
    parser.add_argument('--publish-mode', default='pr-only', choices=['pr-only', 'live'], help='PR-only or live publish')
    parser.add_argument('--no-pr', action='store_true', help='Skip PR creation')
    parser.add_argument('--no-images', action='store_true', help='Skip image rendering')
    parser.add_argument('--author', default='', help='Author name for image cards')
    args = parser.parse_args()

    if args.weekly:
        return run_weekly_batch(args)
    elif args.topic:
        return run_single_topic(args)
    else:
        parser.error('Provide --topic "Your topic" for single mode, or --weekly for 7-day batch.')


if __name__ == '__main__':
    main()
