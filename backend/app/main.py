import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import numpy as np
from deepface import DeepFace
import cv2

from app.imageParser import imageToString
from app.fileUpload import upload_identity_document
from app.models import EnrollResponse, AuthResponse
from app.face_pipeline import FacePipeline
from app.storage import VectorStore
from app.utils.hashing import build_commitment
from app.blockchain.face_auth.service import set_face_commitment as onchain_set, get_face_commitment as onchain_get
from app.blockchain.identity_docs.service import (
    set_identity_commitment,
    get_identity_commitment,
    verify_identity_commitment
)

load_dotenv()
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.6"))

app = FastAPI(title="Face Auth + Identity Docs + Sepolia Commit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

pipeline = FacePipeline(device="cpu")
store = VectorStore(dim=512, use_cosine=True)

def validate_wallet(addr: str) -> str:
    """Validate Ethereum wallet address format."""
    if not isinstance(addr, str) or not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    return addr.lower()


# ==================== FACE AUTHENTICATION ROUTES ====================

@app.post("/enroll", response_model=EnrollResponse)
async def enroll(wallet: str, image: UploadFile = File(...)):
    """Enroll user with face authentication and commit to blockchain."""
    wallet = validate_wallet(wallet)

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")

    image_bytes = await image.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=422, detail="Invalid image content")
    
    # Liveness check
    liveness_result = pipeline.check_liveness_from_bgr(image_bgr)
    if not liveness_result["is_live"]:
        raise HTTPException(status_code=422, detail="Liveness check failed: Spoof detected")

    # Extract face embedding
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        raise HTTPException(status_code=422, detail="No face detected")

    # Remove old wallet binding if exists
    old_rec = store.get_wallet_record(wallet)
    if old_rec and old_rec.get("user_id"):
        old_uid = old_rec["user_id"]
        store.delete_vector(old_uid)

    # Add new vector
    user_id = str(uuid.uuid4())
    digest = store.add_vector(user_id, emb)

    # Build commitment and write on-chain
    commitment_hash, salt = build_commitment(digest)
    try:
        tx_hash = onchain_set(commitment_hash)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"On-chain commit failed: {str(e)}")

    # Bind wallet to the new user_id
    store.bind_wallet_single(wallet, user_id, digest, salt)

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
    """Authenticate user via face recognition."""
    wallet = validate_wallet(wallet)

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")

    image_bytes = await image.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=422, detail="Invalid image content")

    # Liveness detection
    liveness_result = pipeline.check_liveness_from_bgr(image_bgr)
    if not liveness_result["is_live"]:
        return AuthResponse(
            user_id=None, 
            score=0.0, 
            passed=False, 
            message="Liveness check failed: Spoof detected"
        )

    # Face matching
    emb = pipeline.image_to_embedding(image_bytes)
    if emb is None:
        return AuthResponse(
            user_id=None, 
            score=0.0, 
            passed=False, 
            message="No face detected"
        )

    matched_user, score = store.search(emb, k=1)
    passed = bool(matched_user is not None and score >= SIM_THRESHOLD)
    message = "Authenticated" if passed else "Not matched"

    # Verify wallet binding
    rec = store.get_wallet_record(wallet)
    if rec and passed and rec["user_id"] != matched_user:
        passed = False
        message = "Face matches another enrolled user"

    return AuthResponse(
        user_id=matched_user, 
        score=score, 
        passed=passed, 
        message=message
    )


@app.get("/onchain/{wallet}")
def onchain(wallet: str):
    """Get on-chain face authentication commitment for wallet."""
    try:
        commitment = onchain_get(wallet)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"On-chain read failed: {str(e)}")
    return {"wallet": wallet, "commitment": commitment}


@app.get("/binding/{wallet}")
def binding(wallet: str):
    """Get wallet binding information."""
    wallet = validate_wallet(wallet)
    rec = store.get_wallet_record(wallet)
    if not rec:
        raise HTTPException(status_code=404, detail="No binding")
    return {"wallet": wallet, **rec}


# ==================== IDENTITY DOCUMENT ROUTES ====================

