import { type ChangeEvent, type DragEvent, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPresentation } from "../api/presentations";
import LoadingSpinner from "../components/LoadingSpinner";
import type { PresentationDetail, PresentationType } from "../types/api";
import { formatDate, formatFileSize, isAllowedPresentationFile } from "../utils/validation";

const TYPES: { value: PresentationType; label: string }[] = [
  { value: "pitch", label: "Pitch" },
  { value: "interview", label: "Interview" },
  { value: "networking", label: "Networking" },
  { value: "general", label: "General" },
];

export default function UploadPresentation() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [presentation, setPresentation] = useState<PresentationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [presentationType, setPresentationType] = useState<PresentationType>("general");
  const [localFile, setLocalFile] = useState<File | null>(null);

  useEffect(() => {
    if (!id) return;
    void (async () => {
      try {
        const data = await getPresentation(id);
        setPresentation(data);
        setPresentationType(data.presentation_type as PresentationType);
      } catch {
        setError("Could not load presentation");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleFile = (file: File | null) => {
    if (!file) return;
    if (!isAllowedPresentationFile(file.name)) {
      setError("Only PDF and PowerPoint files are allowed");
      return;
    }
    setLocalFile(file);
    setError("");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="mb-6 text-sm text-primary hover:text-primary-dark"
        >
          ← Back to Dashboard
        </button>

        <h1 className="font-display text-3xl text-text">Your Presentation</h1>

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-error">{error}</div>
        )}

        <div className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          {presentation && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold">{presentation.title}</h2>
              <p className="text-sm text-gray-500">Uploaded {formatDate(presentation.created_at)}</p>
              {localFile && (
                <p className="mt-1 text-sm text-gray-600">
                  New file: {localFile.name} ({formatFileSize(localFile.size)})
                </p>
              )}
              {presentation.url?.endsWith(".pdf") && (
                <iframe
                  title="PDF preview"
                  src={presentation.url}
                  className="mt-4 h-96 w-full rounded-lg border border-gray-200"
                />
              )}
            </div>
          )}

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e: DragEvent) => {
              e.preventDefault();
              handleFile(e.dataTransfer.files[0] ?? null);
            }}
            className="rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-8 text-center"
          >
            <p className="text-sm text-gray-600">Drag and drop to replace, or</p>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="mt-2 text-sm font-medium text-primary hover:text-primary-dark"
            >
              choose a file
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.ppt,.pptx"
              className="hidden"
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                handleFile(e.target.files?.[0] ?? null)
              }
            />
          </div>

          <div className="mt-6">
            <label className="mb-2 block text-sm font-medium text-gray-700">Presentation type</label>
            <select
              value={presentationType}
              onChange={(e) => setPresentationType(e.target.value as PresentationType)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => id && navigate(`/presentations/${id}/record`)}
            className="mt-6 w-full rounded-lg bg-primary py-3 text-sm font-semibold text-white transition hover:bg-primary-dark"
          >
            Next → Recording
          </button>
        </div>
      </div>
    </div>
  );
}
