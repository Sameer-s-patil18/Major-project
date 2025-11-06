import { FileText, Shield, CheckCircle, Download, Eye, X, Loader2, ExternalLink, RefreshCw, Mail } from "lucide-react";
import { useState, useEffect } from "react";
import { addDocument, getWalletDocuments, getDocumentData, requestEmailOTP, verifyEmailOTP } from "../api";

export default function DocumentsPanel({ wallet }) {
  const [addDoc, setAddDoc] = useState(false);
  const [viewDoc, setViewDoc] = useState(false);
  const [docType, setDocType] = useState("");
  const [msg, setMsg] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  // ✅ NEW: Document viewing state
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [viewingDocData, setViewingDocData] = useState(null);

  // MFA state
  const [otpModal, setOtpModal] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpVerified, setOtpVerified] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);


  // ✅ NEW: Load documents when view modal opens
  useEffect(() => {
    if (viewDoc && wallet) {
      loadDocuments();
    }
  }, [viewDoc, wallet]);

  const loadDocuments = async () => {
  setLoadingDocs(true);
  try {
    const response = await getWalletDocuments(wallet);
    const allDocs = response.documents || [];

    // ✅ Normalize & filter documents
    const filteredDocs = allDocs
      .map((d) => ({
        document_type: d.document_type?.toLowerCase() || d.type?.toLowerCase(),
        ipfs_cid: d.ipfs_cid || d.ipfs,
        transaction_hash: d.transaction_hash || d.tx_hash || null,
        block_number: d.block_number || d.block,
        timestamp: d.timestamp || d.created_at,
      }))
      .filter(
        (doc) =>
          doc.document_type !== "verified_email" &&
          doc.transaction_hash // only keep docs that have TX hash
      );

    setDocuments(filteredDocs);
  } catch (err) {
    console.error("Error loading documents:", err);
    setDocuments([]);
    setError(true);
    setMsg(`Failed to load documents: ${err.message}`);
  } finally {
    setLoadingDocs(false);
  }
};


  const viewDocumentData = async (ipfsCid, docType) => {
    setLoadingDocs(true);
    setSelectedDoc(ipfsCid);

    try {
      const response = await getDocumentData(ipfsCid);

      // ✅ handle both shapes: wrapped or direct
      const data = response.document_data || response;

      if (!data) throw new Error("Empty document data response");

      setViewingDocData({
        ...data,
        ipfs_cid: ipfsCid,
        doc_type: docType,
      });
    } catch (err) {
      console.error("❌ Error viewing document:", err);
      alert(`Failed to load document: ${err.message}`);
      setSelectedDoc(null);
    } finally {
      setLoadingDocs(false);
    }
  };


