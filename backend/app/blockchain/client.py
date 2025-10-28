import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Shared Web3 connection
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise RuntimeError("Web3 not connected – check RPC URL")

account = w3.eth.account.from_key(PRIVATE_KEY)

print(f"✅ Web3 connected. Using wallet: {account.address}")
