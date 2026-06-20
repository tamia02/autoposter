import os
import requests
from pathlib import Path

API_BASE = 'https://api.linkedin.com'


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
    author = os.getenv('LINKEDIN_AUTHOR_URN', '')
    if not author:
        raise RuntimeError('Missing LINKEDIN_AUTHOR_URN')

    headers = _headers()

    # Try v2 assets API (works with Share on LinkedIn product)
    register_resp = requests.post(
        f'{API_BASE}/v2/assets?action=registerUpload',
        json={
            'registerUploadRequest': {
                'recipes': ['urn:li:digitalmediaRecipe:feedshare-image'],
                'owner': author,
                'serviceRelationships': [
                    {'relationshipType': 'OWNER', 'identifier': 'urn:li:userGeneratedContent'}
                ]
            }
        },
        headers=headers,
    )

    if register_resp.status_code == 426:
        # Try newer REST API
        init_resp = requests.post(
            f'{API_BASE}/rest/images?action=initializeUpload',
            json={'initializeUploadRequest': {'owner': author}},
            headers=headers,
        )
        init_resp.raise_for_status()
        init_data = init_resp.json().get('value', {})
        upload_url = init_data.get('uploadUrl', '')
        image_urn = init_data.get('image', '')
    else:
        register_resp.raise_for_status()
        data = register_resp.json().get('value', {})
        upload_url = data.get('uploadMechanism', {}).get(
            'com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest', {}
        ).get('uploadUrl', '')
        image_urn = data.get('asset', '')

    if not upload_url or not image_urn:
        raise RuntimeError('LinkedIn image registration failed')

    image_bytes = Path(image_path).read_bytes()
    put_resp = requests.put(
        upload_url,
        data=image_bytes,
        headers={'Authorization': headers['Authorization'], 'Content-Type': 'image/png'},
    )
    put_resp.raise_for_status()
    return image_urn


def post(content: str, image_urn: str = None) -> dict:
    author = os.getenv('LINKEDIN_AUTHOR_URN', '')
    if not author:
        raise RuntimeError('Missing LINKEDIN_AUTHOR_URN')

    headers = _headers()

    # Try new API first (/rest/posts)
    payload = {
        'author': author,
        'commentary': content,
        'visibility': 'PUBLIC',
        'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [], 'thirdPartyDistributionChannels': []},
        'lifecycleState': 'PUBLISHED',
    }

    if image_urn:
        payload['content'] = {
            'media': {'title': '', 'id': image_urn}
        }

    resp = requests.post(f'{API_BASE}/rest/posts', json=payload, headers=headers)

    if resp.status_code == 426:
        # Fallback to v2 UGC API
        return _post_v2(content, image_urn, author, headers)

    resp.raise_for_status()
    return {'status': 'published', 'id': resp.headers.get('x-restli-id', '')}


def _post_v2(content: str, image_urn: str, author: str, headers: dict) -> dict:
    """Fallback: use older v2/ugcPosts API."""
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
        share['media'] = [{'status': 'READY', 'media': image_urn, 'title': {'text': ''}, 'description': {'text': ''}}]

    resp = requests.post(f'{API_BASE}/v2/ugcPosts', json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def post_with_image(content: str, image_path: str) -> dict:
    try:
        image_urn = upload_image(image_path)
        return post(content, image_urn=image_urn)
    except Exception as e:
        print(f'Image upload failed ({e}), posting text-only...')
        return post(content)
