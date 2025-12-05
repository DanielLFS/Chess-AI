"""
Optimized Board Representation Module
Pure numpy/numba implementation with minimal OOP overhead.
Focus: Speed and memory efficiency using vectorization.

Board State stored as numpy arrays:
- piece_array[8,8]: int8, 0=empty, 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king  
- color_array[8,8]: int8, 0=empty, 1=white, -1=black
- castling_rights: uint8 bitmask (bit0=WK, bit1=WQ, bit2=BK, bit3=BQ)
- en_passant_sq: int8, 0-63 or -1 for none
- current_player: int8, 1=white, -1=black
- halfmove_clock: int16
- fullmove_number: int16

All operations are numba-compiled where possible.
"""

import numpy as np
from numba import njit, types
from numba.typed import Dict
from typing import Tuple, Optional
from enum import IntEnum

# Piece type constants (matching encoding)
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

# Color constants
WHITE = 1
BLACK = -1

# Castling rights bitmask
CASTLE_WK = 1  # White kingside
CASTLE_WQ = 2  # White queenside
CASTLE_BK = 4  # Black kingside
CASTLE_BQ = 8  # Black queenside

# Move encoding (uint16)
# Bits 0-5: from_square (0-63)
# Bits 6-11: to_square (0-63)
# Bits 12-14: flags (0=normal, 1-4=promotions, 5-6=castling, 7=en passant)
FLAG_NORMAL = 0
FLAG_PROMOTION_QUEEN = 1
FLAG_PROMOTION_ROOK = 2
FLAG_PROMOTION_BISHOP = 3
FLAG_PROMOTION_KNIGHT = 4
FLAG_CASTLING_KINGSIDE = 5
FLAG_CASTLING_QUEENSIDE = 6
FLAG_EN_PASSANT = 7


@njit(cache=True)
def square_to_coords(square: int) -> Tuple[int, int]:
    """Convert square index (0-63) to (row, col)."""
    return square // 8, square % 8


@njit(cache=True)
def coords_to_square(row: int, col: int) -> int:
    """Convert (row, col) to square index (0-63)."""
    return row * 8 + col


@njit(cache=True)
def encode_move(from_sq: int, to_sq: int, flags: int = 0) -> np.uint16:
    """Encode move into 16-bit integer."""
    return np.uint16((flags << 12) | (to_sq << 6) | from_sq)


@njit(cache=True)
def decode_move(encoded: np.uint16) -> Tuple[int, int, int]:
    """Decode move into (from_sq, to_sq, flags)."""
    from_sq = int(encoded & 0x3F)
    to_sq = int((encoded >> 6) & 0x3F)
    flags = int(encoded >> 12)
    return from_sq, to_sq, flags


@njit(cache=True)
def init_board() -> Tuple:
    """Initialize board to starting position. Returns (piece_array, color_array, state)."""
    pieces = np.zeros((8, 8), dtype=np.int8)
    colors = np.zeros((8, 8), dtype=np.int8)
    
    # Back rank pieces
    back_rank = np.array([ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK], dtype=np.int8)
    
    # Black pieces (row 0-1)
    pieces[0, :] = back_rank
    colors[0, :] = BLACK
    pieces[1, :] = PAWN
    colors[1, :] = BLACK
    
    # White pieces (row 6-7)
    pieces[6, :] = PAWN
    colors[6, :] = WHITE
    pieces[7, :] = back_rank
    colors[7, :] = WHITE
    
    # Initial state: (castling_rights, en_passant_sq, current_player, halfmove, fullmove)
    state = np.array([15, -1, WHITE, 0, 1], dtype=np.int16)  # All castling rights enabled
    
    return pieces, colors, state


@njit(cache=True)
def compute_zobrist_hash(pieces: np.ndarray, colors: np.ndarray, state: np.ndarray,
                         zobrist_pieces: np.ndarray, zobrist_castling: np.ndarray,
                         zobrist_en_passant: np.ndarray, zobrist_side: np.uint64) -> np.uint64:
    """
    Compute Zobrist hash for position.
    zobrist_pieces[piece_type, color_idx, square]
    zobrist_castling[castling_rights]
    zobrist_en_passant[file] or 0 for none
    zobrist_side = hash for black to move
    """
    hash_val = np.uint64(0)
    
    # Hash pieces
    for sq in range(64):
        row, col = sq // 8, sq % 8
        piece = pieces[row, col]
        if piece != EMPTY:
            color = colors[row, col]
            color_idx = 0 if color == WHITE else 1
            hash_val ^= zobrist_pieces[piece, color_idx, sq]
    
    # Hash castling rights
    castling = state[0]
    hash_val ^= zobrist_castling[castling]
    
    # Hash en passant
    ep_sq = state[1]
    if ep_sq >= 0:
        ep_file = ep_sq % 8
        hash_val ^= zobrist_en_passant[ep_file]
    
    # Hash side to move
    if state[2] == BLACK:
        hash_val ^= zobrist_side
    
    return hash_val


