import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import ErrorBoundary from "@/components/common/ErrorBoundary";
import { initSecurity } from "@/utils/security";
import { registerServiceWorker } from "@/lib/serviceWorker";

async function bootstrap() {
  try {
    await initSecurity();
  } catch (err) {
    console.error("[Loqui] Security init failed (app will still load):", err);
  }

  registerServiceWorker();

  const rootEl = document.getElementById("root");
  if (!rootEl) {
    console.error("[Loqui] #root element not found");
    return;
  }

  createRoot(rootEl).render(
    <StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ErrorBoundary>
    </StrictMode>,
  );
}

void bootstrap();
