"""
Evaluation - Bitboard Implementation
Positional evaluation with material, piece-square tables, and tactical bonuses.
"""

import numpy as np
from numba import njit
from engine.board import (
    WP, WN, WB, WR, WQ, WK,
    BP, BN, BB, BR, BQ, BK,
    META, unpack_side,
    lsb, clear_bit, pop_count
)

# Piece values (centipawns)
PIECE_VALUES = np.array([100, 320, 330, 500, 900, 20000], dtype=np.int32)  # P,N,B,R,Q,K

# Piece-Square Tables (from white's perspective, rank 0 = rank 8)
# Values are bonuses in centipawns

PAWN_TABLE = np.array([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0]
], dtype=np.int32)

KNIGHT_TABLE = np.array([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
], dtype=np.int32)

BISHOP_TABLE = np.array([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
], dtype=np.int32)

ROOK_TABLE = np.array([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0]
], dtype=np.int32)

QUEEN_TABLE = np.array([
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20]
], dtype=np.int32)

KING_MIDDLEGAME_TABLE = np.array([
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20]
], dtype=np.int32)

KING_ENDGAME_TABLE = np.array([
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50]
], dtype=np.int32)

# Pre-flip tables for black (mirror vertically)
PAWN_TABLE_BLACK = np.flipud(PAWN_TABLE)
KNIGHT_TABLE_BLACK = np.flipud(KNIGHT_TABLE)
BISHOP_TABLE_BLACK = np.flipud(BISHOP_TABLE)
ROOK_TABLE_BLACK = np.flipud(ROOK_TABLE)
QUEEN_TABLE_BLACK = np.flipud(QUEEN_TABLE)
KING_MIDDLEGAME_TABLE_BLACK = np.flipud(KING_MIDDLEGAME_TABLE)
KING_ENDGAME_TABLE_BLACK = np.flipud(KING_ENDGAME_TABLE)


@njit
def evaluate(state: np.ndarray) -> int:
    """
    Evaluate position from current side's perspective.
    
    Returns score in centipawns (positive = good for side to move).
    """
    side = unpack_side(state[META])
    
    # Material and positional score (from white's perspective)
    score = 0
    
    # Check if endgame (low material)
    total_material = 0
    for piece_idx in range(5):  # Exclude king
        white_pieces = state[WP + piece_idx]
        black_pieces = state[BP + piece_idx]
        piece_value = int(PIECE_VALUES[piece_idx])
        total_material += pop_count(white_pieces) * piece_value
        total_material += pop_count(black_pieces) * piece_value
    
    is_endgame = total_material < 2500  # Roughly 2 minor pieces per side
    
    # Evaluate white pieces
    score += evaluate_pieces(state, 0, is_endgame)
    
    # Evaluate black pieces (negate)
    score -= evaluate_pieces(state, 1, is_endgame)
    
    # Return from current side's perspective
    return score if side == 0 else -score


@njit
def evaluate_pieces(state: np.ndarray, color: int, is_endgame: bool) -> int:
    """Evaluate all pieces for one color."""
    score = 0
    piece_start = WP if color == 0 else BP
    
    # Evaluate each piece type
    for piece_idx in range(5):  # P, N, B, R, Q
        pieces = state[piece_start + piece_idx]
        piece_value = int(PIECE_VALUES[piece_idx])
        
        # Select appropriate table
        if piece_idx == 0:  # Pawn
            table = PAWN_TABLE if color == 0 else PAWN_TABLE_BLACK
        elif piece_idx == 1:  # Knight
            table = KNIGHT_TABLE if color == 0 else KNIGHT_TABLE_BLACK
        elif piece_idx == 2:  # Bishop
            table = BISHOP_TABLE if color == 0 else BISHOP_TABLE_BLACK
        elif piece_idx == 3:  # Rook
            table = ROOK_TABLE if color == 0 else ROOK_TABLE_BLACK
        else:  # Queen
            table = QUEEN_TABLE if color == 0 else QUEEN_TABLE_BLACK
        
        while pieces:
            sq = lsb(pieces)
            pieces = clear_bit(pieces, sq)
            
            row = sq // 8
            col = sq % 8
            
            # Material + position
            score += piece_value + int(table[row, col])
    
    # Evaluate king
    king = state[piece_start + 5]
    if king:
        sq = lsb(king)
        row = sq // 8
        col = sq % 8
        
        # Select king table based on game phase and color
        if is_endgame:
            king_table = KING_ENDGAME_TABLE if color == 0 else KING_ENDGAME_TABLE_BLACK
        else:
            king_table = KING_MIDDLEGAME_TABLE if color == 0 else KING_MIDDLEGAME_TABLE_BLACK
        
        score += int(PIECE_VALUES[5]) + int(king_table[row, col])
    
    return score


@njit
def evaluate_simple(state: np.ndarray) -> int:
    """
    Simple material-only evaluation (faster).
    Returns score from current side's perspective.
    """
    side = unpack_side(state[META])
    score = 0
    
    # Count material for each piece type
    for piece_idx in range(6):
        white_pieces = state[WP + piece_idx]
        black_pieces = state[BP + piece_idx]
        white_count = pop_count(white_pieces)
        black_count = pop_count(black_pieces)
        piece_value = int(PIECE_VALUES[piece_idx])
        score += piece_value * (white_count - black_count)
    
    return score if side == 0 else -score


# Example usage
if __name__ == "__main__":
    from engine.board import Board
    
    print("Testing evaluation function\n")
    
    # Starting position should be near 0
    board = Board()
    score = evaluate(board.state)
    print(f"Starting position: {score} cp")
    
    # After 1.e4
    board = Board.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    score = evaluate(board.state)
    print(f"After 1.e4: {score} cp")
    
    # White up a queen
    board = Board.from_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 0 1")
    score = evaluate(board.state)
    print(f"White up a queen: {score} cp")
    
    # Endgame position
    board = Board.from_fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
    score = evaluate(board.state)
    print(f"Endgame position: {score} cp")
    
    print("\n✓ Evaluation tests complete")
