from web3 import Web3
from .client import w3, contract, account

SEPOLIA_CHAIN_ID = 11155111

def set_commitment(commitment_hex: str) -> str:
    """Send transaction to set commitment on Sepolia."""
    # Use pending nonce to handle consecutive txs
    nonce = w3.eth.get_transaction_count(account.address, "pending")

    # Dynamic EIP-1559 fee estimation
    base_fee = w3.eth.gas_price                       # current base fee
    priority_fee = w3.to_wei(2, "gwei")               # tip (bump if network busy)
    max_fee = int(base_fee * 3 + priority_fee)        # cushion x3

    # Build transaction
    txn = contract.functions.setCommitment(
        Web3.to_bytes(hexstr=commitment_hex)
    ).build_transaction({
        "chainId": SEPOLIA_CHAIN_ID,
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,                                # safe gas limit
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee,
    })

    # Sign locally
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.key)

    # Send raw transaction (snake_case in current web3.py)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # Wait longer for mining, with polling
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2)

    return receipt.transactionHash.hex()


def get_commitment(wallet_address: str) -> str:
    """Read commitment from the contract for the given wallet."""
    value = contract.functions.getCommitment(Web3.to_checksum_address(wallet_address)).call()
    return value.hex()
