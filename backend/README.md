# Chess AI Backend

FastAPI REST API server for the Chess AI engine.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### `POST /api/newgame`
Start a new game.

**Response:**
```json
{
  "success": true,
  "fen": "...",
  "legal_moves": ["e2e4", "e2e3", ...],
  "is_checkmate": false,
  "is_stalemate": false
}
```

### `POST /api/move`
Make a move.

**Request:**
```json
{
  "move": "e2e4"
}
```

**Response:**
```json
{
  "success": true,
  "move": "e2e4",
  "fen": "...",
  "legal_moves": [...],
  "is_checkmate": false,
  "is_stalemate": false
}
```

### `POST /api/engine`
Get engine's best move.

**Request:**
```json
{
  "depth": 5,
  "time_ms": 5000
}
```

**Response:**
```json
{
  "best_move": "e2e4",
  "score": 45,
  "depth": 5,
  "nodes": 12345,
  "time_ms": 1234,
  "pv": ["e2e4", "e7e5", "g1f3"],
  "fen": "..."
}
```

### `GET /api/position`
Get current position info.

## Deployment

For production deployment (Vercel, etc.), use:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
