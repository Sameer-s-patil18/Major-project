import os
import json
from web3 import Web3

def build_commitment(embedding_digest: str):
    salt = os.urandom(16).hex()
    payload = {
        "embeddingDigest": embedding_digest,
        "salt": salt
    }
    canonical = json.dumps(payload, sort_keys=True).encode()
    commitment = Web3.keccak(canonical).hex()
    return commitment, salt
