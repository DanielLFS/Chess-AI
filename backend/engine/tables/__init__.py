"""
Pre-computed lookup tables for chess engine.

Tables are stored as NumPy .npy binary files for:
- Ultra-fast loading (memory-mapped)
- Compact storage (~10x smaller than JSON)
- Easy versioning and regeneration
- Zero parsing overhead

Usage:
    from engine.tables import zobrist_keys, magic_tables, pst_tables
    
    # Tables are auto-loaded on import
    zobrist = zobrist_keys.ZOBRIST_PIECES
    magics = magic_tables.ROOK_MAGICS_DATA
    pst = pst_tables.PST_MG

To regenerate tables:
    python -m engine.tables.generation.generate_all
"""

from .generation import zobrist_keys
from .generation import magic_tables  
from .generation import pst_tables

__all__ = [
    'zobrist_keys',
    'magic_tables',
    'pst_tables'
]
