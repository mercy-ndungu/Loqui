import { Link, useNavigate } from "react-router-dom";

const CHALLENGE_OPTIONS = [
  {
    id: "presentation",
    title: "Presentation Practice",
    description: "Upload your slide deck and practice presenting to the camera with AI feedback.",
    href: "/presentations/upload",
    cta: "Start Practice",
  },
  {
    id: "improv",
    title: "Improv Challenge",
    description: "Get 5 random images and tell a creative 1–2 minute story connecting them.",
    href: "/challenges/improv",
    cta: "Start Improv",
  },
  {
    id: "topic",
    title: "Random Topic",
    description: "Receive an AI-generated speaking prompt and talk about it for 1–2 minutes.",
    href: "/challenges/topics",
    cta: "Start Topic",
  },
] as const;

export default function ChallengesHub() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-4xl">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="mb-4 text-sm text-primary hover:text-primary-dark"
        >
          ← Dashboard
        </button>

        <h1 className="font-display text-3xl text-text">Practice Challenges</h1>
        <p className="mt-2 text-gray-600">
          Choose how you want to practice. All modes use the same eloquence scoring.
        </p>

        <div className="mt-8 grid gap-6 sm:grid-cols-1 lg:grid-cols-3">
          {CHALLENGE_OPTIONS.map((option) => (
            <article
              key={option.id}
              className="flex flex-col rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100 transition hover:shadow-md"
            >
              <h2 className="text-lg font-semibold text-text">{option.title}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-600">
                {option.description}
              </p>
              <Link
                to={option.href}
                className="mt-6 inline-flex justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark"
              >
                {option.cta}
              </Link>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
