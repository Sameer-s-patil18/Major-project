import { useState } from "react";
import { Mail, CheckCircle, Send, Loader2 } from "lucide-react";
import { sendEmailVerification, verifyEmailToken } from "../api";

export default function EmailVerifyStep({ wallet, onVerified }) {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [step, setStep] = useState("enter"); // enter | verify
  const [loading, setLoading] = useState(false);
  const [verified, setVerified] = useState(false);

  const handleSendVerification = async () => {
    if (!email) return alert("Please enter an email address.");
    setLoading(true);
    try {
      await sendEmailVerification(wallet, email);
      setStep("verify");
      alert("✅ Verification code sent to your email!");
    } catch (err) {
      alert("Error sending verification email: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async () => {
    if (!token) return alert("Enter the verification code sent to your email.");
    setLoading(true);
    try {
      await verifyEmailToken(wallet, email, token);
      setVerified(true);
      alert("✅ Email verified successfully!");
      onVerified?.(email); // pass verified email upward
    } catch (err) {
      alert("Verification failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (verified) {
    return (
      <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
        <h3 className="text-green-800 font-semibold">Email Verified</h3>
        <p className="text-green-700 text-sm mt-1">
          You can now use MFA for uploads and document access.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-10 max-w-md mx-auto bg-white shadow rounded-xl p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Mail className="w-5 h-5" /> Verify your email
      </h2>

      {step === "enter" && (
        <>
          <input
            type="email"
            placeholder="Enter your email"
            className="border p-2 rounded w-full mb-4"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            onClick={handleSendVerification}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white w-full py-2 rounded flex justify-center items-center gap-2"
          >
            {loading ? (
              <Loader2 className="animate-spin w-4 h-4" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Send Verification Code
          </button>
        </>
      )}

      {step === "verify" && (
        <>
          <input
            placeholder="Enter verification code"
            className="border p-2 rounded w-full mb-4"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <button
            onClick={handleVerifyEmail}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white w-full py-2 rounded flex justify-center items-center gap-2"
          >
            {loading ? (
              <Loader2 className="animate-spin w-4 h-4" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            Verify Email
          </button>
        </>
      )}
    </div>
  );
}
