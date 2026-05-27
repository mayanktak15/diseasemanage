from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from .config import EMBEDDING_MODEL


def _load_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None
    try:
        return SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_embedder():
    return _load_sentence_transformer()


def embed_texts(texts: Iterable[str]):
    model = get_embedder()
    if model is None:
        return None
    try:
        embeddings = model.encode(list(texts), normalize_embeddings=True)
    except Exception:
        return None
    try:
        import numpy as np
    except Exception:
        return None
    return np.asarray(embeddings, dtype="float32")
