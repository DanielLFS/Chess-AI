"""
Move Generation Module - Fully Numba Optimized
Generates legal moves using encoded moves (uint16) and numpy arrays.
All hot paths compiled with numba for maximum performance.

Move Encoding Format (16 bits):
- Bits 0-5:   from_square (0-63)
- Bits 6-11:  to_square (0-63)
- Bits 12-14: flags (0=normal, 1-4=promotions, 5-6=castling, 7=en passant)
"""

from typing import List, Tuple, Optional
from engine.board import Board, Move, Piece, PieceType, Color
import numpy as np
from numba import njit

# Move encoding constants
FLAG_NORMAL = 0
FLAG_PROMOTION_QUEEN = 1
FLAG_PROMOTION_ROOK = 2
FLAG_PROMOTION_BISHOP = 3
FLAG_PROMOTION_KNIGHT = 4
FLAG_CASTLING_KINGSIDE = 5
FLAG_CASTLING_QUEENSIDE = 6
FLAG_EN_PASSANT = 7

MASK_FROM_SQ = 0x3F
MASK_TO_SQ = 0xFC0
MASK_FLAGS = 0x7000
SHIFT_TO_SQ = 6
SHIFT_FLAGS = 12


@njit(cache=True)
def encode_move(from_row: int, from_col: int, to_row: int, to_col: int, flags: int = 0) -> np.uint16:
    """Encode move into 16-bit integer."""
    from_sq = from_row * 8 + from_col
    to_sq = to_row * 8 + to_col
    return np.uint16((flags << SHIFT_FLAGS) | (to_sq << SHIFT_TO_SQ) | from_sq)


@njit(cache=True)
def get_from_square(encoded_move: np.uint16) -> int:
    """Extract from_square (0-63) from encoded move."""
    return encoded_move & MASK_FROM_SQ


@njit(cache=True)
def get_to_square(encoded_move: np.uint16) -> int:
    """Extract to_square (0-63) from encoded move."""
    return (encoded_move & MASK_TO_SQ) >> SHIFT_TO_SQ


@njit(cache=True)
def get_flags(encoded_move: np.uint16) -> int:
    """Extract flags from encoded move."""
    return (encoded_move & MASK_FLAGS) >> SHIFT_FLAGS


@njit(cache=True)
def is_promotion(encoded_move: np.uint16) -> bool:
    """Check if move is a promotion."""
    flags = get_flags(encoded_move)
    return 1 <= flags <= 4

# Pre-computed direction arrays
DIAGONAL_DIRS = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]], dtype=np.int8)
STRAIGHT_DIRS = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]], dtype=np.int8)
QUEEN_DIRS = np.array([[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]], dtype=np.int8)
KNIGHT_OFFSETS = np.array([[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]], dtype=np.int8)
KING_OFFSETS = np.array([[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]], dtype=np.int8)

# Piece type constants (matching board.py)
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6


