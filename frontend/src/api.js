const BACKEND_URL = "http://127.0.0.1:8000";

async function postImage(url, wallet, blob) {
  const fd = new FormData();
  fd.append("image", blob, "photo.jpg");
  const res = await fetch(`${BACKEND_URL}${url}?wallet=${wallet}`, {
    method: "POST",
    body: fd
  });
  return res.json();
}

export async function enroll(wallet, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postImage("/enroll", wallet, blob);
}

export async function auth(wallet, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postImage("/auth", wallet, blob);
}

export async function addDocument(wallet, docType, fileOrBlob) {
  const blob = fileOrBlob instanceof Blob ? fileOrBlob : fileOrBlob;
  return postImage(`/adding/${docType}`, wallet, blob);
}
