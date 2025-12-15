# Vercel Deployment Guide

## 🚀 Deploying to Vercel

Your Chess AI project has separate frontend (React) and backend (Python) that need to be deployed separately.

### Frontend Deployment (Vercel)

1. **Go to Vercel Dashboard**: https://vercel.com/
2. **Import your GitHub repository**
3. **Configure Project Settings**:
   - **Root Directory**: `web` ⚠️ IMPORTANT
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

4. **Environment Variables** (if using external backend):
   - `VITE_API_URL` = Your backend URL (e.g., `https://your-backend.railway.app`)

5. **Deploy**!

### Backend Deployment Options

Since Vercel doesn't support Python FastAPI well, deploy your backend to:

#### Option 1: Railway (Recommended - Free tier)
1. Go to https://railway.app/
2. Create new project from GitHub
3. Select your `Chess-AI` repository
4. Set Root Directory to `backend`
5. Railway will auto-detect Python
6. Add build command: `pip install -r requirements.txt`
7. Add start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
8. Deploy!

#### Option 2: Render (Free tier)
1. Go to https://render.com/
2. New Web Service
3. Connect GitHub repository
4. Settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy!

#### Option 3: Fly.io (Free tier)
Create a `Dockerfile` in backend folder:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Then deploy with:
```bash
fly launch
fly deploy
```

### Connecting Frontend to Backend

After deploying backend, update your frontend to use the backend URL:

**Option A: Environment Variable**
In Vercel, add environment variable:
- `VITE_API_URL` = `https://your-backend-url.com`

Then update `web/vite.config.js`:
```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: import.meta.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

**Option B: Direct API URL**
Update `web/src/App.jsx` to use your backend URL directly:
```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
axios.post(`${API_BASE}/api/move`, ...)
```

### Testing Deployment

1. Visit your Vercel URL
2. Try making a move
3. Check browser console (F12) for any errors
4. Verify API calls are reaching your backend

### Troubleshooting

**Frontend deploys but shows blank page:**
- Check Vercel build logs
- Verify Root Directory is set to `web`
- Check browser console for errors

**API calls failing:**
- Verify backend is running (visit backend URL directly)
- Check CORS settings in backend
- Verify environment variables are set

**Backend deployment fails:**
- Check that all dependencies are in requirements.txt
- Verify Python version compatibility
- Check logs in hosting platform

### Local Development

To test the deployed setup locally:
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend  
cd web
npm run dev
```

Visit http://localhost:3000

## 🎯 Quick Vercel Settings

When you see the Vercel import screen:

```
Root Directory: web
Framework: Vite  
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

That's it! 🚀
