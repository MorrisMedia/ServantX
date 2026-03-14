import html
import re
from typing import Dict, List
from urllib.parse import urlparse

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _safe_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def _search_duckduckgo_instant(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "no_redirect": "1",
                "skip_disambig": "1",
            },
            headers=DEFAULT_HEADERS,
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    results: List[Dict[str, str]] = []
    abstract_text = (payload.get("AbstractText") or "").strip()
    abstract_url = (payload.get("AbstractURL") or "").strip()
    if abstract_text:
        results.append(
            {
                "title": payload.get("Heading") or "Instant Answer",
                "snippet": abstract_text,
                "url": abstract_url,
                "domain": _safe_domain(abstract_url),
            }
        )

    def _walk_related(items):
        for item in items:
            if isinstance(item, dict) and item.get("Topics"):
                yield from _walk_related(item.get("Topics") or [])
            elif isinstance(item, dict):
                text = (item.get("Text") or "").strip()
                first_url = (item.get("FirstURL") or "").strip()
                if text:
                    yield {
                        "title": text.split(" - ", 1)[0][:120],
                        "snippet": text[:320],
                        "url": first_url,
                        "domain": _safe_domain(first_url),
                    }

    related_topics = payload.get("RelatedTopics") or []
    for item in _walk_related(related_topics):
        results.append(item)
        if len(results) >= max_results:
            break

    return results[:max_results]


def _search_duckduckgo_html(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=DEFAULT_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        body = response.text
    except Exception:
        return []

    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.DOTALL,
    )
    results: List[Dict[str, str]] = []
    for match in pattern.finditer(body):
        title = re.sub(r"<[^>]+>", "", match.group("title"))
        snippet = re.sub(r"<[^>]+>", "", match.group("snippet"))
        url = html.unescape(match.group("url"))
        clean_title = html.unescape(title).strip()
        clean_snippet = html.unescape(snippet).strip()
        if not clean_title and not clean_snippet:
            continue
        results.append(
            {
                "title": clean_title[:180] or "Search result",
                "snippet": clean_snippet[:320],
                "url": url,
                "domain": _safe_domain(url),
            }
        )
        if len(results) >= max_results:
            break
    return results


def search_legal_web_context(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Best-effort lightweight web research for legal/contract context.
    Does not require API keys.
    """
    enriched_query = f"{query} contract law healthcare reimbursement"
    instant = _search_duckduckgo_instant(enriched_query, max_results=max_results)
    if len(instant) >= max_results:
        return instant[:max_results]

    html_results = _search_duckduckgo_html(enriched_query, max_results=max_results)
    merged: List[Dict[str, str]] = []
    seen = set()
    for item in instant + html_results:
        key = (item.get("url") or "", item.get("title") or "")
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= max_results:
            break
    return merged
