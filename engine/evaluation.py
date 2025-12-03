"""
Evaluation Module
Evaluates chess positions for the AI engine.
Optimized with numpy for fully vectorized operations - no loops!
"""

from engine.board import Board, PieceType, Color
from typing import Dict
import numpy as np
from numba import njit


@njit(cache=True)
def _create_piece_square_array(board_array, color_array, is_endgame,
                                pawn_table, knight_table, bishop_table,
                                rook_table, queen_table, king_mid_table, king_end_table):
    """
    Ultra-fast vectorized position evaluation using 3D table lookup.
    Creates a 3D array where piece_square_values[piece_type] = table for that piece.
    """
    score = 0
    
    # Single pass through non-empty squares
    for row in range(8):
        for col in range(8):
            piece_type = board_array[row, col]
            if piece_type == 0:
                continue
            
            color = color_array[row, col]
            eval_row = row if color == 1 else 7 - row
            
            # Lookup table value (if/elif is fastest in numba for small branches)
            if piece_type == 1:
                table_value = pawn_table[eval_row, col]
            elif piece_type == 2:
                table_value = knight_table[eval_row, col]
            elif piece_type == 3:
                table_value = bishop_table[eval_row, col]
            elif piece_type == 4:
                table_value = rook_table[eval_row, col]
            elif piece_type == 5:
                table_value = queen_table[eval_row, col]
            elif piece_type == 6:
                table_value = king_end_table[eval_row, col] if is_endgame else king_mid_table[eval_row, col]
            else:
                table_value = 0
            
            score += table_value * color
    
    return score


