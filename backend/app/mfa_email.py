import secrets
import time
import hashlib
import smtplib
from email.message import EmailMessage
from datetime import datetime
from fastapi import HTTPException
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from dotenv import load_dotenv
from app.document_storage import doc_store

load_dotenv()

# ==================== CONFIG ====================
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("GMAIL")
SMTP_PASS = os.getenv("MAIL_PASSWORD")  # use Gmail app password or provider API key
AES_KEY = bytes.fromhex(os.getenv("AES_KEY"))
OTP_TTL_SECONDS = 300  # 5 minutes
AESGCM_KEY = AESGCM(AES_KEY)

# In-memory OTP store: {wallet: {otp_hash, salt, expires_at}}
OTP_CACHE = {}

# ==================== HELPERS ====================
def encrypt_str(data: str) -> str:
    nonce = os.urandom(12)
    ct = AESGCM_KEY.encrypt(nonce, data.encode(), None)
    return (nonce + ct).hex()

def decrypt_str(enc_hex: str) -> str:
    raw = bytes.fromhex(enc_hex)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM_KEY.decrypt(nonce, ct, None).decode()

def send_email(to: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def _hash_otp(otp: str, salt: str):
    return hashlib.sha256(f"{salt}:{otp}".encode()).hexdigest()

# ==================== ENROLL FLOW ====================
def send_verification_email(wallet: str, email: str):
    """Send verification email on enrollment and store only encrypted email."""
    wallet = wallet.lower()
    token = secrets.token_urlsafe(16)
    salt = secrets.token_hex(8)
    token_hash = _hash_otp(token, salt)
    expires = int(time.time()) + OTP_TTL_SECONDS

    # Temporarily keep the token only in memory
    OTP_CACHE[wallet] = {"otp_hash": token_hash, "salt": salt, "expires_at": expires}

    try:
        send_email(
            to=email,
            subject="Verify your email address",
            body=f"Your verification code is: {token}\n\nValid for 5 minutes."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send verification email: {str(e)}")

    return {"status": "sent", "wallet": wallet, "email": email}


def verify_enrollment_email(wallet: str, email: str, token: str):
    """Verify email during enrollment and store encrypted email permanently."""
    wallet = wallet.lower()
    if wallet not in OTP_CACHE:
        raise HTTPException(status_code=400, detail="No verification pending")

    rec = OTP_CACHE[wallet]
    if int(time.time()) > rec["expires_at"]:
        OTP_CACHE.pop(wallet, None)
        raise HTTPException(status_code=400, detail="Verification token expired")

    if _hash_otp(token, rec["salt"]) == rec["otp_hash"]:
        # store encrypted email off-chain
        enc_email = encrypt_str(email)
        record = {
            "doc_type": "verified_email",
            "email_enc": enc_email,
            "created_at": datetime.utcnow().isoformat()
        }
        doc_store.add_document(wallet, record)
        OTP_CACHE.pop(wallet, None)
        return True
    else:
        raise HTTPException(status_code=400, detail="Invalid verification token")

# ==================== OTP FOR EVERY ACTION ====================
def send_action_otp(wallet: str):
    """Send a new OTP to the stored verified email every time."""
    wallet = wallet.lower()
    records = doc_store.get_documents(wallet)
    email_rec = next((r for r in records if r.get("doc_type") == "verified_email"), None)

    if not email_rec:
        raise HTTPException(status_code=403, detail="No verified email for this wallet")

    email = decrypt_str(email_rec["email_enc"])

    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    salt = secrets.token_hex(8)
    otp_hash = _hash_otp(otp, salt)
    expires = int(time.time()) + OTP_TTL_SECONDS

    # store temporarily in memory
    OTP_CACHE[wallet] = {"otp_hash": otp_hash, "salt": salt, "expires_at": expires}

    try:
        send_email(
            to=email,
            subject="Your Verification Code",
            body=f"Your one-time verification code is: {otp}\nValid for 5 minutes."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"status": "sent", "wallet": wallet, "email": email, "expires_in": OTP_TTL_SECONDS}


def verify_action_otp(wallet: str, otp: str):
    """Verify OTP for an action. Does not persist."""
    wallet = wallet.lower()
    if wallet not in OTP_CACHE:
        raise HTTPException(status_code=400, detail="No OTP pending")

    rec = OTP_CACHE[wallet]
    if int(time.time()) > rec["expires_at"]:
        OTP_CACHE.pop(wallet, None)
        raise HTTPException(status_code=400, detail="OTP expired")

    if _hash_otp(otp, rec["salt"]) == rec["otp_hash"]:
        OTP_CACHE.pop(wallet, None)
        return True
    raise HTTPException(status_code=400, detail="Invalid OTP")
