import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateImprovChallenge, uploadChallengeRecording } from "../api/challenges";
import LoadingSpinner from "../components/LoadingSpinner";
import { formatTimer, useMediaRecorder } from "../hooks/useMediaRecorder";
import type { ChallengeUploadResponse, ImprovImage } from "../types/api";

function InlineFeedback({
  result,
  onViewFull,
}: {
  result: ChallengeUploadResponse;
  onViewFull: () => void;
}) {
  return (
    <section className="mt-8 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
      <h2 className="font-display text-2xl text-text">Your Eloquence Feedback</h2>
      <p className="mt-2 font-display text-5xl text-primary">{result.overall_score}</p>
      <p className="mt-1 text-sm text-gray-500">Overall eloquence score</p>
      <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-gray-700">
        {result.improvements.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onViewFull}
        className="mt-6 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
      >
        View Full Feedback
      </button>
    </section>
  );
}

export default function ImprovChallenge() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [images, setImages] = useState<ImprovImage[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState<ChallengeUploadResponse | null>(null);

  const {
    videoRef,
    state,
    error: recorderError,
    setError: setRecorderError,
    duration,
    videoBlob,
    previewUrl,
    countdown,
    startRecording,
    stopRecording,
    retake,
    setUploading,
    maxDurationSeconds,
  } = useMediaRecorder({ enabled: !loading && !!challengeId && !result });

  const loadImages = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await generateImprovChallenge();
      setChallengeId(data.challenge_id);
      setImages(data.images);
    } catch {
      setError("Could not load improv images. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadImages();
  }, [loadImages]);

  const handleSubmit = async () => {
    if (!videoBlob || !challengeId) return;
    setUploading();
    setRecorderError("");
    setUploadProgress(0);
    try {
      const ext = videoBlob.type.includes("mp4") ? "mp4" : "webm";
      const upload = await uploadChallengeRecording(
        challengeId,
        "improv",
        videoBlob,
        duration,
        `improv.${ext}`,
        setUploadProgress,
      );
      setResult(upload);
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? (err.response?.data as { detail?: string })?.detail ?? "Upload failed"
        : "Upload failed";
      setRecorderError(typeof message === "string" ? message : "Upload failed");
      await retake();
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const displayError = error || recorderError;

  return (
    <div className="min-h-screen bg-background px-4 py-6">
      <div className="mx-auto max-w-4xl">
        <button
          type="button"
          onClick={() => navigate("/challenges")}
          className="mb-4 text-sm text-primary hover:text-primary-dark"
        >
          ← Challenges
        </button>

        <h1 className="font-display text-3xl text-text">Improv Challenge</h1>
        <p className="mt-3 text-lg font-medium text-text">
          Tell a story about these images in 1–2 minutes
        </p>
        <p className="mt-1 text-sm text-gray-600">
          Connect the images creatively and speak with clarity and eloquence.
        </p>

        {displayError && (
          <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-error">{displayError}</div>
        )}

        {result && (
          <InlineFeedback
            result={result}
            onViewFull={() => navigate(`/feedback/${result.challenge_id}`)}
          />
        )}

        {!result && challengeId && (
          <>
            <div className="mt-6 rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-6">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {images.map((image, i) => (
                  <img
                    key={`${image.url}-${i}`}
                    src={image.url}
                    alt={image.alt || `Improv prompt ${i + 1}`}
                    className="aspect-[4/3] w-full rounded-lg object-cover ring-1 ring-gray-200"
                    loading="lazy"
                  />
                ))}
              </div>
            </div>

            <div className="relative mt-6 rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100 sm:p-6">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">Recording</h2>
                {(state === "recording" || state === "preview") && (
                  <span
                    className={`font-mono text-2xl font-bold ${
                      duration >= maxDurationSeconds ? "text-error" : "text-primary"
                    }`}
                  >
                    {formatTimer(duration)} / {formatTimer(maxDurationSeconds)}
                  </span>
                )}
              </div>

              {countdown !== null && (
                <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-black/40">
                  <span className="font-display text-6xl text-white">{countdown}</span>
                </div>
              )}

              <div className="overflow-hidden rounded-lg bg-black">
                {state === "preview" && previewUrl ? (
                  <video src={previewUrl} controls className="aspect-video w-full" />
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
                      onClick={() => void handleSubmit()}
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
                      <span className="text-sm text-gray-600">
                        Uploading, transcribing & analyzing…
                      </span>
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
          </>
        )}
      </div>
    </div>
  );
}
