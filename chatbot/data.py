from __future__ import annotations

from functools import lru_cache

from .config import FAQ_FILE_PATH


@lru_cache(maxsize=1)
def load_faq_text() -> str:
    try:
        with open(FAQ_FILE_PATH, "r", encoding="utf-8") as handle:
            return handle.read()
    except Exception:
        return ""


@lru_cache(maxsize=1)
def load_faq_blocks() -> list[str]:
    text = load_faq_text()
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return blocks
