import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

const BACKEND_URL = process.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png", "offline.html"],
      manifest: false,
      injectRegister: false,
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2,webmanifest}"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//, /^\/offline\.html$/],
        offlineGoogleAnalytics: false,
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: "CacheFirst",
            options: {
              cacheName: "google-fonts-stylesheets",
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: "CacheFirst",
            options: {
              cacheName: "google-fonts-webfonts",
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
            },
          },
          {
            urlPattern: new RegExp(
              `^${BACKEND_URL.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}/(users|presentations|recordings|feedback|auth|challenges)(/|$)`,
              "i",
            ),
            handler: "NetworkFirst",
            options: {
              cacheName: "loqui-api-cache",
              networkTimeoutSeconds: 10,
              expiration: { maxEntries: 64, maxAgeSeconds: 60 * 5 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ request }) => request.destination === "document",
            handler: "NetworkFirst",
            options: {
              cacheName: "loqui-pages",
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 32, maxAgeSeconds: 60 * 60 * 24 },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