@njit(cache=True)
def _generate_pseudo_legal_moves_numba(piece_array, color_array, color_val, 
                                       en_passant_row, en_passant_col,
                                       can_castle_kingside, can_castle_queenside):
    """Generate all pseudo-legal moves for a color (numba-compiled, returns uint16 array)."""
    moves_list = []
    
    # Pawns
    direction = -1 if color_val == 1 else 1
    start_row = 6 if color_val == 1 else 1
    promo_row = 0 if color_val == 1 else 7
    
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == PAWN and color_array[row, col] == color_val:
                new_row = row + direction
                if 0 <= new_row < 8 and piece_array[new_row, col] == EMPTY:
                    if new_row == promo_row:
                        moves_list.append(encode_move(row, col, new_row, col, FLAG_PROMOTION_QUEEN))
                        moves_list.append(encode_move(row, col, new_row, col, FLAG_PROMOTION_ROOK))
                        moves_list.append(encode_move(row, col, new_row, col, FLAG_PROMOTION_BISHOP))
                        moves_list.append(encode_move(row, col, new_row, col, FLAG_PROMOTION_KNIGHT))
                    else:
                        moves_list.append(encode_move(row, col, new_row, col, FLAG_NORMAL))
                    
                    if row == start_row:
                        double_row = row + 2 * direction
                        if piece_array[double_row, col] == EMPTY:
                            moves_list.append(encode_move(row, col, double_row, col, FLAG_NORMAL))
                
                for col_offset in [-1, 1]:
                    new_col = col + col_offset
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece != EMPTY and target_color != color_val:
                            if new_row == promo_row:
                                moves_list.append(encode_move(row, col, new_row, new_col, FLAG_PROMOTION_QUEEN))
                                moves_list.append(encode_move(row, col, new_row, new_col, FLAG_PROMOTION_ROOK))
                                moves_list.append(encode_move(row, col, new_row, new_col, FLAG_PROMOTION_BISHOP))
                                moves_list.append(encode_move(row, col, new_row, new_col, FLAG_PROMOTION_KNIGHT))
                            else:
                                moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                        
                        elif en_passant_row >= 0 and new_row == en_passant_row and new_col == en_passant_col:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_EN_PASSANT))
    
    # Knights
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == KNIGHT and color_array[row, col] == color_val:
                for i in range(len(KNIGHT_OFFSETS)):
                    new_row = row + KNIGHT_OFFSETS[i, 0]
                    new_col = col + KNIGHT_OFFSETS[i, 1]
                    
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece == EMPTY or target_color != color_val:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
    
    # Bishops
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == BISHOP and color_array[row, col] == color_val:
                for i in range(len(DIAGONAL_DIRS)):
                    row_dir = DIAGONAL_DIRS[i, 0]
                    col_dir = DIAGONAL_DIRS[i, 1]
                    
                    for distance in range(1, 8):
                        new_row = row + row_dir * distance
                        new_col = col + col_dir * distance
                        
                        if not (0 <= new_row < 8 and 0 <= new_col < 8):
                            break
                        
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece == EMPTY:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                        elif target_color != color_val:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                            break
                        else:
                            break
    
    # Rooks
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == ROOK and color_array[row, col] == color_val:
                for i in range(len(STRAIGHT_DIRS)):
                    row_dir = STRAIGHT_DIRS[i, 0]
                    col_dir = STRAIGHT_DIRS[i, 1]
                    
                    for distance in range(1, 8):
                        new_row = row + row_dir * distance
                        new_col = col + col_dir * distance
                        
                        if not (0 <= new_row < 8 and 0 <= new_col < 8):
                            break
                        
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece == EMPTY:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                        elif target_color != color_val:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                            break
                        else:
                            break
    
    # Queens
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == QUEEN and color_array[row, col] == color_val:
                for i in range(len(QUEEN_DIRS)):
                    row_dir = QUEEN_DIRS[i, 0]
                    col_dir = QUEEN_DIRS[i, 1]
                    
                    for distance in range(1, 8):
                        new_row = row + row_dir * distance
                        new_col = col + col_dir * distance
                        
                        if not (0 <= new_row < 8 and 0 <= new_col < 8):
                            break
                        
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece == EMPTY:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                        elif target_color != color_val:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                            break
                        else:
                            break
    
    # King (regular moves)
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == KING and color_array[row, col] == color_val:
                for i in range(len(KING_OFFSETS)):
                    new_row = row + KING_OFFSETS[i, 0]
                    new_col = col + KING_OFFSETS[i, 1]
                    
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target_piece = piece_array[new_row, new_col]
                        target_color = color_array[new_row, new_col]
                        
                        if target_piece == EMPTY or target_color != color_val:
                            moves_list.append(encode_move(row, col, new_row, new_col, FLAG_NORMAL))
                
                # Castling
                if can_castle_kingside:
                    if piece_array[row, col + 1] == EMPTY and piece_array[row, col + 2] == EMPTY:
                        moves_list.append(encode_move(row, col, row, col + 2, FLAG_CASTLING_KINGSIDE))
                
                if can_castle_queenside:
                    if piece_array[row, col - 1] == EMPTY and piece_array[row, col - 2] == EMPTY and piece_array[row, col - 3] == EMPTY:
                        moves_list.append(encode_move(row, col, row, col - 2, FLAG_CASTLING_QUEENSIDE))
    
    return np.array(moves_list, dtype=np.uint16)


