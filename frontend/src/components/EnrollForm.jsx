import { useState } from "react";
import { enroll } from "../api";

export default function EnrollForm({ wallet }) {
  const [result, setResult] = useState(null);

  const handleEnroll = async (e) => {
    e.preventDefault();
    const file = e.target.elements.image.files[0];
    if (!file) return alert("Please select an image.");
    const res = await enroll(wallet, file);
    setResult(res);
  };

  return (
    <div>
      <h2>Enroll</h2>
      <form onSubmit={handleEnroll}>
        <input type="file" name="image" accept="image/*" />
        <button type="submit">Enroll</button>
      </form>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
