from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from .data import load_faq_blocks
from .retriever import build_retriever
from .responder import build_response


@dataclass
class ChatbotService:
    retriever_ready: bool = False

    def _ensure_retriever(self) -> None:
        if self.retriever_ready:
            return
        self._retriever = build_retriever()
        self.retriever_ready = True

    def get_response(self, query: str, symptoms: Optional[str] = None) -> str | None:
        if not query:
            return None

        if not load_faq_blocks():
            return None

        self._ensure_retriever()
        docs = self._retriever.retrieve(query)
        return build_response(query, symptoms, docs)


@lru_cache(maxsize=1)
def get_service() -> ChatbotService:
    return ChatbotService()


def get_response(query: str, symptoms: Optional[str] = None) -> str | None:
    return get_service().get_response(query, symptoms)
