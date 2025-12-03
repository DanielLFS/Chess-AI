"""
Board Representation Module
Handles chess board state, piece positions, and game rules.
"""

from typing import List, Optional, Tuple, Dict
from enum import Enum
import copy
import numpy as np
from numba import njit


class PieceType(Enum):
    """Enumeration of chess piece types."""
    PAWN = 'P'
    KNIGHT = 'N'
    BISHOP = 'B'
    ROOK = 'R'
    QUEEN = 'Q'
    KING = 'K'
    EMPTY = '.'


class Color(Enum):
    """Enumeration of piece colors."""
    WHITE = 'white'
    BLACK = 'black'


# Piece type to index mapping for fast numpy conversion (after PieceType defined)
PIECE_TYPE_TO_INDEX = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 2,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 4,
    PieceType.QUEEN: 5,
    PieceType.KING: 6
}


class Piece:
    """Represents a chess piece with type and color."""
    __slots__ = ('type', 'color')  # Reduce memory usage
    
    def __init__(self, piece_type: PieceType, color: Color):
        self.type = piece_type
        self.color = color
    
    def __str__(self):
        if self.type == PieceType.EMPTY:
            return '.'
        symbol = self.type.value
        return symbol if self.color == Color.WHITE else symbol.lower()
    
    def __repr__(self):
        return f"Piece({self.type}, {self.color})"


class Move:
    """Represents a chess move with metadata."""
    __slots__ = ('from_pos', 'to_pos', 'promotion', 'is_castling', 'is_en_passant', 
                 'captured_piece', 'prev_castling_rights', 'prev_en_passant_target',
                 'prev_halfmove_clock', 'prev_fullmove_number')
    
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                 promotion: Optional[PieceType] = None, is_castling: bool = False,
                 is_en_passant: bool = False):
        self.from_pos = from_pos  # (row, col)
        self.to_pos = to_pos      # (row, col)
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece: Optional[Piece] = None
        
        # Undo information (set by make_move)
        self.prev_castling_rights = None
        self.prev_en_passant_target = None
        self.prev_halfmove_clock = None
        self.prev_fullmove_number = None
        
    def __str__(self):
        """Convert move to algebraic notation."""
        from_square = self._pos_to_notation(self.from_pos)
        to_square = self._pos_to_notation(self.to_pos)
        promotion_str = f"={self.promotion.value}" if self.promotion else ""
        return f"{from_square}{to_square}{promotion_str}"
    
    def _pos_to_notation(self, pos: Tuple[int, int]) -> str:
        """Convert (row, col) to algebraic notation like 'e4'."""
        row, col = pos
        file = chr(ord('a') + col)
        rank = str(8 - row)
        return f"{file}{rank}"
    
    def __repr__(self):
        return f"Move({self.from_pos} -> {self.to_pos})"


