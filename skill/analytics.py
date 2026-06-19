"""
Analytics: track engagement metrics, generate reports, and feed insights back to content generation.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent


class PostMetrics:
    def __init__(self, platform: str, topic: str, post_id: str = None):
        self.platform = platform
        self.topic = topic
        self.post_id = post_id or f"{platform}_{topic}_{datetime.now().timestamp()}"
        self.created_at = datetime.now().isoformat()
        self.metrics = {
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'views': 0,
            'engagement_rate': 0.0,
        }

    def to_dict(self) -> Dict:
        return {
            'post_id': self.post_id,
            'platform': self.platform,
            'topic': self.topic,
            'created_at': self.created_at,
            'metrics': self.metrics,
        }


class EngagementTracker:
    def __init__(self, log_path: str = None):
        self.log_path = Path(log_path or ROOT / 'reports' / 'engagement.json')
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list:
        if self.log_path.exists():
            with open(self.log_path) as f:
                return json.load(f)
        return []

    def _save(self, data: list):
        with open(self.log_path, 'w') as f:
            json.dump(data, f, indent=2)

    def log_post(self, post_metric: PostMetrics):
        data = self._load()
        data.append(post_metric.to_dict())
        self._save(data)

    def log_published(self, platform: str, topic: str, post_id: str = None, extra: dict = None):
        pm = PostMetrics(platform, topic, post_id)
        if extra:
            pm.metrics.update(extra)
        self.log_post(pm)

    def update_metrics(self, post_id: str, metrics_update: Dict):
        data = self._load()
        for entry in data:
            if entry.get('post_id') == post_id:
                entry['metrics'].update(metrics_update)
                break
        self._save(data)

    def get_platform_summary(self, days: int = 30) -> Dict:
        data = self._load()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        summary = defaultdict(lambda: {
            'count': 0, 'total_likes': 0, 'total_comments': 0,
            'total_shares': 0, 'avg_engagement': 0.0,
        })

        for entry in data:
            if entry.get('created_at', '') >= cutoff:
                platform = entry.get('platform', 'unknown')
                m = entry.get('metrics', {})
                summary[platform]['count'] += 1
                summary[platform]['total_likes'] += m.get('likes', 0)
                summary[platform]['total_comments'] += m.get('comments', 0)
                summary[platform]['total_shares'] += m.get('shares', 0)

        for platform in summary:
            count = summary[platform]['count']
            if count > 0:
                summary[platform]['avg_engagement'] = (
                    (summary[platform]['total_likes'] +
                     summary[platform]['total_comments'] * 2 +
                     summary[platform]['total_shares'] * 3) / count
                )

        return dict(summary)

    def get_top_topics(self, days: int = 30, limit: int = 5) -> List[Dict]:
        data = self._load()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        topic_scores = defaultdict(float)
        topic_counts = defaultdict(int)

        for entry in data:
            if entry.get('created_at', '') >= cutoff:
                topic = entry.get('topic', 'unknown')
                m = entry.get('metrics', {})
                score = m.get('likes', 0) + m.get('comments', 0) * 2 + m.get('shares', 0) * 3
                topic_scores[topic] += score
                topic_counts[topic] += 1

        ranked = sorted(
            [{'topic': t, 'avg_score': topic_scores[t] / topic_counts[t], 'posts': topic_counts[t]}
             for t in topic_scores],
            key=lambda x: x['avg_score'],
            reverse=True,
        )
        return ranked[:limit]

    def get_content_insights(self, days: int = 30) -> str:
        """Generate insights text that can be fed back into AI prompts."""
        top = self.get_top_topics(days=days, limit=3)
        summary = self.get_platform_summary(days=days)

        lines = []
        if top:
            lines.append('Top performing topics:')
            for t in top:
                lines.append(f"- {t['topic']} (score: {t['avg_score']:.0f})")

        best_platform = max(summary.items(), key=lambda x: x[1]['avg_engagement'], default=None)
        if best_platform:
            lines.append(f"\nBest platform: {best_platform[0]} (avg engagement: {best_platform[1]['avg_engagement']:.1f})")

        return '\n'.join(lines) if lines else 'No engagement data yet.'

    def generate_report(self, days: int = 30) -> str:
        platform_summary = self.get_platform_summary(days=days)
        top_topics = self.get_top_topics(days=days)

        lines = [
            f'=== Engagement Report ({days} days) ===\n',
            'Platform Summary:',
        ]

        if not platform_summary:
            lines.append('  No data yet. Publish some posts and update metrics to see results.')

        for platform, stats in platform_summary.items():
            lines.append(f"\n{platform}:")
            lines.append(f"  Posts: {stats['count']}")
            lines.append(f"  Avg Engagement: {stats['avg_engagement']:.1f}")
            lines.append(f"  Likes: {stats['total_likes']}  Comments: {stats['total_comments']}  Shares: {stats['total_shares']}")

        lines.append('\n\nTop Topics:')
        if not top_topics:
            lines.append('  No engagement data yet.')
        for i, topic_stat in enumerate(top_topics, 1):
            lines.append(f"{i}. {topic_stat['topic']} (avg score: {topic_stat['avg_score']:.1f}, posts: {topic_stat['posts']})")

        return '\n'.join(lines)


def save_report(report_text: str, output_path: str = None):
    if output_path is None:
        output_path = ROOT / 'reports' / f"engagement_report_{datetime.now().strftime('%Y%m%d')}.txt"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_text)
