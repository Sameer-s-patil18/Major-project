import json
import os
from web3 import Web3
from ..client import w3, account

IDENTITY_DOC_CONTRACT_ADDRESS = os.getenv("IDENTITY_DOC_CONTRACT_ADDRESS")
SEPOLIA_CHAIN_ID = 11155111

# Load ABI for GlobalIdentityCommitment contract
IDENTITY_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "_commitment", "type": "bytes32"}],
        "name": "setGlobalCommitment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getGlobalCommitment",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    }
]

identity_contract = w3.eth.contract(
    address=Web3.to_checksum_address(IDENTITY_DOC_CONTRACT_ADDRESS),
    abi=IDENTITY_ABI
)

def set_identity_commitment(ipfs_cid: str) -> dict:
    """Store IPFS CID hash on blockchain."""
    try:
        # Convert CID to bytes32
        commitment_hash = w3.keccak(text=ipfs_cid)
        
        nonce = w3.eth.get_transaction_count(account.address, "pending")
        
        base_fee = w3.eth.gas_price
        priority_fee = w3.to_wei(2, "gwei")
        max_fee = int(base_fee * 3 + priority_fee)
        
        txn = identity_contract.functions.setGlobalCommitment(
            commitment_hash
        ).build_transaction({
            "chainId": SEPOLIA_CHAIN_ID,
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        })
        
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2)
        
        return {
            "success": True,
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt['blockNumber'],
            "gas_used": receipt['gasUsed'],
            "ipfs_cid": ipfs_cid,
            "commitment_hash": commitment_hash.hex()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_identity_commitment() -> str:
    """Retrieve current commitment hash from blockchain."""
    try:
        commitment_hash = identity_contract.functions.getGlobalCommitment().call()
        return commitment_hash.hex()
    except Exception as e:
        return f"Error: {str(e)}"

def verify_identity_commitment(ipfs_cid: str) -> bool:
    """Verify if IPFS CID matches blockchain commitment."""
    try:
        current_hash = identity_contract.functions.getGlobalCommitment().call()
        cid_hash = w3.keccak(text=ipfs_cid)
        return current_hash == cid_hash
    except Exception as e:
        print(f"Verification error: {e}")
        return False
