# Deployment Guide

## Quick Setup

### Option 1: Railway (Recommended for now)
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select `Chess-AI` repository
5. Set Root Directory: `api`
6. Add environment variable: `PORT=8000`
7. Deploy!
8. Copy the Railway URL (e.g., `https://your-app.railway.app`)

### Option 2: Fly.io
1. Install Fly CLI: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`
2. Run: `fly auth login`
3. Navigate to api folder: `cd api`
4. Run: `fly launch` (follow prompts)
5. Deploy: `fly deploy`
6. Copy the Fly URL (e.g., `https://your-app.fly.dev`)

### Option 3: Your Home Server (Future)
1. Set up your server with Python and FastAPI
2. Configure Cloudflare Tunnel or port forwarding
3. Get your domain/IP (e.g., `https://chess.yourdomain.com`)

## Connect Frontend to Backend

### For Local Development (Both servers running)
No changes needed - uses proxy in package.json

### For Production (Backend deployed)
1. Create `web/.env` file:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app
   ```

2. In Vercel Dashboard:
   - Go to Project Settings → Environment Variables
   - Add: `REACT_APP_API_URL` = `https://your-railway-app.railway.app`
   - Redeploy

### Switching Between Hosting Options
Just update the `REACT_APP_API_URL` environment variable:
- Railway: `https://your-app.railway.app`
- Fly.io: `https://your-app.fly.dev`
- Home Server: `https://chess.yourdomain.com`

No code changes needed!

## Current Status
- ✅ Frontend: Deployed on Vercel
- ⏳ Backend: Ready to deploy (choose Railway or Fly.io)
- 📋 Future: Migrate to home server when ready
