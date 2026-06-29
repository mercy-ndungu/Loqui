import { type ChangeEvent, type DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listChallenges } from "../api/challenges";
import {
  deletePresentation,
  listPresentations,
  uploadPresentation,
} from "../api/presentations";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../hooks/useAuth";
import type { ChallengeSummary, Presentation, PresentationType } from "../types/api";
import { formatDate, isAllowedPresentationFile } from "../utils/validation";

interface DashboardProps {
  onLogout?: () => void;
}

const PRESENTATION_TYPES: { value: PresentationType; label: string }[] = [
  { value: "pitch", label: "Pitch" },
  { value: "interview", label: "Interview" },
  { value: "networking", label: "Networking" },
  { value: "general", label: "General" },
];

export default function Dashboard({ onLogout }: DashboardProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [presentations, setPresentations] = useState<Presentation[]>([]);
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [presentationType, setPresentationType] = useState<PresentationType>("general");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [pres, ch] = await Promise.all([listPresentations(), listChallenges()]);
      setPresentations(pres);
      setChallenges(ch);
    } catch {
      setError("Could not load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const handleLogout = async () => {
    await logout();
    onLogout?.();
    navigate("/login", { replace: true });
  };

  const pickFile = (file: File | null) => {
    if (!file) return;
    if (!isAllowedPresentationFile(file.name)) {
      setError("Only PDF and PowerPoint files are allowed");
      return;
    }
    setError("");
    setSelectedFile(file);
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    pickFile(e.target.files?.[0] ?? null);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    pickFile(e.dataTransfer.files?.[0] ?? null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadProgress(0);
    setError("");
    try {
      await uploadPresentation(selectedFile, presentationType, setUploadProgress);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchData();
    } catch {
      setError("Upload failed");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deletePresentation(id);
      setPresentations((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setError("Delete failed");
    }
  };

  const completedCount = challenges.length;
  const avgScore =
    completedCount > 0
      ? Math.round(
          challenges.reduce((sum, c) => sum + (c.overall_score ?? 0), 0) / completedCount,
        )
      : null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <span className="font-display text-2xl text-primary">Loqui</span>
          <button
            type="button"
            onClick={() => void handleLogout()}
            className="text-sm font-medium text-primary transition hover:text-primary-dark"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <section className="mb-8">
          <h1 className="font-display text-3xl text-text">
            Welcome, {user?.email ?? "speaker"}!
          </h1>
          <p className="mt-2 text-gray-600">Ready to master eloquent speech? Let&apos;s get started.</p>
        </section>

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-error">{error}</div>
        )}

        <section className="mb-8 grid gap-4 sm:grid-cols-3">
          {[
            { label: "Presentations", value: presentations.length, sub: "Uploaded" },
            { label: "Challenges", value: completedCount, sub: "Completed" },
            {
              label: "Average Score",
              value: avgScore ?? "—",
              sub: "Eloquence rating",
            },
          ].map((card) => (
            <div
              key={card.label}
              className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100 transition hover:shadow-md"
            >
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="mt-1 font-display text-3xl text-primary">{card.value}</p>
              <p className="text-xs text-gray-400">{card.sub}</p>
            </div>
          ))}
        </section>

        <section className="mb-8 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <h2 className="text-lg font-semibold text-text">Practice Challenges</h2>
          <p className="mt-1 text-sm text-gray-600">
            All challenge types use the same universal eloquence scoring.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => navigate("/presentations/upload")}
              className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
            >
              Practice Presentation
            </button>
            <button
              type="button"
              onClick={() => navigate("/challenges/improv")}
              className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
            >
              Improv Challenge
            </button>
            <button
              type="button"
              onClick={() => navigate("/challenges/topics")}
              className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
            >
              Random Topic
            </button>
            <Link
              to="/challenges"
              className="rounded-lg border border-primary px-5 py-2.5 text-sm font-semibold text-primary transition hover:bg-primary-light"
            >
              All Challenges
            </Link>
          </div>

          {challenges.length > 0 && (
            <ul className="mt-6 divide-y divide-gray-100">
              {challenges.slice(0, 5).map((c) => (
                <li key={c.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium text-text">
                      {c.challenge_type === "improv" ? "Improv Challenge" : c.topic_or_images}
                    </p>
                    <p className="text-xs text-gray-500">
                      {c.completed_at ? formatDate(c.completed_at) : "In progress"}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {c.overall_score != null && (
                      <span className="font-display text-xl text-primary">{c.overall_score}</span>
                    )}
                    <button
                      type="button"
                      onClick={() => navigate(`/feedback/${c.id}`)}
                      className="text-sm font-medium text-primary hover:text-primary-dark"
                    >
                      View Feedback
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mb-8 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <h2 className="text-lg font-semibold text-text">Upload Your Presentation</h2>
          <p className="mt-1 text-sm text-gray-600">PDF or PowerPoint slide deck</p>

          <div className="mt-4">
            <label className="mb-2 block text-sm font-medium text-gray-700">Presentation type</label>
            <select
              value={presentationType}
              onChange={(e) => setPresentationType(e.target.value as PresentationType)}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {PRESENTATION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`mt-4 flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 transition ${
              dragOver ? "border-primary bg-primary-light/30" : "border-gray-200 bg-gray-50"
            }`}
          >
            <p className="text-sm text-gray-600">Drag and drop your file here, or</p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 rounded-lg border border-primary px-4 py-2 text-sm font-medium text-primary transition hover:bg-primary-light"
            >
              Choose file
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.ppt,.pptx"
              className="hidden"
              onChange={onFileChange}
            />
            {selectedFile && (
              <p className="mt-3 text-sm font-medium text-text">{selectedFile.name}</p>
            )}
          </div>

          {uploading && (
            <div className="mt-4">
              <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">{uploadProgress}% uploaded</p>
            </div>
          )}

          <button
            type="button"
            disabled={!selectedFile || uploading}
            onClick={() => void handleUpload()}
            className="mt-4 flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark disabled:opacity-50"
          >
            {uploading ? <LoadingSpinner size="sm" className="border-white border-t-transparent" /> : null}
            Upload
          </button>
        </section>

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <h2 className="text-lg font-semibold text-text">Recent Presentations</h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : presentations.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">
              No presentations yet. Upload one to get started.
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-gray-100">
              {presentations.map((p) => (
                <li key={p.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                  <div>
                    <p className="font-medium text-text">{p.title}</p>
                    <p className="text-xs text-gray-500">{formatDate(p.created_at)}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => navigate(`/presentations/${p.id}/record`)}
                      className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-dark"
                    >
                      Practice
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDelete(p.id)}
                      className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 transition hover:border-error hover:text-error"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
