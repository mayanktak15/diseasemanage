from __future__ import annotations

from typing import Iterable


def _tokenize(text: str) -> set[str]:
    return {token for token in text.lower().split() if token.strip()}


def simple_overlap_scores(query: str, docs: Iterable[str]):
    query_tokens = _tokenize(query)
    scores: list[float] = []
    for doc in docs:
        doc_tokens = _tokenize(doc)
        if not doc_tokens or not query_tokens:
            scores.append(0.0)
            continue
        overlap = len(query_tokens & doc_tokens)
        scores.append(overlap / max(len(doc_tokens), 1))
    return scores


def tfidf_scores(query: str, docs: list[str]):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception:
        return None

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(docs + [query])
    doc_vectors = matrix[:-1]
    query_vector = matrix[-1]
    scores = (doc_vectors @ query_vector.T).toarray().ravel().tolist()
    return scores