@njit(cache=True)
def make_move_fast(pieces: np.ndarray, colors: np.ndarray, state: np.ndarray,
                   encoded_move: np.uint16) -> Tuple:
    """
    Make move on board (in-place). Returns undo info for unmake.
    Undo info: (captured_piece, captured_color, old_castling, old_ep, old_halfmove, old_fullmove)
    """
    from_sq, to_sq, flags = decode_move(encoded_move)
    from_row, from_col = from_sq // 8, from_sq % 8
    to_row, to_col = to_sq // 8, to_sq % 8
    
    # Save state for undo
    captured_piece = pieces[to_row, to_col]
    captured_color = colors[to_row, to_col]
    old_castling = state[0]
    old_ep = state[1]
    old_halfmove = state[3]
    old_fullmove = state[4]
    
    piece = pieces[from_row, from_col]
    color = colors[from_row, from_col]
    
    # Reset en passant
    state[1] = -1
    
    # Handle special moves
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        # Move king
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = EMPTY
        colors[from_row, from_col] = 0
        
        # Move rook
        if flags == FLAG_CASTLING_KINGSIDE:
            pieces[from_row, 5] = pieces[from_row, 7]
            colors[from_row, 5] = colors[from_row, 7]
            pieces[from_row, 7] = EMPTY
            colors[from_row, 7] = 0
        else:  # Queenside
            pieces[from_row, 3] = pieces[from_row, 0]
            colors[from_row, 3] = colors[from_row, 0]
            pieces[from_row, 0] = EMPTY
            colors[from_row, 0] = 0
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = EMPTY
        colors[from_row, from_col] = 0
        
        # Remove captured pawn
        captured_row = from_row
        captured_piece = pieces[captured_row, to_col]
        captured_color = colors[captured_row, to_col]
        pieces[captured_row, to_col] = EMPTY
        colors[captured_row, to_col] = 0
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Promote pawn
        promo_pieces = np.array([0, QUEEN, ROOK, BISHOP, KNIGHT], dtype=np.int8)
        pieces[to_row, to_col] = promo_pieces[flags]
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = EMPTY
        colors[from_row, from_col] = 0
    
    else:  # Normal move
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = EMPTY
        colors[from_row, from_col] = 0
    
    # Update castling rights
    if piece == KING:
        if color == WHITE:
            state[0] &= ~(CASTLE_WK | CASTLE_WQ)
        else:
            state[0] &= ~(CASTLE_BK | CASTLE_BQ)
    elif piece == ROOK:
        if color == WHITE:
            if from_col == 0:
                state[0] &= ~CASTLE_WQ
            elif from_col == 7:
                state[0] &= ~CASTLE_WK
        else:
            if from_col == 0:
                state[0] &= ~CASTLE_BQ
            elif from_col == 7:
                state[0] &= ~CASTLE_BK
    
    # Check if rook was captured
    if captured_piece == ROOK:
        if to_row == 0:  # Black rooks
            if to_col == 0:
                state[0] &= ~CASTLE_BQ
            elif to_col == 7:
                state[0] &= ~CASTLE_BK
        elif to_row == 7:  # White rooks
            if to_col == 0:
                state[0] &= ~CASTLE_WQ
            elif to_col == 7:
                state[0] &= ~CASTLE_WK
    
    # Set en passant square for pawn double move
    if piece == PAWN and abs(to_row - from_row) == 2:
        state[1] = (from_row + to_row) // 2 * 8 + from_col
    
    # Update halfmove clock
    if piece == PAWN or captured_piece != EMPTY:
        state[3] = 0
    else:
        state[3] += 1
    
    # Update fullmove number
    if color == BLACK:
        state[4] += 1
    
    # Switch player
    state[2] = -color
    
    return captured_piece, captured_color, old_castling, old_ep, old_halfmove, old_fullmove


@njit(cache=True)
def unmake_move_fast(pieces: np.ndarray, colors: np.ndarray, state: np.ndarray,
                     encoded_move: np.uint16, undo_info: Tuple):
    """
    Unmake move on board (in-place).
    undo_info: (captured_piece, captured_color, old_castling, old_ep, old_halfmove, old_fullmove)
    """
    from_sq, to_sq, flags = decode_move(encoded_move)
    from_row, from_col = from_sq // 8, from_sq % 8
    to_row, to_col = to_sq // 8, to_sq % 8
    
    captured_piece, captured_color, old_castling, old_ep, old_halfmove, old_fullmove = undo_info
    
    piece = pieces[to_row, to_col]
    color = -state[2]  # Current player is opponent now, so switch back
    
    # Restore state
    state[0] = old_castling
    state[1] = old_ep
    state[2] = color
    state[3] = old_halfmove
    state[4] = old_fullmove
    
    # Undo special moves
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        # Move king back
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = EMPTY
        colors[to_row, to_col] = 0
        
        # Move rook back
        if flags == FLAG_CASTLING_KINGSIDE:
            pieces[from_row, 7] = pieces[from_row, 5]
            colors[from_row, 7] = colors[from_row, 5]
            pieces[from_row, 5] = EMPTY
            colors[from_row, 5] = 0
        else:  # Queenside
            pieces[from_row, 0] = pieces[from_row, 3]
            colors[from_row, 0] = colors[from_row, 3]
            pieces[from_row, 3] = EMPTY
            colors[from_row, 3] = 0
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn back
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = EMPTY
        colors[to_row, to_col] = 0
        
        # Restore captured pawn
        captured_row = from_row
        pieces[captured_row, to_col] = captured_piece
        colors[captured_row, to_col] = captured_color
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Restore pawn
        pieces[from_row, from_col] = PAWN
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = captured_piece
        colors[to_row, to_col] = captured_color
    
    else:  # Normal move
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = captured_piece
        colors[to_row, to_col] = captured_color


