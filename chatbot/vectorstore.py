import os
import json
import hashlib
from typing import Optional, List, Tuple
from .config import FAQ_FILE_PATH, EMBEDDING_MODEL
from .data import load_faq_blocks
from .embeddings import embed_texts, get_embedder

INDEX_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "instance")
INDEX_PATH = os.path.join(INDEX_CACHE_DIR, "faq_faiss.idx")
META_PATH = os.path.join(INDEX_CACHE_DIR, "faq_faiss.json")


def _get_faq_hash() -> str:
    try:
        with open(FAQ_FILE_PATH, "rb") as f:
            content = f.read()
        hasher = hashlib.sha256()
        hasher.update(content)
        hasher.update(EMBEDDING_MODEL.encode("utf-8"))
        return hasher.hexdigest()
    except Exception:
        return ""


class FAQVectorStore:
    def __init__(self):
        self.docs = []
        self.index = None
        self.embeddings = None
        self.has_faiss = False
        self._faq_hash = ""

        # Try to import faiss
        try:
            import faiss
            self.has_faiss = True
        except ImportError:
            self.has_faiss = False

    def load_or_build(self) -> bool:
        self.docs = load_faq_blocks()
        if not self.docs:
            return False

        current_hash = _get_faq_hash()
        self._faq_hash = current_hash

        # Attempt to load cached index
        if self._load_cache(current_hash):
            return True

        # Build new index
        return self._build_index(current_hash)

    def _load_cache(self, current_hash: str) -> bool:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
            return False

        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            if meta.get("hash") != current_hash:
                return False

            if self.has_faiss:
                import faiss
                self.index = faiss.read_index(INDEX_PATH)
                return True
            else:
                # Load NumPy embeddings cache if FAISS is not used
                import numpy as np
                npy_path = INDEX_PATH + ".npy"
                if os.path.exists(npy_path):
                    self.embeddings = np.load(npy_path)
                    return True
        except Exception:
            pass
        return False

    def _build_index(self, current_hash: str) -> bool:
        # Embed all texts
        vectors = embed_texts(self.docs)
        if vectors is None:
            return False

        try:
            os.makedirs(INDEX_CACHE_DIR, exist_ok=True)
            
            if self.has_faiss:
                import faiss
                import numpy as np
                dimension = vectors.shape[1]
                index = faiss.IndexFlatIP(dimension)  # Inner Product (Cosine similarity if normalized)
                index.add(np.ascontiguousarray(vectors))
                self.index = index
                faiss.write_index(index, INDEX_PATH)
            else:
                import numpy as np
                self.embeddings = vectors
                np.save(INDEX_PATH + ".npy", vectors)

            # Save metadata
            with open(META_PATH, "w", encoding="utf-8") as f:
                json.dump({"hash": current_hash, "count": len(self.docs)}, f)
            return True
        except Exception:
            return False

    def search(self, query: str, top_k: int = 3) -> List[Tuple[int, float]]:
        if not self.docs:
            return []

        query_vec = embed_texts([query])
        if query_vec is None:
            return []

        q_vec = query_vec[0]

        if self.has_faiss and self.index is not None:
            import numpy as np
            import faiss
            q_arr = np.ascontiguousarray([q_vec])
            scores, indices = self.index.search(q_arr, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:
                    results.append((int(idx), float(score)))
            return results

        elif self.embeddings is not None:
            # Fallback to NumPy matrix multiplication
            scores = self.embeddings @ q_vec
            best_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            return [(idx, float(scores[idx])) for idx in best_idx]
        
        else:
            return []
