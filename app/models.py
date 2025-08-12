from pydantic import BaseModel

class EnrollResponse(BaseModel):
    user_id: str
    embedding_digest: str
    message: str

class AuthResponse(BaseModel):
    user_id: str | None
    score: float
    passed: bool
    message: str
