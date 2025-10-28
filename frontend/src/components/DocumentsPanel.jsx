import { FileText, Shield, CheckCircle, Download, Eye, X, Loader2 } from "lucide-react";
import { useState } from "react";
import { addDocument } from "../api";

export default function DocumentsPanel({ wallet }) {
  const [addDoc, setAddDoc] = useState(false);
  const [viewDoc, setViewDoc] = useState(false);
  const [docType, setDocType] = useState("");
  const [msg, setMsg] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const getDocs = async () => {};

  async function addDocu() {
    // Validation
    if (!docType) {
      setError(true);
      return setMsg("Please select a document type");
    }
    if (!file) {
      setError(true);
      return setMsg("Please select a file to upload");
    }
    if (!wallet) {
      setError(true);
      return setMsg("Please connect your wallet first");
    }

    setLoading(true);
    setMsg(null);
    setError(false);

    try {
      const response = await addDocument(wallet, docType, file);
      
      console.log("✅ Upload response:", response);

      // Handle new response structure
      if (response.status === "success") {
        setUploadResult(response);
        setMsg(null);
        setError(false);
        
        // Success notification
        alert(`✅ Document uploaded successfully!\n\nIPFS CID: ${response.ipfs.cid}\n\nTransaction Hash: ${response.blockchain.transaction_hash}`);
        
        // Reset form
        setAddDoc(false);
        setFile(null);
        setDocType("");
      } else if (response.status === "partial_success") {
        setError(true);
        setMsg(`Partial success: ${response.message}`);
      } else {
        setError(true);
        setMsg("Upload failed. Please try again.");
      }
    } catch (err) {
      console.error("❌ Upload error:", err);
      setError(true);
      
      // Better error messages
      if (err.message.includes("IPFS")) {
        setMsg("IPFS upload error. Make sure IPFS daemon is running.");
      } else if (err.message.includes("blockchain")) {
        setMsg("Blockchain commit failed. Check your wallet and network.");
      } else if (err.message.includes("Invalid image")) {
        setMsg("Please upload a clear, close-up image of the document.");
      } else {
        setMsg(`Upload failed: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <div className="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Authentication Successful!
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Welcome back! You have been successfully authenticated.
          </p>
          <div className="bg-blue-50 text-blue-800 px-4 py-2 rounded-full inline-block text-sm font-medium">
            <Shield className="w-4 h-4 inline mr-2" />
            Secure Access Granted
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <FileText className="w-8 h-8 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Your Documents</h2>
          </div>
          
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Document Access Available
            </h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Your authenticated access allows you to view, upload, and manage your secure documents.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2"
                onClick={() => {setViewDoc(!viewDoc); setAddDoc(false);}}
              >
                <Eye className="w-5 h-5" />
                <span>View Documents</span>
              </button>
              <button 
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2"
                onClick={() => {setAddDoc(!addDoc); setViewDoc(false);}}  
              >
                <Download className="w-5 h-5" />
                <span>Upload New</span>
              </button>
            </div>
          </div>
        </div>

        {/* Upload Modal */}
        {addDoc && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md relative">
              <button
                onClick={() => {
                  setAddDoc(false);
                  setFile(null);
                  setDocType("");
                  setMsg(null);
                }}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
                disabled={loading}
              >
                <X className="w-6 h-6" />
              </button>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Document</h2>
              <p className="text-gray-600 mb-4">Choose a document to upload securely to IPFS and blockchain.</p>
              
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="mb-4 w-full border border-gray-300 rounded-lg p-2 bg-white"
                required
                disabled={loading}
              >
                <option value="">Select Document Type</option>
                <option value="aadhar card">Aadhaar Card</option>
                <option value="Pan Card">PAN Card</option>
                <option value="Driver's License">Driver's License</option>
                <option value="Voter ID">Voter ID</option>
                <option value="Passport">Passport</option>
              </select>

              <input
                type="file"
                accept="image/jpeg,image/png"
                className="mb-4 w-full border border-gray-300 rounded-lg p-2"
                onChange={(e) => setFile(e.target.files[0])}
                disabled={loading}
              />

              {file && (
                <div className="mb-4 text-sm text-gray-600">
                  Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                </div>
              )}

              <button
                onClick={addDocu}
                disabled={loading || !file || !docType}
                className={`w-full py-2 rounded-lg font-medium transition-all flex items-center justify-center space-x-2
                  ${loading || !file || !docType
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    <span>Upload to IPFS & Blockchain</span>
                  </>
                )}
              </button>

              {msg && !error && (
                <div className="mt-4 p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">
                  {msg}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Modal */}
        {error && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md relative">
              <button
                onClick={() => {
                  setError(false);
                  setMsg(null);
                }}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>

              <div className="text-center">
                <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="w-8 h-8 text-red-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Failed</h2>
                {msg && (
                  <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
                    {msg}
                  </div>
                )}
                <button
                  onClick={() => {
                    setError(false);
                    setMsg(null);
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Success Modal */}
        {uploadResult && !error && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg relative max-h-[80vh] overflow-y-auto">
              <button
                onClick={() => setUploadResult(null)}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>

              <div className="text-center mb-6">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Successful!</h2>
                <p className="text-gray-600">Your document has been securely stored</p>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">Extracted Data</h3>
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(uploadResult.extracted_data, null, 2)}
                  </pre>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">IPFS Storage</h3>
                  <p className="text-sm text-gray-700 break-all">
                    <strong>CID:</strong> {uploadResult.ipfs.cid}
                  </p>
                  <p className="text-sm text-green-600 mt-2">✓ Encrypted</p>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">Blockchain Commitment</h3>
                  <p className="text-sm text-gray-700 break-all mb-1">
                    <strong>TX Hash:</strong> {uploadResult.blockchain.transaction_hash}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Block:</strong> {uploadResult.blockchain.block_number}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Gas Used:</strong> {uploadResult.blockchain.gas_used}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setUploadResult(null)}
                className="w-full mt-6 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg"
              >
                Done
              </button>
            </div>
          </div>
        )}

        {/* View Documents Modal */}
        {viewDoc && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg relative">
              <button
                onClick={() => setViewDoc(false)}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Your Documents
              </h2>
              <p className="text-gray-600 mb-4">
                Documents stored for wallet: {wallet?.slice(0, 6)}...{wallet?.slice(-4)}
              </p>
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>Document retrieval feature coming soon!</p>
              </div>
            </div>
          </div>
        )}

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Secure Storage</h3>
            <p className="text-gray-600 text-sm">Your documents are encrypted and stored on IPFS</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">OCR Extraction</h3>
            <p className="text-gray-600 text-sm">Automatic data extraction from your documents</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Blockchain Verified</h3>
            <p className="text-gray-600 text-sm">Immutable commitment on Ethereum Sepolia</p>
          </div>
        </div>
      </div>
    </div>
  );
}
