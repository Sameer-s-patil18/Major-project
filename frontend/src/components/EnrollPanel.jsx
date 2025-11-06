import { useState } from "react";
import { enroll } from "../api";
import CameraCapture from "./CameraCapture";
import { FileText, Camera, ArrowLeft, CheckCircle, XCircle, Upload } from "lucide-react";
import EmailVerifyStep from "./EmailVerifyStep";

export default function EnrollPanel({ wallet, onEnrolled, onBack }) {
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);

  const doEnroll = async (blob) => {
    setBusy(true);
    try {
      const out = await enroll(wallet, blob);
      setRes(out);
      // onEnrolled?.(out);
    } finally {
      setBusy(false);
    }
  };

  const handleEmailVerified = () => {
    setEmailVerified(true);
    onEnrolled?.(res);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Enroll / Re-enroll</h2>
        <p className="text-gray-600">Register your face for authentication</p>
      </div>

      <CameraCapture onCapture={doEnroll} auto={false} />

      {busy && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Enrolling your face...</p>
        </div>
      )}

      {res && (
        <div className={`mt-8 p-6 rounded-xl border-2 ${
          res.tx_hash 
            ? "bg-green-50 border-green-200" 
            : "bg-red-50 border-red-200"
        }`}>
          <div className="flex items-center space-x-3 mb-3">
            {res.tx_hash ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600" />
            )}
            <h3 className={`text-lg font-semibold ${
              res.tx_hash ? "text-green-800" : "text-red-800"
            }`}>
              {res.tx_hash ? "Enrollment Successful!" : "Enrollment Failed"}
            </h3>
          </div>
          <pre className={`text-sm p-3 rounded border overflow-auto ${
            res.tx_hash 
              ? "bg-white/50 text-green-800" 
              : "bg-white/50 text-red-800"
          }`}>
            {JSON.stringify(res, null, 2)}
          </pre>
        </div>
      )}

       {/* Email step after face enroll */}
      {res?.tx_hash && !emailVerified && (
        <EmailVerifyStep wallet={wallet} onVerified={handleEmailVerified} />
      )}

      <div className="flex justify-center mt-8">
        <button 
          onClick={onBack}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Auth</span>
        </button>
      </div>
    </div>
  );
}
