# 🚀 Deployment Guide — RainWise (PS 26080)
## Vercel (Frontend) + Render (Backend)

---

## Architecture

```
Browser
  ↓  HTTPS
Vercel  ──── serves ────  Next.js frontend (rainwise.vercel.app)
                                  ↓  REST API calls
                         Render  ──── serves ────  FastAPI backend (rainwise-api.onrender.com)
```

---

## Step 1 — Push to GitHub

Create a **single GitHub repo** with this structure:
```
megha/
├── frontend/     ← Next.js app (Vercel reads this)
├── backend/      ← FastAPI app (Render reads this)
├── vercel.json   ← Tells Vercel: rootDirectory = frontend
├── render.yaml   ← Tells Render: rootDir = backend
└── ...
```

```bash
cd "c:\My Imp Files\My Projects\megha"
git init
git add .
git commit -m "feat: initial RainWise setup — PS 26080"
git remote add origin https://github.com/YOUR_USERNAME/rainwise-ps26080.git
git push -u origin main
```

---

## Step 2 — Deploy Backend on Render (FREE)

1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. Click **Deploy**
6. Note your URL: `https://rainwise-api.onrender.com`

> ⚠️ Free Render services **spin down** after 15min inactivity (30s cold start).
> For SIH demo day, open the API URL 2 mins before presenting to wake it up.

---

## Step 3 — Deploy Frontend on Vercel (FREE)

1. Go to [vercel.com](https://vercel.com) → Sign up with GitHub
2. Click **Add New Project** → Import your GitHub repo
3. Vercel auto-detects `vercel.json` → sets `rootDirectory = frontend`
4. **Environment Variables** → Add:
   ```
   NEXT_PUBLIC_API_URL = https://rainwise-api.onrender.com
   ```
5. Click **Deploy**
6. Your app is live at: `https://rainwise.vercel.app` 🎉

---

## Step 4 — Set Custom Domain (Optional but impressive)

In Vercel dashboard → **Domains** → Add `rainwise.live` (buy for ≈ ₹800/yr)

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs at: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# Open: http://localhost:3000
```

---

## Environment Variables Summary

| Variable | Where | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Vercel | `https://rainwise-api.onrender.com` |
| `PORT` | Render (auto) | Set by Render automatically |

---

## Verify Deployment

```bash
# Check backend health
curl https://rainwise-api.onrender.com/health

# Check regime endpoint
curl "https://rainwise-api.onrender.com/api/regime?date=2024-07-15&lead_h=24"
```

---

## What Judges Will See

| URL | What |
|---|---|
| `https://rainwise.vercel.app` | Full dashboard — regime card, maps, table |
| `https://rainwise-api.onrender.com/docs` | Auto-generated Swagger API docs |
| GitHub repo | Full source code |

---

*Total hosting cost: **₹0/month** (both free tiers)*
