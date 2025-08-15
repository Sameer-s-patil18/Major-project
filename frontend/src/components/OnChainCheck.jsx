import { useState } from "react";
import { onchain } from "../api";

export default function OnchainCheck({ wallet }) {
  const [result, setResult] = useState(null);

  const check = async () => {
    const res = await onchain(wallet);
    setResult(res);
  };

  return (
    <div>
      <h2>Check On-chain Commitment</h2>
      <button onClick={check}>Check</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