@app.post("/identity/upload")
async def upload_document(
    wallet: str = Form(...),
    document: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Upload identity document (Aadhaar/PAN/DL/Voter ID), 
    extract data via OCR, upload to IPFS, and commit to blockchain.
    
    Args:
        wallet: Ethereum wallet address
        document: Document type (e.g., 'aadhar card', 'Pan Card', etc.)
        image: Uploaded document image
    """
    wallet = validate_wallet(wallet)
    
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG supported")
    
    try:
        # Step 1: Extract document data using OCR
        extracted_data = imageToString(image, document)
        
        if not extracted_data:
            raise HTTPException(status_code=422, detail="Failed to extract data from document")
        
        # Step 2: Upload to IPFS (encrypted)
        ipfs_result = upload_identity_document(
            extracted_data=extracted_data,
            doc_type=document,
            wallet_address=wallet
        )
        
        ipfs_cid = ipfs_result["ipfs_cid"]
        
        # Step 3: Commit IPFS CID hash to blockchain
        blockchain_result = set_identity_commitment(ipfs_cid)
        
        if blockchain_result["success"]:
            return {
                "status": "success",
                "message": "Document processed, uploaded to IPFS, and committed to blockchain",
                "wallet": wallet,
                "document_type": document,
                "extracted_data": extracted_data,
                "ipfs": {
                    "cid": ipfs_cid,
                    "encrypted": True
                },
                "blockchain": {
                    "transaction_hash": blockchain_result["transaction_hash"],
                    "block_number": blockchain_result["block_number"],
                    "gas_used": blockchain_result["gas_used"],
                    "commitment_hash": blockchain_result["commitment_hash"]
                }
            }
        else:
            # Partial success: uploaded to IPFS but blockchain failed
            return {
                "status": "partial_success",
                "message": "Document uploaded to IPFS but blockchain commitment failed",
                "wallet": wallet,
                "extracted_data": extracted_data,
                "ipfs_cid": ipfs_cid,
                "blockchain_error": blockchain_result["error"]
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/identity/verify/{ipfs_cid}")
async def verify_document(ipfs_cid: str):
    """
    Verify if a document's IPFS CID matches the blockchain commitment.
    
    Args:
        ipfs_cid: IPFS Content Identifier to verify
    """
    try:
        is_valid = verify_identity_commitment(ipfs_cid)
        
        return {
            "ipfs_cid": ipfs_cid,
            "verified": is_valid,
            "message": "Document verified on blockchain" if is_valid else "Document not found or tampered",
            "status": "valid" if is_valid else "invalid"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.get("/identity/commitment")
async def get_document_commitment():
    """Get current global document commitment hash from blockchain."""
    try:
        commitment_hash = get_identity_commitment()
        
        return {
            "current_commitment_hash": commitment_hash,
            "message": "Current blockchain commitment retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to retrieve commitment: {str(e)}")


@app.get("/identity/document/{ipfs_cid}")
async def retrieve_document(ipfs_cid: str):
    """
    Retrieve and decrypt document data from IPFS.
    
    Args:
        ipfs_cid: IPFS Content Identifier
    """
    try:
        from app.fileUpload import fetch_json_from_ipfs
        
        document_data = fetch_json_from_ipfs(ipfs_cid)
        
        return {
            "status": "success",
            "ipfs_cid": ipfs_cid,
            "document_data": document_data,
            "message": "Document retrieved and decrypted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


# ==================== LEGACY/DEPRECATED ROUTE ====================

@app.post("/adding/{document}")
async def adding_document_legacy(
    document: str, 
    wallet: str, 
    image: UploadFile = File(...)
):
    """
    DEPRECATED: Use /identity/upload instead.
    Legacy endpoint for backward compatibility.
    """
    return {
        "status": "deprecated",
        "message": "This endpoint is deprecated. Please use POST /identity/upload",
        "new_endpoint": "/identity/upload"
    }


# ==================== UTILITY ROUTES ====================

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Face Auth + Identity Docs",
        "features": [
            "face_authentication",
            "identity_document_ocr",
            "ipfs_storage",
            "blockchain_commitment"
        ]
    }


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "service": "Decentralized Identity System",
        "version": "2.0",
        "endpoints": {
            "face_auth": {
                "enroll": "POST /enroll",
                "authenticate": "POST /auth",
                "check_commitment": "GET /onchain/{wallet}",
                "check_binding": "GET /binding/{wallet}"
            },
            "identity_docs": {
                "upload": "POST /identity/upload",
                "verify": "GET /identity/verify/{ipfs_cid}",
                "get_commitment": "GET /identity/commitment",
                "retrieve": "GET /identity/document/{ipfs_cid}"
            },
            "health": "GET /health"
        }
    }
