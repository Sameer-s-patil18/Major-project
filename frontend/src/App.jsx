import { useState } from "react";
import ConnectWallet from "./components/ConnectWallet";
import FaceAuth from "./components/FaceAuth";
import EnrollPanel from "./components/EnrollPanel";
import DocumentsPanel from "./components/DocumentsPanel";
import { Wallet } from "lucide-react";

function App() {
  const [wallet, setWallet] = useState(null);
  const [view, setView] = useState("connect"); // "connect" | "auth" | "enroll" | "documents"
  const [authResult, setAuthResult] = useState(null);

  const handleWalletConnected = (address) => {
    setWallet(address);
    setView("auth");
  };

  const handleAuthenticated = (result) => {
    setAuthResult(result);
    setView("documents");
  };

  const handleWantEnroll = () => {
    setView("enroll");
  };

  const handleEnrolled = (result) => {
    console.log("Enrolled:", result);
    setView("auth");
  };

  const handleBackToAuth = () => {
    setView("auth");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <div className="bg-blue-600 w-8 h-8 rounded-lg flex items-center justify-center">
                <Wallet className="w-5 h-5 text-white" />
              </div>
              <span>Face Auth Flow</span>
            </h1>
            {wallet && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Connected:</span> {wallet.slice(0, 6)}...{wallet.slice(-4)}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main>
        {view === "connect" && (
          <div className="flex items-center justify-center min-h-[calc(100vh-80px)] p-6">
            <ConnectWallet onConnected={handleWalletConnected} />
          </div>
        )}
        
        {view === "auth" && (
          <FaceAuth 
            wallet={wallet} 
            onAuthed={handleAuthenticated} 
            onWantEnroll={handleWantEnroll} 
          />
        )}
        
        {view === "enroll" && (
          <EnrollPanel 
            wallet={wallet} 
            onEnrolled={handleEnrolled} 
            onBack={handleBackToAuth} 
          />
        )}
        
        {view === "documents" && <DocumentsPanel wallet = {wallet}/>}
      </main>
    </div>
  );
}

export default App;