class Evaluator:
    """Evaluates chess positions with material and positional factors."""
    __slots__ = ('weights', '_board_array', '_color_array')  # Memory optimization
    
    # Piece values in centipawns (1 pawn = 100)
    PIECE_VALUES = {
        PieceType.PAWN: 100,
        PieceType.KNIGHT: 320,
        PieceType.BISHOP: 330,
        PieceType.ROOK: 500,
        PieceType.QUEEN: 900,
        PieceType.KING: 20000
    }
    
    # Convert piece-square tables to numpy arrays for faster access
    # Piece-square tables (values are from white's perspective)
    # Positive values indicate better squares
    
    PAWN_TABLE = np.array([
        [  0,  0,  0,  0,  0,  0,  0,  0],
        [ 50, 50, 50, 50, 50, 50, 50, 50],
        [ 10, 10, 20, 30, 30, 20, 10, 10],
        [  5,  5, 10, 25, 25, 10,  5,  5],
        [  0,  0,  0, 20, 20,  0,  0,  0],
        [  5, -5,-10,  0,  0,-10, -5,  5],
        [  5, 10, 10,-20,-20, 10, 10,  5],
        [  0,  0,  0,  0,  0,  0,  0,  0]
    ], dtype=np.int16)
    
    KNIGHT_TABLE = np.array([
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50]
    ], dtype=np.int16)
    
    BISHOP_TABLE = np.array([
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20]
    ], dtype=np.int16)
    
    ROOK_TABLE = np.array([
        [  0,  0,  0,  0,  0,  0,  0,  0],
        [  5, 10, 10, 10, 10, 10, 10,  5],
        [ -5,  0,  0,  0,  0,  0,  0, -5],
        [ -5,  0,  0,  0,  0,  0,  0, -5],
        [ -5,  0,  0,  0,  0,  0,  0, -5],
        [ -5,  0,  0,  0,  0,  0,  0, -5],
        [ -5,  0,  0,  0,  0,  0,  0, -5],
        [  0,  0,  0,  5,  5,  0,  0,  0]
    ], dtype=np.int16)
    
    QUEEN_TABLE = np.array([
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20]
    ], dtype=np.int16)
    
    KING_MIDDLEGAME_TABLE = np.array([
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20]
    ], dtype=np.int16)
    
    KING_ENDGAME_TABLE = np.array([
        [-50,-40,-30,-20,-20,-30,-40,-50],
        [-30,-20,-10,  0,  0,-10,-20,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-30,  0,  0,  0,  0,-30,-30],
        [-50,-30,-30,-30,-30,-30,-30,-50]
    ], dtype=np.int16)
    
    # Create numpy array for fast piece value lookup
    # Index: 0=empty, 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
    PIECE_VALUE_ARRAY = np.array([0, 100, 320, 330, 500, 900, 20000], dtype=np.int32)
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize evaluator with configurable weights.
        weights: Dictionary with keys like 'material', 'positional', 'mobility'
        """
        self.weights = weights or {
            'material': 1.0,
            'positional': 1.0,
            'mobility': 0.1,
            'king_safety': 0.5,
            'pawn_structure': 0.5
        }
    
    def evaluate(self, board: Board) -> float:
        """
        Evaluate a chess position.
        Returns a score in centipawns from white's perspective.
        Positive = white advantage, Negative = black advantage
        """
        # Lazy evaluation: if material difference is huge, skip detailed eval
        material_score = self.weights['material'] * self._evaluate_material(board)
        
        # If material advantage > 15 pawns (1500 centipawns), position is decided
        if abs(material_score) > 1500:
            return material_score
        
        score = material_score
        
        # Positional evaluation (piece-square tables)
        score += self.weights['positional'] * self._evaluate_position(board)
        
        # Additional evaluation factors (can enable these for stronger play)
        # score += self.weights['mobility'] * self._evaluate_mobility(board)
        # score += self.weights['king_safety'] * self._evaluate_king_safety(board)
        # score += self.weights['pawn_structure'] * self._evaluate_pawn_structure(board)
        
        return score
    
    def _evaluate_material(self, board: Board) -> float:
        """Count material value for both sides using vectorized operations."""
        # Access numpy arrays directly from board (zero conversion overhead!)
        board_array = board.piece_array
        color_array = board.color_array
        
        # Vectorized material calculation
        # Map piece types to values, multiply by colors, sum everything
        values = self.PIECE_VALUE_ARRAY[board_array]
        score = np.sum(values * color_array)
        
        return float(score)
    
    def _evaluate_position(self, board: Board) -> float:
        """Evaluate piece positions using piece-square tables with vectorized operations."""
        # Access numpy arrays directly from board (zero conversion overhead!)
        board_array = board.piece_array
        color_array = board.color_array
        
        # Determine if we're in endgame
        is_endgame = self._is_endgame_fast(board_array, color_array)
        
        # Use numba-compiled function for fast position evaluation
        score = _create_piece_square_array(
            board_array, color_array, is_endgame,
            self.PAWN_TABLE, self.KNIGHT_TABLE, self.BISHOP_TABLE,
            self.ROOK_TABLE, self.QUEEN_TABLE, 
            self.KING_MIDDLEGAME_TABLE, self.KING_ENDGAME_TABLE
        )
        
        return float(score)
    
    def _is_endgame_fast(self, board_array, color_array) -> bool:
        """Fast endgame detection using numpy operations."""
        # Count queens (piece type 5)
        queen_mask = (board_array == 5)
        white_queens = np.sum(queen_mask & (color_array == 1))
        black_queens = np.sum(queen_mask & (color_array == -1))
        
        # If both queens traded, it's endgame
        if white_queens == 0 and black_queens == 0:
            return True
        
        # Count non-pawn, non-king material
        # Pieces 2,3,4,5 (knight, bishop, rook, queen)
        minor_major_mask = (board_array >= 2) & (board_array <= 5)
        values = self.PIECE_VALUE_ARRAY[board_array]
        total_material = np.sum(values[minor_major_mask])
        
        return total_material < 2600
    
    def _get_piece_square_value(self, piece, row: int, col: int, is_endgame: bool) -> float:
        """Get the piece-square table value for a piece."""
        # For black pieces, flip the row (black's perspective)
        if piece.color == Color.BLACK:
            row = 7 - row
        
        if piece.type == PieceType.PAWN:
            return self.PAWN_TABLE[row][col]
        elif piece.type == PieceType.KNIGHT:
            return self.KNIGHT_TABLE[row][col]
        elif piece.type == PieceType.BISHOP:
            return self.BISHOP_TABLE[row][col]
        elif piece.type == PieceType.ROOK:
            return self.ROOK_TABLE[row][col]
        elif piece.type == PieceType.QUEEN:
            return self.QUEEN_TABLE[row][col]
        elif piece.type == PieceType.KING:
            if is_endgame:
                return self.KING_ENDGAME_TABLE[row][col]
            else:
                return self.KING_MIDDLEGAME_TABLE[row][col]
        
        return 0
    
    def _is_endgame(self, board: Board) -> bool:
        """
        Determine if position is in endgame phase.
        Simple heuristic: queens are off the board or total material is low.
        """
        white_queens = 0
        black_queens = 0
        total_material = 0
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece((row, col))
                if piece:
                    if piece.type == PieceType.QUEEN:
                        if piece.color == Color.WHITE:
                            white_queens += 1
                        else:
                            black_queens += 1
                    # Count non-pawn, non-king material
                    if piece.type not in [PieceType.PAWN, PieceType.KING]:
                        total_material += self.PIECE_VALUES[piece.type]
        
        # Endgame if both queens are off or total material is low
        queens_traded = (white_queens == 0 and black_queens == 0)
        low_material = total_material < 2600  # Less than 2 rooks + 2 bishops worth
        
        return queens_traded or low_material
    
    def _evaluate_mobility(self, board: Board) -> float:
        """
        Evaluate piece mobility (number of legal moves).
        More mobility generally means better position.
        """
        from engine.moves import MoveGenerator
        
        gen = MoveGenerator(board)
        white_moves = len(gen.generate_legal_moves(Color.WHITE))
        black_moves = len(gen.generate_legal_moves(Color.BLACK))
        
        return (white_moves - black_moves) * 0.1
    
    def _evaluate_king_safety(self, board: Board) -> float:
        """
        Evaluate king safety based on pawn shield and attacking pieces.
        """
        # TODO: Implement king safety evaluation
        # - Check pawn shield in front of king
        # - Count attacking pieces near king
        # - Penalize open files near king
        return 0
    
    def _evaluate_pawn_structure(self, board: Board) -> float:
        """
        Evaluate pawn structure.
        Penalize doubled, isolated, and backward pawns.
        Reward passed pawns.
        """
        # TODO: Implement pawn structure evaluation
        return 0
    
    def quick_evaluate(self, board: Board) -> float:
        """
        Quick evaluation using only material count.
        Useful for leaf nodes in quiescence search.
        """
        return self._evaluate_material(board)
