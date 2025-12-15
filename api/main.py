"""
Chess AI - FastAPI Backend
Clean REST API for the React frontend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add backend directory to path for engine imports
# This works whether running from project root or api/ directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(os.path.dirname(current_dir), 'backend')

# Also try absolute path from /app if on Railway
if not os.path.exists(backend_path):
    backend_path = '/app/backend'

if os.path.exists(backend_path):
    sys.path.insert(0, backend_path)
else:
    raise RuntimeError(f"Cannot find backend directory. Tried: {backend_path}")

from engine.board import Board
from engine.search import Search
from engine.moves import generate_legal_moves_numba, Moves

app = FastAPI(title="Chess AI API", version="1.0.0")

# CORS - allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game state storage
game_state = {
    "board": Board(),
    "search": Search(tt_size_mb=64),
    "move_history": []
}


# Health check endpoint for Railway
@app.get("/")
async def root():
    return {"status": "ok", "message": "Chess AI Backend"}


# Request/Response models
class MoveRequest(BaseModel):
    move: str  # UCI format: "e2e4"


class AnalysisRequest(BaseModel):
    depth: Optional[int] = 5


class GameResponse(BaseModel):
    fen: str
    legal_moves: List[str]
    is_checkmate: bool
    is_stalemate: bool
    is_check: bool


class EngineResponse(BaseModel):
    best_move: str
    score: int
    depth: int
    nodes: int
    time_ms: int
    pv: List[str]


# API Endpoints

@app.post("/api/newgame", response_model=GameResponse)
async def new_game():
    """Start a new game."""
    try:
        game_state["board"] = Board()
        game_state["search"] = Search(tt_size_mb=64)
        game_state["move_history"] = []
        
        board = game_state["board"]
        moves_util = Moves(board)
        
        return GameResponse(
            fen=board.to_fen(),
            legal_moves=get_legal_moves_uci(board),
            is_checkmate=False,
            is_stalemate=False,
            is_check=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/move", response_model=GameResponse)
async def make_move(request: MoveRequest):
    """Make a move on the board."""
    try:
        board = game_state["board"]
        move_str = request.move
        
        # Parse UCI move
        if len(move_str) < 4:
            raise HTTPException(status_code=400, detail="Invalid move format")
        
        from_sq = uci_to_square(move_str[0:2])
        to_sq = uci_to_square(move_str[2:4])
        promotion = move_str[4] if len(move_str) > 4 else None
        
        # Find legal move
        legal_moves = generate_legal_moves_numba(board.state, int(board.current_player))
        move = None
        
        for legal_move in legal_moves:
            move_from = legal_move & 0x3F
            move_to = (legal_move >> 6) & 0x3F
            move_flags = (legal_move >> 12) & 0xF
            
            if move_from == from_sq and move_to == to_sq:
                if promotion:
                    promo_pieces = {'q': 1, 'r': 2, 'b': 3, 'n': 4}
                    expected_flag = 8 if promotion == 'q' else 8 + promo_pieces.get(promotion.lower(), 0)
                    if move_flags == expected_flag:
                        move = legal_move
                        break
                else:
                    move = legal_move
                    break
        
        if move is None:
            raise HTTPException(status_code=400, detail="Illegal move")
        
        # Make move
        board.make_move(move)
        game_state["move_history"].append(move_str)
        
        # Check game state
        moves_util = Moves(board)
        
        return GameResponse(
            fen=board.to_fen(),
            legal_moves=get_legal_moves_uci(board),
            is_checkmate=moves_util.is_checkmate(),
            is_stalemate=moves_util.is_stalemate(),
            is_check=moves_util.is_check()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/engine", response_model=EngineResponse)
async def get_engine_move(request: AnalysisRequest):
    """Get best move from engine."""
    try:
        board = game_state["board"]
        search = game_state["search"]
        
        depth = request.depth or 5
        
        # Run search
        import time
        start_time = time.time()
        best_move, score = search.search(board, depth=depth)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if best_move is None:
            raise HTTPException(status_code=500, detail="Engine failed to find move")
        
        # Get PV
        pv = search.get_pv(board, max_depth=10)
        pv_uci = [move_to_uci(m) for m in pv]
        
        return EngineResponse(
            best_move=move_to_uci(best_move),
            score=score,
            depth=depth,
            nodes=search.stats.nodes,
            time_ms=elapsed_ms,
            pv=pv_uci
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/position")
async def get_position():
    """Get current position."""
    board = game_state["board"]
    return {
        "fen": board.to_fen(),
        "legal_moves": get_legal_moves_uci(board),
        "move_history": game_state["move_history"]
    }


# Helper functions

def uci_to_square(uci: str) -> int:
    """Convert UCI (e.g., 'e2') to square index (0-63)."""
    file = ord(uci[0]) - ord('a')
    rank = int(uci[1]) - 1
    return rank * 8 + file


def square_to_uci(square: int) -> str:
    """Convert square index to UCI."""
    file = chr((square % 8) + ord('a'))
    rank = str((square // 8) + 1)
    return file + rank


def move_to_uci(move: int) -> str:
    """Convert encoded move to UCI string."""
    from_sq = move & 0x3F
    to_sq = (move >> 6) & 0x3F
    flags = (move >> 12) & 0xF
    
    uci = square_to_uci(from_sq) + square_to_uci(to_sq)
    
    # Add promotion
    if flags >= 8 and flags <= 11:
        promo_map = {8: 'q', 9: 'r', 10: 'b', 11: 'n'}
        uci += promo_map.get(flags, 'q')
    
    return uci


def get_legal_moves_uci(board: Board) -> List[str]:
    """Get all legal moves in UCI format."""
    legal_moves = generate_legal_moves_numba(board.state, int(board.current_player))
    return [move_to_uci(move) for move in legal_moves]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
