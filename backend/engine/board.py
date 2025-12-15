"""
Board Representation - Bitboard Implementation
Pure numpy + numba for maximum performance. Zero Python overhead.

State Array Layout (20 × uint64):
  [0-5]:   White pieces [Pawn, Knight, Bishop, Rook, Queen, King]
  [6-11]:  Black pieces [Pawn, Knight, Bishop, Rook, Queen, King]
  [12]:    Occupied squares (all pieces)
  [13]:    Metadata (castling|ep|halfmove|side packed into single uint64)
  [14-19]: Reserved for NN features

Move Encoding (uint16):
  Bits 0-5:   from_square (0-63)
  Bits 6-11:  to_square (0-63)
  Bits 12-15: flags (0=normal, 1-4=promotions, 5-6=castling, 7=en passant)
"""

import numpy as np
from numba import njit
from typing import Tuple, Optional
from enum import IntEnum


# ============================================================================
# CONSTANTS
# ============================================================================

# State array indices
WP, WN, WB, WR, WQ, WK = 0, 1, 2, 3, 4, 5  # White pieces
BP, BN, BB, BR, BQ, BK = 6, 7, 8, 9, 10, 11  # Black pieces
OCCUPIED = 12
META = 13

# Piece types
class PieceType(IntEnum):
    EMPTY = -1
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

# Colors
class Color(IntEnum):
    WHITE = 0
    BLACK = 1

# Move flags
FLAG_NORMAL = 0
FLAG_PROMOTION_QUEEN = 1
FLAG_PROMOTION_ROOK = 2
FLAG_PROMOTION_BISHOP = 3
FLAG_PROMOTION_KNIGHT = 4
FLAG_CASTLING_KINGSIDE = 5
FLAG_CASTLING_QUEENSIDE = 6
FLAG_EN_PASSANT = 7

# Castling rights (bits in metadata)
CASTLE_WK = 0b0001
CASTLE_WQ = 0b0010
CASTLE_BK = 0b0100
CASTLE_BQ = 0b1000
CASTLE_ALL = 0b1111

# Square constants for readability
A1, B1, C1, D1, E1, F1, G1, H1 = 56, 57, 58, 59, 60, 61, 62, 63
A8, B8, C8, D8, E8, F8, G8, H8 = 0, 1, 2, 3, 4, 5, 6, 7


# ============================================================================
# BITBOARD UTILITIES (ALL NUMBA - MAXIMUM PERFORMANCE)
# ============================================================================

@njit(cache=True, inline='always')
def set_bit(bb: np.uint64, square: int) -> np.uint64:
    """Set bit at square position."""
    return bb | (np.uint64(1) << square)

@njit(cache=True, inline='always')
def clear_bit(bb: np.uint64, square: int) -> np.uint64:
    """Clear bit at square position."""
    return bb & ~(np.uint64(1) << square)

@njit(cache=True, inline='always')
def get_bit(bb: np.uint64, square: int) -> bool:
    """Check if bit is set at square."""
    return (bb & (np.uint64(1) << square)) != 0

@njit(cache=True)
def pop_count(bb: np.uint64) -> int:
    """Count number of set bits (Brian Kernighan's algorithm)."""
    count = 0
    while bb:
        count += 1
        bb &= bb - np.uint64(1)
    return count

@njit(cache=True)
def lsb(bb: np.uint64) -> int:
    """Get index of least significant bit using De Bruijn multiplication."""
    if bb == 0:
        return -1
    debruijn = np.uint64(0x03f79d71b4cb0a89)
    index_table = np.array([
        0, 47,  1, 56, 48, 27,  2, 60, 57, 49, 41, 37, 28, 16,  3, 61,
        54, 58, 35, 52, 50, 42, 21, 44, 38, 32, 29, 23, 17, 11,  4, 62,
        46, 55, 26, 59, 40, 36, 15, 53, 34, 51, 20, 43, 31, 22, 10, 45,
        25, 39, 14, 33, 19, 30,  9, 24, 13, 18,  8, 12,  7,  6,  5, 63
    ], dtype=np.int32)
    return int(index_table[((bb ^ (bb - 1)) * debruijn) >> 58])


# ============================================================================
# SQUARE/COORDINATE UTILITIES
# ============================================================================

@njit(cache=True, inline='always')
def square_to_coords(square: int) -> Tuple[int, int]:
    """Convert square index (0-63) to (row, col). Row 0 = rank 8."""
    return square // 8, square % 8

@njit(cache=True, inline='always')
def coords_to_square(row: int, col: int) -> int:
    """Convert (row, col) to square index (0-63)."""
    return row * 8 + col


# ============================================================================
# MOVE ENCODING/DECODING
# ============================================================================

