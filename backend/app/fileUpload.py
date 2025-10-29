import ipfshttpclient
import io
from fastapi.responses import StreamingResponse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import zipfile
from dotenv import load_dotenv
import json

# Encryption key should be 16, 24, or 32 bytes long (AES-128, AES-192, AES-256)
# Store and manage this securely!
# AES_KEY = os.urandom(32) 

# print(AES_KEY) # For example purpose, generate a random key
load_dotenv()

ipfs_client = ipfshttpclient.connect()

AES_KEY = os.getenv("AES_KEY")

def encrypt_file(data: bytes) -> bytes:
    aesgcm = AESGCM(AES_KEY)
    nonce = os.urandom(12)  # 96-bit nonce
    encrypted = aesgcm.encrypt(nonce, data, None)
    return nonce + encrypted  # prepend nonce for decryption

def decrypt_file(data: bytes) -> bytes:
    aesgcm = AESGCM(AES_KEY)
    nonce = data[:12]
    encrypted = data[12:]
    decrypted = aesgcm.decrypt(nonce, encrypted, None)
    return decrypted

def fetch_json_from_ipfs(cid: str) -> dict:
    file_bytes = ipfs_client.cat(cid)
    decrypted_bytes = decrypt_file(file_bytes)
    json_str = decrypted_bytes.decode('utf-8')
    return json.loads(json_str)

def upload_json_to_ipfs(data: dict) -> str:
    import io
    json_bytes = json.dumps(data).encode("utf-8")
    encrypted_bytes = encrypt_file(json_bytes)
    filelike = io.BytesIO(encrypted_bytes)
    res = ipfs_client.add(filelike, pin=True)
    return res["Hash"]

{
# def encrypt_file(data: bytes) -> bytes:
#     aesgcm = AESGCM(AES_KEY)
#     nonce = os.urandom(12)  # 96-bit nonce
#     encrypted = aesgcm.encrypt(nonce, data, None)
#     return nonce + encrypted  # prepend nonce for decryption

# def decrypt_file(data: bytes) -> bytes:
#     aesgcm = AESGCM(AES_KEY)
#     nonce = data[:12]
#     encrypted = data[12:]
#     decrypted = aesgcm.decrypt(nonce, encrypted, None)
#     return decrypted


# def uploadImageIPFS(image):
#     client = ipfshttpclient.connect()
#     fileBytes = image.file.read()
#     encrypted_bytes = encrypt_file(fileBytes)   # Encrypt before uploading

#     res = client.add_bytes(encrypted_bytes)
#     return res


# def fileRetrieve(cidLis):
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
#         client = ipfshttpclient.connect()
#         for cid in cidLis:
#             try:
#                 content = client.cat(cid)
#                 decrypted_content = decrypt_file(content)  # Decrypt after retrieval
#                 zip_file.writestr(cid, decrypted_content)
#             except Exception as e:
#                 zip_file.writestr(f"{cid}_ERROR.txt", str(e))
#     zip_buffer.seek(0)
#     return StreamingResponse(zip_buffer, media_type='application/zip', headers={
#         "Content-Disposition": "attachment; filename=ipfs_files.zip"
#     })


# def DeleteFile(cid):
#     client = ipfshttpclient.connect()
#     try:
#         client.pin.rm(cid)
#         client.repo.gc()
#         return {"message": f"Unpinned and garbage collected CID {cid} successfully."}
#     except Exception as e:
#         return {"error": str(e)}
}