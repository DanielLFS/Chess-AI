"""
Board Representation Module - OPTIMIZED
Focus: Maximum speed with numba, clean separation for testing, perfect logic

Key optimizations:
- IntEnum instead of Enum (faster comparisons, works with numba)
- Castling rights as bitmask (faster than nested dicts)
- Hot path functions separated and numba-compiled
- Debug mode available (zero cost when disabled)
"""

from typing import List, Optional, Tuple, Dict
from enum import IntEnum
import copy
import numpy as np
from numba import njit

# Global debug flag (set to False for production - zero overhead)
DEBUG_MODE = False

# Use IntEnum for speed - works with numba, faster comparisons
class PieceType(IntEnum):
    EMPTY = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6
    
    def __str__(self):
        symbols = {0: '.', 1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}
        return symbols.get(self.value, '?')


class Color(IntEnum):
    WHITE = 1
    BLACK = -1
    
    def __str__(self):
        return 'white' if self.value == 1 else 'black'


# Castling rights as bitmask (4x faster than nested dicts)
CASTLE_WK = 0b0001  # White kingside
CASTLE_WQ = 0b0010  # White queenside
CASTLE_BK = 0b0100  # Black kingside
CASTLE_BQ = 0b1000  # Black queenside
CASTLE_ALL = 0b1111

# Move encoding flags
FLAG_NORMAL = 0
FLAG_PROMOTION_QUEEN = 1
FLAG_PROMOTION_ROOK = 2
FLAG_PROMOTION_BISHOP = 3
FLAG_PROMOTION_KNIGHT = 4
FLAG_CASTLING_KINGSIDE = 5
FLAG_CASTLING_QUEENSIDE = 6
FLAG_EN_PASSANT = 7

# Legacy mapping for backward compatibility
PIECE_TYPE_TO_INDEX = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 2,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 4,
    PieceType.QUEEN: 5,
    PieceType.KING: 6
}


# ============================================================================
# HOT PATH: Numba-compiled functions (separated for easy testing)
# ============================================================================

@njit(cache=True, inline='always')
def decode_move(encoded: np.uint16):
    """Decode encoded move. Returns (from_sq, to_sq, flags)."""
    from_sq = int(encoded & 0x3F)
    to_sq = int((encoded >> 6) & 0x3F)
    flags = int(encoded >> 12)
    return from_sq, to_sq, flags


@njit(cache=True)
def make_move_fast(pieces: np.ndarray, colors: np.ndarray, 
                   from_row: int, from_col: int, to_row: int, to_col: int, 
                   flags: int):
    """
    HOT PATH: Apply move to arrays (numba-optimized).
    Returns: (captured_piece, captured_color, ep_captured_piece, ep_captured_color)
    """
    piece = pieces[from_row, from_col]
    color = colors[from_row, from_col]
    captured = pieces[to_row, to_col]
    captured_color = colors[to_row, to_col]
    ep_captured = np.int8(0)
    ep_captured_color = np.int8(0)
    
    # Handle special moves
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        # Move king
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = 0
        colors[from_row, from_col] = 0
        
        # Move rook
        if flags == FLAG_CASTLING_KINGSIDE:
            pieces[from_row, 5] = pieces[from_row, 7]
            colors[from_row, 5] = colors[from_row, 7]
            pieces[from_row, 7] = 0
            colors[from_row, 7] = 0
        else:  # Queenside
            pieces[from_row, 3] = pieces[from_row, 0]
            colors[from_row, 3] = colors[from_row, 0]
            pieces[from_row, 0] = 0
            colors[from_row, 0] = 0
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = 0
        colors[from_row, from_col] = 0
        
        # Capture en passant pawn (on same row as moving pawn)
        ep_captured = pieces[from_row, to_col]
        ep_captured_color = colors[from_row, to_col]
        pieces[from_row, to_col] = 0
        colors[from_row, to_col] = 0
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Promote pawn
        promo_pieces = np.array([0, PieceType.QUEEN, PieceType.ROOK, 
                                PieceType.BISHOP, PieceType.KNIGHT], dtype=np.int8)
        pieces[to_row, to_col] = promo_pieces[flags]
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = 0
        colors[from_row, from_col] = 0
    
    else:  # Normal move
        pieces[to_row, to_col] = piece
        colors[to_row, to_col] = color
        pieces[from_row, from_col] = 0
        colors[from_row, from_col] = 0
    
    return captured, captured_color, ep_captured, ep_captured_color


