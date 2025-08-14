import json
import os
import hashlib
from typing import Optional, Tuple
import faiss
import numpy as np

DATA_DIR = "data"
USERS_JSON = os.path.join(DATA_DIR, "users.json")
FAISS_INDEX_BIN = os.path.join(DATA_DIR, "faiss_index.bin")
WALLETS_JSON = os.path.join(DATA_DIR, "wallets.json")

os.makedirs(DATA_DIR, exist_ok=True)

class VectorStore:
    def __init__(self, dim: int = 512, use_cosine: bool = True):
        self.dim = dim
        self.use_cosine = use_cosine
        self.index = faiss.IndexFlatIP(dim) if use_cosine else faiss.IndexFlatL2(dim)
        self.id_map: list[str] = []
        self.wallets = {}

        if os.path.isfile(FAISS_INDEX_BIN) and os.path.isfile(USERS_JSON):
            try:
                self.index = faiss.read_index(FAISS_INDEX_BIN)
                with open(USERS_JSON, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f).get("id_map", [])
            except:
                pass

        if os.path.isfile(WALLETS_JSON):
            try:
                with open(WALLETS_JSON, "r", encoding="utf-8") as f:
                    self.wallets = json.load(f)
            except:
                pass

    def persist(self):
        faiss.write_index(self.index, FAISS_INDEX_BIN)
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump({"id_map": self.id_map}, f)
        with open(WALLETS_JSON, "w", encoding="utf-8") as f:
            json.dump(self.wallets, f)

    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vec, axis=1, keepdims=True) + 1e-12
        return vec / norms

    def add_vector(self, user_id: str, embedding: np.ndarray) -> str:
        vec = embedding.reshape(1, -1).astype("float32")
        if self.use_cosine:
            vec = self._l2_normalize(vec)
        self.index.add(vec)
        self.id_map.append(user_id)
        self.persist()
        return hashlib.sha256(embedding.tobytes()).hexdigest()

    def search(self, query: np.ndarray, k: int = 1) -> Tuple[Optional[str], float]:
        vec = query.reshape(1, -1).astype("float32")
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

    def bind_wallet(self, wallet: str, user_id: str, digest: str, salt: str):
        self.wallets[wallet.lower()] = {
            "user_id": user_id,
            "embedding_digest": digest,
            "salt": salt
        }
        self.persist()

    def get_wallet_record(self, wallet: str):
        return self.wallets.get(wallet.lower())
