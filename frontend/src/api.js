const BACKEND_URL = "http://127.0.0.1:8000"; // Change if backend hosted elsewhere

export async function enroll(wallet, file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${BACKEND_URL}/enroll?wallet=${wallet}`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function auth(wallet, file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${BACKEND_URL}/auth?wallet=${wallet}`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function onchain(wallet) {
  const res = await fetch(`${BACKEND_URL}/onchain/${wallet}`);
  return res.json();
}
