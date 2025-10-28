const BACKEND_URL = "http://127.0.0.1:8000";

// ==================== HELPER FUNCTIONS ====================

async function postImage(url, wallet, blob) {
  const fd = new FormData();
  fd.append("image", blob, "photo.jpg");
  const res = await fetch(`${BACKEND_URL}${url}?wallet=${wallet}`, {
    method: "POST",
    body: fd
  });
  
  if (!res.ok) {
    throw new Error(`Request failed: ${res.statusText}`);
  }
  
  return res.json();
}

async function postDocument(wallet, docType, blob) {
  const fd = new FormData();
  fd.append("wallet", wallet);
  fd.append("document", docType);
  fd.append("image", blob, "document.jpg");
  
  const res = await fetch(`${BACKEND_URL}/identity/upload`, {
    method: "POST",
    body: fd
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Document upload failed");
  }
  
  return res.json();
}

// ==================== FACE AUTHENTICATION APIs ====================

export async function enroll(wallet, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postImage("/enroll", wallet, blob);
}

export async function auth(wallet, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postImage("/auth", wallet, blob);
}

export async function getOnChainCommitment(wallet) {
  const res = await fetch(`${BACKEND_URL}/onchain/${wallet}`);
  
  if (!res.ok) {
    throw new Error(`Failed to get commitment: ${res.statusText}`);
  }
  
  return res.json();
}

export async function getWalletBinding(wallet) {
  const res = await fetch(`${BACKEND_URL}/binding/${wallet}`);
  
  if (!res.ok) {
    throw new Error(`Failed to get binding: ${res.statusText}`);
  }
  
  return res.json();
}

// ==================== IDENTITY DOCUMENT APIs ====================

// ✅ NEW - Updated function
export async function addDocument(wallet, docType, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postDocument(wallet, docType, blob);
}

// ✅ NEW - Additional document APIs
export async function verifyDocument(ipfsCid) {
  const res = await fetch(`${BACKEND_URL}/identity/verify/${ipfsCid}`);
  
  if (!res.ok) {
    throw new Error(`Verification failed: ${res.statusText}`);
  }
  
  return res.json();
}

export async function getDocumentCommitment() {
  const res = await fetch(`${BACKEND_URL}/identity/commitment`);
  
  if (!res.ok) {
    throw new Error(`Failed to get commitment: ${res.statusText}`);
  }
  
  return res.json();
}

export async function retrieveDocument(ipfsCid) {
  const res = await fetch(`${BACKEND_URL}/identity/document/${ipfsCid}`);
  
  if (!res.ok) {
    throw new Error(`Failed to retrieve document: ${res.statusText}`);
  }
  
  return res.json();
}

// ==================== UTILITY APIs ====================

export async function checkHealth() {
  const res = await fetch(`${BACKEND_URL}/health`);
  
  if (!res.ok) {
    throw new Error("Health check failed");
  }
  
  return res.json();
}
