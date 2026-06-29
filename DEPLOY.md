# Loqui — Deploy guide (Render + Vercel)

Use this checklist in order. Copy/paste the blocks into the places indicated.

---

## Important: your Render URL

`ed8fc46a09b1f5a50a05099b50feb8d5` is a **Render service ID**, not the public API URL.

Your API URL looks like:

```text
https://YOUR-SERVICE-NAME.onrender.com
```

Find it in Render → your web service → top of the page (click to open).  
Test it:

```bash
curl -s https://YOUR-SERVICE-NAME.onrender.com/health
```

Expected: `{"status":"ok"}`

Use that full `https://...onrender.com` URL everywhere below (no trailing slash).

---

## Step 1 — Render backend environment variables

Render → **loqui-backend** (or your service) → **Environment** → add each variable.

Paste values from your local `backend/.env` where noted.

| Key | Paste this |
|-----|------------|
| `SUPABASE_URL` | From `backend/.env` |
| `SUPABASE_SERVICE_ROLE_KEY` | From `backend/.env` (must be **service_role**, not anon) |
| `JWT_SECRET` | From `backend/.env` |
| `ANTHROPIC_API_KEY` | From `backend/.env` (optional; topics only) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` |
| `UNSPLASH_ACCESS_KEY` | From `backend/.env` (optional) |
| `TRANSCRIPTION_PROVIDER` | `whisper` |
| `WHISPER_MODEL` | `base` |
| `WHISPER_DEVICE` | `cpu` |
| `WHISPER_COMPUTE_TYPE` | `int8` |
| `ENVIRONMENT` | `production` |
| `COOKIE_SECURE` | `true` |
| `CORS_ORIGINS` | `https://YOUR-VERCEL-APP.vercel.app` *(update after Step 4)* |

Click **Save Changes** → Render redeploys (5–10 min first time).

**Render service settings (if not set yet):**

| Setting | Value |
|---------|--------|
| Root Directory | `backend` |
| Environment | Docker |
| Instance Type | Free |
| Health Check Path | `/health` |

---

## Step 2 — Confirm backend is live

Replace `YOUR-SERVICE-NAME` with your real subdomain:

```bash
curl -s https://YOUR-SERVICE-NAME.onrender.com/health
curl -s https://YOUR-SERVICE-NAME.onrender.com/docs
```

If you get 502 or “Application failed to respond”, open Render → **Logs** and wait for `Application startup complete`.

Free tier: first request after idle can take **30–60 seconds** (cold start).

---

## Step 3 — Update `frontend/vercel.json`

Replace `YOUR-SERVICE-NAME` with your Render hostname (no `https://` in the hostname part only in the full URL below):

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://YOUR-SERVICE-NAME.onrender.com/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Example** (if your URL is `https://loqui-backend.onrender.com`):

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://loqui-backend.onrender.com/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Commit and push:

```bash
cd ~/loqui
git add frontend/vercel.json backend/Dockerfile backend/.dockerignore DEPLOY.md
git commit -m "Configure production deploy for Render and Vercel"
git push origin main
```

---

## Step 4 — Deploy frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import GitHub repo: `mercy-ndungu/Loqui`
3. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
4. **Environment Variables** → add:

| Name | Value | Environments |
|------|--------|--------------|
| `VITE_API_URL` | `/api` | Production, Preview, Development |

5. Click **Deploy**

Copy your live URL, e.g. `https://loqui-xxxxx.vercel.app`

---

## Step 5 — Point Render CORS at Vercel

Render → **Environment** → edit `CORS_ORIGINS`:

```text
https://loqui-xxxxx.vercel.app
```

Use your **exact** Vercel URL — no trailing slash.

Save → wait for redeploy.

---

## Step 6 — Production smoke test

Open in browser: `https://loqui-xxxxx.vercel.app`

1. **Landing** page loads
2. **Sign up** → dashboard
3. **Upload** a PDF presentation
4. **Practice** → short recording → feedback

Quick API checks:

```bash
curl -s https://loqui-xxxxx.vercel.app/api/health
curl -s https://loqui-xxxxx.vercel.app/api/auth/csrf
```

Both should return JSON (not 404).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Signup 403 | Hard refresh; check `/api/auth/csrf` works via Vercel |
| CORS error in browser | `CORS_ORIGINS` must match Vercel URL exactly |
| Cookies not saved | `COOKIE_SECURE=true` on Render; use HTTPS on Vercel |
| 502 on Render | Check logs; Docker build must finish; use `/health` |
| Slow first request | Render free tier cold start — normal |
| Feedback fails | Check Render logs; spaCy/NLTK now installed in Dockerfile |

---

## Quick reference

| What | Where |
|------|--------|
| Backend API (direct) | `https://YOUR-SERVICE-NAME.onrender.com` |
| Frontend (users) | `https://YOUR-VERCEL-APP.vercel.app` |
| API via proxy (production) | `https://YOUR-VERCEL-APP.vercel.app/api/...` |
| Render service ID (internal) | `ed8fc46a09b1f5a50a05099b50feb8d5` — **do not** use as API URL |
