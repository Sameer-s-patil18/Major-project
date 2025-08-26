import { useState } from "react";
import { Wallet, Shield, Zap, CheckCircle, AlertCircle } from "lucide-react";

async function ensureSepolia() {
  const CHAIN_ID = "0xaa36a7"; 
  try {
    const cid = await window.ethereum.request({ method: "eth_chainId" });
    if (cid === CHAIN_ID) return;
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: CHAIN_ID }],
    });
  } catch (err) {
    if (err?.code === 4902) {
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [{
          chainId: CHAIN_ID,
          chainName: "Sepolia Test Network",
          nativeCurrency: { name: "SepoliaETH", symbol: "SEP", decimals: 18 },
          rpcUrls: ["https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY"],
          blockExplorerUrls: ["https://sepolia.etherscan.io"],
        }],
      });
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: CHAIN_ID }],
      });
    } else {
      throw err;
    }
  }
}

export default function ConnectWallet({ onConnected }) {
  const [address, setAddress] = useState(null);
  const [status, setStatus] = useState("idle"); 

  const connect = async () => {
    if (!window.ethereum) {
      alert("MetaMask not installed. Please install MetaMask to continue.");
      return;
    }
    
    try {
      setStatus("connecting");
      const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
      const addr = accounts[0]; 
      await ensureSepolia();
      setAddress(addr);
      onConnected(addr);
      setStatus("connected");
    } catch (e) {
      console.error(e);
      alert("Connection failed: " + (e?.message || e));
      setStatus("error");
    }
  };

  return (
    <div className="max-w-md w-full mx-auto">
      <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
        <div className="bg-gradient-to-br from-blue-500 to-purple-600 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
          <Wallet className="w-10 h-10 text-white" />
        </div>

        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Connect Your Wallet
        </h2>
        <p className="text-gray-600 mb-8">
          Connect with MetaMask to access your secure face authentication system
        </p>

        {status === "idle" && (
          <button
            onClick={connect}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center space-x-3 mb-6"
          >
            <Wallet className="w-5 h-5" />
            <span>Connect MetaMask</span>
          </button>
        )}

        {status === "connecting" && (
          <div className="mb-6">
            <button
              disabled
              className="w-full bg-gray-400 text-white font-semibold py-4 px-6 rounded-xl flex items-center justify-center space-x-3 mb-4"
            >
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Connecting...</span>
            </button>
            <p className="text-sm text-gray-500">Please check MetaMask popup</p>
          </div>
        )}

        {status === "connected" && (
          <div className="mb-6">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-800">Connected Successfully!</span>
              </div>
              <p className="text-sm text-green-700">
                Wallet: {address?.slice(0, 6)}...{address?.slice(-4)}
              </p>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-center space-x-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="font-semibold text-red-800">Connection Failed</span>
              </div>
            </div>
            <button
              onClick={connect}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
            >
              Try Again
            </button>
          </div>
        )}

        {!address && (
          <div className="bg-gray-50 rounded-xl p-4 mb-6">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Status:</span> Not connected
            </p>
          </div>
        )}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-4">
        <div className="bg-white/50 backdrop-blur-sm rounded-xl p-4 flex items-center space-x-3">
          <div className="bg-blue-100 w-10 h-10 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">Secure Authentication</h3>
            <p className="text-xs text-gray-600">Blockchain-verified face recognition</p>
          </div>
        </div>

        <div className="bg-white/50 backdrop-blur-sm rounded-xl p-4 flex items-center space-x-3">
          <div className="bg-purple-100 w-10 h-10 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">Fast & Seamless</h3>
            <p className="text-xs text-gray-600">Quick access to your documents</p>
          </div>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500">
          Connected to <span className="font-medium text-blue-600">Sepolia Test Network</span>
        </p>
      </div>

      {!window.ethereum && (
        <div className="mt-6 bg-orange-50 border border-orange-200 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="w-5 h-5 text-orange-600" />
            <span className="font-semibold text-orange-800">MetaMask Required</span>
          </div>
          <p className="text-sm text-orange-700 mb-3">
            Please install MetaMask to use this application.
          </p>
          <a
            href="https://metamask.io/download/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-orange-600 hover:bg-orange-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors duration-200"
          >
            Install MetaMask
          </a>
        </div>
      )}
    </div>
  );
}