@njit(cache=True)
def unmake_move_fast(pieces: np.ndarray, colors: np.ndarray,
                     from_row: int, from_col: int, to_row: int, to_col: int,
                     flags: int, captured: int, captured_color: int,
                     ep_captured: int, ep_captured_color: int):
    """HOT PATH: Undo move on arrays (numba-optimized)."""
    piece = pieces[to_row, to_col]
    color = colors[to_row, to_col]
    
    if flags == FLAG_CASTLING_KINGSIDE or flags == FLAG_CASTLING_QUEENSIDE:
        # Move king back
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = 0
        colors[to_row, to_col] = 0
        
        # Move rook back
        if flags == FLAG_CASTLING_KINGSIDE:
            pieces[from_row, 7] = pieces[from_row, 5]
            colors[from_row, 7] = colors[from_row, 5]
            pieces[from_row, 5] = 0
            colors[from_row, 5] = 0
        else:
            pieces[from_row, 0] = pieces[from_row, 3]
            colors[from_row, 0] = colors[from_row, 3]
            pieces[from_row, 3] = 0
            colors[from_row, 3] = 0
    
    elif flags == FLAG_EN_PASSANT:
        # Move pawn back
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = 0
        colors[to_row, to_col] = 0
        
        # Restore captured pawn
        pieces[from_row, to_col] = ep_captured
        colors[from_row, to_col] = ep_captured_color
    
    elif FLAG_PROMOTION_QUEEN <= flags <= FLAG_PROMOTION_KNIGHT:
        # Restore pawn
        pieces[from_row, from_col] = PieceType.PAWN
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = captured
        colors[to_row, to_col] = captured_color
    
    else:  # Normal move
        pieces[from_row, from_col] = piece
        colors[from_row, from_col] = color
        pieces[to_row, to_col] = captured
        colors[to_row, to_col] = captured_color


@njit(cache=True, inline='always')
def update_castling_rights(castling: int, piece: int, color: int, 
                          from_col: int, to_row: int, to_col: int,
                          captured: int) -> int:
    """HOT PATH: Update castling rights bitmask."""
    # King moves - lose both castling rights
    if piece == PieceType.KING:
        if color == Color.WHITE:
            castling &= ~(CASTLE_WK | CASTLE_WQ)
        else:
            castling &= ~(CASTLE_BK | CASTLE_BQ)
    
    # Rook moves - lose castling right for that side
    elif piece == PieceType.ROOK:
        if color == Color.WHITE:
            if from_col == 0:
                castling &= ~CASTLE_WQ
            elif from_col == 7:
                castling &= ~CASTLE_WK
        else:
            if from_col == 0:
                castling &= ~CASTLE_BQ
            elif from_col == 7:
                castling &= ~CASTLE_BK
    
    # Rook captured - opponent loses castling right
    if captured == PieceType.ROOK:
        if to_row == 0:  # Black rooks
            if to_col == 0:
                castling &= ~CASTLE_BQ
            elif to_col == 7:
                castling &= ~CASTLE_BK
        elif to_row == 7:  # White rooks
            if to_col == 0:
                castling &= ~CASTLE_WQ
            elif to_col == 7:
                castling &= ~CASTLE_WK
    
    return castling


# ============================================================================
# Lightweight classes for compatibility (minimal OOP overhead)
# ============================================================================

class Piece:
    """Minimal piece representation. Use __slots__ to reduce memory."""
    __slots__ = ('type', 'color')
    
    def __init__(self, piece_type: int, color: int):
        self.type = piece_type  # int for speed
        self.color = color      # int for speed
    
    def __str__(self):
        if self.type == PieceType.EMPTY:
            return '.'
        symbols = {1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}
        symbol = symbols.get(self.type, '?')
        return symbol if self.color == Color.WHITE else symbol.lower()
    
    def __repr__(self):
        return f"Piece({self.type}, {self.color})"


