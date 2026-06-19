"""
Routine entry points for Claude Code scheduler.
- daily: run today's scheduled topic
- weekly: generate a full 7-day batch + notify
- report: engagement report
- next: show next scheduled topic
- publish: publish drafts from a directory
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

from skill.scheduler import get_next_scheduled_run, RoutineScheduler, log_execution, advance_calendar_item_schedule
from skill.notification import send_email_notification, send_weekly_content_ready

ROOT = Path(__file__).resolve().parent.parent


def routine_daily_check():
    """Run today's scheduled topic through the full pipeline."""
    scheduler = RoutineScheduler(max_runs=1)
    scheduled_items = scheduler.run_if_scheduled()

    if not scheduled_items:
        print('No topics scheduled for today.')
        return

    for item in scheduled_items:
        topic = item['topic']
        print(f'\nRunning scheduled topic: {topic}')

        try:
            from skill.orchestrate import run_single_topic

            class Args:
                pass

            args = Args()
            args.topic = topic
            args.publish_mode = os.getenv('PUBLISH_MODE', 'pr-only')
            args.no_pr = False
            args.audio = None
            args.hashtags = 'AI,automation'
            args.competitors = ''
            args.competitor_urls = ''
            args.google_sheet_id = None
            args.google_sheet_range = 'Sheet1!A1:C10'
            args.google_doc_id = None
            args.no_images = False
            args.author = ''

            run_single_topic(args)
            log_execution(topic, 'success', {'run_type': 'daily_scheduled'})

            try:
                advance_calendar_item_schedule(item)
            except Exception as e:
                print(f'Could not advance schedule: {e}')

            try:
                send_email_notification(
                    subject=f'Content ready: {topic}',
                    body=f'The scheduled content for "{topic}" was generated successfully.\nCheck the drafts/ folder for review.',
                )
            except Exception as e:
                print(f'Email notification skipped: {e}')

        except Exception as e:
            log_execution(topic, 'failed', {'error': str(e)})
            print(f'Error: {e}')
            try:
                send_email_notification(
                    subject=f'Content FAILED: {topic}',
                    body=f'Generation failed for "{topic}":\n{e}',
                )
            except Exception:
                pass


def routine_weekly_batch():
    """Generate a full 7-day content batch and send notification."""
    from skill.orchestrate import run_weekly_batch

    class Args:
        pass

    args = Args()
    args.publish_mode = os.getenv('PUBLISH_MODE', 'pr-only')
    args.no_pr = False
    args.competitors = os.getenv('COMPETITORS', '')
    args.competitor_urls = os.getenv('COMPETITOR_URLS', '')
    args.no_images = False
    args.author = os.getenv('AUTHOR_NAME', '')

    return run_weekly_batch(args)


def routine_publish_drafts(drafts_dir: str = None, platforms: list = None):
    """Publish existing drafts from a directory."""
    if drafts_dir is None:
        drafts_dir = str(ROOT / 'drafts')
    if platforms is None:
        platforms = ['linkedin', 'x', 'threads']

    drafts_path = Path(drafts_dir)
    publish_mode = os.getenv('PUBLISH_MODE', 'pr-only')

    if publish_mode != 'live':
        print('PUBLISH_MODE is not "live". Set PUBLISH_MODE=live to publish.')
        return

    from skill.orchestrate import _publish_single

    for platform in platforms:
        draft_file = drafts_path / f'{platform}_draft.md'
        if not draft_file.exists():
            print(f'No draft found for {platform}: {draft_file}')
            continue

        content = draft_file.read_text(encoding='utf-8')
        image_path = str(drafts_path / 'share_image.png')
        if not Path(image_path).exists():
            image_path = None

        try:
            result = _publish_single(platform, content, image_path)
            print(f'Published to {platform}: {result}')

            from skill.notification import send_post_published
            send_post_published(content[:50], platform)
        except Exception as e:
            print(f'{platform} publish failed: {e}')


def routine_engagement_report():
    from skill.analytics import EngagementTracker, save_report
    tracker = EngagementTracker()
    report = tracker.generate_report(days=30)
    print(report)
    save_report(report)
    print('\nReport saved to reports/')


def main():
    p = argparse.ArgumentParser(description='Routine scheduler and automation CLI.')
    subparsers = p.add_subparsers(dest='command', help='Command to run.')

    subparsers.add_parser('daily', help='Run today\'s scheduled topic.')
    subparsers.add_parser('weekly', help='Generate full 7-day content batch + email notify.')

    publish_p = subparsers.add_parser('publish', help='Publish existing drafts live.')
    publish_p.add_argument('--dir', default=None, help='Drafts directory to publish from.')
    publish_p.add_argument('--platforms', default='linkedin,x,threads', help='Comma-separated platforms.')

    subparsers.add_parser('report', help='Generate engagement report.')
    subparsers.add_parser('next', help='Show next scheduled topic.')

    args = p.parse_args()

    if args.command == 'daily':
        routine_daily_check()
    elif args.command == 'weekly':
        routine_weekly_batch()
    elif args.command == 'publish':
        platforms = [p.strip() for p in args.platforms.split(',')]
        routine_publish_drafts(drafts_dir=args.dir, platforms=platforms)
    elif args.command == 'report':
        routine_engagement_report()
    elif args.command == 'next':
        next_topic = get_next_scheduled_run()
        if next_topic:
            print(f"Next: {next_topic.get('topic')} on {next_topic.get('scheduled_date')}")
        else:
            print('No scheduled topics found.')
    else:
        p.print_help()


if __name__ == '__main__':
    main()
