import { useEffect, useRef, useState } from "react";
import { Camera, RotateCcw, X } from "lucide-react";

export default function CameraCapture({
  onCapture,
  facingMode = "user",
  auto = true,
  autoDelayMs = 3000,
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState("");
  const [autoStatus, setAutoStatus] = useState("idle");
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    let active = true;
    let timeoutId = null;
    let intervalId = null;

    async function init() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode },
          audio: false,
        });
        if (!active) return;
        
        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play();
        }

        if (!auto) return;

        setAutoStatus("countdown");
        let secondsLeft = Math.ceil(autoDelayMs / 1000);
        setCountdown(secondsLeft);

        intervalId = setInterval(() => {
          secondsLeft -= 1;
          setCountdown(secondsLeft);
          if (secondsLeft <= 0) {
            clearInterval(intervalId);
          }
        }, 1000);

        timeoutId = setTimeout(() => {
          if (!active) return;
          setAutoStatus("capturing");
          capturePhoto();
        }, autoDelayMs);

      } catch (e) {
        console.error("Camera error:", e);
        setError(e?.message || "Camera access denied");
      }
    }

    function capturePhoto() {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;

      const w = video.videoWidth || video.clientWidth;
      const h = video.videoHeight || video.clientHeight;
      
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, w, h);
      
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop());
          streamRef.current = null;
        }
        
        try {
          await onCapture(blob);
        } catch (e) {
          console.error("onCapture error:", e);
          setError("Failed to process image");
        }
      }, "image/jpeg", 0.92);
    }

    init();

    return () => {
      active = false;
      if (timeoutId) clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, [facingMode, auto, autoDelayMs, onCapture]);

  const takePhoto = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    
    const w = video.videoWidth || video.clientWidth;
    const h = video.videoHeight || video.clientHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);
    
    const blob = await new Promise(resolve => 
      canvas.toBlob(resolve, "image/jpeg", 0.92)
    );
    if (blob) onCapture(blob);
  };

  const retakePhoto = () => {
    window.location.reload(); 
  };

  return (
    <div className="flex flex-col items-center space-y-6 p-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Face Authentication
        </h2>
        <p className="text-gray-600">
          Position your face in the camera view
        </p>
      </div>

      <div className="relative">
        <div className="relative w-80 h-80 rounded-2xl overflow-hidden bg-gray-900 shadow-2xl ring-4 ring-blue-500/20">
          <video 
            ref={videoRef} 
            playsInline 
            className="w-full h-full object-cover"
          />
          
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-64 h-64 rounded-full border-2 border-white/30 flex items-center justify-center">
              <div className="w-48 h-48 rounded-full border-2 border-blue-400/50"></div>
            </div>
          </div>

          <div className="absolute top-4 left-4 w-6 h-6 border-l-3 border-t-3 border-white/60 rounded-tl-lg"></div>
          <div className="absolute top-4 right-4 w-6 h-6 border-r-3 border-t-3 border-white/60 rounded-tr-lg"></div>
          <div className="absolute bottom-4 left-4 w-6 h-6 border-l-3 border-b-3 border-white/60 rounded-bl-lg"></div>
          <div className="absolute bottom-4 right-4 w-6 h-6 border-r-3 border-b-3 border-white/60 rounded-br-lg"></div>

          {auto && autoStatus === "countdown" && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <div className="bg-white rounded-full w-20 h-20 flex items-center justify-center shadow-lg">
                <span className="text-3xl font-bold text-blue-600">{countdown}</span>
              </div>
            </div>
          )}

          {auto && autoStatus === "capturing" && (
            <div className="absolute inset-0 bg-white/90 flex items-center justify-center">
              <div className="text-center">
                <Camera className="w-12 h-12 text-blue-600 mx-auto mb-2 animate-pulse" />
                <p className="text-lg font-semibold text-gray-900">Capturing...</p>
              </div>
            </div>
          )}
        </div>

        {auto && autoStatus === "countdown" && (
          <div className="absolute -bottom-16 left-1/2 transform -translate-x-1/2">
            <div className="bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium shadow-sm">
              📸 Auto-capture in {countdown} seconds
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg max-w-md text-center">
          <X className="w-5 h-5 inline mr-2" />
          {error}
        </div>
      )}

      {!auto && (
        <div className="flex space-x-4">
          <button 
            onClick={takePhoto}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold shadow-lg transition-all duration-200 flex items-center space-x-2"
          >
            <Camera className="w-5 h-5" />
            <span>Take Photo</span>
          </button>
          <button 
            onClick={retakePhoto}
            className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-xl font-semibold shadow-lg transition-all duration-200 flex items-center space-x-2"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Retake</span>
          </button>
        </div>
      )}

      {auto && autoStatus === "idle" && (
        <div className="text-center text-gray-500 max-w-md">
          <p className="text-sm">
            Camera is starting... Position your face within the guide circle
          </p>
        </div>
      )}

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
