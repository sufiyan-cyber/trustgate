"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, RefreshCw, Upload, AlertCircle, Video } from "lucide-react";

interface CameraCaptureProps {
  mode: "document" | "selfie";
  title: string;
  subtitle: string;
  onCaptured: (blob: Blob, previewUrl: string) => void;
}

export default function CameraCapture({ mode, title, subtitle, onCaptured }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedUrl, setCapturedUrl] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRequesting, setIsRequesting] = useState(false);

  const startCamera = async () => {
    setIsRequesting(true);
    setErrorMessage(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Webcam API not supported in this browser. Please use Chrome, Edge, or Firefox.");
      }

      let s: MediaStream | null = null;
      try {
        // First try ideal HD resolution
        s = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
          audio: false,
        });
      } catch (constraintErr) {
        // Fallback to basic unrestricted video stream for older built-in webcams
        console.warn("Retrying camera with generic constraints:", constraintErr);
        s = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      setStream(s);
      setIsCameraActive(true);

      if (videoRef.current) {
        videoRef.current.srcObject = s;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch((e) => console.warn("Video play exception:", e));
        };
      }
    } catch (err: any) {
      console.warn("Webcam access error:", err);
      setIsCameraActive(false);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setErrorMessage("Camera permission was denied in your browser. Please click the camera/lock icon in the browser address bar and select 'Allow', then click 'Enable Webcam'.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setErrorMessage("No built-in or USB webcam was found on your computer. You can upload an image file instead.");
      } else {
        setErrorMessage(`Camera unavailable (${err.message || err.name}). Please grant permission or upload an image file.`);
      }
    } finally {
      setIsRequesting(false);
    }
  };

  useEffect(() => {
    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [mode]);

  const handleCapture = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          setCapturedUrl(url);
          onCaptured(blob, url);
        }
      },
      "image/jpeg",
      0.95
    );
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setCapturedUrl(url);
      onCaptured(file, url);
    }
  };

  const handleRetake = () => {
    setCapturedUrl(null);
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col items-center">
      <div className="text-center mb-4">
        <h3 className="text-base font-serif-display font-bold text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
      </div>

      {/* Video / Captured Preview Area */}
      <div className="relative w-full max-w-md aspect-[4/3] bg-surface rounded-lg overflow-hidden border border-border flex items-center justify-center shadow-inner">
        {capturedUrl ? (
          <img src={capturedUrl} alt="Captured" className="w-full h-full object-cover" />
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${mode === "selfie" ? "scale-x-[-1]" : ""}`}
            />

            {/* Editorial Alignment Guide Overlays */}
            {isCameraActive && (
              mode === "document" ? (
                <div className="absolute inset-8 border border-dashed border-primary/80 rounded pointer-events-none flex items-center justify-center">
                  <span className="text-[11px] font-mono text-foreground bg-white/90 px-3 py-1 rounded shadow-sm border border-border">
                    ALIGN ID CARD WITHIN RULE FRAME
                  </span>
                </div>
              ) : (
                <div className="absolute w-44 h-56 border border-dashed border-primary/80 rounded-full pointer-events-none flex items-center justify-center">
                  <span className="text-[11px] font-mono text-foreground bg-white/90 px-3 py-1 rounded shadow-sm border border-border">
                    CENTER BIOMETRIC PORTRAIT
                  </span>
                </div>
              )
            )}
          </>
        )}

        {/* Error / Permission Request Prompt */}
        {!capturedUrl && !isCameraActive && (
          <div className="absolute inset-0 bg-white/95 p-6 flex flex-col items-center justify-center text-center space-y-3">
            <Video className="w-10 h-10 text-primary mb-1" />
            <p className="font-serif-display font-bold text-foreground text-sm">
              Webcam Access Required
            </p>
            <p className="text-xs text-muted-foreground max-w-xs font-sans leading-relaxed">
              {errorMessage || "Click below to grant camera access for document and face capture."}
            </p>
            <button
              onClick={startCamera}
              disabled={isRequesting}
              className="px-4 py-2 rounded-md bg-primary hover:bg-primary-hover text-white font-serif-display font-bold text-xs shadow-sm transition-all active:scale-95"
            >
              {isRequesting ? "Prompting Browser..." : "Enable Built-In Webcam"}
            </button>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-5 flex items-center gap-3">
        {capturedUrl ? (
          <button
            onClick={handleRetake}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface border border-border text-xs font-mono font-medium text-foreground hover:bg-surface/80 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retake Image
          </button>
        ) : (
          <>
            {isCameraActive && (
              <button
                onClick={handleCapture}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white font-serif-display font-bold text-sm shadow-md transition-all active:scale-95"
              >
                <Camera className="w-4 h-4" />
                Capture Exposure
              </button>
            )}

            <label className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-surface border border-border text-xs font-mono text-foreground hover:bg-surface/80 cursor-pointer transition-colors">
              <Upload className="w-3.5 h-3.5 text-primary" />
              Upload Document File
              <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
            </label>
          </>
        )}
      </div>
    </div>
  );
}
