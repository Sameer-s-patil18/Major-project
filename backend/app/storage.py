import json
import os
import hashlib
from typing import Optional, Tuple, List

import faiss
import numpy as np

DATA_DIR = "data"
USERS_JSON = os.path.join(DATA_DIR, "users.json")
FAISS_INDEX_BIN = os.path.join(DATA_DIR, "faiss_index.bin")
WALLETS_JSON = os.path.join(DATA_DIR, "wallets.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _ensure_float32_2d(vec: np.ndarray) -> np.ndarray:
    if vec.ndim == 1:
        vec = vec.reshape(1, -1)
    return vec.astype("float32", copy=False)

def _l2_normalize_rows(vec: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vec, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return vec / norms

class VectorStore:
    def __init__(self, dim: int = 512, use_cosine: bool = True):
        """
        For cosine similarity, we use IndexFlatIP and L2-normalize vectors
        both when adding and querying, so the returned inner product equals cosine.
        """
        self.dim = dim
        self.use_cosine = use_cosine
        self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
        self.id_map: List[str] = []
        self.wallets = {}

        # Load persisted index/id_map
        if os.path.isfile(FAISS_INDEX_BIN) and os.path.isfile(USERS_JSON):
            try:
                self.index = faiss.read_index(FAISS_INDEX_BIN)
                with open(USERS_JSON, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f).get("id_map", [])
            except Exception:
                self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
                self.id_map = []

        if os.path.isfile(WALLETS_JSON):
            try:
                with open(WALLETS_JSON, "r", encoding="utf-8") as f:
                    self.wallets = json.load(f)
            except Exception:
                self.wallets = {}

        # Diagnostics: ensure correct index type
        # print("FAISS index type:", type(self.index).__name__, "dim:", self.index.d)

    def persist(self):
        faiss.write_index(self.index, FAISS_INDEX_BIN)
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump({"id_map": self.id_map}, f)
        with open(WALLETS_JSON, "w", encoding="utf-8") as f:
            json.dump(self.wallets, f)

    def add_vector(self, user_id: str, embedding: np.ndarray) -> str:
        """
        embedding: raw model output, shape (512,), float32 or convertible.
        We normalize before adding to IndexFlatIP to get cosine similarity.
        Returns a SHA-256 digest of the RAW embedding for audit.
        """
        raw = _ensure_float32_2d(embedding)
        if raw.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {raw.shape[1]}")

        vec = _l2_normalize_rows(raw) if self.use_cosine else raw

        # Optional diagnostics
        # print("Add norm:", float(np.linalg.norm(vec, axis=1)[0]))

        self.index.add(vec)
        self.id_map.append(user_id)
        self.persist()

        digest = hashlib.sha256(embedding.astype("float32", copy=False).tobytes()).hexdigest()
        return digest

    def search(self, query: np.ndarray, k: int = 1) -> Tuple[Optional[str], float]:
        """
        query: raw model output, shape (512,).
        We normalize before search to keep cosine in [-1,1].
        """
        raw = _ensure_float32_2d(query)
        if raw.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {raw.shape[1]}")

        vec = _l2_normalize_rows(raw) if self.use_cosine else raw

        # Optional diagnostics
        # print("Search norm:", float(np.linalg.norm(vec, axis=1)[0]))

        if self.index.ntotal == 0:
            return None, 0.0

        scores, idxs = self.index.search(vec, k)
        top_idx = int(idxs[0][0])
        top_score = float(scores[0][0])
        if top_idx == -1 or top_idx >= len(self.id_map):
            return None, 0.0
        return self.id_map[top_idx], top_score

    def rebuild_index_from_vectors(self, vectors: List[np.ndarray], ids: List[str]):
        """
        Rebuild the index from RAW embeddings if old index had unnormalized vectors.
        """
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have same length")

        self.index = faiss.IndexFlatIP(self.dim) if self.use_cosine else faiss.IndexFlatL2(self.dim)
        self.id_map = []

        if not vectors:
            self.persist()
            return

        arr = np.stack([v.astype("float32", copy=False) for v in vectors], axis=0)
        if self.use_cosine:
            arr = _l2_normalize_rows(arr)

        self.index.add(arr)
        self.id_map.extend(ids)
        self.persist()

    def bind_wallet(self, wallet: str, user_id: str, digest: str, salt: str):
        self.wallets[wallet.lower()] = {
            "user_id": user_id,
            "embedding_digest": digest,
            "salt": salt
        }
        self.persist()

    def get_wallet_record(self, wallet: str):
        return self.wallets.get(wallet.lower())
