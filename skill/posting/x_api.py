import os
import json
import requests
from pathlib import Path

TWEET_URL = 'https://api.twitter.com/2/tweets'
MEDIA_UPLOAD_URL = 'https://upload.twitter.com/1.1/media/upload.json'


def _get_oauth_session():
    """Create an OAuth 1.0a session for X/Twitter write access."""
    try:
        import tweepy
    except ImportError:
        raise RuntimeError('tweepy is required for X posting. Run: pip install tweepy')

    api_key = os.getenv('X_API_KEY', '')
    api_secret = os.getenv('X_API_SECRET', '')
    access_token = os.getenv('X_ACCESS_TOKEN', '')
    access_secret = os.getenv('X_ACCESS_TOKEN_SECRET', '')

    if not all([api_key, api_secret, access_token, access_secret]):
        raise RuntimeError(
            'Missing X/Twitter OAuth credentials. '
            'Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET.'
        )

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )
    return client


def _get_tweepy_api():
    """Get Tweepy API v1.1 (needed for media upload)."""
    try:
        import tweepy
    except ImportError:
        raise RuntimeError('tweepy is required for X media upload. Run: pip install tweepy')

    api_key = os.getenv('X_API_KEY', '')
    api_secret = os.getenv('X_API_SECRET', '')
    access_token = os.getenv('X_ACCESS_TOKEN', '')
    access_secret = os.getenv('X_ACCESS_TOKEN_SECRET', '')

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    return tweepy.API(auth)


def upload_media(image_path: str) -> str:
    """Upload media to X/Twitter and return the media_id string."""
    api = _get_tweepy_api()
    media = api.media_upload(filename=image_path)
    return str(media.media_id)


def post(content: str, media_ids: list = None) -> dict:
    """Post a tweet using Twitter API v2 via tweepy."""
    client = _get_oauth_session()

    kwargs = {'text': content}
    if media_ids:
        kwargs['media_ids'] = media_ids

    response = client.create_tweet(**kwargs)
    return {'id': response.data.get('id'), 'text': response.data.get('text', '')}


def post_thread(tweets: list, media_id: str = None) -> list:
    """
    Post an X thread (multiple tweets as a reply chain).
    tweets: list of strings, each under 280 chars.
    media_id: optional media to attach to the first tweet.
    """
    client = _get_oauth_session()

    results = []
    reply_to = None

    for i, text in enumerate(tweets):
        kwargs = {'text': text}
        if i == 0 and media_id:
            kwargs['media_ids'] = [media_id]
        if reply_to:
            kwargs['in_reply_to_tweet_id'] = reply_to

        response = client.create_tweet(**kwargs)
        tweet_id = response.data.get('id')
        results.append({'id': tweet_id, 'text': text})
        reply_to = tweet_id

    return results


def parse_thread_text(thread_text: str) -> list:
    """Parse numbered thread text (1/ ..., 2/ ...) into individual tweets."""
    import re
    parts = re.split(r'\n*\d+/\s*', thread_text)
    tweets = [p.strip() for p in parts if p.strip()]
    return tweets
