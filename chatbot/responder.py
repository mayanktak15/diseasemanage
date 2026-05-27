from __future__ import annotations

from typing import Iterable

from .config import MAX_CONTEXT_CHARS
from .fallback import best_faq_block, rule_based_response
from .types import Document


def build_response(query: str, symptoms: str | None, docs: Iterable[Document]) -> str | None:
    rule_based = rule_based_response(query)
    if rule_based:
        return rule_based

    doc_list = list(docs)
    if doc_list:
        content = _join_docs(doc_list)
        if symptoms:
            return (
                f"{content}\n\n"
                f"User Symptoms: {symptoms}\n"
                "If symptoms are severe or persistent, please submit a consultation form."
            )
        return content

    fallback = best_faq_block(query)
    if fallback:
        return fallback

    return (
        "I'm here to help with questions about Docify Online and general guidance. "
        "Please ask about consultations, certificates, or common health concerns."
    )


def _join_docs(docs: list[Document]) -> str:
    chunks: list[str] = []
    remaining = MAX_CONTEXT_CHARS
    for doc in docs:
        if remaining <= 0:
            break
        content = doc.content.strip()
        if not content:
            continue
        if len(content) > remaining:
            content = content[:remaining].rstrip() + "..."
        chunks.append(content)
        remaining -= len(content)
    return "\n\n".join(chunks)
