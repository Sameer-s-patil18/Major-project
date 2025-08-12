import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.models import EnrollResponse, AuthResponse
from app.face_pipeline import FacePipeline
from app.storage import VectorStore
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()  
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.6"))

app = FastAPI(title="Local Face Auth MVP (MTCNN + FaceNet)")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
pipeline = FacePipeline(device="cpu")
store = VectorStore(dim=512, use_cosine=True)

@app.post("/enroll", response_model=EnrollResponse)
async def enroll(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")
    image_bytes = await image.read()
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        raise HTTPException(status_code=422, detail="No face detected")
    user_id = str(uuid.uuid4())
    digest = store.add_vector(user_id, emb)
    return EnrollResponse(user_id=user_id, embedding_digest=digest, message="Enrollment successful")

@app.post("/auth", response_model=AuthResponse)
async def auth(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")
    image_bytes = await image.read()
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        return AuthResponse(user_id=None, score=0.0, passed=False, message="No face detected")
    matched_user, score = store.search(emb, k=1)
    passed = bool(matched_user is not None and score >= SIM_THRESHOLD)
    message = "Authenticated" if passed else "Not matched"
    return AuthResponse(user_id=matched_user, score=score, passed=passed, message=message)

@app.get("/health")
def health():
    return {"status": "ok"}
