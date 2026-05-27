from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .config import HYBRID_WEIGHT_KEYWORD, TOP_K
from .data import load_faq_blocks
from .embeddings import embed_texts
from .keyword import simple_overlap_scores, tfidf_scores
from .types import Document


@dataclass
class HybridRetriever:
    docs: list[str]

    def retrieve(self, query: str, top_k: int | None = None) -> list[Document]:
        if not query:
            return []

        limit = top_k or TOP_K
        docs = self.docs

        keyword_scores = tfidf_scores(query, docs)
        if keyword_scores is None:
            keyword_scores = simple_overlap_scores(query, docs)

        embedding_scores = self._embedding_scores(query, docs)

        combined = self._combine_scores(keyword_scores, embedding_scores)
        if not combined:
            return []

        best_idx = self._top_indices(combined, limit)
        results: list[Document] = []
        for idx in best_idx:
            score = float(combined[idx])
            if score <= 0:
                continue
            results.append(Document(content=docs[idx], score=score, source="faq"))
        return results

    def _embedding_scores(self, query: str, docs: Iterable[str]):
        embeddings = embed_texts(docs)
        if embeddings is None:
            return None

        query_embedding = embed_texts([query])
        if query_embedding is None:
            return None

        query_vec = query_embedding[0]
        scores = embeddings @ query_vec
        try:
            return scores.astype("float32")
        except Exception:
            return scores.tolist()

    def _combine_scores(self, keyword_scores, embedding_scores):
        if embedding_scores is None:
            return list(keyword_scores) if keyword_scores else []

        combined: list[float] = []
        for idx, keyword_score in enumerate(keyword_scores):
            combined.append(
                (HYBRID_WEIGHT_KEYWORD * float(keyword_score))
                + ((1.0 - HYBRID_WEIGHT_KEYWORD) * float(embedding_scores[idx]))
            )
        return combined

    def _top_indices(self, scores: list[float], limit: int) -> list[int]:
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]


def build_retriever() -> HybridRetriever:
    return HybridRetriever(docs=load_faq_blocks())
