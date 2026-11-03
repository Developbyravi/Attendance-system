"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Camera,
  RefreshCw,
  RotateCcw,
  Check,
  VideoOff,
  Scan
} from "lucide-react";

interface CameraCaptureProps {
  mode?: "portrait" | "classroom";
  title?: string;
  guidanceText?: string;
  onCapture: (blob: Blob, file: File, dataUrl: string) => void;
  onRetake?: () => void;
  onCancel?: () => void;
  isProcessing?: boolean;
}

export default function CameraCapture({
  mode = "portrait",
  title,
  guidanceText,
  onCapture,
  onRetake,
  onCancel,
  isProcessing = false,
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [facingMode, setFacingMode] = useState<"user" | "environment">(
    mode === "portrait" ? "user" : "environment"
  );
  const [hasMultipleCameras, setHasMultipleCameras] = useState(false);
  const [cameraState, setCameraState] = useState<"loading" | "active" | "captured" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [capturedDataUrl, setCapturedDataUrl] = useState<string | null>(null);

  // Stop camera tracks cleanly
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // Check available camera devices
  useEffect(() => {
    async function checkDevices() {
      try {
        if (navigator?.mediaDevices?.enumerateDevices) {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const videoInputs = devices.filter((d) => d.kind === "videoinput");
          setHasMultipleCameras(videoInputs.length > 1);
        }
      } catch {
        // Ignored in restricted environments
      }
    }
    checkDevices();
  }, []);

  // Start video stream
  const startCamera = useCallback(async () => {
    stopStream();
    setCameraState("loading");
    setErrorMessage(null);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraState("error");
      setErrorMessage(
        "Camera API is not supported in this browser environment. Please use a modern browser (Chrome, Firefox, Edge, Safari) with HTTPS or localhost."
      );
      return;
    }

    try {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: mode === "classroom" ? 1920 : 1280 },
          height: { ideal: mode === "classroom" ? 1080 : 720 },
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraState("active");
      }
    } catch (err: unknown) {
      setCameraState("error");
      if (err instanceof DOMException) {
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
          setErrorMessage(
            "Camera permission was denied. Please click the camera icon in your browser URL bar and allow access to enable live capture."
          );
        } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
          setErrorMessage("No video camera device was found on this system. Please connect an external webcam.");
        } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
          setErrorMessage(
            "Your camera is currently in use by another application or browser tab. Please close other apps and try again."
          );
        } else {
          setErrorMessage(`Unable to access camera: ${err.message}`);
        }
      } else {
        setErrorMessage("An unexpected hardware error occurred while connecting to the camera.");
      }
    }
  }, [facingMode, mode, stopStream]);

  // Launch on mount or when facingMode changes
  useEffect(() => {
    if (cameraState !== "captured") {
      startCamera();
    }
    return () => {
      stopStream();
    };
  }, [startCamera, stopStream]);

  // Capture current frame
  function handleCaptureFrame() {
    if (!videoRef.current) return;
    const video = videoRef.current;

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    let canvas = canvasRef.current;
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvasRef.current = canvas;
    }

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // In portrait selfie mode, mirror horizontally to match user perception
    if (facingMode === "user") {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, width, height);

    // Convert to dataUrl and Blob
    const dataUrl = canvas.toDataURL("image/jpeg", 0.95);
    setCapturedDataUrl(dataUrl);
    setCameraState("captured");

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const filename =
          mode === "portrait"
            ? `student_enroll_${Date.now()}.jpg`
            : `classroom_session_${Date.now()}.jpg`;
        const file = new File([blob], filename, { type: "image/jpeg" });
        onCapture(blob, file, dataUrl);
      },
      "image/jpeg",
      0.95
    );
  }

  // Retake photo
  function handleRetake() {
    setCapturedDataUrl(null);
    if (onRetake) onRetake();
    startCamera();
  }

  // Toggle front/back camera
  function toggleCamera() {
    setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
  }

  return (
    <div className="w-full bg-[#111114] border border-[#2A2A30] rounded-3xl p-5 sm:p-6 shadow-2xl relative overflow-hidden">
      {/* Header Info */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm sm:text-base font-bold text-[#F5F5F5] flex items-center gap-2">
            <Camera className="w-4 h-4 text-[#FFD700]" />
            <span>{title || (mode === "portrait" ? "Live Face Biometric Enrollment" : "Live Classroom Photo Capture")}</span>
          </h3>
          <p className="text-xs text-[#A1A1AA] mt-0.5">
            {guidanceText ||
              (mode === "portrait"
                ? "Position your face squarely within the oval guideline with neutral expression & good lighting."
                : "Point camera towards the entire classroom seating arrangement to capture all student faces.")}
          </p>
        </div>

        {hasMultipleCameras && cameraState === "active" && (
          <button
            type="button"
            onClick={toggleCamera}
            className="px-3 py-1.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[11px] font-semibold text-[#A1A1AA] hover:text-[#FFD700] hover:border-[#FFD700]/40 transition-colors flex items-center gap-1.5"
            title="Switch front/back camera"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Switch Lens</span>
          </button>
        )}
      </div>

      {/* Viewport Frame */}
      <div className="relative w-full aspect-[4/3] sm:aspect-[16/9] max-h-[460px] bg-[#0B0B0D] rounded-2xl overflow-hidden border border-[#2A2A30] flex items-center justify-center">
        {/* Loading State */}
        {cameraState === "loading" && (
          <div className="flex flex-col items-center gap-2 text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700]" />
            <span>Connecting to live video device...</span>
          </div>
        )}

        {/* Error State */}
        {cameraState === "error" && (
          <div className="p-6 text-center max-w-md">
            <div className="w-12 h-12 rounded-2xl bg-red-950/40 border border-red-800/60 text-red-400 flex items-center justify-center mx-auto mb-3">
              <VideoOff className="w-6 h-6" />
            </div>
            <p className="text-xs sm:text-sm font-semibold text-red-200 mb-2">Camera Access Blocked</p>
            <p className="text-xs text-[#A1A1AA] leading-relaxed mb-4">{errorMessage}</p>
            <button
              type="button"
              onClick={startCamera}
              className="px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] hover:text-[#FFD700] hover:border-[#FFD700] transition-colors inline-flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Permission</span>
            </button>
          </div>
        )}

        {/* Live Active Stream */}
        <video
          ref={videoRef}
          playsInline
          autoPlay
          muted
          className={`w-full h-full object-cover ${
            facingMode === "user" ? "-scale-x-100" : ""
          } ${cameraState === "active" ? "block" : "hidden"}`}
        />

        {/* Captured Snapshot Display */}
        {cameraState === "captured" && capturedDataUrl && (
          <img
            src={capturedDataUrl}
            alt="Captured Snapshot"
            className="w-full h-full object-cover"
          />
        )}

        {/* Visual Overlay Guides */}
        {cameraState === "active" && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            {mode === "portrait" ? (
              // Portrait Oval Face Target
              <div className="relative w-48 h-64 sm:w-56 sm:h-72 border-2 border-dashed border-[#FFD700]/70 rounded-[50%] flex items-center justify-center shadow-[0_0_30px_rgba(255,215,0,0.15)] animate-pulse">
                <span className="text-[10px] uppercase tracking-widest text-[#FFD700] font-bold bg-[#0B0B0D]/80 px-2 py-0.5 rounded-full border border-[#FFD700]/30 absolute -top-3">
                  Align Face Here
                </span>
                <div className="w-2 h-2 rounded-full bg-[#FFD700]/40" />
              </div>
            ) : (
              // Classroom Viewfinder Box
              <div className="relative w-[85%] h-[80%] border-2 border-[#FFD700]/50 rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(255,215,0,0.1)]">
                <span className="text-[10px] uppercase tracking-widest text-[#FFD700] font-bold bg-[#0B0B0D]/80 px-3 py-1 rounded-full border border-[#FFD700]/30 absolute -top-3">
                  Classroom Viewfinder &bull; InsightFace SCRFD-10G Active
                </span>
                <Scan className="w-8 h-8 text-[#FFD700]/30" />
              </div>
            )}
          </div>
        )}

        {/* Live Processing Indicator */}
        {isProcessing && (
          <div className="absolute inset-0 bg-[#0B0B0D]/85 backdrop-blur-sm flex flex-col items-center justify-center gap-3 text-center p-6 z-20">
            <RefreshCw className="w-8 h-8 animate-spin text-[#FFD700]" />
            <div>
              <p className="text-sm font-bold text-[#F5F5F5]">Running AI Inference...</p>
              <p className="text-xs text-[#A1A1AA] mt-1 max-w-xs">
                Executing SCRFD-10G multi-face detection & ArcFace 512-d feature extraction.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Hidden processing canvas */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Bottom Action Controls */}
      <div className="mt-4 flex items-center justify-between gap-3">
        {cameraState === "active" ? (
          <div className="w-full flex items-center justify-center gap-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-3 rounded-2xl bg-[#17171B] hover:bg-[#202026] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] font-semibold text-xs transition-colors"
              >
                Cancel
              </button>
            )}
            <button
              type="button"
              onClick={handleCaptureFrame}
              disabled={isProcessing}
              className="px-6 py-3 rounded-2xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-extrabold text-xs tracking-wider flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,215,0,0.3)] transition-all transform active:scale-95 disabled:opacity-50"
            >
              <Camera className="w-4 h-4" />
              <span>CAPTURE PHOTOGRAPH</span>
            </button>
          </div>
        ) : cameraState === "captured" ? (
          <div className="w-full flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleRetake}
              disabled={isProcessing}
              className="flex-1 py-3 rounded-2xl bg-[#17171B] hover:bg-[#202026] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] font-semibold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Retake Photo</span>
            </button>

            <div className="flex items-center gap-1.5 text-xs text-[#7BD88F] font-semibold px-3">
              <Check className="w-4 h-4" />
              <span>Image Captured</span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
