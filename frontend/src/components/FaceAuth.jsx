import { useState } from "react";
import { auth } from "../api";
import CameraCapture from "./CameraCapture";
import { FileText, Camera, ArrowLeft, CheckCircle, XCircle, AlertTriangle, UserX } from "lucide-react";

export default function FaceAuth({ wallet, onAuthed, onWantEnroll }) {
  const [result, setResult] = useState(null);
  const [mode, setMode] = useState("file");
  const [busy, setBusy] = useState(false);

  const doAuth = async (blob) => {
    setBusy(true);
    try {
      const res = await auth(wallet, blob);
      setResult(res);
      if (res?.passed) {
        onAuthed(res);
      }
    } finally {
      setBusy(false);
    }
  };

  const onFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    await doAuth(f);
  };

  const getAuthMessage = (result) => {
    if (!result) return null;

    if (result.passed) {
      return {
        type: "success",
        title: "Authentication Successful!",
        message: "Your identity has been verified successfully. Welcome back!",
        icon: CheckCircle,
        color: "green"
      };
    }

    const message = result.message?.toLowerCase() || "";
    
    if (message.includes("not matched") || message.includes("no match")) {
      return {
        type: "error",
        title: "Face Not Recognized",
        message: "The face in your image doesn't match our records. Please try again or re-enroll your face.",
        icon: UserX,
        color: "red"
      };
    }
    
    if (message.includes("no face") || message.includes("face not found")) {
      return {
        type: "warning",
        title: "No Face Detected",
        message: "We couldn't detect a face in your image. Please make sure your face is clearly visible and try again.",
        icon: AlertTriangle,
        color: "orange"
      };
    }
    
    if (message.includes("multiple faces")) {
      return {
        type: "warning",
        title: "Multiple Faces Detected",
        message: "We detected multiple faces in your image. Please ensure only your face is visible and try again.",
        icon: AlertTriangle,
        color: "orange"
      };
    }
    
    if (message.includes("not enrolled")) {
      return {
        type: "warning",
        title: "Face Not Enrolled",
        message: "Your face is not enrolled in our system. Please enroll your face first to enable authentication.",
        icon: AlertTriangle,
        color: "orange"
      };
    }

    return {
      type: "error",
      title: "Authentication Failed",
      message: "We couldn't verify your identity. Please check your image and try again.",
      icon: XCircle,
      color: "red"
    };
  };

  const authMessage = getAuthMessage(result);

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Face Authentication</h2>
        <p className="text-gray-600">Choose your preferred authentication method</p>
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
            <span>Upload File</span>
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
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors duration-200">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-lg font-medium text-gray-700 hover:text-blue-600">
              Click to upload an image
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

      {mode === "camera" && <CameraCapture onCapture={doAuth} auto={true} />}

      {busy && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying your identity...</p>
        </div>
      )}

      {authMessage && (
        <div className={`mt-8 p-6 rounded-xl border-2 ${
          authMessage.color === 'green' 
            ? "bg-green-50 border-green-200" 
            : authMessage.color === 'orange'
            ? "bg-orange-50 border-orange-200"
            : "bg-red-50 border-red-200"
        }`}>
          <div className="flex items-start space-x-4">
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
              authMessage.color === 'green' 
                ? "bg-green-100" 
                : authMessage.color === 'orange'
                ? "bg-orange-100"
                : "bg-red-100"
            }`}>
              <authMessage.icon className={`w-6 h-6 ${
                authMessage.color === 'green' 
                  ? "text-green-600" 
                  : authMessage.color === 'orange'
                  ? "text-orange-600"
                  : "text-red-600"
              }`} />
            </div>
            <div className="flex-1">
              <h3 className={`text-lg font-semibold mb-2 ${
                authMessage.color === 'green' 
                  ? "text-green-800" 
                  : authMessage.color === 'orange'
                  ? "text-orange-800"
                  : "text-red-800"
              }`}>
                {authMessage.title}
              </h3>
              <p className={`${
                authMessage.color === 'green' 
                  ? "text-green-700" 
                  : authMessage.color === 'orange'
                  ? "text-orange-700"
                  : "text-red-700"
              }`}>
                {authMessage.message}
              </p>
              
              {!result?.passed && (
                <div className="flex flex-col sm:flex-row gap-3 mt-4">
                  <button 
                    onClick={() => setResult(null)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 text-sm"
                  >
                    Try Again
                  </button>
                  <button 
                    onClick={onWantEnroll}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 text-sm"
                  >
                    Re-enroll Face
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!result && (
        <div className="flex justify-center space-x-4 mt-8">
          <button 
            onClick={onWantEnroll}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Enroll / Re-enroll</span>
          </button>
        </div>
      )}
    </div>
  );
}
