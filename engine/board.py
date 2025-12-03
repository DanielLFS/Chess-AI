"""
Board Representation Module
Handles chess board state, piece positions, and game rules.
"""

from typing import List, Optional, Tuple, Dict
from enum import Enum
import copy


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


class Piece:
    """Represents a chess piece with type and color."""
    
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
    
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                 promotion: Optional[PieceType] = None, is_castling: bool = False,
                 is_en_passant: bool = False):
        self.from_pos = from_pos  # (row, col)
        self.to_pos = to_pos      # (row, col)
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece: Optional[Piece] = None
        
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
        
        # Pawns
        for col in range(8):
            self.board[1][col] = Piece(PieceType.PAWN, Color.BLACK)
            self.board[6][col] = Piece(PieceType.PAWN, Color.WHITE)
        
        # Empty squares
        for row in range(2, 6):
            for col in range(8):
                self.board[row][col] = None
    
    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """Get piece at given position."""
        row, col = pos
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def set_piece(self, pos: Tuple[int, int], piece: Optional[Piece]):
        """Set piece at given position."""
        row, col = pos
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
    
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
        
        # Store captured piece for undo
        move.captured_piece = self.get_piece(move.to_pos)
        
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
        
        # Record move
        self.move_history.append(move)
        self.position_history.append(self.to_fen())
        
        return True
    
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
    
    def copy(self) -> 'Board':
        """Create a deep copy of the board."""
        return copy.deepcopy(self)
    
    def find_king(self, color: Color) -> Optional[Tuple[int, int]]:
        """Find the position of the king for the given color."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.type == PieceType.KING and piece.color == color:
                    return (row, col)
        return None
