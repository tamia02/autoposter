import os
import requests
from pathlib import Path

API_BASE = 'https://api.linkedin.com/rest'


def _headers():
    token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not token:
        raise RuntimeError('Missing LINKEDIN_ACCESS_TOKEN')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202401',
    }


def upload_image(image_path: str) -> str:
    """
    Upload an image to LinkedIn and return the image URN.
    Uses the Images API (initializeUpload → PUT binary → image URN).
    """
    author = os.getenv('LINKEDIN_AUTHOR_URN', '')
    if not author:
        raise RuntimeError('Missing LINKEDIN_AUTHOR_URN')

    headers = _headers()

    init_resp = requests.post(
        f'{API_BASE}/images?action=initializeUpload',
        json={
            'initializeUploadRequest': {
                'owner': author,
            }
        },
        headers=headers,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json().get('value', {})
    upload_url = init_data.get('uploadUrl', '')
    image_urn = init_data.get('image', '')

    if not upload_url or not image_urn:
        raise RuntimeError(f'LinkedIn image init failed: {init_data}')

    image_bytes = Path(image_path).read_bytes()
    put_resp = requests.put(
        upload_url,
        data=image_bytes,
        headers={
            'Authorization': headers['Authorization'],
            'Content-Type': 'application/octet-stream',
        },
    )
    put_resp.raise_for_status()

    return image_urn


def post(content: str, image_urn: str = None) -> dict:
    """Publish a LinkedIn post, optionally with an image."""
    author = os.getenv('LINKEDIN_AUTHOR_URN', '')
    if not author:
        raise RuntimeError('Missing LINKEDIN_AUTHOR_URN')

    headers = _headers()

    payload = {
        'author': author,
        'lifecycleState': 'PUBLISHED',
        'specificContent': {
            'com.linkedin.ugc.ShareContent': {
                'shareCommentary': {'text': content},
                'shareMediaCategory': 'NONE',
            }
        },
        'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
    }

    if image_urn:
        share = payload['specificContent']['com.linkedin.ugc.ShareContent']
        share['shareMediaCategory'] = 'IMAGE'
        share['media'] = [
            {
                'status': 'READY',
                'description': {'text': ''},
                'media': image_urn,
                'title': {'text': ''},
            }
        ]

    resp = requests.post(f'{API_BASE}/posts', json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def post_with_image(content: str, image_path: str) -> dict:
    """Upload image then publish post in one call."""
    image_urn = upload_image(image_path)
    return post(content, image_urn=image_urn)