@njit(cache=True)
def find_king(pieces: np.ndarray, colors: np.ndarray, color: int) -> int:
    """Find king square for given color. Returns square index (0-63) or -1 if not found."""
    for sq in range(64):
        row, col = sq // 8, sq % 8
        if pieces[row, col] == KING and colors[row, col] == color:
            return sq
    return -1


@njit(cache=True)
def count_pieces(pieces: np.ndarray, colors: np.ndarray) -> Tuple[int, int]:
    """Count total pieces for white and black."""
    white_count = 0
    black_count = 0
    
    for sq in range(64):
        row, col = sq // 8, sq % 8
        if pieces[row, col] != EMPTY:
            if colors[row, col] == WHITE:
                white_count += 1
            else:
                black_count += 1
    
    return white_count, black_count


@njit(cache=True)
def is_endgame(pieces: np.ndarray) -> bool:
    """
    Determine if position is endgame.
    Simple heuristic: queens traded or limited material.
    """
    queens = 0
    minor_pieces = 0
    
    for sq in range(64):
        row, col = sq // 8, sq % 8
        piece = pieces[row, col]
        if piece == QUEEN:
            queens += 1
        elif piece == KNIGHT or piece == BISHOP:
            minor_pieces += 1
    
    # Endgame if no queens or very few pieces
    return queens == 0 or (queens <= 1 and minor_pieces <= 2)


# Minimal Board wrapper for compatibility with existing code
class BoardState:
    """Lightweight wrapper around numpy arrays. Minimal OOP overhead."""
    __slots__ = ('pieces', 'colors', 'state', 'zobrist_pieces', 'zobrist_castling',
                 'zobrist_en_passant', 'zobrist_side')
    
    def __init__(self):
        self.pieces, self.colors, self.state = init_board()
        
        # Zobrist hashing tables (lazy loaded from files)
        self.zobrist_pieces = None
        self.zobrist_castling = None
        self.zobrist_en_passant = None
        self.zobrist_side = None
    
    def load_zobrist_tables(self):
        """Lazy load Zobrist tables from .npy files."""
        if self.zobrist_pieces is None:
            import os
            tables_dir = os.path.join(os.path.dirname(__file__), 'tables')
            self.zobrist_pieces = np.load(os.path.join(tables_dir, 'zobrist_pieces.npy'))
            self.zobrist_castling = np.load(os.path.join(tables_dir, 'zobrist_castling.npy'))
            self.zobrist_en_passant = np.load(os.path.join(tables_dir, 'zobrist_en_passant.npy'))
            self.zobrist_side_to_move = np.load(os.path.join(tables_dir, 'zobrist_side_to_move.npy'))
            self.zobrist_side = self.zobrist_side_to_move[0]
    
    def get_hash(self) -> np.uint64:
        """Compute Zobrist hash for current position."""
        if self.zobrist_pieces is None:
            self.load_zobrist_tables()
        return compute_zobrist_hash(self.pieces, self.colors, self.state,
                                   self.zobrist_pieces, self.zobrist_castling,
                                   self.zobrist_en_passant, self.zobrist_side)
    
    def make_move(self, encoded_move: np.uint16):
        """Make move and return undo info."""
        return make_move_fast(self.pieces, self.colors, self.state, encoded_move)
    
    def unmake_move(self, encoded_move: np.uint16, undo_info):
        """Unmake move using undo info."""
        unmake_move_fast(self.pieces, self.colors, self.state, encoded_move, undo_info)
    
    def copy(self):
        """Create deep copy of board state."""
        new_board = BoardState.__new__(BoardState)
        new_board.pieces = self.pieces.copy()
        new_board.colors = self.colors.copy()
        new_board.state = self.state.copy()
        new_board.zobrist_pieces = self.zobrist_pieces
        new_board.zobrist_castling = self.zobrist_castling
        new_board.zobrist_en_passant = self.zobrist_en_passant
        new_board.zobrist_side = self.zobrist_side
        return new_board
    
    @property
    def current_player(self) -> int:
        """Get current player (WHITE=1 or BLACK=-1)."""
        return int(self.state[2])
    
    @property
    def halfmove_clock(self) -> int:
        """Get halfmove clock for 50-move rule."""
        return int(self.state[3])
    
    @property
    def fullmove_number(self) -> int:
        """Get fullmove number."""
        return int(self.state[4])
