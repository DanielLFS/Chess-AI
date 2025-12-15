# Chess AI Web Interface

Beautiful React web interface for the Chess AI engine.

## Setup

1. Install Node.js (https://nodejs.org/)

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Production Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Features

- 🎨 Beautiful, responsive chessboard UI
- 🤖 Play against the AI engine
- 📊 Real-time engine analysis
- 🎯 Principal Variation (PV) display
- 📈 Move history
- ⚙️ Adjustable engine depth (3-8)
- 🎮 Drag-and-drop piece movement

## Deployment to Vercel

1. Push your code to GitHub

2. Go to [Vercel](https://vercel.com/)

3. Click "New Project"

4. Import your GitHub repository

5. Configure:
   - Framework Preset: Vite
   - Root Directory: `web`
   - Build Command: `npm run build`
   - Output Directory: `dist`

6. Add environment variable:
   - `VITE_API_URL` = your backend API URL

7. Deploy!

## Requirements

- Node.js 16+
- Backend API running on `http://localhost:8000` (or configure in `vite.config.js`)
