"""
Piece-Square Tables for position evaluation.

Pre-computed bonuses for piece placement (Stockfish-inspired values).
Run save_pst_tables() to regenerate or tune values.
"""

import numpy as np
from pathlib import Path

# Global tables (loaded on import)
PST_MG = None  # Middlegame piece-square tables [12, 64]
PST_EG = None  # Endgame piece-square tables [12, 64]
PIECE_VALUES = None  # Material values [12]


def _get_table_path(name: str) -> Path:
    """Get path to .npy table file."""
    return Path(__file__).parent.parent / f"{name}.npy"


def get_default_piece_values():
    """Get default piece values in centipawns."""
    PAWN_VALUE = 100
    KNIGHT_VALUE = 320
    BISHOP_VALUE = 330
    ROOK_VALUE = 500
    QUEEN_VALUE = 900
    KING_VALUE = 0
    
    return np.array([
        PAWN_VALUE, KNIGHT_VALUE, BISHOP_VALUE, ROOK_VALUE, QUEEN_VALUE, KING_VALUE,
        PAWN_VALUE, KNIGHT_VALUE, BISHOP_VALUE, ROOK_VALUE, QUEEN_VALUE, KING_VALUE
    ], dtype=np.int16)


def get_default_pawn_pst_mg():
    """Default pawn PST middlegame (white perspective, flipped for black)."""
    return np.array([
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ], dtype=np.int16)


def get_default_knight_pst_mg():
    """Default knight PST middlegame."""
    return np.array([
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ], dtype=np.int16)


def get_default_bishop_pst_mg():
    """Default bishop PST middlegame."""
    return np.array([
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ], dtype=np.int16)


def get_default_rook_pst_mg():
    """Default rook PST middlegame."""
    return np.array([
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ], dtype=np.int16)


def get_default_queen_pst_mg():
    """Default queen PST middlegame."""
    return np.array([
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ], dtype=np.int16)


def get_default_king_pst_mg():
    """Default king PST middlegame (prefer safety)."""
    return np.array([
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ], dtype=np.int16)


def generate_pst_tables():
    """
    Generate full PST tables for all pieces.
    
    Returns:
        Tuple of (pst_mg, pst_eg, piece_values)
    """
    pst_mg = np.zeros((12, 64), dtype=np.int16)
    pst_eg = np.zeros((12, 64), dtype=np.int16)
    
    # White pieces (indices 0-5)
    pst_mg[0] = get_default_pawn_pst_mg()
    pst_mg[1] = get_default_knight_pst_mg()
    pst_mg[2] = get_default_bishop_pst_mg()
    pst_mg[3] = get_default_rook_pst_mg()
    pst_mg[4] = get_default_queen_pst_mg()
    pst_mg[5] = get_default_king_pst_mg()
    
    # Black pieces (indices 6-11) - flip vertically
    for piece_type in range(6):
        for sq in range(64):
            rank = sq // 8
            file = sq % 8
            flipped_sq = (7 - rank) * 8 + file
            pst_mg[piece_type + 6, sq] = -pst_mg[piece_type, flipped_sq]
    
    # Endgame tables (simplified: king to center, pawns advanced)
    pst_eg[:] = pst_mg // 2  # Simplified: half of middlegame
    
    piece_values = get_default_piece_values()
    
    return pst_mg, pst_eg, piece_values


def save_pst_tables():
    """Save PST tables to .npy files."""
    pst_mg, pst_eg, piece_values = generate_pst_tables()
    
    np.save(_get_table_path('pst_mg'), pst_mg)
    np.save(_get_table_path('pst_eg'), pst_eg)
    np.save(_get_table_path('piece_values'), piece_values)
    
    print(f"[PST] Saved tables")
    print(f"  - PST MG: {pst_mg.nbytes // 1024}KB")
    print(f"  - PST EG: {pst_eg.nbytes // 1024}KB")
    print(f"  - Piece values: {piece_values.nbytes} bytes")


def load_pst_tables():
    """Load PST tables from .npy files."""
    global PST_MG, PST_EG, PIECE_VALUES
    
    try:
        PST_MG = np.load(_get_table_path('pst_mg'))
        PST_EG = np.load(_get_table_path('pst_eg'))
        PIECE_VALUES = np.load(_get_table_path('piece_values'))
    except FileNotFoundError:
        # Generate if files don't exist
        print("[PST] Tables not found, generating...")
        save_pst_tables()
        load_pst_tables()


def _ensure_loaded():
    """Lazy load tables on first access."""
    global PST_MG
    if PST_MG is None:
        load_pst_tables()


# Lazy loading wrappers
def get_pst_mg():
    """Get middlegame PST (lazy loaded)."""
    _ensure_loaded()
    return PST_MG


def get_pst_eg():
    """Get endgame PST (lazy loaded)."""
    _ensure_loaded()
    return PST_EG


def get_piece_values():
    """Get piece material values (lazy loaded)."""
    _ensure_loaded()
    return PIECE_VALUES