@njit(cache=True)
def _is_square_attacked_numba(piece_array, color_array, target_row, target_col, attacker_color_val):
    """Check if a square is attacked by any piece of given color (numba-compiled)."""
    # Pawn attacks
    pawn_dir = 1 if attacker_color_val == 1 else -1
    for col_offset in [-1, 1]:
        pawn_row = target_row - pawn_dir
        pawn_col = target_col + col_offset
        if 0 <= pawn_row < 8 and 0 <= pawn_col < 8:
            if piece_array[pawn_row, pawn_col] == PAWN and color_array[pawn_row, pawn_col] == attacker_color_val:
                return True
    
    # Knight attacks
    for i in range(len(KNIGHT_OFFSETS)):
        knight_row = target_row + KNIGHT_OFFSETS[i, 0]
        knight_col = target_col + KNIGHT_OFFSETS[i, 1]
        if 0 <= knight_row < 8 and 0 <= knight_col < 8:
            if piece_array[knight_row, knight_col] == KNIGHT and color_array[knight_row, knight_col] == attacker_color_val:
                return True
    
    # King attacks
    for i in range(len(KING_OFFSETS)):
        king_row = target_row + KING_OFFSETS[i, 0]
        king_col = target_col + KING_OFFSETS[i, 1]
        if 0 <= king_row < 8 and 0 <= king_col < 8:
            if piece_array[king_row, king_col] == KING and color_array[king_row, king_col] == attacker_color_val:
                return True
    
    # Diagonal attacks (bishop, queen)
    for i in range(len(DIAGONAL_DIRS)):
        row_dir = DIAGONAL_DIRS[i, 0]
        col_dir = DIAGONAL_DIRS[i, 1]
        for distance in range(1, 8):
            check_row = target_row + row_dir * distance
            check_col = target_col + col_dir * distance
            
            if not (0 <= check_row < 8 and 0 <= check_col < 8):
                break
            
            piece = piece_array[check_row, check_col]
            if piece != EMPTY:
                if color_array[check_row, check_col] == attacker_color_val:
                    if piece == BISHOP or piece == QUEEN:
                        return True
                break
    
    # Straight attacks (rook, queen)
    for i in range(len(STRAIGHT_DIRS)):
        row_dir = STRAIGHT_DIRS[i, 0]
        col_dir = STRAIGHT_DIRS[i, 1]
        for distance in range(1, 8):
            check_row = target_row + row_dir * distance
            check_col = target_col + col_dir * distance
            
            if not (0 <= check_row < 8 and 0 <= check_col < 8):
                break
            
            piece = piece_array[check_row, check_col]
            if piece != EMPTY:
                if color_array[check_row, check_col] == attacker_color_val:
                    if piece == ROOK or piece == QUEEN:
                        return True
                break
    
    return False


@njit(cache=True)
def _find_king_position(piece_array, color_array, color_val):
    """Find king position for given color (numba-compiled)."""
    for row in range(8):
        for col in range(8):
            if piece_array[row, col] == KING and color_array[row, col] == color_val:
                return row, col
    return -1, -1  # Should never happen in valid position