async function addDocu() {
  // Validation
  if (!docType) return setMsg("Please select a document type");
  if (!file) return setMsg("Please select a file to upload");
  if (!wallet) return setMsg("Please connect your wallet first");

  if (!otpVerified) {
    setOtpModal(true);
    return; // block upload until OTP verified
  }

  setLoading(true);
  setMsg(null);
  setError(false);

  try {
    const response = await addDocument(wallet, docType, file);
    console.log("✅ Upload response:", response);

    if (response.status === "success") {
      setUploadResult(response);
      alert(`✅ Document uploaded successfully!\n\nCID: ${response.ipfs.cid}`);
      setAddDoc(false);
      setFile(null);
      setDocType("");
      setOtpVerified(false); // reset MFA after successful upload
    } else {
      throw new Error(response.message || "Upload failed");
    }
  } catch (err) {
    console.error("❌ Upload error:", err);
    setError(true);
    setMsg(err.message);
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
                onClick={() => {setViewDoc(!viewDoc); setAddDoc(false); setViewingDocData(null);}}
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

        {/* 🔐 OTP MFA Modal */}
        {otpModal && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md relative">
              <button
                onClick={() => {
                  setOtpModal(false);
                  setOtp("");
                  setOtpSent(false);
                }}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>

              <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verification</h2>
              <p className="text-gray-600 mb-6 text-sm">
                Verify the OTP sent to your registered email to continue.
              </p>

              {!otpSent ? (
                <button
                  onClick={async () => {
                    setSendingOtp(true);
                    try {
                      await requestEmailOTP(wallet);
                      setOtpSent(true);
                      alert("✅ OTP sent to your verified email!");
                    } catch (err) {
                      alert("❌ Failed to send OTP: " + err.message);
                    } finally {
                      setSendingOtp(false);
                    }
                  }}
                  disabled={sendingOtp}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg flex items-center justify-center space-x-2"
                >
                  {sendingOtp ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Mail className="w-5 h-5" />
                  )}
                  <span>{sendingOtp ? "Sending..." : "Send OTP"}</span>
                </button>
              ) : (
                <>
                  <input
                    type="text"
                    placeholder="Enter OTP"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="border border-gray-300 rounded-lg p-2 w-full mb-4"
                  />
                  <button
                    onClick={async () => {
                      setVerifyingOtp(true);
                      try {
                        await verifyEmailOTP(wallet, otp);
                        setOtpVerified(true);
                        setOtpModal(false);
                        alert("✅ OTP verified successfully!");
                      } catch (err) {
                        alert("❌ Invalid OTP: " + err.message);
                      } finally {
                        setVerifyingOtp(false);
                      }
                    }}
                    disabled={verifyingOtp}
                    className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg flex items-center justify-center space-x-2"
                  >
                    {verifyingOtp ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <CheckCircle className="w-5 h-5" />
                    )}
                    <span>{verifyingOtp ? "Verifying..." : "Verify OTP"}</span>
                  </button>
                </>
              )}
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

        {otpVerified && (
            <div className="flex items-center text-green-600 text-sm mb-3">
              <CheckCircle className="w-4 h-4 mr-1" /> MFA Verified
            </div>
          )}


        {/* ✅ UPDATED: View Documents Modal with Full Functionality */}
        {viewDoc && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto relative">
              <button
                onClick={() => {
                  setViewDoc(false);
                  setViewingDocData(null);
                  setSelectedDoc(null);
                }}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 z-10"
              >
                <X className="w-6 h-6" />
              </button>

              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Your Documents</h2>
                  <p className="text-gray-600 mt-1">
                    Wallet: {wallet?.slice(0, 6)}...{wallet?.slice(-4)}
                  </p>
                </div>
                <button
                  onClick={loadDocuments}
                  className="flex items-center space-x-2 bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-lg transition-colors"
                  disabled={loadingDocs}
                >
                  <RefreshCw className={`w-4 h-4 ${loadingDocs ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>

              {loadingDocs && !viewingDocData ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  <span className="ml-3 text-gray-600">Loading documents...</span>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600 mb-2 font-semibold">No documents found</p>
                  <p className="text-sm text-gray-500">Upload your first document to get started!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {documents.map((doc, index) => (
                    <div
                      key={index}
                      className={`border rounded-lg p-4 transition-all ${
                        selectedDoc === doc.ipfs_cid
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:shadow-md'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-3">
                            <FileText className="w-5 h-5 text-blue-600" />
                            <h3 className="font-semibold text-gray-900 capitalize">
                              {doc.document_type}
                            </h3>
                          </div>
                          
                          <div className="text-sm text-gray-600 space-y-1.5">
                            <p>
                              <strong className="text-gray-700">Uploaded:</strong>{" "}
                              {new Date(doc.timestamp).toLocaleString('en-IN', { 
                                dateStyle: 'medium', 
                                timeStyle: 'short' 
                              })}
                            </p>
                            <p className="break-all">
                              <strong className="text-gray-700">IPFS CID:</strong>{" "}
                              <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">
                                {doc.ipfs_cid}
                              </code>
                            </p>
                            <p className="break-all">
                              <strong className="text-gray-700">TX Hash:</strong>{" "}
                              {doc.transaction_hash ? (
                                <a
                                  href={`https://sepolia.etherscan.io/tx/0x${doc.transaction_hash}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline inline-flex items-center"
                                >
                                  {doc.transaction_hash.slice(0, 10)}...
                                  {doc.transaction_hash.slice(-8)}
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              ) : (
                                <span className="text-gray-500 italic">Not available</span>
                              )}
                            </p>
                            <p>
                              <strong className="text-gray-700">Block:</strong> {doc.block_number}
                            </p>
                          </div>
                        </div>

                        <button
                          onClick={() => viewDocumentData(doc.ipfs_cid, doc.document_type)}
                          disabled={loadingDocs && selectedDoc === doc.ipfs_cid}
                          className="ml-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-colors"
                        >
                          {loadingDocs && selectedDoc === doc.ipfs_cid ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Loading...</span>
                            </>
                          ) : (
                            <>
                              <Eye className="w-4 h-4" />
                              <span>View Data</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ✅ NEW: Document Data Viewer */}
              {viewingDocData && (
                <div className="mt-6 border-t-2 pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900">
                      📄 Document Details
                    </h3>
                    <button
                      onClick={() => {
                        setViewingDocData(null);
                        setSelectedDoc(null);
                      }}
                      className="text-gray-500 hover:text-gray-700 text-sm font-medium"
                    >
                      Close Details
                    </button>
                  </div>
                  
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5 space-y-5">
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-blue-600" />
                        Document Type
                      </h4>
                      <p className="text-gray-900 capitalize font-medium">
                        {viewingDocData.document_type}
                      </p>
                    </div>

                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                        Extracted Data
                      </h4>
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <pre className="text-sm text-gray-900 whitespace-pre-wrap font-mono">
                        {viewingDocData?.extracted_data
                          ? JSON.stringify(viewingDocData.extracted_data, null, 2)
                          : "No extracted data available."}
                      </pre>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Shield className="w-4 h-4 mr-2 text-purple-600" />
                        Metadata
                      </h4>
                      <div className="text-sm space-y-2">
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                          <span className="text-gray-600 font-medium">Timestamp:</span>
                          <span className="text-gray-900">
                            {new Date(viewingDocData.timestamp).toLocaleString('en-IN', {
                              dateStyle: 'full',
                              timeStyle: 'short'
                            })}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                          <span className="text-gray-600 font-medium">Version:</span>
                          <span className="text-gray-900">{viewingDocData.version}</span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span className="text-gray-600 font-medium">Encryption:</span>
                          <span className={viewingDocData.encrypted ? "text-green-600 font-semibold" : "text-red-600"}>
                            {viewingDocData.encrypted ? "✅ Encrypted" : "❌ Not encrypted"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
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
