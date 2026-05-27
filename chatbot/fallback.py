from __future__ import annotations

from difflib import SequenceMatcher

from .data import load_faq_blocks


def rule_based_response(query: str) -> str | None:
    query_lower = (query or "").lower()

    if "fever" in query_lower or "temperature" in query_lower:
        return (
            "I understand you have a fever. Here are some general tips:\n\n"
            "- Stay hydrated and rest.\n"
            "- Monitor your temperature.\n"
            "- Consider over-the-counter fever reducers if appropriate.\n\n"
            "If the fever is high or lasts more than a few days, please submit a consultation form."
        )

    if "docify" in query_lower or "what is" in query_lower:
        return (
            "Docify Online is a platform for medical consultations and certificates, backed by certified doctors."
        )

    if "consult" in query_lower or "form" in query_lower or "submit" in query_lower:
        return (
            "To submit a consultation form: log in, open the dashboard, and fill in your symptoms."
        )

    if "secure" in query_lower or "privacy" in query_lower or "data" in query_lower:
        return "Yes. We protect your data with secure storage and password hashing."

    if "support" in query_lower or "contact" in query_lower or "help" in query_lower:
        return "You can contact support via the chatbot or email at support@docify.online."

    return None


def best_faq_block(query: str) -> str | None:
    blocks = load_faq_blocks()
    if not query or not blocks:
        return None

    query_lower = query.lower().strip()
    best_score = 0.0
    best_block = None
    for block in blocks:
        first_line = block.splitlines()[0] if block else ""
        candidate = first_line.lower().strip()
        if not candidate:
            continue
        score = SequenceMatcher(None, query_lower, candidate).ratio()
        if score > best_score:
            best_score = score
            best_block = block

    if best_score >= 0.35:
        return best_block
    return None
