import os
import time
import requests

GRAPH_URL = 'https://graph.threads.net/v1.0'


def _get_config():
    token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    if not token:
        raise RuntimeError('Missing THREADS_ACCESS_TOKEN')
    if not user_id:
        raise RuntimeError('Missing THREADS_USER_ID')
    return token, user_id


def create_text_container(text: str) -> str:
    """Step 1: Create a text-only media container."""
    token, user_id = _get_config()

    resp = requests.post(
        f'{GRAPH_URL}/{user_id}/threads',
        params={
            'media_type': 'TEXT',
            'text': text,
            'access_token': token,
        },
    )
    resp.raise_for_status()
    return resp.json().get('id', '')


def create_media_container(text: str, image_url: str) -> str:
    """Step 1: Create an image media container (image must be a public URL)."""
    token, user_id = _get_config()

    resp = requests.post(
        f'{GRAPH_URL}/{user_id}/threads',
        params={
            'media_type': 'IMAGE',
            'image_url': image_url,
            'text': text,
            'access_token': token,
        },
    )
    resp.raise_for_status()
    return resp.json().get('id', '')


def _wait_for_container(container_id: str, max_wait: int = 30):
    """Poll until the container is ready for publishing."""
    token, user_id = _get_config()
    for _ in range(max_wait):
        resp = requests.get(
            f'{GRAPH_URL}/{container_id}',
            params={'fields': 'status', 'access_token': token},
        )
        if resp.ok:
            status = resp.json().get('status', '')
            if status == 'FINISHED':
                return True
            if status == 'ERROR':
                raise RuntimeError(f'Threads container error: {resp.json()}')
        time.sleep(1)
    raise RuntimeError('Threads container timed out waiting for FINISHED status.')


def publish(content: str, image_url: str = None) -> dict:
    """
    Full publish flow:
    1. Create container (text or image)
    2. Wait for container to be ready
    3. Publish the container
    """
    token, user_id = _get_config()

    if image_url:
        container_id = create_media_container(content, image_url)
    else:
        container_id = create_text_container(content)

    _wait_for_container(container_id)

    resp = requests.post(
        f'{GRAPH_URL}/{user_id}/threads_publish',
        params={
            'creation_id': container_id,
            'access_token': token,
        },
    )
    resp.raise_for_status()
    return resp.json()
