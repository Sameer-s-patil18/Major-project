import { useState } from 'react';

function Enroll() {
  const [file, setFile] = useState(null);
  const [res, setRes] = useState(null);

  const submit = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append('image', file);
    const r = await fetch('http://127.0.0.1:8000/enroll', {
      method: 'POST',
      body: fd
    });
    const data = await r.json();
    setRes(data);
  };

  return (
    <div>
      <h2>Enroll</h2>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={submit} disabled={!file}>Submit</button>
      <pre>{res && JSON.stringify(res, null, 2)}</pre>
    </div>
  );
}

function Auth() {
  const [file, setFile] = useState(null);
  const [res, setRes] = useState(null);

  const submit = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append('image', file);
    const r = await fetch('http://127.0.0.1:8000/auth', {
      method: 'POST',
      body: fd
    });
    const data = await r.json();
    setRes(data);
  };

  return (
    <div>
      <h2>Auth</h2>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={submit} disabled={!file}>Submit</button>
      <pre>{res && JSON.stringify(res, null, 2)}</pre>
    </div>
  );
}

export default function App() {
  return (
    <div style={{ padding: 16, fontFamily: 'Arial' }}>
      <h1>Face Auth Frontend</h1>
      <Enroll />
      <hr />
      <Auth />
    </div>
  );
}
