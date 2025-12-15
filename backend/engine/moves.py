"""
Move Generation - Bitboard Implementation
Generates legal moves using bitboards and pre-computed attack tables.
All hot paths compiled with numba for maximum performance.
"""

import numpy as np
from numba import njit
from numba.typed import List
from typing import Tuple

# Import from board.py
from engine.board import (
    # State indices
    WP, WN, WB, WR, WQ, WK,
    BP, BN, BB, BR, BQ, BK,
    OCCUPIED, META,
    # Move encoding
    encode_move, decode_move,
    FLAG_NORMAL, FLAG_PROMOTION_QUEEN, FLAG_PROMOTION_ROOK,
    FLAG_PROMOTION_BISHOP, FLAG_PROMOTION_KNIGHT,
    FLAG_CASTLING_KINGSIDE, FLAG_CASTLING_QUEENSIDE, FLAG_EN_PASSANT,
    # Castling constants
    CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ,
    # Square constants
    A1, B1, C1, D1, E1, F1, G1, H1,
    A8, B8, C8, D8, E8, F8, G8, H8,
    # Bitboard operations
    get_bit, set_bit, clear_bit, lsb, pop_count,
    square_to_coords, coords_to_square,
    # Metadata unpacking
    unpack_castling, unpack_ep_square, unpack_side,
    # Attack generation
    KNIGHT_ATTACKS, KING_ATTACKS, PAWN_ATTACKS,
    rook_attacks, bishop_attacks, queen_attacks,
    # Move execution
    make_move_numba, unmake_move_numba,
)

# ============================================================================
# MOVE GENERATION (ALL NUMBA)
# ============================================================================

@njit(cache=True)
def generate_pawn_moves(state: np.ndarray, color: int, moves):
    """Generate pawn moves (pushes, captures, promotions, en passant)."""
    pawn_idx = WP if color == 0 else BP
    pawns = state[pawn_idx]
    occupied = state[OCCUPIED]
    opponent_pieces = np.uint64(0)
    
    # Get opponent pieces
    if color == 0:  # White
        for i in range(6):
            opponent_pieces |= state[BP + i]
        push_dir = -8  # Move up the board
        start_rank = 6  # Rank 2 (row 6)
        promo_rank = 0  # Rank 8 (row 0)
    else:  # Black
        for i in range(6):
            opponent_pieces |= state[WP + i]
        push_dir = 8  # Move down the board
        start_rank = 1  # Rank 7 (row 1)
        promo_rank = 7  # Rank 1 (row 7)
    
    # Get en passant square
    ep_square = unpack_ep_square(state[META])
    
    # Iterate through pawns
    while pawns:
        from_sq = lsb(pawns)
        pawns = clear_bit(pawns, from_sq)
        
        row, col = square_to_coords(from_sq)
        to_sq = from_sq + push_dir
        
        # Single push
        if not get_bit(occupied, to_sq):
            to_row = row + (1 if color == 1 else -1)
            
            # Promotion
            if to_row == promo_rank:
                moves.append(encode_move(from_sq, to_sq, FLAG_PROMOTION_QUEEN))
                moves.append(encode_move(from_sq, to_sq, FLAG_PROMOTION_ROOK))
                moves.append(encode_move(from_sq, to_sq, FLAG_PROMOTION_BISHOP))
                moves.append(encode_move(from_sq, to_sq, FLAG_PROMOTION_KNIGHT))
            else:
                moves.append(encode_move(from_sq, to_sq, FLAG_NORMAL))
                
                # Double push
                if row == start_rank:
                    to_sq2 = from_sq + 2 * push_dir
                    if not get_bit(occupied, to_sq2):
                        moves.append(encode_move(from_sq, to_sq2, FLAG_NORMAL))
        
        # Captures (left and right)
        for cap_offset in [-1, 1]:
            cap_col = col + cap_offset
            if 0 <= cap_col < 8:
                cap_sq = coords_to_square(row + (1 if color == 1 else -1), cap_col)
                
                # Normal capture
                if get_bit(opponent_pieces, cap_sq):
                    cap_row = row + (1 if color == 1 else -1)
                    
                    # Promotion capture
                    if cap_row == promo_rank:
                        moves.append(encode_move(from_sq, cap_sq, FLAG_PROMOTION_QUEEN))
                        moves.append(encode_move(from_sq, cap_sq, FLAG_PROMOTION_ROOK))
                        moves.append(encode_move(from_sq, cap_sq, FLAG_PROMOTION_BISHOP))
                        moves.append(encode_move(from_sq, cap_sq, FLAG_PROMOTION_KNIGHT))
                    else:
                        moves.append(encode_move(from_sq, cap_sq, FLAG_NORMAL))
                
                # En passant - check independently
                if ep_square >= 0 and cap_sq == ep_square:
                    moves.append(encode_move(from_sq, cap_sq, FLAG_EN_PASSANT))


