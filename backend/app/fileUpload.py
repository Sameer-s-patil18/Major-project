import subprocess
import io
import logging
from fastapi.responses import StreamingResponse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import os
import zipfile
from dotenv import load_dotenv
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
AES_KEY = bytes.fromhex(os.getenv("AES_KEY"))

# Validate AES key length (must be 16, 24, or 32 bytes)
if len(AES_KEY) not in [16, 24, 32]:
    raise ValueError("AES_KEY must be 16, 24, or 32 bytes (128, 192, or 256 bits)")


def encrypt_file(data: bytes) -> bytes:
    """
    Encrypt data using AES-GCM.
    """
    try:
        aesgcm = AESGCM(AES_KEY)
        nonce = os.urandom(12)
        encrypted = aesgcm.encrypt(nonce, data, None)
        return nonce + encrypted
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise RuntimeError(f"Encryption error: {str(e)}")


def decrypt_file(data: bytes) -> bytes:
    """
    Decrypt AES-GCM encrypted data.
    """
    if len(data) < 13:
        raise ValueError("Encrypted data is too short")
    
    try:
        aesgcm = AESGCM(AES_KEY)
        nonce = data[:12]
        encrypted = data[12:]
        decrypted = aesgcm.decrypt(nonce, encrypted, None)
        return decrypted
    except InvalidTag:
        logger.error("Decryption failed: Authentication tag verification failed")
        raise ValueError("Decryption failed: Data may be corrupted or tampered")
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise RuntimeError(f"Decryption error: {str(e)}")


def upload_json_to_ipfs(data: dict) -> str:
    """
    Upload JSON data to IPFS (encrypted).
    """
    try:
        # Convert dict to JSON string, then to bytes
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        encrypted_bytes = encrypt_file(json_bytes)
        
        # Upload to IPFS
        result = subprocess.run(
            ['ipfs', 'add', '-Q', '--pin=true'],
            input=encrypted_bytes,
            capture_output=True,
            check=True,
            timeout=30
        )
        
        # ✅ FIX: Decode bytes to string
        cid = result.stdout.decode('utf-8').strip()
        
        if not cid:
            raise RuntimeError("IPFS returned empty CID")
        
        logger.info(f"Successfully uploaded to IPFS: {cid}")
        return cid
        
    except subprocess.CalledProcessError as e:
        # ✅ FIX: Properly decode stderr if it exists
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        logger.error(f"IPFS upload failed: {error_msg}")
        raise RuntimeError(f"IPFS upload failed: {error_msg}")
    except subprocess.TimeoutExpired:
        logger.error("IPFS upload timed out")
        raise RuntimeError("IPFS upload timed out after 30 seconds")
    except FileNotFoundError:
        logger.error("IPFS command not found. Is IPFS installed and in PATH?")
        raise RuntimeError("IPFS not installed or not in system PATH")
    except Exception as e:
        logger.error(f"Unexpected error during IPFS upload: {str(e)}")
        raise RuntimeError(f"IPFS upload error: {str(e)}")


def fetch_json_from_ipfs(cid: str) -> dict:
    """
    Fetch and decrypt JSON data from IPFS.
    """
    if not cid or not isinstance(cid, str):
        raise ValueError("Invalid CID provided")
    
    try:
        result = subprocess.run(
            ['ipfs', 'cat', cid],
            capture_output=True,
            check=True,
            timeout=60
        )
        
        # ✅ FIX: result.stdout is already bytes, no need to decode
        file_bytes = result.stdout
        
        if not file_bytes:
            raise ValueError(f"No data retrieved for CID: {cid}")
        
        # Decrypt the bytes
        decrypted_bytes = decrypt_file(file_bytes)
        
        # ✅ FIX: Now decode to string
        json_str = decrypted_bytes.decode('utf-8')
        
        # Parse JSON
        data = json.loads(json_str)
        logger.info(f"Successfully fetched and decrypted data from IPFS: {cid}")
        return data
        
    except subprocess.CalledProcessError as e:
        # ✅ FIX: Properly decode stderr
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        logger.error(f"IPFS fetch failed for CID {cid}: {error_msg}")
        raise RuntimeError(f"IPFS fetch failed: {error_msg}")
    except subprocess.TimeoutExpired:
        logger.error(f"IPFS fetch timed out for CID: {cid}")
        raise RuntimeError("IPFS fetch timed out")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON data from IPFS CID {cid}: {str(e)}")
        raise ValueError("Retrieved data is not valid JSON")
    except ValueError as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching from IPFS: {str(e)}")
        raise RuntimeError(f"IPFS fetch error: {str(e)}")


def upload_identity_document(
    extracted_data: dict, 
    doc_type: str, 
    wallet_address: str = None
) -> dict:
    """
    Upload extracted identity document data to IPFS with metadata.
    """
    if not extracted_data or not isinstance(extracted_data, dict):
        raise ValueError("Invalid extracted_data: must be a non-empty dictionary")
    
    if not doc_type or not isinstance(doc_type, str):
        raise ValueError("Invalid doc_type: must be a non-empty string")
    
    try:
        # Create structured metadata
        metadata = {
            "document_type": doc_type.lower(),
            "extracted_data": extracted_data,
            "timestamp": datetime.now().isoformat(),
            "wallet_address": wallet_address.lower() if wallet_address else None,
            "version": "1.0",
            "encrypted": True
        }
        
        # Upload to IPFS
        ipfs_cid = upload_json_to_ipfs(metadata)
        
        logger.info(f"Document uploaded: type={doc_type}, wallet={wallet_address}, CID={ipfs_cid}")
        
        return {
            "ipfs_cid": ipfs_cid,
            "metadata": metadata,
            "encrypted": True
        }
        
    except Exception as e:
        logger.error(f"Failed to upload identity document: {str(e)}")
        raise


def verify_ipfs_daemon() -> bool:
    """
    Check if IPFS daemon is running.
    """
    try:
        result = subprocess.run(
            ['ipfs', 'id'],
            capture_output=True,
            timeout=5,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Optional: Run verification on module import
if not verify_ipfs_daemon():
    logger.warning("⚠️  IPFS daemon may not be running. Start it with 'ipfs daemon'")
else:
    logger.info("✅ IPFS daemon is running")
