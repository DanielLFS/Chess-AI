"""
FastAPI backend server for Chess AI.
Provides REST API endpoints for the React frontend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board
from engine.search import Search
from engine.moves import generate_legal_moves_numba, Moves

app = FastAPI(title="Chess AI API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game state
game_state = {
    "board": Board(),
    "search": Search(tt_size_mb=64),
    "move_history": []
}


class MoveRequest(BaseModel):
    move: str  # UCI format: e2e4, e7e5q (promotion)
    

class NewGameRequest(BaseModel):
    fen: Optional[str] = None  # Start from custom position


class AnalysisRequest(BaseModel):
    depth: Optional[int] = 5
    time_ms: Optional[int] = None


class MoveResponse(BaseModel):
    success: bool
    move: Optional[str] = None
    fen: str
    legal_moves: List[str]
    is_checkmate: bool
    is_stalemate: bool
    error: Optional[str] = None


class EngineResponse(BaseModel):
    best_move: str
    score: int
    depth: int
    nodes: int
    time_ms: int
    pv: List[str]
    fen: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Chess AI API is running"}


@app.post("/api/newgame", response_model=MoveResponse)
async def new_game(request: NewGameRequest):
    """Start a new game."""
    try:
        game_state["board"] = Board()
        game_state["search"] = Search(tt_size_mb=64)
        game_state["move_history"] = []
        
        if request.fen:
            # TODO: Add FEN parsing support
            pass
        
        legal_moves = _get_legal_moves_uci(game_state["board"])
        
        return MoveResponse(
            success=True,
            fen=_board_to_fen(game_state["board"]),
            legal_moves=legal_moves,
            is_checkmate=False,
            is_stalemate=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/move", response_model=MoveResponse)
async def make_move(request: MoveRequest):
    """Make a move on the board."""
    try:
        board = game_state["board"]
        move_str = request.move
        
        # Parse UCI move (e.g., "e2e4" or "e7e8q")
        if len(move_str) < 4:
            return MoveResponse(
                success=False,
                fen=_board_to_fen(board),
                legal_moves=_get_legal_moves_uci(board),
                is_checkmate=False,
                is_stalemate=False,
                error="Invalid move format"
            )
        
        from_square = _uci_to_square(move_str[0:2])
        to_square = _uci_to_square(move_str[2:4])
        promotion = move_str[4] if len(move_str) > 4 else None
        
        # Find matching legal move
        legal_moves = generate_legal_moves_numba(board.state, int(board.current_player))
        move = None
        
        for legal_move in legal_moves:
            move_from = legal_move & 0x3F
            move_to = (legal_move >> 6) & 0x3F
            move_flags = (legal_move >> 12) & 0xF
            
            if move_from == from_square and move_to == to_square:
                # Check promotion
                if promotion:
                    promo_pieces = {'q': 3, 'r': 4, 'b': 5, 'n': 6}
                    expected_flag = 8 + promo_pieces.get(promotion.lower(), 0)
                    if move_flags == expected_flag:
                        move = legal_move
                        break
                else:
                    move = legal_move
                    break
        
        if move is None:
            return MoveResponse(
                success=False,
                fen=_board_to_fen(board),
                legal_moves=_get_legal_moves_uci(board),
                is_checkmate=False,
                is_stalemate=False,
                error="Illegal move"
            )
        
        # Make the move
        board.make_move(move)
        game_state["move_history"].append(move_str)
        
        # Check game state
        moves_util = Moves(board)
        new_legal_moves = generate_legal_moves_numba(board.state, int(board.current_player))
        is_checkmate = moves_util.is_checkmate()
        is_stalemate = moves_util.is_stalemate()
        
        return MoveResponse(
            success=True,
            move=move_str,
            fen=_board_to_fen(board),
            legal_moves=_get_legal_moves_uci(board),
            is_checkmate=is_checkmate,
            is_stalemate=is_stalemate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/engine", response_model=EngineResponse)
async def get_engine_move(request: AnalysisRequest):
    """Get the best move from the engine."""
    try:
        board = game_state["board"]
        search = game_state["search"]
        
        depth = request.depth or 5
        time_limit = request.time_ms / 1000.0 if request.time_ms else None
        
        # Run search
        import time
        start_time = time.time()
        best_move, score = search.search(board, depth=depth, time_limit=time_limit)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if best_move is None:
            raise HTTPException(status_code=500, detail="Engine failed to find a move")
        
        # Get principal variation
        pv = search.get_pv(board, max_depth=10)
        pv_uci = [_move_to_uci(m, board) for m in pv]
        
        # Convert best move to UCI
        best_move_uci = _move_to_uci(best_move, board)
        
        return EngineResponse(
            best_move=best_move_uci,
            score=score,
            depth=depth,
            nodes=search.stats.nodes,
            time_ms=elapsed_ms,
            pv=pv_uci,
            fen=_board_to_fen(board)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/position")
async def get_position():
    """Get current board position."""
    board = game_state["board"]
    return {
        "fen": _board_to_fen(board),
        "legal_moves": _get_legal_moves_uci(board),
        "move_history": game_state["move_history"]
    }


# Helper functions

def _uci_to_square(uci: str) -> int:
    """Convert UCI notation (e.g., 'e2') to square index (0-63)."""
    file = ord(uci[0]) - ord('a')
    rank = int(uci[1]) - 1
    return rank * 8 + file


def _square_to_uci(square: int) -> str:
    """Convert square index to UCI notation."""
    file = chr((square % 8) + ord('a'))
    rank = str((square // 8) + 1)
    return file + rank


def _move_to_uci(move: int, board: Board) -> str:
    """Convert encoded move to UCI string."""
    from_sq = move & 0x3F
    to_sq = (move >> 6) & 0x3F
    flags = (move >> 12) & 0xF
    
    uci = _square_to_uci(from_sq) + _square_to_uci(to_sq)
    
    # Add promotion piece
    if flags >= 8 and flags <= 11:
        promo_map = {8: 'q', 9: 'r', 10: 'b', 11: 'n'}
        uci += promo_map.get(flags, 'q')
    
    return uci


def _get_legal_moves_uci(board: Board) -> List[str]:
    """Get all legal moves in UCI format."""
    legal_moves = generate_legal_moves_numba(board.state, int(board.current_player))
    return [_move_to_uci(move, board) for move in legal_moves]


def _board_to_fen(board: Board) -> str:
    """Convert board to FEN string (simplified)."""
    # TODO: Implement full FEN conversion
    # For now, return a placeholder
    return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