@njit(cache=True, inline='always')
def encode_move(from_sq: int, to_sq: int, flags: int = 0) -> np.uint16:
    """Encode move as uint16."""
    return np.uint16((flags << 12) | (to_sq << 6) | from_sq)

@njit(cache=True, inline='always')
def decode_move(move: np.uint16) -> Tuple[int, int, int]:
    """Decode move into (from_square, to_square, flags)."""
    from_sq = int(move & 0x3F)
    to_sq = int((move >> 6) & 0x3F)
    flags = int(move >> 12)
    return from_sq, to_sq, flags


# ============================================================================
# METADATA PACKING/UNPACKING
# ============================================================================

@njit(cache=True, inline='always')
def pack_metadata(castling: int, ep_square: int, halfmove: int, side: int) -> np.uint64:
    """Pack metadata: castling(4) | ep(7) | halfmove(9) | side(1)."""
    ep_encoded = (ep_square + 1) & 0x7F  # Store as +1 so 0 = no EP
    return np.uint64(
        (castling & 0xF) | 
        (ep_encoded << 4) | 
        ((halfmove & 0x1FF) << 11) | 
        ((side & 0x1) << 20)
    )

@njit(cache=True, inline='always')
def unpack_castling(meta: np.uint64) -> int:
    return int(meta & 0xF)

@njit(cache=True, inline='always')
def unpack_ep_square(meta: np.uint64) -> int:
    """Returns -1 if no en passant square."""
    ep = int((meta >> 4) & 0x7F)
    return ep - 1

@njit(cache=True, inline='always')
def unpack_halfmove(meta: np.uint64) -> int:
    return int((meta >> 11) & 0x1FF)

@njit(cache=True, inline='always')
def unpack_side(meta: np.uint64) -> int:
    return int((meta >> 20) & 0x1)


# ============================================================================
# ATTACK TABLES (PRE-COMPUTED FOR SPEED)
# ============================================================================

@njit(cache=True)
def init_knight_attacks():
    """Pre-compute knight attack bitboards."""
    attacks = np.zeros(64, dtype=np.uint64)
    offsets = np.array([
        [-2, -1], [-2, 1], [-1, -2], [-1, 2],
        [1, -2], [1, 2], [2, -1], [2, 1]
    ], dtype=np.int8)
    
    for sq in range(64):
        row, col = square_to_coords(sq)
        bb = np.uint64(0)
        for i in range(8):
            r = row + offsets[i, 0]
            c = col + offsets[i, 1]
            if 0 <= r < 8 and 0 <= c < 8:
                bb = set_bit(bb, coords_to_square(r, c))
        attacks[sq] = bb
    return attacks

@njit(cache=True)
def init_king_attacks():
    """Pre-compute king attack bitboards."""
    attacks = np.zeros(64, dtype=np.uint64)
    offsets = np.array([
        [-1, -1], [-1, 0], [-1, 1], [0, -1],
        [0, 1], [1, -1], [1, 0], [1, 1]
    ], dtype=np.int8)
    
    for sq in range(64):
        row, col = square_to_coords(sq)
        bb = np.uint64(0)
        for i in range(8):
            r = row + offsets[i, 0]
            c = col + offsets[i, 1]
            if 0 <= r < 8 and 0 <= c < 8:
                bb = set_bit(bb, coords_to_square(r, c))
        attacks[sq] = bb
    return attacks

@njit(cache=True)
def init_pawn_attacks():
    """Pre-compute pawn attack bitboards for both colors."""
    attacks = np.zeros((2, 64), dtype=np.uint64)
    
    for sq in range(64):
        row, col = square_to_coords(sq)
        
        # White pawns (attack upward)
        if row > 0:
            if col > 0:
                attacks[0, sq] = set_bit(attacks[0, sq], coords_to_square(row - 1, col - 1))
            if col < 7:
                attacks[0, sq] = set_bit(attacks[0, sq], coords_to_square(row - 1, col + 1))
        
        # Black pawns (attack downward)
        if row < 7:
            if col > 0:
                attacks[1, sq] = set_bit(attacks[1, sq], coords_to_square(row + 1, col - 1))
            if col < 7:
                attacks[1, sq] = set_bit(attacks[1, sq], coords_to_square(row + 1, col + 1))
    
    return attacks

# Initialize attack tables (happens once on import)
KNIGHT_ATTACKS = init_knight_attacks()
KING_ATTACKS = init_king_attacks()
PAWN_ATTACKS = init_pawn_attacks()


# ============================================================================
# SLIDING PIECE ATTACKS (VECTORIZED)
# ============================================================================

