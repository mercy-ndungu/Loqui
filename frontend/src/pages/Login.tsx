import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, signup } from "@/services/auth";
import { getMe } from "@/services/users";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/utils/apiErrors";
import { sanitizeInput } from "@/utils/sanitize";
import {
  getPasswordErrors,
  isValidEmail,
  passwordMeetsRequirements,
} from "@/utils/validation";

type Tab = "login" | "signup";

interface LoginProps {
  onLoginSuccess?: () => void;
}

const FEATURES = [
  { title: "AI-Powered Feedback", desc: "Get eloquence scores and actionable coaching" },
  { title: "Practice Presentations", desc: "Record yourself and refine your delivery" },
  { title: "Sound Natural & Eloquent", desc: "Build confidence for high-stakes moments" },
];

function CheckIcon() {
  return (
    <svg className="h-5 w-5 shrink-0 text-primary" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const navigate = useNavigate();
  const { loginSuccess } = useAuth();
  const [tab, setTab] = useState<Tab>("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [fullName, setFullName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<string[]>([]);

  const handleAuthSuccess = async () => {
    try {
      const user = await getMe();
      loginSuccess(user);
      onLoginSuccess?.();
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, "Logged in but could not load your profile. Try again."));
      throw err;
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    const email = sanitizeInput(loginEmail);
    if (!email || !loginPassword) {
      setError("Login failed");
      return;
    }
    if (!isValidEmail(email)) {
      setError("Login failed");
      return;
    }
    setLoading(true);
    try {
      await login(email, loginPassword);
      await handleAuthSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err, "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setFieldErrors([]);

    const name = sanitizeInput(fullName);
    const email = sanitizeInput(signupEmail);
    const errors: string[] = [];

    if (!name) errors.push("Full name is required");
    if (!email) errors.push("Email is required");
    else if (!isValidEmail(email)) errors.push("Enter a valid email address");
    if (!passwordMeetsRequirements(signupPassword)) {
      errors.push(...getPasswordErrors(signupPassword));
    }
    if (signupPassword !== confirmPassword) {
      errors.push("Passwords do not match");
    }

    if (errors.length) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      await signup(email, signupPassword, name);
      await handleAuthSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
  };

  const passwordHints = getPasswordErrors(signupPassword);

  return (
    <div className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto max-w-lg">
        <div className="mb-8 text-center">
          <h1 className="font-display text-4xl text-text">Loqui</h1>
          <p className="mt-2 text-sm text-gray-600">Master eloquent speech with AI coaching</p>
        </div>

        <div className="overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-gray-100 transition-shadow">
          <div className="flex border-b border-gray-100">
            {(["login", "signup"] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => {
                  setTab(t);
                  setError("");
                  setFieldErrors([]);
                }}
                className={`flex-1 py-4 text-sm font-semibold capitalize transition-colors ${
                  tab === t
                    ? "border-b-2 border-primary text-primary"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {t === "login" ? "Login" : "Sign Up"}
              </button>
            ))}
          </div>

          <div className="p-6 sm:p-8">
            {error && (
              <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-error" role="alert">
                {error}
              </div>
            )}

            {tab === "login" ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label htmlFor="login-email" className="mb-1 block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="you@example.com"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="login-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-sm font-semibold text-white transition hover:bg-primary-dark disabled:opacity-60"
                >
                  {loading ? <LoadingSpinner size="sm" className="border-white border-t-transparent" /> : null}
                  Login
                </button>
              </form>
            ) : (
              <form onSubmit={handleSignup} className="space-y-4">
                {fieldErrors.length > 0 && (
                  <ul className="space-y-1 rounded-lg bg-red-50 px-4 py-3 text-sm text-error">
                    {fieldErrors.map((msg) => (
                      <li key={msg}>• {msg}</li>
                    ))}
                  </ul>
                )}
                <div>
                  <label htmlFor="full-name" className="mb-1 block text-sm font-medium text-gray-700">
                    Full Name
                  </label>
                  <input
                    id="full-name"
                    type="text"
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="signup-email" className="mb-1 block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    id="signup-email"
                    type="email"
                    autoComplete="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="signup-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <input
                    id="signup-password"
                    type="password"
                    autoComplete="new-password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                  <ul className="mt-2 space-y-0.5 text-xs text-gray-500">
                    {["At least 8 characters", "One uppercase letter", "One number"].map((rule) => (
                      <li
                        key={rule}
                        className={
                          signupPassword && !passwordHints.includes(rule) ? "text-primary" : ""
                        }
                      >
                        {signupPassword && !passwordHints.includes(rule) ? "✓" : "○"} {rule}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <label htmlFor="confirm-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Confirm Password
                  </label>
                  <input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-sm font-semibold text-white transition hover:bg-primary-dark disabled:opacity-60"
                >
                  {loading ? <LoadingSpinner size="sm" className="border-white border-t-transparent" /> : null}
                  Create Account
                </button>
              </form>
            )}
          </div>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100 transition hover:shadow-md"
            >
              <div className="mb-2 flex items-center gap-2">
                <CheckIcon />
                <h3 className="text-sm font-semibold text-text">{f.title}</h3>
              </div>
              <p className="text-xs text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
