import { type ReactNode } from "react";
import { Link } from "react-router-dom";

function DotGridBackground({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen bg-background"
      style={{
        backgroundImage: "radial-gradient(circle, #E5E7EB 1px, transparent 1px)",
        backgroundSize: "24px 24px",
      }}
    >
      {children}
    </div>
  );
}

function LoquiLogo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-80">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary">
        <svg className="h-4 w-4 text-white" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Z" />
          <path d="M19 10v1a7 7 0 0 1-14 0v-1" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <path d="M12 18v3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </span>
      <span className="font-display text-xl font-normal text-text">Loqui</span>
    </Link>
  );
}

function SparkleIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
      />
    </svg>
  );
}

function ChartIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function ShieldIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
      />
    </svg>
  );
}

function UploadIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
    </svg>
  );
}

function MicIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 18v3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
    </svg>
  );
}

interface FeatureRowProps {
  icon: ReactNode;
  title: string;
  description?: string;
}

function FeatureRow({ icon, title, description }: FeatureRowProps) {
  return (
    <div className="flex gap-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center text-primary">{icon}</div>
      <div>
        <p className="font-semibold text-text">{title}</p>
        {description && <p className="mt-0.5 text-sm leading-relaxed text-gray-600">{description}</p>}
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-100 transition hover:shadow-md">
      <div className="mb-4 flex h-10 w-10 items-center justify-center text-primary">{icon}</div>
      <h3 className="font-semibold text-text">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-gray-600">{description}</p>
    </div>
  );
}

const HERO_FEATURES = [
  { icon: <SparkleIcon />, title: "AI-powered speech coaching" },
  { icon: <SparkleIcon />, title: "Real-time AI feedback" },
  { icon: <ChartIcon />, title: "Track your progress" },
];

const HOW_IT_WORKS = [
  {
    step: 1,
    icon: <UploadIcon />,
    title: "Upload Your Presentation",
    description: "Add your slides or talking points so Loqui understands your content and goals.",
  },
  {
    step: 2,
    icon: <MicIcon />,
    title: "Record Yourself Speaking",
    description: "Practice your delivery while Loqui captures your pacing, tone, and clarity.",
  },
  {
    step: 3,
    icon: <SparkleIcon className="h-6 w-6" />,
    title: "Get AI Feedback",
    description: "Receive instant coaching on filler words, structure, and eloquence to improve every session.",
  },
];

const KEY_FEATURES = [
  {
    icon: <SparkleIcon />,
    title: "Real-time AI Feedback",
    description: "Instant guidance on pacing, clarity, and filler words.",
  },
  {
    icon: <ChartIcon />,
    title: "Track Your Progress",
    description: "Watch your eloquence score climb session after session.",
  },
  {
    icon: <ShieldIcon />,
    title: "Private & Secure",
    description: "Your practice sessions stay yours. Always.",
  },
];

export default function Landing() {
  const year = new Date().getFullYear();

  return (
    <DotGridBackground>
      {/* Hero */}
      <header className="mx-auto max-w-6xl px-6 pt-8">
        <nav className="flex items-center justify-between">
          <LoquiLogo />
          <div className="flex items-center gap-6">
            <span className="hidden text-sm text-gray-500 sm:inline">Your AI speech coach</span>
            <Link
              to="/login"
              className="text-sm font-medium text-gray-600 transition-colors hover:text-text"
            >
              Login
            </Link>
          </div>
        </nav>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20 pt-12 lg:pb-28 lg:pt-16">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-primary-light px-3 py-1 text-xs font-medium text-primary-dark">
              <SparkleIcon className="h-3.5 w-3.5" />
              AI-powered speech coaching
            </span>

            <h1 className="mt-6 font-display text-4xl leading-tight text-text sm:text-5xl lg:text-[3.25rem] lg:leading-[1.15]">
              Speak With <span className="text-primary">Confidence,</span>
              <br />
              <span className="text-primary">Sound</span> With Eloquence
            </h1>

            <p className="mt-5 max-w-lg text-base leading-relaxed text-gray-600 sm:text-lg">
              Master the art of eloquent speech with AI-powered feedback that helps you sound clear,
              calm, and compelling.
            </p>

            <div className="mt-8 space-y-5">
              {HERO_FEATURES.map((feature) => (
                <FeatureRow key={feature.title} icon={feature.icon} title={feature.title} />
              ))}
            </div>

            <Link
              to="/login"
              className="mt-10 inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-dark"
            >
              Get Started
              <ArrowRightIcon />
            </Link>
          </div>

          <div className="hidden lg:block">
            <div className="rounded-2xl bg-white p-8 shadow-lg ring-1 ring-gray-100">
              <p className="font-display text-2xl text-text">Your AI speech coach</p>
              <p className="mt-2 text-sm text-gray-600">
                Practice presentations, get instant feedback, and build confidence for every
                speaking moment.
              </p>
              <div className="mt-8 space-y-6">
                {KEY_FEATURES.map((feature) => (
                  <FeatureRow
                    key={feature.title}
                    icon={feature.icon}
                    title={feature.title}
                    description={feature.description}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t border-gray-200/80 bg-white/60 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl text-text sm:text-4xl">How It Works</h2>
            <p className="mt-3 text-gray-600">
              Three simple steps to sharper, more confident speech.
            </p>
          </div>

          <div className="mt-14 grid gap-8 md:grid-cols-3">
            {HOW_IT_WORKS.map((item) => (
              <div
                key={item.step}
                className="relative rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-100"
              >
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary-light text-sm font-semibold text-primary-dark">
                  {item.step}
                </span>
                <div className="mt-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-light text-primary">
                  {item.icon}
                </div>
                <h3 className="mt-4 font-semibold text-text">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl text-text sm:text-4xl">Key Features</h2>
            <p className="mt-3 text-gray-600">
              Everything you need to practice, improve, and speak with eloquence.
            </p>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {KEY_FEATURES.map((feature) => (
              <FeatureCard
                key={feature.title}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
              />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-200/80 bg-white/60 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-3xl text-text sm:text-4xl">
            Ready to improve your eloquence?
          </h2>
          <p className="mt-4 text-gray-600">
            Join Loqui and start building confidence with AI-powered speech coaching today.
          </p>
          <Link
            to="/login"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-dark"
          >
            Start Free
            <ArrowRightIcon />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200/80 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <p className="text-sm text-gray-500">&copy; {year} Loqui. All rights reserved.</p>
          <div className="flex items-center gap-6 text-sm">
            <a href="#" className="text-gray-600 transition-colors hover:text-text">
              Privacy
            </a>
            <a href="#" className="text-gray-600 transition-colors hover:text-text">
              Terms
            </a>
            <a href="#" className="text-gray-600 transition-colors hover:text-text">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </DotGridBackground>
  );
}
