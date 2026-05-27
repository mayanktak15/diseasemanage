from __future__ import annotations

from typing import Optional

from app.extensions import cache
from chatbot import get_response


def get_chatbot_response(query: str, symptoms: Optional[str] = None) -> Optional[str]:
    cache_key = f"chatbot:{query}:{symptoms or ''}"
    try:
        cached = cache.get(cache_key)
    except Exception:
        cached = None

    if cached:
        return cached

    response = get_response(query, symptoms)
    if response:
        try:
            cache.set(cache_key, response)
        except Exception:
            pass
    return response
