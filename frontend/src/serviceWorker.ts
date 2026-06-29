/** Service worker registration and PWA lifecycle hooks. */

type RegisterSWOptions = {
  immediate?: boolean;
  onNeedRefresh?: () => void;
  onOfflineReady?: () => void;
};

export function registerServiceWorker(): void {
  if (!import.meta.env.PROD) return;

  import("virtual:pwa-register")
    .then(({ registerSW }) => {
      registerSW({
        immediate: true,
        onOfflineReady() {
          console.info("Loqui is ready for offline use");
        },
        onNeedRefresh() {
          console.info("Loqui update available — refresh to upgrade");
        },
      } satisfies RegisterSWOptions);
    })
    .catch((err) => {
      console.warn("PWA registration unavailable:", err);
    });
}

/** Prompt the user when a new service worker version is waiting. */
export function onServiceWorkerUpdate(callback: () => void): void {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("controllerchange", callback);
  }
}
