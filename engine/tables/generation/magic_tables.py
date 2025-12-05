"""
Magic bitboard tables for sliding piece move generation.

Pre-computed magic numbers and attack tables for rooks and bishops.
Run save_magic_tables() to regenerate or expand tables.
"""

import numpy as np
from pathlib import Path

# Global tables (loaded on import)
ROOK_MAGICS_DATA = None
BISHOP_MAGICS_DATA = None


def _get_table_path(name: str) -> Path:
    """Get path to .npy table file."""
    return Path(__file__).parent.parent / f"{name}.npy"


def get_default_rook_magics():
    """Get default rook magic numbers."""
    return [
        0x0080001020400080, 0x0040001000200040, 0x0080081000200080, 0x0080040800100080,
        0x0080020400080080, 0x0080010200040080, 0x0080008001000200, 0x0080002040800100,
        0x0000800020400080, 0x0000400020005000, 0x0000801000200080, 0x0000800800100080,
        0x0000800400080080, 0x0000800200040080, 0x0000800100020080, 0x0000800040800100,
        0x0000208000400080, 0x0000404000201000, 0x0000808010000800, 0x0000808008000400,
        0x0000808004000200, 0x0000808002000100, 0x0000800100020080, 0x0000800041000080,
        0x00FFFCDDFCED714A, 0x007FFCDDFCED714A, 0x003FFFCDFFD88096, 0x0000040810002101,
        0x0001000204080011, 0x0001000204000801, 0x0001000082000401, 0x0001FFFAABFAD1A2,
        0x0000040008001020, 0x0000020008001020, 0x0000010008001020, 0x0000008008001020,
        0x0000004008001020, 0x0000002008001020, 0x0000001008001020, 0x0000000808001020,
        0x0000400080002040, 0x0000200040002040, 0x0000100020002040, 0x0000080010002040,
        0x0000040008002040, 0x0000020004002040, 0x0000010002002040, 0x0000008001002040,
        0x0000004000800204, 0x0000002000400204, 0x0000001000200204, 0x0000000800100204,
        0x0000000400080204, 0x0000000200040204, 0x0000000100020204, 0x0000000080010204,
        0x0000000040008002, 0x0000000020004002, 0x0000000010002002, 0x0000000008001002,
        0x0000000004000802, 0x0000000002000402, 0x0000000001000202, 0x0000000000800102,
    ]


def get_default_bishop_magics():
    """Get default bishop magic numbers."""
    return [
        0x0002020202020200, 0x0002020202020000, 0x0004010202000000, 0x0004040080000000,
        0x0001104000000000, 0x0000821040000000, 0x0000410410400000, 0x0000104104104000,
        0x0000040404040400, 0x0000020202020200, 0x0000040102020000, 0x0000040400800000,
        0x0000011040000000, 0x0000008210400000, 0x0000004104104000, 0x0000002082082000,
        0x0004000808080800, 0x0002000404040400, 0x0001000202020200, 0x0000800802004000,
        0x0000800400A00000, 0x0000200100884000, 0x0000400082082000, 0x0000200041041000,
        0x0002080010101000, 0x0001040008080800, 0x0000208004010400, 0x0000404004010200,
        0x0000840000802000, 0x0000404002011000, 0x0000808001041000, 0x0000404000820800,
        0x0001041000202000, 0x0000820800101000, 0x0000104400080800, 0x0000020080080080,
        0x0000404040040100, 0x0000808100020100, 0x0001010100020800, 0x0000808080010400,
        0x0000820820004000, 0x0000410410002000, 0x0000082088001000, 0x0000002011000800,
        0x0000080100400400, 0x0001010101000200, 0x0002020202000400, 0x0001010101000200,
        0x0000410410400000, 0x0000208208200000, 0x0000002084100000, 0x0000000020880000,
        0x0000001002020000, 0x0000040408020000, 0x0004040404040000, 0x0002020202020000,
        0x0000104104104000, 0x0000002082082000, 0x0000000020841000, 0x0000000000208800,
        0x0000000010020200, 0x0000000404080200, 0x0000040404040400, 0x0002020202020200,
    ]


def save_magic_tables():
    """Save magic bitboard tables to .npy files."""
    rook_magics = np.array(get_default_rook_magics(), dtype=np.uint64)
    bishop_magics = np.array(get_default_bishop_magics(), dtype=np.uint64)
    
    np.save(_get_table_path('rook_magics'), rook_magics)
    np.save(_get_table_path('bishop_magics'), bishop_magics)
    
    print(f"[Magic] Saved tables")
    print(f"  - Rook magics: {rook_magics.nbytes} bytes")
    print(f"  - Bishop magics: {bishop_magics.nbytes} bytes")


def load_magic_tables():
    """Load magic tables from .npy files, generate if missing."""
    global ROOK_MAGICS_DATA, BISHOP_MAGICS_DATA
    
    try:
        ROOK_MAGICS_DATA = np.load(_get_table_path('rook_magics'))
        BISHOP_MAGICS_DATA = np.load(_get_table_path('bishop_magics'))
    except FileNotFoundError:
        # Generate and save if files don't exist
        print("[Magic] Tables not found, generating...")
        save_magic_tables()
        load_magic_tables()


def _ensure_loaded():
    """Lazy load tables on first access."""
    global ROOK_MAGICS_DATA
    if ROOK_MAGICS_DATA is None:
        load_magic_tables()


# Lazy loading wrappers
def get_rook_magics():
    """Get rook magic numbers (lazy loaded)."""
    _ensure_loaded()
    return ROOK_MAGICS_DATA


def get_bishop_magics():
    """Get bishop magic numbers (lazy loaded)."""
    _ensure_loaded()
    return BISHOP_MAGICS_DATA

