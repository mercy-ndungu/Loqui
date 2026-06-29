import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getFeedback } from "@/services/feedback";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { FeedbackResponse } from "@/types";
import { sanitizeText } from "../utils/sanitize";

interface FeedbackResultsProps {
  recordingId?: string;
}

function ScoreBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="font-semibold text-primary">{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function benchmarkLabel(score: number): string {
  if (score >= 90) return "Top 10% for pitches";
  if (score >= 80) return "Top 25% for pitches";
  if (score >= 70) return "Above average";
  if (score >= 60) return "Room to grow";
  return "Keep practicing";
}

export default function FeedbackResults({ recordingId: propId }: FeedbackResultsProps) {
  const { recordingId: paramId } = useParams<{ recordingId: string }>();
  const recordingId = propId ?? paramId;
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!recordingId) return;
    void (async () => {
      try {
        const data = await getFeedback(recordingId);
        setFeedback(data);
      } catch {
        setError("Could not load feedback");
      } finally {
        setLoading(false);
      }
    })();
  }, [recordingId]);

  const handleDownloadPdf = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !feedback) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background">
        <p className="text-error">{error || "Feedback not found"}</p>
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="text-primary hover:text-primary-dark"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const { scores, feedback_text, improvements, strengths } = feedback;

  return (
    <div className="min-h-screen bg-background px-4 py-8 print:bg-white">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 text-center">
          <h1 className="font-display text-3xl text-text">Your Feedback</h1>
          <p className="mt-2 text-sm text-gray-500">{benchmarkLabel(scores.overall)}</p>
        </header>

        <section className="mb-8 flex flex-col items-center rounded-2xl bg-white p-8 shadow-sm ring-1 ring-gray-100">
          <p className="text-sm font-medium uppercase tracking-wide text-gray-500">
            Overall Eloquence
          </p>
          <div
            className="mt-4 flex h-36 w-36 items-center justify-center rounded-full border-8 border-primary-light bg-primary-light/30"
            style={{
              background: `conic-gradient(#10B981 ${scores.overall * 3.6}deg, #D1FAE5 0deg)`,
            }}
          >
            <div className="flex h-28 w-28 items-center justify-center rounded-full bg-white">
              <span className="font-display text-4xl text-primary">{scores.overall}</span>
            </div>
          </div>
        </section>

        <section className="mb-8 grid gap-4 sm:grid-cols-2">
          {[
            { label: "Grammar", value: scores.grammar },
            { label: "Vocabulary", value: scores.vocabulary },
            { label: "Filler Words", value: scores.filler_words_count, max: 20, invert: true },
            { label: "Pacing", value: scores.pacing },
          ].map((card) => (
            <div
              key={card.label}
              className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100"
            >
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="font-display text-3xl text-primary">
                {card.invert ? card.value : card.value}
                {card.label === "Filler Words" ? "" : ""}
              </p>
              {!card.invert && <ScoreBar label={card.label} value={card.value} />}
              {card.invert && (
                <p className="mt-2 text-xs text-gray-500">Lower is better</p>
              )}
            </div>
          ))}
        </section>

        <section className="mb-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <h2 className="text-lg font-semibold text-text">Key Improvements</h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-gray-700">
            {improvements.map((item) => (
              <li key={item}>{sanitizeText(item)}</li>
            ))}
          </ul>
        </section>

        <section className="mb-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <h2 className="text-lg font-semibold text-text">Detailed Feedback</h2>
          <div className="mt-3 space-y-3 text-sm text-gray-700">
            {Object.entries(feedback_text).map(([key, text]) => (
              <div key={key}>
                <p className="font-medium capitalize text-gray-800">{key.replace(/_/g, " ")}</p>
                <p className="mt-1">{sanitizeText(text)}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-8 rounded-xl bg-primary-light/40 p-6 ring-1 ring-primary/20">
          <h2 className="text-lg font-semibold text-primary-dark">Strengths</h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-gray-800">
            {strengths.map((s) => (
              <li key={s}>{sanitizeText(s)}</li>
            ))}
          </ul>
        </section>

        <div className="flex flex-wrap gap-3 print:hidden">
          <button
            type="button"
            onClick={() => navigate("/challenges")}
            className="rounded-lg border border-primary px-5 py-2.5 text-sm font-medium text-primary transition hover:bg-primary-light"
          >
            Practice Again
          </button>
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium transition hover:bg-gray-50"
          >
            Download PDF
          </button>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
