# 🔐 Decentralized Identity & Document Management System

A blockchain-based identity verification system combining **face authentication**, **OCR document extraction**, **IPFS storage**, and **Ethereum smart contracts** for secure, decentralized identity management.

---

## 📝 About

This system allows users to:
- Authenticate using **face recognition** with liveness detection
- Upload and extract data from identity documents (Aadhaar, PAN, Driver's License, Voter ID)
- Store encrypted documents on **IPFS** (decentralized storage)
- Commit document proofs to **Ethereum blockchain** for verification
- Retrieve and verify documents linked to their wallet address

**Key Feature**: Sensitive data is encrypted and stored on IPFS, only hash commitments go on-chain for privacy and cost efficiency.

---

## 🛠️ Tech Stack

### Frontend
- React + Vite
- TailwindCSS
- MetaMask (Web3 wallet)

### Backend
- FastAPI (Python)
- DeepFace + FAISS (Face recognition)
- EasyOCR (Document OCR)
- OpenCV (Image processing)
- Web3.py (Blockchain interaction)
- AES-GCM encryption

### Blockchain & Storage
- Solidity smart contracts
- Ethereum Sepolia testnet
- IPFS (decentralized storage)

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- IPFS Desktop or CLI
- MetaMask browser extension
- Sepolia testnet ETH

### 1. Clone Repository

```
git clone https://github.com/yourusername/decentralized-identity-system.git
cd decentralized-identity-system
```

### 2. Backend Setup

```
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file in `backend/` directory:

```
RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_metamask_private_key
CONTRACT_ADDRESS=0xYourFaceAuthContractAddress
IDENTITY_DOC_CONTRACT_ADDRESS=0xYourDocContractAddress
AES_KEY=generate_32_byte_hex_key_here
SIM_THRESHOLD=0.6
```

Generate AES key:
```
python -c "import os; print(os.urandom(32).hex())"
```

### 3. Frontend Setup

```
cd frontend
npm install
```

### 4. Install and Start IPFS

**Option A - IPFS Desktop (Recommended)**:
1. Download from [https://docs.ipfs.tech/install/ipfs-desktop/](https://docs.ipfs.tech/install/ipfs-desktop/)
2. Install and start the application

**Option B - Command Line**:

macOS:
```
brew install ipfs
ipfs init
ipfs daemon
```

Linux:
```
wget https://dist.ipfs.tech/kubo/v0.29.0/kubo_v0.29.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.29.0_linux-amd64.tar.gz
cd kubo && sudo bash install.sh
ipfs init
ipfs daemon
```

### 5. Deploy Smart Contracts

1. Open [Remix IDE](https://remix.ethereum.org)
2. Create two Solidity files (0.8.19):
   - `FaceAuthCommitment.sol`
   - `IdentityDocumentCommitment.sol`
3. Connect MetaMask to Sepolia network
4. Deploy both contracts
5. Copy deployed addresses to your `.env` file

### 6. Run Application

**Terminal 1 - Backend:**
```
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```
cd frontend
npm run dev
```

**Terminal 3 - IPFS (if not using Desktop):**
```
ipfs daemon
```

Access the application at [**http://localhost:5173**](http://localhost:5173)

---

## 📖 Usage

1. **Connect Wallet**: Click "Connect Wallet" and approve MetaMask connection
2. **Enroll Face**: Register your face biometrics (creates blockchain commitment)
3. **Authenticate**: Verify your identity using face recognition
4. **Upload Document**: 
   - Select document type (Aadhaar, PAN, etc.)
   - Upload clear image
   - OCR extracts data → Encrypts → Uploads to IPFS → Commits hash to blockchain
5. **View Documents**: Browse, decrypt, and verify your stored documents

---

## 📂 Project Structure

```
decentralized-identity-system/
├── backend/
│   ├── app/
│   │   ├── blockchain/          # Smart contract interaction
│   │   ├── face_pipeline.py     # Face recognition logic
│   │   ├── imageParser.py       # OCR extraction
│   │   ├── fileUpload.py        # IPFS operations
│   │   ├── document_storage.py  # Document indexing
│   │   └── main.py              # FastAPI routes
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentsPanel.jsx
│   │   │   ├── FaceAuth.jsx
│   │   │   └── ConnectWallet.jsx
│   │   ├── api.js               # Backend API calls
│   │   └── App.jsx
│   └── package.json
└── contracts/                    # Solidity smart contracts
```

---

## 📜 License

MIT License

---

## 🙏 Credits

- **DeepFace** for face recognition
- **EasyOCR** for OCR capabilities
- **IPFS** for decentralized storage
- **Ethereum** for blockchain infrastructure
---
```

