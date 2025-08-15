import { useState } from "react";
import ConnectWallet from "./components/ConnectWallet";
import EnrollForm from "./components/EnrollForm";
import AuthForm from "./components/AuthForm";
import OnchainCheck from "./components/OnchainCheck";

export default function App() {
  const [wallet, setWallet] = useState(null);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Face Auth + Sepolia Commitment (Phase 1)</h1>
      <ConnectWallet onConnected={setWallet} />
      {wallet && (
        <>
          <EnrollForm wallet={wallet} />
          <AuthForm wallet={wallet} />
          <OnchainCheck wallet={wallet} />
        </>
      )}
    </div>
  );
}