@njit(cache=True)
def generate_knight_moves(state: np.ndarray, color: int, moves):
    """Generate knight moves using pre-computed attack table."""
    knight_idx = WN if color == 0 else BN
    knights = state[knight_idx]
    own_pieces = np.uint64(0)
    
    # Get own pieces
    start_idx = WP if color == 0 else BP
    for i in range(6):
        own_pieces |= state[start_idx + i]
    
    while knights:
        from_sq = lsb(knights)
        knights = clear_bit(knights, from_sq)
        
        # Get attacks from pre-computed table
        attacks = KNIGHT_ATTACKS[from_sq]
        
        # Remove attacks on own pieces
        attacks &= ~own_pieces
        
        # Generate moves
        while attacks:
            to_sq = lsb(attacks)
            attacks = clear_bit(attacks, to_sq)
            moves.append(encode_move(from_sq, to_sq, FLAG_NORMAL))


@njit(cache=True)
def generate_sliding_moves(state: np.ndarray, color: int, piece_type: int, moves):
    """Generate sliding piece moves (bishop, rook, queen)."""
    if color == 0:  # White
        piece_idx = WB + piece_type - 2  # Bishop=2→WB, Rook=3→WR, Queen=4→WQ
        own_start = WP
    else:  # Black
        piece_idx = BB + piece_type - 2
        own_start = BP
    
    pieces = state[piece_idx]
    occupied = state[OCCUPIED]
    own_pieces = np.uint64(0)
    
    for i in range(6):
        own_pieces |= state[own_start + i]
    
    while pieces:
        from_sq = lsb(pieces)
        pieces = clear_bit(pieces, from_sq)
        
        # Get attacks based on piece type
        if piece_type == 2:  # Bishop
            attacks = bishop_attacks(from_sq, occupied)
        elif piece_type == 3:  # Rook
            attacks = rook_attacks(from_sq, occupied)
        else:  # Queen
            attacks = queen_attacks(from_sq, occupied)
        
        # Remove attacks on own pieces
        attacks &= ~own_pieces
        
        while attacks:
            to_sq = lsb(attacks)
            attacks = clear_bit(attacks, to_sq)
            moves.append(encode_move(from_sq, to_sq, FLAG_NORMAL))


@njit(cache=True)
def generate_king_moves(state: np.ndarray, color: int, moves):
    """Generate king moves (regular + castling)."""
    king_idx = WK if color == 0 else BK
    king_bb = state[king_idx]
    
    if king_bb == 0:
        return  # No king (shouldn't happen)
    
    from_sq = lsb(king_bb)
    own_pieces = np.uint64(0)
    
    # Get own pieces
    start_idx = WP if color == 0 else BP
    for i in range(6):
        own_pieces |= state[start_idx + i]
    
    # Regular king moves
    attacks = KING_ATTACKS[from_sq]
    attacks &= ~own_pieces
    
    while attacks:
        to_sq = lsb(attacks)
        attacks = clear_bit(attacks, to_sq)
        moves.append(encode_move(from_sq, to_sq, FLAG_NORMAL))
    
    # Castling
    castling = unpack_castling(state[META])
    occupied = state[OCCUPIED]
    
    if color == 0:  # White
        # Kingside (e1-g1)
        if castling & CASTLE_WK:
            if not get_bit(occupied, F1) and not get_bit(occupied, G1):
                moves.append(encode_move(E1, G1, FLAG_CASTLING_KINGSIDE))
        
        # Queenside (e1-c1)
        if castling & CASTLE_WQ:
            if not get_bit(occupied, D1) and not get_bit(occupied, C1) and not get_bit(occupied, B1):
                moves.append(encode_move(E1, C1, FLAG_CASTLING_QUEENSIDE))
    
    else:  # Black
        # Kingside (e8-g8)
        if castling & CASTLE_BK:
            if not get_bit(occupied, F8) and not get_bit(occupied, G8):
                moves.append(encode_move(E8, G8, FLAG_CASTLING_KINGSIDE))
        
        # Queenside (e8-c8)
        if castling & CASTLE_BQ:
            if not get_bit(occupied, D8) and not get_bit(occupied, C8) and not get_bit(occupied, B8):
                moves.append(encode_move(E8, C8, FLAG_CASTLING_QUEENSIDE))


@njit(cache=True)
def is_square_attacked(state: np.ndarray, square: int, by_color: int) -> bool:
    """Check if square is attacked by given color using bitboard attacks."""
    occupied = state[OCCUPIED]
    
    # Check pawn attacks
    pawn_idx = WP if by_color == 0 else BP
    pawns = state[pawn_idx]
    # Pawn attacks are from opponent's perspective
    pawn_attack_bb = PAWN_ATTACKS[1 - by_color, square]
    if pawns & pawn_attack_bb:
        return True
    
    # Check knight attacks
    knight_idx = WN if by_color == 0 else BN
    knights = state[knight_idx]
    if knights & KNIGHT_ATTACKS[square]:
        return True
    
    # Check king attacks
    king_idx = WK if by_color == 0 else BK
    king = state[king_idx]
    if king & KING_ATTACKS[square]:
        return True
    
    # Check bishop/queen diagonal attacks
    bishop_idx = WB if by_color == 0 else BB
    queen_idx = WQ if by_color == 0 else BQ
    diag_attackers = state[bishop_idx] | state[queen_idx]
    if diag_attackers & bishop_attacks(square, occupied):
        return True
    
    # Check rook/queen straight attacks
    rook_idx = WR if by_color == 0 else BR
    straight_attackers = state[rook_idx] | state[queen_idx]
    if straight_attackers & rook_attacks(square, occupied):
        return True
    
    return False


