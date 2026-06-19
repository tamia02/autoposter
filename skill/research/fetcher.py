import re
import time
import requests
from typing import List, Dict

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

_last_request_time = 0.0


def _clean_html(html: str) -> str:
    text = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.S | re.I)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&\w+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _throttle(min_gap: float = 1.5):
    global _last_request_time
    now = time.time()
    wait = min_gap - (now - _last_request_time)
    if wait > 0:
        time.sleep(wait)
    _last_request_time = time.time()


def search_duckduckgo(query: str, limit: int = 8) -> List[Dict]:
    """Search DuckDuckGo HTML endpoint."""
    _throttle()
    try:
        resp = requests.post(
            'https://html.duckduckgo.com/html/',
            data={'q': query, 'kl': 'us-en'},
            headers=_HEADERS,
            timeout=12,
        )
        if resp.status_code != 200:
            return []

        results = []

        blocks = re.findall(
            r'<a[^>]+class="result__a"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            resp.text, flags=re.S | re.I,
        )
        for title_raw, snippet_raw in blocks[:limit]:
            title = _clean_html(title_raw)
            snippet = _clean_html(snippet_raw)
            if title or snippet:
                results.append({'title': title, 'snippet': snippet, 'source': 'web'})

        if not results:
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.S | re.I)
            for s in snippets[:limit]:
                text = _clean_html(s)
                if text and len(text) > 20:
                    results.append({'title': '', 'snippet': text, 'source': 'web'})

        return results
    except Exception as e:
        print(f'DuckDuckGo error: {e}')
        return []


def search_google_scrape(query: str, limit: int = 8) -> List[Dict]:
    """Fallback: scrape Google search results."""
    _throttle()
    try:
        resp = requests.get(
            'https://www.google.com/search',
            params={'q': query, 'num': limit, 'hl': 'en'},
            headers=_HEADERS,
            timeout=12,
        )
        if resp.status_code != 200:
            return []

        results = []
        h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text, re.S | re.I)
        spans = re.findall(r'<span[^>]*>(.*?)</span>', resp.text, re.S | re.I)

        clean_spans = []
        for s in spans:
            text = _clean_html(s)
            if len(text) > 40 and not text.startswith('http'):
                clean_spans.append(text)

        for i, h3 in enumerate(h3s[:limit]):
            title = _clean_html(h3)
            snippet = clean_spans[i] if i < len(clean_spans) else ''
            if title:
                results.append({'title': title, 'snippet': snippet[:200], 'source': 'web'})

        return results
    except Exception as e:
        print(f'Google scrape error: {e}')
        return []


def search_web(query: str, limit: int = 8) -> List[Dict]:
    """Search the web using DuckDuckGo → Google scrape fallback chain."""
    results = search_duckduckgo(query, limit=limit)
    if not results:
        results = search_google_scrape(query, limit=limit)
    return results


def fetch_competitor_content(
    competitor_names: List[str] = None,
    competitor_urls: List[str] = None,
    topic: str = '',
    limit: int = 5,
) -> List[Dict]:
    """Scrape competitor content from URLs and web search."""
    snippets: List[Dict] = []

    if competitor_urls:
        for url in competitor_urls[:limit]:
            _throttle(0.5)
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=10)
                resp.raise_for_status()

                title = ''
                title_match = re.search(r'<title>(.*?)</title>', resp.text, re.I | re.S)
                if title_match:
                    title = _clean_html(title_match.group(1))

                desc = ''
                desc_match = re.search(
                    r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
                    resp.text, re.I,
                )
                if desc_match:
                    desc = desc_match.group(1)

                paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', resp.text, re.I | re.S)
                body_text = ' '.join(_clean_html(p) for p in paragraphs[:5])

                snippet = desc or body_text[:300] or title
                if snippet:
                    snippets.append({
                        'source': url,
                        'title': title[:120],
                        'snippet': snippet[:300],
                        'type': 'direct_url',
                    })
            except Exception as e:
                print(f'Error fetching {url}: {e}')

    if competitor_names:
        for name in competitor_names:
            if len(snippets) >= limit:
                break
            query = f'{name} LinkedIn post {topic}'.strip()
            results = search_web(query, limit=2)
            for r in results:
                if len(snippets) >= limit:
                    break
                snippets.append({
                    'source': name,
                    'title': r.get('title', ''),
                    'snippet': r.get('snippet', ''),
                    'type': 'competitor_search',
                })

    return snippets[:limit]


def research_topic(topic: str, limit: int = 10) -> List[Dict]:
    """Research a topic using web search queries."""
    queries = [
        topic,
        f'{topic} tips advice 2025',
        f'{topic} trends insights',
    ]

    all_results = []
    seen = set()

    for q in queries:
        results = search_web(q, limit=limit // len(queries) + 2)
        for r in results:
            key = r.get('snippet', '')[:50]
            if key and key not in seen:
                seen.add(key)
                all_results.append(r)

    return all_results[:limit]


def combine_research(
    topic: str,
    competitor_names: List[str] = None,
    competitor_urls: List[str] = None,
    return_details: bool = False,
):
    """Full research: web search + competitor analysis."""
    web_results = research_topic(topic, limit=8)
    competitor_snippets = []

    if competitor_names or competitor_urls:
        competitor_snippets = fetch_competitor_content(
            competitor_names=competitor_names,
            competitor_urls=competitor_urls,
            topic=topic,
            limit=5,
        )

    lines = [f'Research on: {topic}', '']

    if web_results:
        lines.append('Web Research:')
        for r in web_results:
            title = r.get('title', '')
            snippet = r.get('snippet', '')
            line = f'- {title}: {snippet}' if title else f'- {snippet}'
            lines.append(line[:200])
        lines.append('')

    if competitor_snippets:
        lines.append('Competitor signals:')
        for item in competitor_snippets:
            source = item.get('source', 'unknown')
            snippet = item.get('snippet', '')
            lines.append(f'- {source}: {snippet[:180]}')
        lines.append('')

    if not web_results and not competitor_snippets:
        lines.append(f'Using topic context for: "{topic}" (web search unavailable).')
        lines.append('')

    research_text = '\n'.join(lines)

    if return_details:
        return research_text, {'web_results': web_results, 'competitors': competitor_snippets}
    return research_text
