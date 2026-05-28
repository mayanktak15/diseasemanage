from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
from functools import lru_cache

from .config import HYBRID_WEIGHT_KEYWORD, TOP_K
from .data import load_faq_blocks
from .keyword import simple_overlap_scores, tfidf_scores
from .types import Document
from .vectorstore import FAQVectorStore

_vector_store_instance: Optional[FAQVectorStore] = None

def get_vector_store() -> FAQVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        store = FAQVectorStore()
        store.load_or_build()
        _vector_store_instance = store
    return _vector_store_instance


@dataclass
class HybridRetriever:
    docs: list[str]

    def retrieve(self, query: str, top_k: int | None = None) -> list[Document]:
        if not query:
            return []

        limit = top_k or TOP_K
        docs = self.docs

        # 1. Keyword search (TF-IDF with overlap fallback)
        keyword_scores = tfidf_scores(query, docs)
        if keyword_scores is None:
            keyword_scores = simple_overlap_scores(query, docs)

        # 2. Embedding semantic search
        embedding_scores = [0.0] * len(docs)
        store = get_vector_store()
        try:
            vector_results = store.search(query, top_k=len(docs))
            for idx, score in vector_results:
                if 0 <= idx < len(embedding_scores):
                    embedding_scores[idx] = score
        except Exception:
            pass

        # 3. Combine rankings
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

    def _combine_scores(self, keyword_scores: List[float], embedding_scores: List[float]) -> List[float]:
        combined: list[float] = []
        for idx, keyword_score in enumerate(keyword_scores):
            emb_score = embedding_scores[idx] if idx < len(embedding_scores) else 0.0
            combined.append(
                (HYBRID_WEIGHT_KEYWORD * float(keyword_score))
                + ((1.0 - HYBRID_WEIGHT_KEYWORD) * float(emb_score))
            )
        return combined

    def _top_indices(self, scores: list[float], limit: int) -> list[int]:
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]


def build_retriever() -> HybridRetriever:
    return HybridRetriever(docs=load_faq_blocks())
