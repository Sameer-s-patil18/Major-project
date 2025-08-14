from pydantic import BaseModel

class EnrollResponse(BaseModel):
    user_id: str
    embedding_digest: str
    commitment_hash: str
    salt: str
    tx_hash: str
    message: str

class AuthResponse(BaseModel):
    user_id: str | None
    score: float
    passed: bool
    message: str
