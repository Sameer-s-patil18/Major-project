import { useState } from "react";
import { auth } from "../api";

export default function AuthForm({ wallet }) {
  const [result, setResult] = useState(null);

  const handleAuth = async (e) => {
    e.preventDefault();
    const file = e.target.elements.image.files[0];
    if (!file) return alert("Please select an image.");
    const res = await auth(wallet, file);
    setResult(res);
  };

  return (
    <div>
      <h2>Authenticate</h2>
      <form onSubmit={handleAuth}>
        <input type="file" name="image" accept="image/*" />
        <button type="submit">Auth</button>
      </form>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