class Board:
    """Represents a chess board and game state."""
    
    def __init__(self):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = Color.WHITE
        self.castling_rights = {
            Color.WHITE: {'kingside': True, 'queenside': True},
            Color.BLACK: {'kingside': True, 'queenside': True}
        }
        self.en_passant_target: Optional[Tuple[int, int]] = None
        self.halfmove_clock = 0  # For 50-move rule
        self.fullmove_number = 1
        self.move_history: List[Move] = []
        self.position_history: List[str] = []
        self.track_history = True  # Disable during search for performance
        
        # Cache king positions for fast lookup (optimization)
        self.king_positions: Dict[Color, Optional[Tuple[int, int]]] = {
            Color.WHITE: None,
            Color.BLACK: None
        }
        
        # Numpy arrays for fast evaluation (synced with board)
        # piece_array: 0=empty, 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        # color_array: 0=empty, 1=white, -1=black
        self.piece_array = np.zeros((8, 8), dtype=np.int8)
        self.color_array = np.zeros((8, 8), dtype=np.int8)
        
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        """Set up the standard starting position."""
        # Black pieces (row 0-1)
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for col, piece_type in enumerate(piece_order):
            self.board[0][col] = Piece(piece_type, Color.BLACK)
            self.board[7][col] = Piece(piece_type, Color.WHITE)
            # Cache king positions
            if piece_type == PieceType.KING:
                self.king_positions[Color.BLACK] = (0, col)
                self.king_positions[Color.WHITE] = (7, col)
        
        # Pawns
        for col in range(8):
            self.board[1][col] = Piece(PieceType.PAWN, Color.BLACK)
            self.board[6][col] = Piece(PieceType.PAWN, Color.WHITE)
        
        # Empty squares
        for row in range(2, 6):
            for col in range(8):
                self.board[row][col] = None
        
        # Initialize numpy arrays from board
        self._sync_numpy_arrays()
    
    def _sync_numpy_arrays(self):
        """Synchronize numpy arrays with board state. Called after bulk updates."""
        # Reset arrays
        self.piece_array.fill(0)
        self.color_array.fill(0)
        
        # Single pass through board - minimal Python overhead
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None:
                    # Use dict lookup instead of if/elif chain (faster)
                    self.piece_array[row, col] = PIECE_TYPE_TO_INDEX.get(piece.type, 0)
                    self.color_array[row, col] = 1 if piece.color == Color.WHITE else -1
    
    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """Get piece at given position. Assumes valid position for performance."""
        row, col = pos
        return self.board[row][col] if (0 <= row < 8 and 0 <= col < 8) else None
    
    def set_piece(self, pos: Tuple[int, int], piece: Optional[Piece]):
        """Set piece at given position. Assumes valid position for performance."""
        row, col = pos
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
            # Update numpy arrays (dict lookup faster than if/elif chain)
            if piece is None:
                self.piece_array[row, col] = 0
                self.color_array[row, col] = 0
            else:
                self.piece_array[row, col] = PIECE_TYPE_TO_INDEX.get(piece.type, 0)
                self.color_array[row, col] = 1 if piece.color == Color.WHITE else -1
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within board bounds."""
        row, col = pos
        return 0 <= row < 8 and 0 <= col < 8
    
    def make_move(self, move: Move) -> bool:
        """
        Execute a move on the board.
        Returns True if move was successfully made.
        """
        piece = self.get_piece(move.from_pos)
        if piece is None or piece.color != self.current_player:
            return False
        
        # Store state for undo (deep copy castling rights dict)
        move.prev_castling_rights = {
            Color.WHITE: self.castling_rights[Color.WHITE].copy(),
            Color.BLACK: self.castling_rights[Color.BLACK].copy()
        }
        move.prev_en_passant_target = self.en_passant_target
        move.prev_halfmove_clock = self.halfmove_clock
        move.prev_fullmove_number = self.fullmove_number
        
        # Store captured piece for undo
        move.captured_piece = self.get_piece(move.to_pos)
        
        # Update king position cache if king moves
        if piece.type == PieceType.KING:
            self.king_positions[piece.color] = move.to_pos
        
        # Handle castling
        if move.is_castling:
            self._execute_castling(move)
        # Handle en passant
        elif move.is_en_passant:
            self._execute_en_passant(move)
        # Regular move
        else:
            self.set_piece(move.to_pos, piece)
            self.set_piece(move.from_pos, None)
            
            # Handle pawn promotion
            if move.promotion:
                self.set_piece(move.to_pos, Piece(move.promotion, piece.color))
        
        # Update game state
        self._update_castling_rights(move, piece)
        self._update_en_passant_target(move, piece)
        
        # Update clocks
        if piece.type == PieceType.PAWN or move.captured_piece:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        
        if self.current_player == Color.BLACK:
            self.fullmove_number += 1
        
        # Switch players
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        # Record move (only if tracking enabled)
        if self.track_history:
            self.move_history.append(move)
            self.position_history.append(self.to_fen())
        
        return True
    
    def unmake_move(self, move: Optional[Move] = None):
        """
        Undo a move on the board.
        If move is None, undoes the last move from history (for encoded moves).
        This is much faster than copying the board for each move during search.
        """
        # If no move provided, unmake from history (for encoded moves)
        if move is None:
            if not self.move_history:
                return
            
            history_entry = self.move_history.pop()
            encoded_move = history_entry['encoded_move']
            
            # Decode move inline
            from_sq = int(encoded_move & 0x3F)
            to_sq = int((encoded_move & 0xFC0) >> 6)
            flags = int((encoded_move & 0x7000) >> 12)
            
            from_row, from_col = from_sq // 8, from_sq % 8
            to_row, to_col = to_sq // 8, to_sq % 8
            
            piece = self.get_piece((to_row, to_col))
            
            # Undo special moves (flags: 5=kingside, 6=queenside, 7=en passant, 1-4=promotions)
            if flags == 5 or flags == 6:  # Castling
                self.set_piece((from_row, from_col), piece)
                self.set_piece((to_row, to_col), None)
                
                if flags == 5:  # Kingside
                    rook = self.get_piece((from_row, 5))
                    self.set_piece((from_row, 7), rook)
                    self.set_piece((from_row, 5), None)
                else:  # Queenside
                    rook = self.get_piece((from_row, 3))
                    self.set_piece((from_row, 0), rook)
                    self.set_piece((from_row, 3), None)
            
            elif flags == 7:  # En passant
                self.set_piece((from_row, from_col), piece)
                self.set_piece((to_row, to_col), None)
                # Restore captured pawn
                self.set_piece((from_row, to_col), history_entry.get('ep_captured_piece'))
            
            elif 1 <= flags <= 4:  # Promotion - restore pawn
                pawn = Piece(PieceType.PAWN, piece.color)
                self.set_piece((from_row, from_col), pawn)
                self.set_piece((to_row, to_col), history_entry['captured_piece'])
            
            else:  # Regular move
                self.set_piece((from_row, from_col), piece)
                self.set_piece((to_row, to_col), history_entry['captured_piece'])
            
            # Restore game state
            self.castling_rights = history_entry['prev_castling_rights']
            self.en_passant_target = history_entry['prev_en_passant_target']
            self.halfmove_clock = history_entry['prev_halfmove_clock']
            self.fullmove_number = history_entry['prev_fullmove_number']
            
            # Switch player back
            self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
            
            return
        
        # Original unmake_move for Move objects
        # Switch player back
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        piece = self.get_piece(move.to_pos)
        
        # Restore king position cache if king moved
        if piece and piece.type == PieceType.KING:
            self.king_positions[piece.color] = move.from_pos
        
        # Undo castling
        if move.is_castling:
            self._undo_castling(move)
        # Undo en passant
        elif move.is_en_passant:
            self._undo_en_passant(move)
        # Undo regular move
        else:
            # Move piece back
            self.set_piece(move.from_pos, piece)
            # Restore captured piece or empty square
            self.set_piece(move.to_pos, move.captured_piece)
            
            # Undo pawn promotion (restore pawn)
            if move.promotion:
                self.set_piece(move.from_pos, Piece(PieceType.PAWN, piece.color))
        
        # Restore game state
        self.castling_rights = move.prev_castling_rights
        self.en_passant_target = move.prev_en_passant_target
        self.halfmove_clock = move.prev_halfmove_clock
        self.fullmove_number = move.prev_fullmove_number
        
        # Remove from history (only if tracking enabled)
        if self.track_history:
            if self.move_history and self.move_history[-1] == move:
                self.move_history.pop()
            if self.position_history:
                self.position_history.pop()
    
    def _execute_castling(self, move: Move):
        """Execute castling move."""
        piece = self.get_piece(move.from_pos)
        row = move.from_pos[0]
        
        # Move king
        self.set_piece(move.to_pos, piece)
        self.set_piece(move.from_pos, None)
        
        # Move rook
        if move.to_pos[1] == 6:  # Kingside
            rook = self.get_piece((row, 7))
            self.set_piece((row, 5), rook)
            self.set_piece((row, 7), None)
        else:  # Queenside (col == 2)
            rook = self.get_piece((row, 0))
            self.set_piece((row, 3), rook)
            self.set_piece((row, 0), None)
    
    def _undo_castling(self, move: Move):
        """Undo castling move."""
        piece = self.get_piece(move.to_pos)
        row = move.from_pos[0]
        
        # Move king back
        self.set_piece(move.from_pos, piece)
        self.set_piece(move.to_pos, None)
        
        # Move rook back
        if move.to_pos[1] == 6:  # Kingside
            rook = self.get_piece((row, 5))
            self.set_piece((row, 7), rook)
            self.set_piece((row, 5), None)
        else:  # Queenside (col == 2)
            rook = self.get_piece((row, 3))
            self.set_piece((row, 0), rook)
            self.set_piece((row, 3), None)
    
    def _execute_en_passant(self, move: Move):
        """Execute en passant capture."""
        piece = self.get_piece(move.from_pos)
        self.set_piece(move.to_pos, piece)
        self.set_piece(move.from_pos, None)
        
        # Remove captured pawn
        captured_row = move.from_pos[0]
        captured_col = move.to_pos[1]
        move.captured_piece = self.get_piece((captured_row, captured_col))
        self.set_piece((captured_row, captured_col), None)
    
    def _undo_en_passant(self, move: Move):
        """Undo en passant capture."""
        piece = self.get_piece(move.to_pos)
        
        # Move piece back
        self.set_piece(move.from_pos, piece)
        self.set_piece(move.to_pos, None)
        
        # Restore captured pawn
        captured_row = move.from_pos[0]
        captured_col = move.to_pos[1]
        self.set_piece((captured_row, captured_col), move.captured_piece)
    
    def _update_castling_rights(self, move: Move, piece: Piece):
        """Update castling rights based on move."""
        # King moves
        if piece.type == PieceType.KING:
            self.castling_rights[piece.color]['kingside'] = False
            self.castling_rights[piece.color]['queenside'] = False
        
        # Rook moves
        if piece.type == PieceType.ROOK:
            if move.from_pos[1] == 0:  # Queenside rook
                self.castling_rights[piece.color]['queenside'] = False
            elif move.from_pos[1] == 7:  # Kingside rook
                self.castling_rights[piece.color]['kingside'] = False
        
        # Rook captured
        if move.captured_piece and move.captured_piece.type == PieceType.ROOK:
            if move.to_pos == (0, 0):
                self.castling_rights[Color.BLACK]['queenside'] = False
            elif move.to_pos == (0, 7):
                self.castling_rights[Color.BLACK]['kingside'] = False
            elif move.to_pos == (7, 0):
                self.castling_rights[Color.WHITE]['queenside'] = False
            elif move.to_pos == (7, 7):
                self.castling_rights[Color.WHITE]['kingside'] = False
    
    def _update_en_passant_target(self, move: Move, piece: Piece):
        """Update en passant target square."""
        self.en_passant_target = None
        
        # Check for pawn double move
        if piece.type == PieceType.PAWN:
            row_diff = abs(move.to_pos[0] - move.from_pos[0])
            if row_diff == 2:
                # En passant target is the square the pawn passed over
                target_row = (move.from_pos[0] + move.to_pos[0]) // 2
                target_col = move.from_pos[1]
                self.en_passant_target = (target_row, target_col)
    
    def to_fen(self) -> str:
        """
        Convert board to FEN (Forsyth-Edwards Notation).
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
        
        # 3. Castling availability
        castling = ""
        if self.castling_rights[Color.WHITE]['kingside']:
            castling += "K"
        if self.castling_rights[Color.WHITE]['queenside']:
            castling += "Q"
        if self.castling_rights[Color.BLACK]['kingside']:
            castling += "k"
        if self.castling_rights[Color.BLACK]['queenside']:
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
        """
        Load board position from FEN notation.
        """
        parts = fen.split()
        if len(parts) != 6:
            raise ValueError("Invalid FEN string")
        
        # Clear board
        self.board = [[None for _ in range(8)] for _ in range(8)]
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
                    piece_type = PieceType(char.upper())
                    self.board[row_idx][col_idx] = Piece(piece_type, color)
                    # Cache king positions
                    if piece_type == PieceType.KING:
                        self.king_positions[color] = (row_idx, col_idx)
                    col_idx += 1
        
        # 2. Active color
        self.current_player = Color.WHITE if parts[1] == 'w' else Color.BLACK
        
        # 3. Castling rights
        castling = parts[2]
        self.castling_rights = {
            Color.WHITE: {'kingside': 'K' in castling, 'queenside': 'Q' in castling},
            Color.BLACK: {'kingside': 'k' in castling, 'queenside': 'q' in castling}
        }
        
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
        
        # Sync numpy arrays after FEN load
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



