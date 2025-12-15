# Chess AI - Web Application Setup

Complete setup guide to run the Chess AI web application locally.

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd web
npm install
```

### 3. Start the Backend (Terminal 1)

```bash
cd backend
python main.py
```

The API will run on `http://localhost:8000`

### 4. Start the Frontend (Terminal 2)

```bash
cd web
npm run dev
```

The web app will open at `http://localhost:3000`

## 🎮 How to Use

1. **Start a Game**: The board is ready when you load the page
2. **Make Your Move**: Click and drag pieces to move
3. **AI Responds**: The engine automatically makes its move
4. **View Analysis**: See engine evaluation, nodes searched, and principal variation
5. **Adjust Difficulty**: Use the depth selector (3-8)
6. **New Game**: Click "New Game" button anytime

## 📁 Project Structure

```
Chess-AI/
├── backend/           # FastAPI REST API
│   ├── main.py       # API server
│   └── requirements.txt
├── web/              # React frontend
│   ├── src/
│   │   ├── App.jsx   # Main app component
│   │   └── App.css   # Styling
│   ├── package.json
│   └── vite.config.js
├── engine/           # Chess engine (existing)
└── uci/             # UCI protocol (existing)
```

## 🌐 Deployment

### Deploy to Vercel (Frontend)

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Set root directory to `web`
5. Deploy!

### Backend Hosting Options

- **Railway**: Easy Python app hosting
- **Render**: Free tier available
- **DigitalOcean**: App Platform
- **AWS/GCP**: EC2 or Cloud Run

## 🎨 Features

✅ Beautiful responsive UI
✅ Real-time engine analysis
✅ Move history display
✅ Principal Variation (PV) visualization
✅ Adjustable engine depth
✅ Drag-and-drop pieces
✅ Legal move validation
✅ Checkmate detection

## 🐛 Troubleshooting

**Backend not starting?**
- Make sure all dependencies are installed: `pip install -r backend/requirements.txt`
- Check if port 8000 is available

**Frontend not connecting to backend?**
- Verify backend is running on port 8000
- Check browser console for errors

**Pieces not moving?**
- Make sure you're dragging from a valid starting square
- Only your pieces (white) can be moved when it's your turn

## 📦 Dependencies

**Backend:**
- FastAPI
- Uvicorn
- Pydantic

**Frontend:**
- React
- Vite
- react-chessboard
- chess.js
- axios

## 🎯 Next Steps

Want to add more features? Consider:
- Time controls
- Undo/Redo moves
- Save/Load games (PGN)
- Multiple difficulty presets
- Opening book
- Mobile app (React Native)
