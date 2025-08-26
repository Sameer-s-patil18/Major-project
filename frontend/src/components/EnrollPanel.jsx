import { useState } from "react";
import { enroll } from "../api";
import CameraCapture from "./CameraCapture";
import { FileText, Camera, ArrowLeft, CheckCircle, XCircle, Upload } from "lucide-react";

export default function EnrollPanel({ wallet, onEnrolled, onBack }) {
  const [mode, setMode] = useState("file");
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);

  const doEnroll = async (blob) => {
    setBusy(true);
    try {
      const out = await enroll(wallet, blob);
      setRes(out);
      onEnrolled?.(out);
    } finally {
      setBusy(false);
    }
  };

  const onFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    await doEnroll(f);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Enroll / Re-enroll</h2>
        <p className="text-gray-600">Register your face for authentication</p>
      </div>

      <div className="flex justify-center mb-8">
        <div className="bg-gray-100 p-1 rounded-xl flex space-x-1">
          <button 
            onClick={() => setMode("file")}
            className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
              mode === "file" 
                ? "bg-white text-blue-600 shadow-sm" 
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Use File</span>
          </button>
          <button 
            onClick={() => setMode("camera")}
            className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
              mode === "camera" 
                ? "bg-white text-blue-600 shadow-sm" 
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <Camera className="w-4 h-4" />
            <span>Use Camera</span>
          </button>
        </div>
      </div>

      {mode === "file" && (
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors duration-200 mb-6">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-lg font-medium text-gray-700 hover:text-blue-600">
              Click to upload your photo
            </span>
            <input 
              type="file" 
              accept="image/*" 
              onChange={onFile}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-500 mt-2">PNG, JPG, GIF up to 10MB</p>
        </div>
      )}

      {mode === "camera" && <CameraCapture onCapture={doEnroll} auto={true} />}

      {busy && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Enrolling your face...</p>
        </div>
      )}

      {res && (
        <div className={`mt-8 p-6 rounded-xl border-2 ${
          res.success 
            ? "bg-green-50 border-green-200" 
            : "bg-red-50 border-red-200"
        }`}>
          <div className="flex items-center space-x-3 mb-3">
            {res.success ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600" />
            )}
            <h3 className={`text-lg font-semibold ${
              res.success ? "text-green-800" : "text-red-800"
            }`}>
              {res.success ? "Enrollment Successful!" : "Enrollment Failed"}
            </h3>
          </div>
          <pre className={`text-sm p-3 rounded border overflow-auto ${
            res.success 
              ? "bg-white/50 text-green-800" 
              : "bg-white/50 text-red-800"
          }`}>
            {JSON.stringify(res, null, 2)}
          </pre>
        </div>
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
