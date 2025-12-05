"""
Zobrist hashing keys for transposition table.

Pre-computed random 64-bit keys for position hashing.
Run generate_zobrist_keys() to regenerate with new seed.
"""

import numpy as np
from pathlib import Path

# Table dimensions
ZOBRIST_PIECES_SHAPE = (12, 64)  # 12 piece types × 64 squares
ZOBRIST_CASTLING_SHAPE = 16      # 2^4 castling rights combinations
ZOBRIST_EN_PASSANT_SHAPE = 8     # 8 files for en passant
ZOBRIST_SIDE_SHAPE = 1           # Side to move toggle

# Global tables (loaded on import)
ZOBRIST_PIECES = None
ZOBRIST_CASTLING = None
ZOBRIST_EN_PASSANT = None
ZOBRIST_SIDE_TO_MOVE = None


def _get_table_path(name: str) -> Path:
    """Get path to .npy table file."""
    return Path(__file__).parent.parent / f"{name}.npy"


def generate_zobrist_keys(seed: int = 42):
    """
    Generate Zobrist keys with given random seed.
    
    Args:
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (pieces, castling, en_passant, side_to_move)
    """
    rng = np.random.RandomState(seed)
    
    # Generate random 64-bit keys (combine two 32-bit integers)
    def rand64(size):
        if isinstance(size, int):
            size = (size,)
        high = rng.randint(0, 2**31, size=size, dtype=np.int64).astype(np.uint64) << 32
        low = rng.randint(0, 2**31, size=size, dtype=np.int64).astype(np.uint64)
        return high | low
    
    pieces = rand64(ZOBRIST_PIECES_SHAPE)
    castling = rand64(ZOBRIST_CASTLING_SHAPE)
    en_passant = rand64(ZOBRIST_EN_PASSANT_SHAPE)
    side_to_move = rand64(1)[0]  # Scalar for side to move
    
    return pieces, castling, en_passant, side_to_move


def save_zobrist_keys(seed: int = 42):
    """Save Zobrist keys to .npy files."""
    pieces, castling, en_passant, side = generate_zobrist_keys(seed)
    
    np.save(_get_table_path('zobrist_pieces'), pieces)
    np.save(_get_table_path('zobrist_castling'), castling)
    np.save(_get_table_path('zobrist_en_passant'), en_passant)
    np.save(_get_table_path('zobrist_side_to_move'), np.array([side], dtype=np.uint64))
    
    print(f"[Zobrist] Saved keys (seed={seed})")
    print(f"  - Pieces: {pieces.nbytes // 1024}KB")
    print(f"  - Castling: {castling.nbytes} bytes")
    print(f"  - En passant: {en_passant.nbytes} bytes")
    print(f"  - Side to move: 8 bytes")


def load_zobrist_keys():
    """Load Zobrist keys from .npy files, generate if missing."""
    global ZOBRIST_PIECES, ZOBRIST_CASTLING, ZOBRIST_EN_PASSANT, ZOBRIST_SIDE_TO_MOVE
    
    try:
        ZOBRIST_PIECES = np.load(_get_table_path('zobrist_pieces'))
        ZOBRIST_CASTLING = np.load(_get_table_path('zobrist_castling'))
        ZOBRIST_EN_PASSANT = np.load(_get_table_path('zobrist_en_passant'))
        ZOBRIST_SIDE_TO_MOVE = np.load(_get_table_path('zobrist_side_to_move'))[0]
    except FileNotFoundError:
        # Generate and save if files don't exist
        print("[Zobrist] Keys not found, generating...")
        save_zobrist_keys()
        load_zobrist_keys()


def _ensure_loaded():
    """Lazy load tables on first access."""
    global ZOBRIST_PIECES
    if ZOBRIST_PIECES is None:
        load_zobrist_keys()


# Lazy loading wrappers
def get_zobrist_pieces():
    """Get Zobrist piece keys (lazy loaded)."""
    _ensure_loaded()
    return ZOBRIST_PIECES


def get_zobrist_castling():
    """Get Zobrist castling keys (lazy loaded)."""
    _ensure_loaded()
    return ZOBRIST_CASTLING


def get_zobrist_en_passant():
    """Get Zobrist en passant keys (lazy loaded)."""
    _ensure_loaded()
    return ZOBRIST_EN_PASSANT


def get_zobrist_side_to_move():
    """Get Zobrist side to move key (lazy loaded)."""
    _ensure_loaded()
    return ZOBRIST_SIDE_TO_MOVE