class Move:
    """Minimal move representation with undo info."""
    __slots__ = ('from_pos', 'to_pos', 'promotion', 'is_castling', 'is_en_passant',
                 'captured_piece', 'prev_castling_rights', 'prev_en_passant_target',
                 'prev_halfmove_clock', 'prev_fullmove_number', 'moving_piece')
    
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int],
                 promotion: Optional[int] = None, is_castling: bool = False,
                 is_en_passant: bool = False):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece: Optional[Piece] = None
        self.moving_piece: Optional[Piece] = None  # Store moving piece
        
        # Undo info
        self.prev_castling_rights = None
        self.prev_en_passant_target = None
        self.prev_halfmove_clock = None
        self.prev_fullmove_number = None
    
    def __str__(self):
        """Algebraic notation."""
        from_sq = chr(ord('a') + self.from_pos[1]) + str(8 - self.from_pos[0])
        to_sq = chr(ord('a') + self.to_pos[1]) + str(8 - self.to_pos[0])
        promo = f"={PieceType(self.promotion)}" if self.promotion else ""
        return f"{from_sq}{to_sq}{promo}"
    
    def __repr__(self):
        return f"Move({self.from_pos} -> {self.to_pos})"


# ============================================================================
# Board class - thin wrapper over numpy arrays with hot path optimization
# ============================================================================

