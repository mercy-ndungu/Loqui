import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { analyzeFeedback } from "@/services/feedback";
import { getPresentation } from "@/services/presentations";
import { uploadRecording } from "@/services/recordings";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { PresentationDetail } from "@/types";

type RecordingState = "idle" | "recording" | "preview" | "uploading";

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export default function RecordPresentation() {
  const { id: presentationId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const [presentation, setPresentation] = useState<PresentationDetail | null>(null);
  const [state, setState] = useState<RecordingState>("idle");
  const [error, setError] = useState("");
  const [duration, setDuration] = useState(0);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    if (!presentationId) return;
    void getPresentation(presentationId)
      .then(setPresentation)
      .catch(() => setError("Could not load presentation"));
  }, [presentationId]);

  const stopStream = useCallback(() => {
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(() => () => {
    stopStream();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (timerRef.current) window.clearInterval(timerRef.current);
  }, [stopStream, previewUrl]);

  const startCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch {
      setError("Camera and microphone access is required to record");
    }
  };

  useEffect(() => {
    void startCamera();
    return () => stopStream();
  }, [stopStream]);

  const runCountdown = (): Promise<void> =>
    new Promise((resolve) => {
      setCountdown(3);
      let n = 3;
      const id = window.setInterval(() => {
        n -= 1;
        if (n <= 0) {
          window.clearInterval(id);
          setCountdown(null);
          resolve();
        } else {
          setCountdown(n);
        }
      }, 1000);
    });

  const startRecording = async () => {
    setError("");
    const stream = videoRef.current?.srcObject as MediaStream | null;
    if (!stream) {
      setError("Camera not ready");
      return;
    }

    await runCountdown();
    chunksRef.current = [];
    const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
      ? "video/webm;codecs=vp9,opus"
      : "video/webm";

    const recorder = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      setVideoBlob(blob);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setState("preview");
      if (timerRef.current) window.clearInterval(timerRef.current);
    };

    recorder.start(1000);
    setState("recording");
    setDuration(0);
    timerRef.current = window.setInterval(() => setDuration((d) => d + 1), 1000);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    stopStream();
  };

  const retake = async () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setVideoBlob(null);
    setDuration(0);
    setState("idle");
    await startCamera();
  };

  const submitFeedback = async () => {
    if (!videoBlob || !presentationId) return;
    setState("uploading");
    setError("");
    setUploadProgress(0);
    try {
      const ext = videoBlob.type.includes("mp4") ? "mp4" : "webm";
      const upload = await uploadRecording(
        presentationId,
        videoBlob,
        duration,
        `recording.${ext}`,
        setUploadProgress,
      );
      await analyzeFeedback(upload.id, upload.transcription);
      navigate(`/feedback/${upload.id}`, { replace: true });
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? (err.response?.data as { detail?: string })?.detail ?? "Upload failed"
        : "Upload failed";
      setError(typeof message === "string" ? message : "Upload failed");
      setState("preview");
    }
  };

  return (
    <div className="min-h-screen bg-background px-4 py-6">
      <div className="mx-auto max-w-6xl">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="mb-4 text-sm text-primary hover:text-primary-dark"
        >
          ← Dashboard
        </button>

        <h1 className="font-display text-3xl text-text">Record Your Practice</h1>
        <p className="mt-1 text-sm text-gray-600">
          Present &ldquo;{presentation?.title ?? "your deck"}&rdquo; to the camera
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-error">{error}</div>
        )}

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">Presentation</h2>
            {presentation?.url?.includes(".pdf") ? (
              <iframe
                title="Slides"
                src={presentation.url}
                className="h-64 w-full rounded-lg border border-gray-200 lg:h-80"
              />
            ) : (
              <div className="flex h-64 items-center justify-center rounded-lg bg-gray-50 text-sm text-gray-500">
                {presentation?.title ?? "Loading slides…"}
              </div>
            )}
          </div>

          <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700">Camera</h2>
              {(state === "recording" || state === "preview") && (
                <span className="font-mono text-lg font-semibold text-primary">
                  {formatTimer(duration)}
                </span>
              )}
            </div>

            {countdown !== null && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/40">
                <span className="font-display text-6xl text-white">{countdown}</span>
              </div>
            )}

            <div className="relative overflow-hidden rounded-lg bg-black">
              {state === "preview" && previewUrl ? (
                <video ref={previewRef} src={previewUrl} controls className="aspect-video w-full" />
              ) : (
                <video ref={videoRef} muted playsInline className="aspect-video w-full" />
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              {state === "idle" && (
                <button
                  type="button"
                  onClick={() => void startRecording()}
                  className="rounded-lg bg-red-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-red-600"
                >
                  Start Recording
                </button>
              )}
              {state === "recording" && (
                <button
                  type="button"
                  onClick={stopRecording}
                  className="rounded-lg bg-gray-800 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-gray-900"
                >
                  Stop Recording
                </button>
              )}
              {state === "preview" && (
                <>
                  <button
                    type="button"
                    onClick={() => void retake()}
                    className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium transition hover:bg-gray-50"
                  >
                    Retake
                  </button>
                  <button
                    type="button"
                    onClick={() => void submitFeedback()}
                    className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
                  >
                    Submit for Feedback
                  </button>
                </>
              )}
              {state === "uploading" && (
                <div className="flex w-full flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <span className="text-sm text-gray-600">Uploading & analyzing…</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
