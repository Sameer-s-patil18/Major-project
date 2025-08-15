import json
import os
import hashlib
from typing import Optional, Tuple, List, Dict

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
        self.dim = dim
        self.use_cosine = use_cosine
        self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
        self.id_map: List[str] = []
        self.wallets: Dict[str, Dict[str, str]] = {}
        self._uid_to_idx: Dict[str, int] = {}  # user_id -> index in id_map

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

        # Build reverse map
        for i, uid in enumerate(self.id_map):
            self._uid_to_idx[uid] = i

    def persist(self):
        faiss.write_index(self.index, FAISS_INDEX_BIN)
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump({"id_map": self.id_map}, f)
        with open(WALLETS_JSON, "w", encoding="utf-8") as f:
            json.dump(self.wallets, f)

    def _rebuild_index_from_arrays(self, vectors: np.ndarray, ids: List[str]):
        """Internal: rebuild index from normalized float32 vectors and aligned ids."""
        self.index = faiss.IndexFlatIP(self.dim) if self.use_cosine else faiss.IndexFlatL2(self.dim)
        if vectors.size:
            self.index.add(vectors)
        self.id_map = ids[:]
        # Rebuild reverse map
        self._uid_to_idx = {uid: i for i, uid in enumerate(self.id_map)}
        self.persist()

    def delete_vector(self, user_id: str) -> bool:
        if user_id not in self._uid_to_idx:
            return False
        idx_to_remove = self._uid_to_idx[user_id]

        nt = self.index.ntotal
        if nt == 0:
            return False

        # Reconstruct each vector (IndexFlat supports reconstruct)
        kept_vecs = []
        kept_ids = []
        for i in range(nt):
            if i == idx_to_remove:
                continue
            v = self.index.reconstruct(i)           # returns np.ndarray shape (dim,)
            kept_vecs.append(v.astype('float32', copy=False))
            kept_ids.append(self.id_map[i])

        if kept_vecs:
            arr = np.stack(kept_vecs, axis=0)       # (N-1, dim)
        else:
            arr = np.zeros((0, self.dim), dtype='float32')

        # Rebuild index with the kept vectors
        self._rebuild_index_from_arrays(arr, kept_ids)
        return True

    def add_vector(self, user_id: str, embedding: np.ndarray) -> str:
        raw = _ensure_float32_2d(embedding)
        if raw.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {raw.shape}")

        vec = _l2_normalize_rows(raw) if self.use_cosine else raw

        # Add to index
        self.index.add(vec)
        self.id_map.append(user_id)
        self._uid_to_idx[user_id] = len(self.id_map) - 1
        self.persist()

        digest = hashlib.sha256(embedding.astype("float32", copy=False).tobytes()).hexdigest()
        return digest

    def search(self, query: np.ndarray, k: int = 1) -> Tuple[Optional[str], float]:
        raw = _ensure_float32_2d(query)
        if raw.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {raw.shape}")

        vec = _l2_normalize_rows(raw) if self.use_cosine else raw

        if self.index.ntotal == 0:
            return None, 0.0

        scores, idxs = self.index.search(vec, k)
        top_idx = int(idxs)
        top_score = float(scores)
        if top_idx == -1 or top_idx >= len(self.id_map):
            return None, 0.0
        return self.id_map[top_idx], top_score

    def bind_wallet_single(self, wallet: str, user_id: str, digest: str, salt: str):
        """Bind wallet to exactly one user_id. Overwrites previous binding."""
        self.wallets[wallet.lower()] = {
            "user_id": user_id,
            "embedding_digest": digest,
            "salt": salt
        }
        self.persist()

    def get_wallet_record(self, wallet: str):
        return self.wallets.get(wallet.lower())

    def get_user_ids_for_wallet(self, wallet: str) -> List[str]:
        rec = self.get_wallet_record(wallet)
        return [rec["user_id"]] if rec and "user_id" in rec else []