class MoveGenerator:
    """Generates legal moves for chess pieces using numba-optimized functions."""
    __slots__ = ('board',)
    
    def __init__(self, board: Board):
        self.board = board
    
    def generate_legal_moves(self, color: Optional[Color] = None) -> List[Move]:
        """Generate all legal moves for the given color (returns Move objects for compatibility)."""
        if color is None:
            color = self.board.current_player
        
        # Generate encoded moves
        encoded_moves = self.generate_legal_moves_encoded(color)
        
        # Convert to Move objects for backward compatibility
        moves = []
        for encoded in encoded_moves:
            from_sq = get_from_square(encoded)
            to_sq = get_to_square(encoded)
            from_row, from_col = from_sq // 8, from_sq % 8
            to_row, to_col = to_sq // 8, to_sq % 8
            
            # Create Move object
            from_pos = (from_row, from_col)
            to_pos = (to_row, to_col)
            flags = get_flags(encoded)
            
            # Handle special moves
            if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
                move = Move(from_pos, to_pos, is_castling=True)
            elif flags == FLAG_EN_PASSANT:
                move = Move(from_pos, to_pos, is_en_passant=True)
            elif is_promotion(encoded):
                promo_map = {
                    FLAG_PROMOTION_QUEEN: PieceType.QUEEN,
                    FLAG_PROMOTION_ROOK: PieceType.ROOK,
                    FLAG_PROMOTION_BISHOP: PieceType.BISHOP,
                    FLAG_PROMOTION_KNIGHT: PieceType.KNIGHT
                }
                move = Move(from_pos, to_pos, promotion=promo_map[flags])
            else:
                move = Move(from_pos, to_pos)
            
            # Set captured piece if there's a piece at the target square
            move.captured_piece = self.board.get_piece(to_pos)
            
            moves.append(move)
        
        return moves
    
    def generate_legal_moves_encoded(self, color: Optional[Color] = None) -> np.ndarray:
        """Generate all legal moves (returns uint16 array for maximum performance)."""
        if color is None:
            color = self.board.current_player
        
        # Generate pseudo-legal moves
        color_val = 1 if color == Color.WHITE else -1
        en_passant_row = self.board.en_passant_target[0] if self.board.en_passant_target else -1
        en_passant_col = self.board.en_passant_target[1] if self.board.en_passant_target else -1
        
        castling_rights = self.board.castling_rights.get(color, {})
        can_castle_kingside = castling_rights.get('kingside', False)
        can_castle_queenside = castling_rights.get('queenside', False)
        
        pseudo_moves = _generate_pseudo_legal_moves_numba(
            self.board.piece_array, 
            self.board.color_array,
            color_val,
            en_passant_row,
            en_passant_col,
            can_castle_kingside,
            can_castle_queenside
        )
        
        # Filter to legal moves (not in check)
        legal_moves = []
        for encoded_move in pseudo_moves:
            if self._is_legal_move_encoded(encoded_move, color):
                legal_moves.append(encoded_move)
        
        return np.array(legal_moves, dtype=np.uint16)
    
    def _is_legal_move_encoded(self, encoded_move: np.uint16, color: Color) -> bool:
        """Check if an encoded move is legal (doesn't leave king in check)."""
        flags = get_flags(encoded_move)
        
        # Special validation for castling - can't castle through check
        if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
            from_sq = get_from_square(encoded_move)
            from_row, from_col = from_sq // 8, from_sq % 8
            
            color_val = 1 if color == Color.WHITE else -1
            opponent_color_val = -color_val
            
            # Can't castle if king is currently in check
            if _is_square_attacked_numba(
                self.board.piece_array,
                self.board.color_array,
                from_row,
                from_col,
                opponent_color_val
            ):
                return False
            
            # Can't castle if king passes through attacked square
            direction = 1 if flags == FLAG_CASTLING_KINGSIDE else -1
            middle_col = from_col + direction
            if _is_square_attacked_numba(
                self.board.piece_array,
                self.board.color_array,
                from_row,
                middle_col,
                opponent_color_val
            ):
                return False
        
        # Make the move temporarily
        self.board.make_move_encoded(encoded_move)
        
        # Check if our king is in check
        color_val = 1 if color == Color.WHITE else -1
        king_row, king_col = _find_king_position(
            self.board.piece_array,
            self.board.color_array,
            color_val
        )
        
        opponent_color_val = -color_val
        in_check = _is_square_attacked_numba(
            self.board.piece_array,
            self.board.color_array,
            king_row,
            king_col,
            opponent_color_val
        )
        
        # Unmake the move
        self.board.unmake_move()
        
        return not in_check
    
    # Legacy methods for backward compatibility
    def generate_pseudo_legal_moves(self, color: Color) -> List[Move]:
        """Generate pseudo-legal moves (returns Move objects for compatibility)."""
        color_val = 1 if color == Color.WHITE else -1
        en_passant_row = self.board.en_passant_target[0] if self.board.en_passant_target else -1
        en_passant_col = self.board.en_passant_target[1] if self.board.en_passant_target else -1
        
        castling_rights = self.board.castling_rights.get(color, {})
        can_castle_kingside = castling_rights.get('kingside', False)
        can_castle_queenside = castling_rights.get('queenside', False)
        
        encoded_moves = _generate_pseudo_legal_moves_numba(
            self.board.piece_array,
            self.board.color_array,
            color_val,
            en_passant_row,
            en_passant_col,
            can_castle_kingside,
            can_castle_queenside
        )
        
        # Convert to Move objects
        moves = []
        for encoded in encoded_moves:
            moves.append(Move.from_encoded(encoded, self.board))
        
        return moves
    
    def is_legal_move(self, move: Move) -> bool:
        """Check if a Move object is legal."""
        # Get piece at from position to determine color
        piece = self.board.get_piece(move.from_pos)
        if not piece:
            return False
        return self._is_legal_move_encoded(self._move_to_encoded(move), piece.color)
    
    def _move_to_encoded(self, move: Move) -> np.uint16:
        """Convert Move object to encoded uint16."""
        flags = FLAG_NORMAL
        if move.is_castling:
            flags = FLAG_CASTLING_KINGSIDE if move.to_pos[1] > move.from_pos[1] else FLAG_CASTLING_QUEENSIDE
        elif move.is_en_passant:
            flags = FLAG_EN_PASSANT
        elif move.promotion:
            promo_map = {
                PieceType.QUEEN: FLAG_PROMOTION_QUEEN,
                PieceType.ROOK: FLAG_PROMOTION_ROOK,
                PieceType.BISHOP: FLAG_PROMOTION_BISHOP,
                PieceType.KNIGHT: FLAG_PROMOTION_KNIGHT
            }
            flags = promo_map.get(move.promotion, FLAG_NORMAL)
        return encode_move(move.from_pos[0], move.from_pos[1], move.to_pos[0], move.to_pos[1], flags)
    
    def is_in_check(self, color: Color) -> bool:
        """Check if the given color's king is in check."""
        color_val = 1 if color == Color.WHITE else -1
        king_row, king_col = _find_king_position(
            self.board.piece_array,
            self.board.color_array,
            color_val
        )
        
        if king_row < 0:
            return False  # No king found
        
        opponent_color_val = -color_val
        return _is_square_attacked_numba(
            self.board.piece_array,
            self.board.color_array,
            king_row,
            king_col,
            opponent_color_val
        )
    
    def is_checkmate(self, color: Color) -> bool:
        """Check if the given color is in checkmate."""
        if not self.is_in_check(color):
            return False
        
        # Check if there are any legal moves
        legal_moves = self.generate_legal_moves_encoded(color)
        return len(legal_moves) == 0
    
    def is_stalemate(self, color: Color) -> bool:
        """Check if the given color is in stalemate."""
        if self.is_in_check(color):
            return False
        
        # Check if there are any legal moves
        legal_moves = self.generate_legal_moves_encoded(color)
        return len(legal_moves) == 0
