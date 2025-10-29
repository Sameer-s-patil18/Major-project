import json
import os
from web3 import Web3
from ..client import w3, account

FACE_AUTH_CONTRACT_ADDRESS = os.getenv("FACE_AUTH_CONTRACT_ADDRESS")
SEPOLIA_CHAIN_ID = 11155111

# Load ABI
with open("app/blockchain/face_auth/abi.json", "r", encoding="utf-8") as f:
    ABI = json.load(f)

face_auth_contract = w3.eth.contract(
    address=Web3.to_checksum_address(FACE_AUTH_CONTRACT_ADDRESS),
    abi=ABI
)

def set_face_commitment(commitment_hex: str) -> str:
    """Set face authentication commitment."""
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    
    base_fee = w3.eth.gas_price
    priority_fee = w3.to_wei(2, "gwei")
    max_fee = int(base_fee * 3 + priority_fee)
    
    txn = face_auth_contract.functions.setCommitment(
        Web3.to_bytes(hexstr=commitment_hex)
    ).build_transaction({
        "chainId": SEPOLIA_CHAIN_ID,
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee,
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2)
    
    return receipt.transactionHash.hex()

def get_face_commitment(wallet_address: str) -> str:
    """Read face commitment from contract."""
    value = face_auth_contract.functions.getCommitment(
        Web3.to_checksum_address(wallet_address)
    ).call()
    return value.hex()
