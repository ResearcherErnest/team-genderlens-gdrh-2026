"""
Link Checker — HTTP HEAD-based URL health monitoring with caching.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import requests

logger = logging.getLogger(__name__)

# In-memory cache for link check results (URL → (status_code, is_alive))
_cache: Dict[str, Tuple[int, bool]] = {}


def check_url(url: str, timeout: int = 5) -> Tuple[int, bool]:
    """
    HEAD-request a URL. Returns (status_code, is_alive).
    Results are cached in-memory for the session.
    """
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return (0, False)

    if url in _cache:
        return _cache[url]

    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        alive = resp.status_code < 400
        result = (resp.status_code, alive)
    except requests.RequestException as e:
        logger.warning("Link check failed for %s: %s", url, e)
        result = (0, False)

    _cache[url] = result
    return result


def status_badge(status_code: int, is_alive: bool) -> str:
    """Return an emoji badge for link status."""
    if is_alive:
        return "🟢 Online"
    elif status_code >= 400:
        return f"🔴 Error ({status_code})"
    else:
        return "⚫ Unreachable"


def clear_cache() -> None:
    """Clear the link check cache."""
    _cache.clear()
