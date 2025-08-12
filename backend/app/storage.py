import json
import os
import hashlib
from typing import Optional, Tuple

import faiss
import numpy as np

DATA_DIR = "data"
USERS_JSON = os.path.join(DATA_DIR, "users.json")
FAISS_INDEX_BIN = os.path.join(DATA_DIR, "faiss_index.bin")

os.makedirs(DATA_DIR, exist_ok=True)

class VectorStore:
    def __init__(self, dim: int = 512, use_cosine: bool = True):
        """
        dim: dimension of embeddings (512 for facenet-pytorch InceptionResnetV1)
        use_cosine: if True, uses cosine similarity (via L2-normalize + IndexFlatIP)
        """
        self.dim = dim
        self.use_cosine = use_cosine
        self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
        self.id_map: list[str] = []  # index position -> user_id

        if os.path.isfile(FAISS_INDEX_BIN) and os.path.isfile(USERS_JSON):
            try:
                self.index = faiss.read_index(FAISS_INDEX_BIN)
                with open(USERS_JSON, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f).get("id_map", [])
            except Exception:
                self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
                self.id_map = []

    def persist(self):
        faiss.write_index(self.index, FAISS_INDEX_BIN)
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump({"id_map": self.id_map}, f)

    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vec, axis=1, keepdims=True) + 1e-12
        return vec / norms

    def add_vector(self, user_id: str, embedding: np.ndarray) -> str:
        """
        embedding: np.ndarray of shape (512,) float32
        Returns a SHA-256 hex digest of the embedding bytes (for audit).
        """
        vec = embedding.reshape(1, -1).astype("float32")
        if vec.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {vec.shape[1]}")
        if self.use_cosine:
            vec = self._l2_normalize(vec)
        self.index.add(vec)
        self.id_map.append(user_id)
        self.persist()
        digest = hashlib.sha256(embedding.tobytes()).hexdigest()
        return digest

    def search(self, query: np.ndarray, k: int = 1) -> Tuple[Optional[str], float]:
        vec = query.reshape(1, -1).astype("float32")
        if vec.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {vec.shape[1]}")
        if self.use_cosine:
            vec = self._l2_normalize(vec)
        if self.index.ntotal == 0:
            return None, 0.0
        scores, idxs = self.index.search(vec, k)
        top_idx = idxs[0][0]
        top_score = float(scores[0][0])
        if top_idx == -1 or top_idx >= len(self.id_map):
            return None, 0.0
        return self.id_map[top_idx], top_score