@njit(cache=True)
def rook_attacks(square: int, occupied: np.uint64) -> np.uint64:
    """Generate rook attacks (classical approach - vectorized loops)."""
    attacks = np.uint64(0)
    row, col = square_to_coords(square)
    
    # North
    for r in range(row - 1, -1, -1):
        sq = coords_to_square(r, col)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
    
    # South
    for r in range(row + 1, 8):
        sq = coords_to_square(r, col)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
    
    # West
    for c in range(col - 1, -1, -1):
        sq = coords_to_square(row, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
    
    # East
    for c in range(col + 1, 8):
        sq = coords_to_square(row, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
    
    return attacks

@njit(cache=True)
def bishop_attacks(square: int, occupied: np.uint64) -> np.uint64:
    """Generate bishop attacks (classical approach - vectorized loops)."""
    attacks = np.uint64(0)
    row, col = square_to_coords(square)
    
    # NW
    r, c = row - 1, col - 1
    while r >= 0 and c >= 0:
        sq = coords_to_square(r, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
        r -= 1
        c -= 1
    
    # NE
    r, c = row - 1, col + 1
    while r >= 0 and c < 8:
        sq = coords_to_square(r, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
        r -= 1
        c += 1
    
    # SW
    r, c = row + 1, col - 1
    while r < 8 and c >= 0:
        sq = coords_to_square(r, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
        r += 1
        c -= 1
    
    # SE
    r, c = row + 1, col + 1
    while r < 8 and c < 8:
        sq = coords_to_square(r, c)
        attacks = set_bit(attacks, sq)
        if get_bit(occupied, sq):
            break
        r += 1
        c += 1
    
    return attacks

@njit(cache=True, inline='always')
def queen_attacks(square: int, occupied: np.uint64) -> np.uint64:
    """Queen attacks = rook + bishop."""
    return rook_attacks(square, occupied) | bishop_attacks(square, occupied)


# ============================================================================
# STATE INITIALIZATION
# ============================================================================

@njit(cache=True)
def create_initial_state() -> np.ndarray:
    """Create starting position state."""
    state = np.zeros(20, dtype=np.uint64)
    
    # White pieces (rank 1-2, squares 48-63)
    state[WP] = np.uint64(0x00FF000000000000)  # Pawns on rank 2 (squares 48-55)
    state[WN] = np.uint64(0x4200000000000000)  # Knights b1, g1 (squares 57, 62)
    state[WB] = np.uint64(0x2400000000000000)  # Bishops c1, f1 (squares 58, 61)
    state[WR] = np.uint64(0x8100000000000000)  # Rooks a1, h1 (squares 56, 63)
    state[WQ] = np.uint64(0x0800000000000000)  # Queen d1 (square 59)
    state[WK] = np.uint64(0x1000000000000000)  # King e1 (square 60)
    
    # Black pieces (rank 7-8, squares 0-15)
    state[BP] = np.uint64(0x000000000000FF00)  # Pawns on rank 7 (squares 8-15)
    state[BN] = np.uint64(0x0000000000000042)  # Knights b8, g8 (squares 1, 6)
    state[BB] = np.uint64(0x0000000000000024)  # Bishops c8, f8 (squares 2, 5)
    state[BR] = np.uint64(0x0000000000000081)  # Rooks a8, h8 (squares 0, 7)
    state[BQ] = np.uint64(0x0000000000000008)  # Queen d8 (square 3)
    state[BK] = np.uint64(0x0000000000000010)  # King e8 (square 4)
    
    # Occupied
    state[OCCUPIED] = np.uint64(0xFFFF00000000FFFF)
    
    # Metadata: all castling, no ep, halfmove=0, white to move
    state[META] = pack_metadata(CASTLE_ALL, -1, 0, Color.WHITE)
    
    # Compute Zobrist hash
    state[HASH] = compute_zobrist_hash(state)
    
    return state

@njit(cache=True)
def copy_state(state: np.ndarray) -> np.ndarray:
    """Fast state copy."""
    return state.copy()


# ============================================================================
# PIECE LOOKUP
# ============================================================================

@njit(cache=True)
def get_piece_at(state: np.ndarray, square: int) -> Tuple[int, int]:
    """
    Get (piece_type, color) at square.
    Returns (PieceType.EMPTY, -1) if empty.
    """
    for piece_idx in range(6):
        if get_bit(state[piece_idx], square):  # White piece
            return piece_idx, 0
        if get_bit(state[piece_idx + 6], square):  # Black piece
            return piece_idx, 1
    return -1, -1  # Empty


# ============================================================================
# MAKE/UNMAKE MOVE (ALL NUMBA - CORE PERFORMANCE)
# ============================================================================

@njit(cache=True)
def make_move_numba(state: np.ndarray, move: np.uint16) -> np.ndarray:
    """
    Execute move on state. Returns undo_info for unmake.
    Undo format: [old_meta, captured_piece_type, captured_color, old_fullmove]
    """
    from_sq, to_sq, flags = decode_move(move)
    piece_type, color = get_piece_at(state, from_sq)
    
    # Save undo info (including old hash)
    undo_info = np.array([
        state[META],  # Old metadata
        -1,  # Captured piece type
        -1,  # Captured color
        state[HASH]  # Old hash
    ], dtype=np.int64)
    
    # Start with current hash
    hash_val = np.uint64(state[HASH])
    
    # Get piece bitboard index
    piece_idx = piece_type if color == 0 else piece_type + 6
    
    # Handle captures
    cap_type, cap_color = get_piece_at(state, to_sq)
    if cap_type >= 0:
        undo_info[1] = cap_type
        undo_info[2] = cap_color
        cap_idx = cap_type if cap_color == 0 else cap_type + 6
        state[cap_idx] = clear_bit(state[cap_idx], to_sq)
        # Update hash: remove captured piece
        hash_val = update_hash_piece_remove(hash_val, cap_idx, to_sq)
    
    # Get current metadata
    castling = unpack_castling(state[META])
    ep_square = unpack_ep_square(state[META])
    halfmove = unpack_halfmove(state[META])
    side = unpack_side(state[META])
    
    # Handle special moves
    if flags == FLAG_CASTLING_KINGSIDE:
        # King
        state[piece_idx] = clear_bit(state[piece_idx], from_sq)
        state[piece_idx] = set_bit(state[piece_idx], to_sq)
        hash_val = update_hash_piece_move(hash_val, piece_idx, from_sq, to_sq)
        # Rook
        rook_idx = WR if color == 0 else BR
        rook_from = H1 if color == 0 else H8
        rook_to = F1 if color == 0 else F8
        state[rook_idx] = clear_bit(state[rook_idx], rook_from)
        state[rook_idx] = set_bit(state[rook_idx], rook_to)
        hash_val = update_hash_piece_move(hash_val, rook_idx, rook_from, rook_to)
    
    elif flags == FLAG_CASTLING_QUEENSIDE:
        # King
        state[piece_idx] = clear_bit(state[piece_idx], from_sq)
        state[piece_idx] = set_bit(state[piece_idx], to_sq)
        hash_val = update_hash_piece_move(hash_val, piece_idx, from_sq, to_sq)
        # Rook
        rook_idx = WR if color == 0 else BR
        rook_from = A1 if color == 0 else A8
        rook_to = D1 if color == 0 else D8
        state[rook_idx] = clear_bit(state[rook_idx], rook_from)
        state[rook_idx] = set_bit(state[rook_idx], rook_to)
        hash_val = update_hash_piece_move(hash_val, rook_idx, rook_from, rook_to)
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn
        state[piece_idx] = clear_bit(state[piece_idx], from_sq)
        state[piece_idx] = set_bit(state[piece_idx], to_sq)
        hash_val = update_hash_piece_move(hash_val, piece_idx, from_sq, to_sq)
        # Capture en passant pawn
        ep_capture_sq = ep_square + 8 if color == 0 else ep_square - 8
        ep_pawn_idx = BP if color == 0 else WP
        state[ep_pawn_idx] = clear_bit(state[ep_pawn_idx], ep_capture_sq)
        hash_val = update_hash_piece_remove(hash_val, ep_pawn_idx, ep_capture_sq)
        # NOTE: Don't set undo_info for captured piece - EP unmake handles it specially
        # undo_info[1] and undo_info[2] stay at -1
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Remove pawn
        state[piece_idx] = clear_bit(state[piece_idx], from_sq)
        hash_val = update_hash_piece_remove(hash_val, piece_idx, from_sq)
        # Add promoted piece
        promo_types = np.array([0, 4, 3, 2, 1], dtype=np.int8)  # Q, R, B, N
        promo_piece = promo_types[flags]
        promo_idx = promo_piece if color == 0 else promo_piece + 6
        state[promo_idx] = set_bit(state[promo_idx], to_sq)
        hash_val = update_hash_piece_add(hash_val, promo_idx, to_sq)
    
    else:  # Normal move
        state[piece_idx] = clear_bit(state[piece_idx], from_sq)
        state[piece_idx] = set_bit(state[piece_idx], to_sq)
        hash_val = update_hash_piece_move(hash_val, piece_idx, from_sq, to_sq)
    
    # Update castling rights
    if piece_type == 5:  # King
        if color == 0:
            castling &= ~(CASTLE_WK | CASTLE_WQ)
        else:
            castling &= ~(CASTLE_BK | CASTLE_BQ)
    elif piece_type == 3:  # Rook
        if color == 0:
            if from_sq == A1:
                castling &= ~CASTLE_WQ
            elif from_sq == H1:
                castling &= ~CASTLE_WK
        else:
            if from_sq == A8:
                castling &= ~CASTLE_BQ
            elif from_sq == H8:
                castling &= ~CASTLE_BK
    
    # Rook captured
    if cap_type == 3:
        if to_sq == A1:
            castling &= ~CASTLE_WQ
        elif to_sq == H1:
            castling &= ~CASTLE_WK
        elif to_sq == A8:
            castling &= ~CASTLE_BQ
        elif to_sq == H8:
            castling &= ~CASTLE_BK
    
    # Update en passant
    new_ep = -1
    if piece_type == 0:  # Pawn
        if abs(to_sq - from_sq) == 16:  # Double push
            new_ep = (from_sq + to_sq) // 2
    
    # Update halfmove clock
    if piece_type == 0 or cap_type >= 0:
        halfmove = 0
    else:
        halfmove += 1
    
    # Update occupied bitboard
    state[OCCUPIED] = np.uint64(0)
    for i in range(12):
        state[OCCUPIED] |= state[i]
    
    # Pack new metadata
    new_side = 1 - side
    state[META] = pack_metadata(castling, new_ep, halfmove, new_side)
    
    # Update hash for metadata changes
    old_castling = unpack_castling(undo_info[0])
    old_ep = unpack_ep_square(undo_info[0])
    hash_val = update_hash_castling(hash_val, old_castling, castling)
    hash_val = update_hash_ep(hash_val, old_ep, new_ep)
    hash_val = update_hash_side(hash_val)  # Flip side
    
    # Store updated hash
    state[HASH] = hash_val
    
    return undo_info

@njit(cache=True)
def unmake_move_numba(state: np.ndarray, move: np.uint16, undo_info: np.ndarray):
    """Undo a move using undo_info."""
    from_sq, to_sq, flags = decode_move(move)
    
    # Get the side that MADE the move (before it was flipped)
    current_side = unpack_side(state[META])
    moving_side = 1 - current_side  # Side that made the move
    
    # Restore metadata AFTER we get moving_side
    state[META] = np.uint64(undo_info[0])
    
    # Determine piece type
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        piece_type = 5  # King
    elif flags >= FLAG_PROMOTION_QUEEN:
        piece_type = 0  # Was a pawn before promotion
    else:
        piece_type, _ = get_piece_at(state, to_sq)
    
    piece_idx = piece_type if moving_side == 0 else piece_type + 6
    
    # Handle special moves
    if flags == FLAG_CASTLING_KINGSIDE:
        # King
        state[piece_idx] = clear_bit(state[piece_idx], to_sq)
        state[piece_idx] = set_bit(state[piece_idx], from_sq)
        # Rook
        rook_idx = WR if moving_side == 0 else BR
        rook_from = H1 if moving_side == 0 else H8
        rook_to = F1 if moving_side == 0 else F8
        state[rook_idx] = clear_bit(state[rook_idx], rook_to)
        state[rook_idx] = set_bit(state[rook_idx], rook_from)
    
    elif flags == FLAG_CASTLING_QUEENSIDE:
        # King
        state[piece_idx] = clear_bit(state[piece_idx], to_sq)
        state[piece_idx] = set_bit(state[piece_idx], from_sq)
        # Rook
        rook_idx = WR if moving_side == 0 else BR
        rook_from = A1 if moving_side == 0 else A8
        rook_to = D1 if moving_side == 0 else D8
        state[rook_idx] = clear_bit(state[rook_idx], rook_to)
        state[rook_idx] = set_bit(state[rook_idx], rook_from)
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn back
        state[piece_idx] = clear_bit(state[piece_idx], to_sq)
        state[piece_idx] = set_bit(state[piece_idx], from_sq)
        # Restore captured pawn
        # NOTE: Must calculate from to_sq, not from ep_square in metadata (already restored to old value)
        ep_capture_sq = to_sq + 8 if moving_side == 0 else to_sq - 8
        ep_pawn_idx = BP if moving_side == 0 else WP
        state[ep_pawn_idx] = set_bit(state[ep_pawn_idx], ep_capture_sq)
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Remove promoted piece
        promo_types = np.array([0, 4, 3, 2, 1], dtype=np.int8)
        promo_piece = promo_types[flags]
        promo_idx = promo_piece if moving_side == 0 else promo_piece + 6
        state[promo_idx] = clear_bit(state[promo_idx], to_sq)
        # Restore pawn
        pawn_idx = WP if moving_side == 0 else BP
        state[pawn_idx] = set_bit(state[pawn_idx], from_sq)
    
    else:  # Normal move
        state[piece_idx] = clear_bit(state[piece_idx], to_sq)
        state[piece_idx] = set_bit(state[piece_idx], from_sq)
    
    # Restore captured piece
    cap_type = int(undo_info[1])
    cap_color = int(undo_info[2])
    if cap_type >= 0:
        cap_idx = cap_type if cap_color == 0 else cap_type + 6
        state[cap_idx] = set_bit(state[cap_idx], to_sq)
    
    # Update occupied
    state[OCCUPIED] = np.uint64(0)
    for i in range(12):
        state[OCCUPIED] |= state[i]
    
    # Restore hash from undo_info
    state[HASH] = np.uint64(undo_info[3])


# ============================================================================
# FEN CONVERSION (NUMBA WHERE POSSIBLE)
# ============================================================================

def to_fen(state: np.ndarray, fullmove: int) -> str:
    """Convert state to FEN string."""
    pieces = {
        0: ('P', 'p'), 1: ('N', 'n'), 2: ('B', 'b'),
        3: ('R', 'r'), 4: ('Q', 'q'), 5: ('K', 'k')
    }
    
    # Piece placement
    fen_parts = []
    for row in range(8):
        empty = 0
        row_str = ""
        for col in range(8):
            sq = coords_to_square(row, col)
            piece_type, color = get_piece_at(state, sq)
            if piece_type < 0:
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                row_str += pieces[piece_type][color]
        if empty > 0:
            row_str += str(empty)
        fen_parts.append(row_str)
    
    fen = "/".join(fen_parts)
    
    # Side to move
    side = unpack_side(state[META])
    fen += " w" if side == 0 else " b"
    
    # Castling
    castling = unpack_castling(state[META])
    castling_str = ""
    if castling & CASTLE_WK:
        castling_str += "K"
    if castling & CASTLE_WQ:
        castling_str += "Q"
    if castling & CASTLE_BK:
        castling_str += "k"
    if castling & CASTLE_BQ:
        castling_str += "q"
    fen += " " + (castling_str if castling_str else "-")
    
    # En passant
    ep = unpack_ep_square(state[META])
    if ep >= 0:
        row, col = square_to_coords(ep)
        fen += f" {chr(ord('a') + col)}{8 - row}"
    else:
        fen += " -"
    
    # Clocks
    halfmove = unpack_halfmove(state[META])
    fen += f" {halfmove} {fullmove}"
    
    return fen

def from_fen(fen: str) -> Tuple[np.ndarray, int]:
    """Parse FEN and return (state, fullmove)."""
    parts = fen.split()
    if len(parts) != 6:
        raise ValueError(f"Invalid FEN: expected 6 parts, got {len(parts)}")
    
    state = np.zeros(20, dtype=np.uint64)
    
    piece_map = {
        'P': (0, 0), 'p': (0, 1), 'N': (1, 0), 'n': (1, 1),
        'B': (2, 0), 'b': (2, 1), 'R': (3, 0), 'r': (3, 1),
        'Q': (4, 0), 'q': (4, 1), 'K': (5, 0), 'k': (5, 1)
    }
    
    # Parse pieces
    rows = parts[0].split('/')
    for row_idx, row_str in enumerate(rows):
        col_idx = 0
        for char in row_str:
            if char.isdigit():
                col_idx += int(char)
            else:
                piece_type, color = piece_map[char]
                sq = coords_to_square(row_idx, col_idx)
                piece_idx = piece_type if color == 0 else piece_type + 6
                state[piece_idx] = set_bit(state[piece_idx], sq)
                col_idx += 1
    
    # Side to move
    side = 0 if parts[1] == 'w' else 1
    
    # Castling
    castling = 0
    if 'K' in parts[2]:
        castling |= CASTLE_WK
    if 'Q' in parts[2]:
        castling |= CASTLE_WQ
    if 'k' in parts[2]:
        castling |= CASTLE_BK
    if 'q' in parts[2]:
        castling |= CASTLE_BQ
    
    # En passant
    ep = -1
    if parts[3] != '-':
        col = ord(parts[3][0]) - ord('a')
        row = 8 - int(parts[3][1])
        ep = coords_to_square(row, col)
    
    # Clocks
    halfmove = int(parts[4])
    fullmove = int(parts[5])
    
    # Pack metadata
    state[META] = pack_metadata(castling, ep, halfmove, side)
    
    # Update occupied
    for i in range(12):
        state[OCCUPIED] |= state[i]
    
    # Compute Zobrist hash
    state[HASH] = compute_zobrist_hash(state)
    
    return state, fullmove


# ============================================================================
# ZOBRIST HASHING
# ============================================================================

# Initialize Zobrist keys at module load (deterministic seed for debugging)
def _init_zobrist_keys():
    """Initialize all Zobrist hash keys with deterministic seed."""
    rng = np.random.RandomState(seed=0)  # Deterministic for reproducibility
    
    # Generate random uint64 values by combining two uint32 values
    # (randint with 2**32 causes overflow, use bytes instead)
    
    # 12 piece types × 64 squares = 768 keys
    pieces_bytes = rng.bytes(12 * 64 * 8)  # 768 uint64 values
    pieces = np.frombuffer(pieces_bytes, dtype=np.uint64).reshape(12, 64)
    
    # 16 castling right combinations (0-15)
    castling_bytes = rng.bytes(16 * 8)  # 16 uint64 values
    castling = np.frombuffer(castling_bytes, dtype=np.uint64)
    
    # 8 en passant files (a-h)
    ep_bytes = rng.bytes(8 * 8)  # 8 uint64 values
    ep = np.frombuffer(ep_bytes, dtype=np.uint64)
    
    # Side to move (1 key for black, XOR when black to move)
    side_bytes = rng.bytes(8)  # 1 uint64 value
    side = np.frombuffer(side_bytes, dtype=np.uint64)[0]
    
    return pieces, castling, ep, side

# Global Zobrist keys (initialized once at module load)
ZOBRIST_PIECES, ZOBRIST_CASTLING, ZOBRIST_EP, ZOBRIST_SIDE = _init_zobrist_keys()

# Add HASH constant for state array index
HASH = 14  # Store hash at index 14 (reserved slot)


@njit(cache=True)
def compute_zobrist_hash(state: np.ndarray) -> np.uint64:
    """
    Compute Zobrist hash from scratch.
    Used for FEN loading and hash verification.
    """
    hash_val = np.uint64(0)
    
    # XOR each piece on the board
    for piece_idx in range(12):
        pieces = state[piece_idx]
        while pieces:
            sq = lsb(pieces)
            pieces = clear_bit(pieces, sq)
            hash_val ^= ZOBRIST_PIECES[piece_idx][sq]
    
    # XOR castling rights (use full 4-bit value as index)
    castling = unpack_castling(state[META])
    hash_val ^= ZOBRIST_CASTLING[castling]
    
    # XOR en passant file (if EP square is set)
    ep_sq = unpack_ep_square(state[META])
    if ep_sq >= 0:
        ep_file = ep_sq % 8
        hash_val ^= ZOBRIST_EP[ep_file]
    
    # XOR side to move (if black to move)
    side = unpack_side(state[META])
    if side == 1:  # Black
        hash_val ^= ZOBRIST_SIDE
    
    return hash_val


@njit(cache=True)
def update_hash_piece_move(hash_val: np.uint64, piece_idx: int, from_sq: int, to_sq: int) -> np.uint64:
    """Update hash for a piece moving from one square to another."""
    hash_val ^= ZOBRIST_PIECES[piece_idx][from_sq]  # Remove from old square
    hash_val ^= ZOBRIST_PIECES[piece_idx][to_sq]    # Add to new square
    return hash_val


@njit(cache=True)
def update_hash_piece_add(hash_val: np.uint64, piece_idx: int, sq: int) -> np.uint64:
    """Update hash for adding a piece."""
    hash_val ^= ZOBRIST_PIECES[piece_idx][sq]
    return hash_val


@njit(cache=True)
def update_hash_piece_remove(hash_val: np.uint64, piece_idx: int, sq: int) -> np.uint64:
    """Update hash for removing a piece."""
    hash_val ^= ZOBRIST_PIECES[piece_idx][sq]
    return hash_val


@njit(cache=True)
def update_hash_castling(hash_val: np.uint64, old_castling: int, new_castling: int) -> np.uint64:
    """Update hash for castling rights change."""
    hash_val ^= ZOBRIST_CASTLING[old_castling]
    hash_val ^= ZOBRIST_CASTLING[new_castling]
    return hash_val


@njit(cache=True)
def update_hash_ep(hash_val: np.uint64, old_ep: int, new_ep: int) -> np.uint64:
    """Update hash for en passant square change."""
    if old_ep >= 0:
        hash_val ^= ZOBRIST_EP[old_ep % 8]
    if new_ep >= 0:
        hash_val ^= ZOBRIST_EP[new_ep % 8]
    return hash_val


@njit(cache=True)
def update_hash_side(hash_val: np.uint64) -> np.uint64:
    """Update hash for side to move flip."""
    hash_val ^= ZOBRIST_SIDE
    return hash_val


# ============================================================================
# BOARD CLASS (MINIMAL WRAPPER)
# ============================================================================

class Board:
    """
    Minimal wrapper around bitboard state.
    All logic in numba - this is just API sugar.
    """
    __slots__ = ('state', 'fullmove')
    
    def __init__(self, fen: str = None):
        """Create board from FEN or starting position."""
        if fen:
            self.state, self.fullmove = from_fen(fen)
        else:
            self.state = create_initial_state()
            self.fullmove = 1
    
    def copy(self):
        """Deep copy."""
        new_board = Board.__new__(Board)
        new_board.state = copy_state(self.state)
        new_board.fullmove = self.fullmove
        return new_board
    
    def make_move(self, move: np.uint16):
        """Execute move and update fullmove counter."""
        undo_info = make_move_numba(self.state, move)
        if unpack_side(self.state[META]) == 0:  # Side flipped, was black
            self.fullmove += 1
        return undo_info
    
    def unmake_move(self, move: np.uint16, undo_info: np.ndarray):
        """Undo move and restore fullmove counter."""
        if unpack_side(self.state[META]) == 0:  # Currently white, will be black
            self.fullmove -= 1
        unmake_move_numba(self.state, move, undo_info)
    
    def make_null_move(self) -> np.ndarray:
        """
        Make a null move (pass turn, no piece moved).
        Used for null move pruning in search.
        Returns undo info to restore the position.
        """
        # Save old metadata
        old_meta = self.state[META]
        old_hash = self.state[HASH]
        
        # Flip side to move
        side = unpack_side(old_meta)
        new_meta = old_meta ^ np.uint64(1)  # Toggle side bit
        
        # Clear en passant (it expires)
        new_meta &= ~(np.uint64(0xFF) << 2)  # Clear EP file bits
        
        self.state[META] = new_meta
        
        # Update hash (flip side, clear EP if any)
        new_hash = old_hash ^ ZOBRIST_SIDE
        ep_file = (old_meta >> 2) & 0xFF
        if ep_file < 8:
            new_hash ^= ZOBRIST_EP[ep_file]
        
        self.state[HASH] = new_hash
        
        # Return undo info
        return np.array([old_meta, old_hash], dtype=np.uint64)
    
    def unmake_null_move(self, undo_info: np.ndarray):
        """Undo null move."""
        self.state[META] = undo_info[0]
        self.state[HASH] = undo_info[1]
    
    def to_fen(self) -> str:
        """Export to FEN notation."""
        return to_fen(self.state, self.fullmove)
    
    @classmethod
    def from_fen(cls, fen: str) -> 'Board':
        """Create board from FEN string."""
        return cls(fen=fen)
    
    @property
    def current_player(self) -> Color:
        """Side to move."""
        return Color(unpack_side(self.state[META]))
    
    @property
    def castling_rights(self) -> int:
        """Castling rights bitmask."""
        return unpack_castling(self.state[META])
    
    @property
    def en_passant_target(self) -> Optional[Tuple[int, int]]:
        """En passant target square as (row, col) or None."""
        ep = unpack_ep_square(self.state[META])
        if ep < 0:
            return None
        return square_to_coords(ep)
    
    @property
    def halfmove_clock(self) -> int:
        """Halfmove clock for 50-move rule."""
        return unpack_halfmove(self.state[META])
    
    def display(self) -> str:
        """ASCII board display."""
        pieces = {
            0: ('P', 'p'), 1: ('N', 'n'), 2: ('B', 'b'),
            3: ('R', 'r'), 4: ('Q', 'q'), 5: ('K', 'k')
        }
        
        output = "  a b c d e f g h\n"
        for row in range(8):
            output += f"{8 - row} "
            for col in range(8):
                sq = coords_to_square(row, col)
                piece_type, color = get_piece_at(self.state, sq)
                if piece_type < 0:
                    output += '. '
                else:
                    char = pieces[piece_type][color]
                    output += char + ' '
            output += f"{8 - row}\n"
        output += "  a b c d e f g h\n"
        return output


# Export commonly used items
__all__ = [
    'Board', 'PieceType', 'Color',
    'encode_move', 'decode_move',
    'FLAG_NORMAL', 'FLAG_PROMOTION_QUEEN', 'FLAG_PROMOTION_ROOK',
    'FLAG_PROMOTION_BISHOP', 'FLAG_PROMOTION_KNIGHT',
    'FLAG_CASTLING_KINGSIDE', 'FLAG_CASTLING_QUEENSIDE', 'FLAG_EN_PASSANT',
    'CASTLE_WK', 'CASTLE_WQ', 'CASTLE_BK', 'CASTLE_BQ', 'CASTLE_ALL',
    'WP', 'WN', 'WB', 'WR', 'WQ', 'WK',
    'BP', 'BN', 'BB', 'BR', 'BQ', 'BK',
    'OCCUPIED', 'META'
]