class Board:
    """
    Optimized chess board representation.
    Uses numpy arrays + numba for speed, minimal OOP overhead.
    """
    __slots__ = ('board', 'current_player', 'castling_rights', 'en_passant_target',
                 'halfmove_clock', 'fullmove_number', 'move_history', 'position_history',
                 'track_history', 'king_positions', 'piece_array', 'color_array')
    
    def __init__(self):
        # 2D list for compatibility (could remove later if not needed)
        self.board: List[List[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        
        # Game state
        self.current_player = Color.WHITE
        self.castling_rights = CASTLE_ALL  # Use bitmask instead of dict!
        self.en_passant_target: Optional[Tuple[int, int]] = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        # History
        self.move_history: List = []
        self.position_history: List[str] = []
        self.track_history = True
        
        # Cached king positions (faster than searching)
        self.king_positions: Dict[int, Optional[Tuple[int, int]]] = {
            Color.WHITE: None,
            Color.BLACK: None
        }
        
        # HOT PATH: Numpy arrays (main data structure)
        self.piece_array = np.zeros((8, 8), dtype=np.int8)
        self.color_array = np.zeros((8, 8), dtype=np.int8)
        
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        """Set up starting position efficiently."""
        # Use numpy for fast initialization
        back_rank = np.array([PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN, 
                             PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK], dtype=np.int8)
        
        # Black pieces
        self.piece_array[0, :] = back_rank
        self.color_array[0, :] = Color.BLACK
        self.piece_array[1, :] = PieceType.PAWN
        self.color_array[1, :] = Color.BLACK
        
        # White pieces
        self.piece_array[6, :] = PieceType.PAWN
        self.color_array[6, :] = Color.WHITE
        self.piece_array[7, :] = back_rank
        self.color_array[7, :] = Color.WHITE
        
        # Sync 2D board list
        self._sync_board_from_arrays()
        
        # Cache king positions
        self.king_positions[Color.WHITE] = (7, 4)
        self.king_positions[Color.BLACK] = (0, 4)
    
    def _sync_board_from_arrays(self):
        """Sync board list from numpy arrays (for compatibility)."""
        for row in range(8):
            for col in range(8):
                piece_type = self.piece_array[row, col]
                if piece_type == 0:
                    self.board[row][col] = None
                else:
                    color = self.color_array[row, col]
                    self.board[row][col] = Piece(piece_type, color)
    
    def _sync_numpy_arrays(self):
        """Sync numpy arrays from board list (when needed)."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is None:
                    self.piece_array[row, col] = 0
                    self.color_array[row, col] = 0
                else:
                    self.piece_array[row, col] = piece.type
                    self.color_array[row, col] = piece.color
    
    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """Get piece at position."""
        row, col = pos
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def set_piece(self, pos: Tuple[int, int], piece: Optional[Piece]):
        """Set piece at position (updates both arrays and board list)."""
        row, col = pos
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        
        self.board[row][col] = piece
        
        if piece is None:
            self.piece_array[row, col] = 0
            self.color_array[row, col] = 0
        else:
            self.piece_array[row, col] = piece.type
            self.color_array[row, col] = piece.color
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is on board."""
        row, col = pos
        return 0 <= row < 8 and 0 <= col < 8
    
    
    def make_move(self, move: Move) -> bool:
        """
        OPTIMIZED: Execute move using numba hot path.
        Returns True if successful.
        """
        piece = self.get_piece(move.from_pos)
        if piece is None or piece.color != self.current_player:
            return False
        
        # Save state for undo
        move.prev_castling_rights = self.castling_rights  # Just save int, not dict
        move.prev_en_passant_target = self.en_passant_target
        move.prev_halfmove_clock = self.halfmove_clock
        move.prev_fullmove_number = self.fullmove_number
        move.moving_piece = piece
        move.captured_piece = self.get_piece(move.to_pos)
        
        # Determine flags for encoding
        flags = FLAG_NORMAL
        if move.is_castling:
            flags = FLAG_CASTLING_KINGSIDE if move.to_pos[1] > move.from_pos[1] else FLAG_CASTLING_QUEENSIDE
        elif move.is_en_passant:
            flags = FLAG_EN_PASSANT
        elif move.promotion:
            promo_map = {PieceType.QUEEN: FLAG_PROMOTION_QUEEN, PieceType.ROOK: FLAG_PROMOTION_ROOK,
                        PieceType.BISHOP: FLAG_PROMOTION_BISHOP, PieceType.KNIGHT: FLAG_PROMOTION_KNIGHT}
            flags = promo_map.get(move.promotion, FLAG_NORMAL)
        
        # HOT PATH: Use numba function to update arrays
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        captured, captured_color, ep_captured, ep_captured_color = make_move_fast(
            self.piece_array, self.color_array, from_row, from_col, to_row, to_col, flags
        )
        
        # Sync board list (could be optimized further by only updating changed squares)
        self._sync_board_from_arrays()
        
        # Update king cache if king moved
        if piece.type == PieceType.KING:
            self.king_positions[piece.color] = move.to_pos
        
        # Update castling rights (using fast bitmask logic)
        self.castling_rights = update_castling_rights(
            self.castling_rights, piece.type, piece.color,
            from_col, to_row, to_col, captured
        )
        
        # Update en passant target
        self.en_passant_target = None
        if piece.type == PieceType.PAWN and abs(to_row - from_row) == 2:
            ep_row = (from_row + to_row) // 2
            self.en_passant_target = (ep_row, from_col)
        
        # Update clocks
        if piece.type == PieceType.PAWN or move.captured_piece:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        
        if self.current_player == Color.BLACK:
            self.fullmove_number += 1
        
        # Switch player
        self.current_player = -self.current_player
        
        # Track history if enabled
        if self.track_history:
            self.move_history.append(move)
            self.position_history.append(self.to_fen())
        
        return True
    
    
    def unmake_move(self, move: Move):
        """
        OPTIMIZED: Undo move using numba hot path.
        """
        if move is None or move.moving_piece is None:
            return
        
        # Switch player back first
        self.current_player = -self.current_player
        
        # Determine flags
        flags = FLAG_NORMAL
        if move.is_castling:
            flags = FLAG_CASTLING_KINGSIDE if move.to_pos[1] > move.from_pos[1] else FLAG_CASTLING_QUEENSIDE
        elif move.is_en_passant:
            flags = FLAG_EN_PASSANT
        elif move.promotion:
            promo_map = {PieceType.QUEEN: FLAG_PROMOTION_QUEEN, PieceType.ROOK: FLAG_PROMOTION_ROOK,
                        PieceType.BISHOP: FLAG_PROMOTION_BISHOP, PieceType.KNIGHT: FLAG_PROMOTION_KNIGHT}
            flags = promo_map.get(move.promotion, FLAG_NORMAL)
        
        # Prepare undo data
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        captured = move.captured_piece.type if move.captured_piece else 0
        captured_color = move.captured_piece.color if move.captured_piece else 0
        ep_captured = 0
        ep_captured_color = 0
        
        # For en passant, need to restore pawn on correct square
        if flags == FLAG_EN_PASSANT:
            ep_captured = PieceType.PAWN
            ep_captured_color = -move.moving_piece.color
        
        # HOT PATH: Use numba function to restore arrays
        unmake_move_fast(
            self.piece_array, self.color_array,
            from_row, from_col, to_row, to_col, flags,
            captured, captured_color, ep_captured, ep_captured_color
        )
        
        # Sync board list
        self._sync_board_from_arrays()
        
        # Restore king cache if king moved
        if move.moving_piece.type == PieceType.KING:
            self.king_positions[move.moving_piece.color] = move.from_pos
        
        # Restore game state
        self.castling_rights = move.prev_castling_rights
        self.en_passant_target = move.prev_en_passant_target
        self.halfmove_clock = move.prev_halfmove_clock
        self.fullmove_number = move.prev_fullmove_number
        
        # Remove from history if tracking
        if self.track_history:
            if self.move_history and self.move_history[-1] == move:
                self.move_history.pop()
            if self.position_history:
                self.position_history.pop()
    
    def to_fen(self) -> str:
        """
        Convert board to FEN notation.
        Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        """
        fen_parts = []
        
        # 1. Piece placement
        for row in range(8):
            empty_count = 0
            row_str = ""
            for col in range(8):
                piece = self.board[row][col]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += str(piece)
            if empty_count > 0:
                row_str += str(empty_count)
            fen_parts.append(row_str)
        
        fen = "/".join(fen_parts)
        
        # 2. Active color
        fen += " w" if self.current_player == Color.WHITE else " b"
        
        # 3. Castling availability (from bitmask)
        castling = ""
        if self.castling_rights & CASTLE_WK:
            castling += "K"
        if self.castling_rights & CASTLE_WQ:
            castling += "Q"
        if self.castling_rights & CASTLE_BK:
            castling += "k"
        if self.castling_rights & CASTLE_BQ:
            castling += "q"
        fen += " " + (castling if castling else "-")
        
        # 4. En passant target
        if self.en_passant_target:
            row, col = self.en_passant_target
            file = chr(ord('a') + col)
            rank = str(8 - row)
            fen += f" {file}{rank}"
        else:
            fen += " -"
        
        # 5. Halfmove clock
        fen += f" {self.halfmove_clock}"
        
        # 6. Fullmove number
        fen += f" {self.fullmove_number}"
        
        return fen
    
    def from_fen(self, fen: str):
        """Load board position from FEN notation."""
        parts = fen.split()
        if len(parts) != 6:
            raise ValueError("Invalid FEN string")
        
        # Clear board
        self.board = [[None] * 8 for _ in range(8)]
        self.king_positions = {Color.WHITE: None, Color.BLACK: None}
        
        # 1. Piece placement
        rows = parts[0].split('/')
        for row_idx, row_str in enumerate(rows):
            col_idx = 0
            for char in row_str:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    color = Color.WHITE if char.isupper() else Color.BLACK
                    # Convert char to PieceType int
                    piece_map = {'P': PieceType.PAWN, 'N': PieceType.KNIGHT, 'B': PieceType.BISHOP,
                                'R': PieceType.ROOK, 'Q': PieceType.QUEEN, 'K': PieceType.KING}
                    piece_type = piece_map[char.upper()]
                    self.board[row_idx][col_idx] = Piece(piece_type, color)
                    
                    # Cache king positions
                    if piece_type == PieceType.KING:
                        self.king_positions[color] = (row_idx, col_idx)
                    col_idx += 1
        
        # 2. Active color
        self.current_player = Color.WHITE if parts[1] == 'w' else Color.BLACK
        
        # 3. Castling rights (convert to bitmask)
        castling = parts[2]
        self.castling_rights = 0
        if 'K' in castling:
            self.castling_rights |= CASTLE_WK
        if 'Q' in castling:
            self.castling_rights |= CASTLE_WQ
        if 'k' in castling:
            self.castling_rights |= CASTLE_BK
        if 'q' in castling:
            self.castling_rights |= CASTLE_BQ
        
        # 4. En passant target
        if parts[3] != '-':
            file = ord(parts[3][0]) - ord('a')
            rank = 8 - int(parts[3][1])
            self.en_passant_target = (rank, file)
        else:
            self.en_passant_target = None
        
        # 5. Halfmove clock
        self.halfmove_clock = int(parts[4])
        
        # 6. Fullmove number
        self.fullmove_number = int(parts[5])
        
        # Sync numpy arrays
        self._sync_numpy_arrays()
    
    def display(self) -> str:
        """Return a string representation of the board."""
        display_str = "  a b c d e f g h\n"
        for row in range(8):
            display_str += f"{8-row} "
            for col in range(8):
                piece = self.board[row][col]
                display_str += (str(piece) if piece else '.') + ' '
            display_str += f"{8-row}\n"
        display_str += "  a b c d e f g h\n"
        return display_str
    
    def load_from_fen(self, fen: str):
        """Alias for from_fen() for backwards compatibility."""
        self.from_fen(fen)

    def copy(self) -> 'Board':
        """Create a deep copy of the board."""
        return copy.deepcopy(self)
    
    def find_king(self, color: Color) -> Optional[Tuple[int, int]]:
        """Find the position of the king for the given color."""
        # Use cached position for O(1) lookup
        return self.king_positions.get(color)
    
    def make_move_encoded(self, encoded_move: np.uint16):
        """Make a move using encoded format (fast path for search)."""
        # Decode move inline (avoid import)
        from_sq = int(encoded_move & 0x3F)
        to_sq = int((encoded_move & 0xFC0) >> 6)
        flags = int((encoded_move & 0x7000) >> 12)
        
        from_row, from_col = from_sq // 8, from_sq % 8
        to_row, to_col = to_sq // 8, to_sq % 8
        
        # Save state for undo
        self.move_history.append({
            'encoded_move': encoded_move,
            'captured_piece': self.get_piece((to_row, to_col)),
            'prev_castling_rights': copy.deepcopy(self.castling_rights),
            'prev_en_passant_target': self.en_passant_target,
            'prev_halfmove_clock': self.halfmove_clock,
            'prev_fullmove_number': self.fullmove_number
        })
        
        piece = self.get_piece((from_row, from_col))
        
        # Handle special moves (flags: 5=kingside, 6=queenside, 7=en passant, 1-4=promotions)
        if flags == 5 or flags == 6:  # Castling
            self.set_piece((to_row, to_col), piece)
            self.set_piece((from_row, from_col), None)
            
            # Move rook
            if flags == 5:  # Kingside
                rook = self.get_piece((from_row, 7))
                self.set_piece((from_row, 5), rook)
                self.set_piece((from_row, 7), None)
            else:  # Queenside
                rook = self.get_piece((from_row, 0))
                self.set_piece((from_row, 3), rook)
                self.set_piece((from_row, 0), None)
        
        elif flags == 7:  # En passant
            self.set_piece((to_row, to_col), piece)
            self.set_piece((from_row, from_col), None)
            # Remove captured pawn
            captured_pawn_row = from_row
            self.move_history[-1]['ep_captured_piece'] = self.get_piece((captured_pawn_row, to_col))
            self.set_piece((captured_pawn_row, to_col), None)
        
        elif 1 <= flags <= 4:  # Promotion
            promo_map = {1: PieceType.QUEEN, 2: PieceType.ROOK, 3: PieceType.BISHOP, 4: PieceType.KNIGHT}
            promoted_piece = Piece(promo_map[flags], piece.color)
            self.set_piece((to_row, to_col), promoted_piece)
            self.set_piece((from_row, from_col), None)
        
        else:  # Normal move
            self.set_piece((to_row, to_col), piece)
            self.set_piece((from_row, from_col), None)
        
        # Update castling rights
        if piece.type == PieceType.KING:
            self.castling_rights[piece.color]['kingside'] = False
            self.castling_rights[piece.color]['queenside'] = False
        elif piece.type == PieceType.ROOK:
            if from_col == 0:
                self.castling_rights[piece.color]['queenside'] = False
            elif from_col == 7:
                self.castling_rights[piece.color]['kingside'] = False
        
        # Update en passant target
        self.en_passant_target = None
        if piece.type == PieceType.PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, from_col)
        
        # Update move counters
        if piece.type == PieceType.PAWN or self.move_history[-1]['captured_piece']:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        
        if self.current_player == Color.BLACK:
            self.fullmove_number += 1
        
        # Switch player
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE



