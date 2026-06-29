# Loqui Requirements

Project requirements and deployment notes for the Loqui AI speech coach.

---

## Deployment — Backend

**Platform:** [Render](https://render.com) (free web service tier)

Render is used instead of Railway for the FastAPI backend. The free tier supports Docker, sets `PORT` automatically, and needs no paid plan for hobby deployments. Services spin down after ~15 minutes of inactivity (expect a cold start on the first request after idle).

**Stack pairing:** Frontend on [Vercel](https://vercel.com), database/storage on [Supabase](https://supabase.com).

### Prerequisites

- GitHub repo with `backend/` containing `Dockerfile` and `requirements.txt`
- Supabase project + `service_role` key
- Anthropic API key (optional — topic generation only; feedback uses local spaCy/NLTK scoring)
- Vercel project for the React frontend

### 1. Deploy backend on Render

1. Push code to GitHub (optional: use repo-root `render.yaml` blueprint for one-click setup).
2. [render.com](https://render.com) → **New +** → **Web Service** (or **Blueprint** if using `render.yaml`).
3. Connect the Loqui repository.
4. Configure:
   - **Name:** `loqui-backend` (or your choice)
   - **Root Directory:** `backend`
   - **Environment:** **Docker**
   - **Instance Type:** **Free**
   - **Health Check Path:** `/health`
5. Add environment variables (Render → service → **Environment**):

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_SECRET
JWT_SECRET=YOUR_JWT_SECRET
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY
CLAUDE_MODEL=claude-sonnet-4-6
TRANSCRIPTION_PROVIDER=whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
ENVIRONMENT=production
COOKIE_SECURE=true
CORS_ORIGINS=https://YOUR_VERCEL_APP.vercel.app
UNSPLASH_ACCESS_KEY=YOUR_UNSPLASH_KEY
```

6. Click **Create Web Service** and wait for the deploy to finish.
7. Copy the public URL (e.g. `https://loqui-backend.onrender.com`).

**Verify:**

```bash
curl -s https://YOUR_RENDER_BACKEND_URL/health
# {"status":"ok"}
```

**Troubleshoot:**

- **502 / deploy failed** → Check Render logs; confirm `Dockerfile` builds and `PORT` is used (`uvicorn ... --port ${PORT:-8000}`).
- **Startup errors** → Confirm `SUPABASE_SERVICE_ROLE_KEY` is the service role secret, not the anon key.
- **Slow first request** → Free tier cold start after idle; normal for Render.
- **Recording/feedback timeout** → First Whisper run downloads the model; keep recordings short on free tier or upgrade instance RAM.

### 2. Wire frontend (Vercel) to Render

Use the Vercel `/api` proxy so httpOnly auth cookies stay same-origin.

1. In `frontend/vercel.json`, set the Render URL (no trailing slash):

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://YOUR_RENDER_BACKEND_URL/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

2. Vercel → **Environment Variables** → `VITE_API_URL=/api` (Production + Preview).
3. Redeploy Vercel after updating `vercel.json`.
4. Update Render `CORS_ORIGINS` to your exact Vercel URL (no trailing slash), then redeploy if needed.

**Verify CSRF + auth proxy:**

```bash
curl -s https://YOUR_VERCEL_APP.vercel.app/api/auth/csrf
curl -s https://YOUR_VERCEL_APP.vercel.app/api/health
```

### 3. Production auth notes

- Set `COOKIE_SECURE=true` on Render and serve the frontend over HTTPS on Vercel.
- Do **not** point the browser directly at the Render URL for API calls in production; use `VITE_API_URL=/api` and the Vercel rewrite.
- After deploy, run a full smoke test: signup → login → upload → record → feedback.

### 4. Optional: custom API domain

- Render → service → **Settings** → **Custom Domains** → e.g. `api.yourdomain.com`
- Update `frontend/vercel.json` proxy destination to the custom domain.
- Update `CORS_ORIGINS` to your frontend domain (e.g. `https://app.yourdomain.com`).

### Free tier limits (Render)

| Item | Free tier behavior |
|------|-------------------|
| Cost | $0 / month for one web service |
| Idle | Spins down after ~15 min inactivity |
| Cold start | ~30–60 s after spin-down |
| RAM | 512 MB (tight for Whisper + spaCy; use `WHISPER_MODEL=base`) |
| Build minutes | Limited monthly build time |

For heavier production traffic or faster cold starts, upgrade to a paid Render instance.

---

## Deployment — Frontend

See **§2 Wire frontend** above. Frontend deploys to Vercel with root directory `frontend`, framework **Vite**, and `VITE_API_URL=/api`.

---

## Local development

| Service | URL |
|---------|-----|
| Backend | `http://127.0.0.1:8000` |
| Frontend | `http://localhost:5173` |
| API (dev proxy) | `http://localhost:5173/api` via Vite |

Backend:

```bash
cd ~/loqui/backend && source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd ~/loqui/frontend && npm run dev
```

Use `VITE_API_URL=/api` in `frontend/.env` so CSRF cookies stay same-origin in dev.
