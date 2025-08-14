import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import numpy as np

from app.models import EnrollResponse, AuthResponse
from app.face_pipeline import FacePipeline
from app.storage import VectorStore
from app.utils.hashing import build_commitment
from app.blockchain.service import set_commitment as onchain_set, get_commitment as onchain_get

load_dotenv()
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.6"))

app = FastAPI(title="Face Auth + Sepolia Commit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

pipeline = FacePipeline(device="cpu")
store = VectorStore(dim=512, use_cosine=True)

@app.post("/enroll", response_model=EnrollResponse)
async def enroll(wallet: str, image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")

    image_bytes = await image.read()
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        raise HTTPException(status_code=422, detail="No face detected")

    # Optional: check raw norm (not required to be 1)
    # print("Raw embed norm (enroll):", float(np.linalg.norm(emb)))

    user_id = str(uuid.uuid4())
    digest = store.add_vector(user_id, emb)

    commitment_hash, salt = build_commitment(digest)
    try:
        tx_hash = onchain_set(commitment_hash)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"On-chain commit failed: {str(e)}")

    store.bind_wallet(wallet, user_id, digest, salt)

    return EnrollResponse(
        user_id=user_id,
        embedding_digest=digest,
        commitment_hash=commitment_hash,
        salt=salt,
        tx_hash=tx_hash,
        message="Enrollment successful and on-chain commitment written"
    )

@app.post("/auth", response_model=AuthResponse)
async def auth(wallet: str, image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")

    image_bytes = await image.read()
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        return AuthResponse(user_id=None, score=0.0, passed=False, message="No face detected")

    # Optional: check raw norm
    # print("Raw embed norm (auth):", float(np.linalg.norm(emb)))

    matched_user, score = store.search(emb, k=1)

    passed = bool(matched_user is not None and score >= SIM_THRESHOLD)
    message = "Authenticated" if passed else "Not matched"

    rec = store.get_wallet_record(wallet)
    if rec and passed and rec["user_id"] != matched_user:
        passed = False
        message = "Face matches another enrolled user"

    # Optional: ensure score is within [-1,1] if cosine is active
    # print("Score (cosine):", score)

    return AuthResponse(user_id=matched_user, score=score, passed=passed, message=message)

@app.get("/onchain/{wallet}")
def onchain(wallet: str):
    try:
        commitment = onchain_get(wallet)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"On-chain read failed: {str(e)}")
    return {"wallet": wallet, "commitment": commitment}

@app.get("/health")
def health():
    return {"status": "ok"}
