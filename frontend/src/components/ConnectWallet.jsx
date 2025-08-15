import { useState } from "react";

export default function ConnectWallet({ onConnected }) {
  const [address, setAddress] = useState(null);

  const connect = async () => {
    if (window.ethereum) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const addr = accounts[0];
        setAddress(addr);
        onConnected(addr);

        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        if (chainId !== "0xaa36a7") {
          alert("Please switch MetaMask to Sepolia network.");
        }
      } catch (e) {
        alert("Connection failed: " + e.message);
      }
    } else {
      alert("MetaMask is not installed.");
    }
  };

  return (
    <div>
      <button onClick={connect}>Connect Wallet</button>
      <p>Wallet: {address || "Not connected"}</p>
    </div>
  );
}
