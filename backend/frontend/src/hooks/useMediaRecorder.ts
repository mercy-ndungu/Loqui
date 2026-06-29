import { useCallback, useEffect, useRef, useState } from "react";

export type RecordingState = "idle" | "recording" | "preview" | "uploading";

export const MAX_RECORDING_SECONDS = 120;

export function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

interface UseMediaRecorderOptions {
  maxDurationSeconds?: number;
  enabled?: boolean;
}

export function useMediaRecorder(options: UseMediaRecorderOptions = {}) {
  const { maxDurationSeconds = MAX_RECORDING_SECONDS, enabled = true } = options;
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const [state, setState] = useState<RecordingState>("idle");
  const [error, setError] = useState("");
  const [duration, setDuration] = useState(0);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);

  const stopStream = useCallback(() => {
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(
    () => () => {
      stopStream();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (timerRef.current) window.clearInterval(timerRef.current);
    },
    [stopStream, previewUrl],
  );

  const startCamera = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    if (!enabled) return;
    void startCamera();
    return () => stopStream();
  }, [enabled, startCamera, stopStream]);

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

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    stopStream();
  }, [stopStream]);

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
    timerRef.current = window.setInterval(() => {
      setDuration((d) => {
        const next = d + 1;
        if (next >= maxDurationSeconds) {
          stopRecording();
        }
        return next;
      });
    }, 1000);
  };

  const retake = async () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setVideoBlob(null);
    setDuration(0);
    setState("idle");
    await startCamera();
  };

  const setUploading = () => setState("uploading");

  return {
    videoRef,
    state,
    error,
    setError,
    duration,
    videoBlob,
    previewUrl,
    countdown,
    startRecording,
    stopRecording,
    retake,
    setUploading,
    maxDurationSeconds,
  };
}
