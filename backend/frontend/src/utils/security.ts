/** Security helpers for the Loqui frontend. */

const AUTH_FLAG_KEY = "loqui_authenticated";
const CSRF_COOKIE_NAME = "csrf_token";

/** In dev, default to the Vite `/api` proxy so CSRF cookies stay same-origin. */
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "/api" : "http://localhost:8000");

let csrfToken: string | null = null;

export function setAuthenticatedFlag(value: boolean): void {
  if (value) {
    sessionStorage.setItem(AUTH_FLAG_KEY, "1");
  } else {
    sessionStorage.removeItem(AUTH_FLAG_KEY);
  }
}

export function hasAuthenticatedFlag(): boolean {
  return sessionStorage.getItem(AUTH_FLAG_KEY) === "1";
}

/** Redirect to HTTPS in production builds. */
export function enforceHttps(): void {
  if (
    import.meta.env.PROD &&
    typeof window !== "undefined" &&
    window.location.protocol === "http:" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  ) {
    window.location.replace(window.location.href.replace("http:", "https:"));
  }
}

function readCsrfFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${CSRF_COOKIE_NAME}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

/** Fetch and cache a CSRF token from the backend (uses fetch to avoid circular imports). */
export async function initCsrfToken(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (response.ok) {
      const data = (await response.json()) as { csrf_token: string };
      csrfToken = data.csrf_token ?? readCsrfFromCookie();
    } else {
      csrfToken = readCsrfFromCookie();
    }
  } catch {
    csrfToken = readCsrfFromCookie();
  }
}

export function getCsrfToken(): string | null {
  return csrfToken ?? readCsrfFromCookie();
}

/** CSRF + AJAX headers for state-changing API requests. */
export function getCsrfHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Requested-With": "XMLHttpRequest",
  };
  const token = getCsrfToken();
  if (token) {
    headers["X-CSRF-Token"] = token;
  }
  return headers;
}

/** Initialize all client-side security measures. */
export async function initSecurity(): Promise<void> {
  enforceHttps();
  await initCsrfToken();
}