@njit(cache=True)
def find_king_square(state: np.ndarray, color: int) -> int:
    """Find king square for given color."""
    king_idx = WK if color == 0 else BK
    king_bb = state[king_idx]
    if king_bb == 0:
        return -1
    return lsb(king_bb)


@njit(cache=True)
def generate_pseudo_legal_moves(state: np.ndarray, color: int) -> np.ndarray:
    """Generate all pseudo-legal moves (may leave king in check)."""
    moves = List.empty_list(np.uint16)
    
    # Generate moves for each piece type
    generate_pawn_moves(state, color, moves)
    generate_knight_moves(state, color, moves)
    generate_sliding_moves(state, color, 2, moves)  # Bishops
    generate_sliding_moves(state, color, 3, moves)  # Rooks
    generate_sliding_moves(state, color, 4, moves)  # Queens
    generate_king_moves(state, color, moves)
    
    # Convert to array manually
    result = np.empty(len(moves), dtype=np.uint16)
    for i in range(len(moves)):
        result[i] = moves[i]
    return result


@njit(cache=True)
def is_legal_move(state: np.ndarray, move: np.uint16, color: int) -> bool:
    """Check if move is legal (doesn't leave king in check)."""
    from_sq, to_sq, flags = decode_move(move)
    
    # Special handling for castling - can't castle through check
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        king_sq = from_sq
        opponent_color = 1 - color
        
        # Can't castle if king is in check
        if is_square_attacked(state, king_sq, opponent_color):
            return False
        
        # Can't castle through attacked square
        direction = 1 if flags == FLAG_CASTLING_KINGSIDE else -1
        through_sq = king_sq + direction
        if is_square_attacked(state, through_sq, opponent_color):
            return False
    
    # Make move on copy
    state_copy = state.copy()
    undo_info = make_move_numba(state_copy, move)
    
    # Check if king is in check
    king_sq = find_king_square(state_copy, color)
    opponent_color = 1 - color
    in_check = is_square_attacked(state_copy, king_sq, opponent_color)
    
    # No need to unmake on copy
    return not in_check


@njit(cache=True)
def generate_legal_moves_numba(state: np.ndarray, color: int) -> np.ndarray:
    """Generate all legal moves (filtered from pseudo-legal)."""
    pseudo_moves = generate_pseudo_legal_moves(state, color)
    legal = List.empty_list(np.uint16)
    
    for move in pseudo_moves:
        if is_legal_move(state, move, color):
            legal.append(move)
    
    # Convert to array manually
    result = np.empty(len(legal), dtype=np.uint16)
    for i in range(len(legal)):
        result[i] = legal[i]
    return result


# ============================================================================
# MOVES CLASS (THIN WRAPPER)
# ============================================================================

class Moves:
    """
    Move generator using bitboards.
    Thin wrapper around numba functions - all logic is compiled.
    """
    __slots__ = ('board',)
    
    def __init__(self, board):
        """Initialize with board instance."""
        self.board = board
    
    def generate(self) -> np.ndarray:
        """
        Generate all legal moves for current side.
        Returns uint16 array of encoded moves.
        """
        color = unpack_side(self.board.state[META])
        return generate_legal_moves_numba(self.board.state, color)
    
    def is_check(self, color: int = None) -> bool:
        """Check if given color's king is in check."""
        if color is None:
            color = unpack_side(self.board.state[META])
        
        king_sq = find_king_square(self.board.state, color)
        if king_sq < 0:
            return False
        
        opponent_color = 1 - color
        return is_square_attacked(self.board.state, king_sq, opponent_color)
    
    def is_checkmate(self, color: int = None) -> bool:
        """Check if given color is in checkmate."""
        if color is None:
            color = unpack_side(self.board.state[META])
        
        if not self.is_check(color):
            return False
        
        legal_moves = generate_legal_moves_numba(self.board.state, color)
        return len(legal_moves) == 0
    
    def is_stalemate(self, color: int = None) -> bool:
        """Check if given color is in stalemate."""
        if color is None:
            color = unpack_side(self.board.state[META])
        
        if self.is_check(color):
            return False
        
        legal_moves = generate_legal_moves_numba(self.board.state, color)
        return len(legal_moves) == 0


# Export
__all__ = ['Moves', 'generate_pseudo_legal_moves', 'generate_legal_moves_numba', 
           'is_square_attacked', 'find_king_square']
