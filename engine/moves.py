"""
Move Generation Module
Generates legal moves for all chess pieces including special moves.
"""

from typing import List, Tuple, Optional
from engine.board import Board, Move, Piece, PieceType, Color


class MoveGenerator:
    """Generates legal moves for chess pieces."""
    
    def __init__(self, board: Board):
        self.board = board
    
    def generate_legal_moves(self, color: Optional[Color] = None) -> List[Move]:
        """
        Generate all legal moves for the given color.
        If color is None, uses current player from board.
        """
        if color is None:
            color = self.board.current_player
        
        pseudo_legal_moves = self.generate_pseudo_legal_moves(color)
        legal_moves = []
        
        for move in pseudo_legal_moves:
            if self.is_legal_move(move):
                legal_moves.append(move)
        
        return legal_moves
    
    def generate_pseudo_legal_moves(self, color: Color) -> List[Move]:
        """
        Generate pseudo-legal moves (may leave king in check).
        """
        moves = []
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece((row, col))
                if piece and piece.color == color:
                    moves.extend(self.generate_piece_moves((row, col), piece))
        
        return moves
    
    def generate_piece_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate moves for a specific piece."""
        if piece.type == PieceType.PAWN:
            return self._generate_pawn_moves(pos, piece)
        elif piece.type == PieceType.KNIGHT:
            return self._generate_knight_moves(pos, piece)
        elif piece.type == PieceType.BISHOP:
            return self._generate_bishop_moves(pos, piece)
        elif piece.type == PieceType.ROOK:
            return self._generate_rook_moves(pos, piece)
        elif piece.type == PieceType.QUEEN:
            return self._generate_queen_moves(pos, piece)
        elif piece.type == PieceType.KING:
            return self._generate_king_moves(pos, piece)
        return []
    
    def _generate_pawn_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate pawn moves including en passant and promotion."""
        moves = []
        row, col = pos
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = 6 if piece.color == Color.WHITE else 1
        promotion_row = 0 if piece.color == Color.WHITE else 7
        
        # Forward move
        new_row = row + direction
        if 0 <= new_row < 8:
            if self.board.get_piece((new_row, col)) is None:
                # Check for promotion
                if new_row == promotion_row:
                    for promo_type in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                        moves.append(Move(pos, (new_row, col), promotion=promo_type))
                else:
                    moves.append(Move(pos, (new_row, col)))
                
                # Double move from starting position
                if row == start_row:
                    double_row = row + 2 * direction
                    if self.board.get_piece((double_row, col)) is None:
                        moves.append(Move(pos, (double_row, col)))
        
        # Captures (diagonal)
        for col_offset in [-1, 1]:
            new_col = col + col_offset
            new_row = row + direction
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = self.board.get_piece((new_row, new_col))
                
                # Regular capture
                if target and target.color != piece.color:
                    if new_row == promotion_row:
                        for promo_type in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                            moves.append(Move(pos, (new_row, new_col), promotion=promo_type))
                    else:
                        moves.append(Move(pos, (new_row, new_col)))
                
                # En passant
                if self.board.en_passant_target == (new_row, new_col):
                    moves.append(Move(pos, (new_row, new_col), is_en_passant=True))
        
        return moves
    
    def _generate_knight_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate knight moves (L-shaped)."""
        moves = []
        row, col = pos
        
        # All possible knight moves
        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for row_offset, col_offset in knight_offsets:
            new_row = row + row_offset
            new_col = col + col_offset
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = self.board.get_piece((new_row, new_col))
                if target is None or target.color != piece.color:
                    moves.append(Move(pos, (new_row, new_col)))
        
        return moves
    
    def _generate_sliding_moves(self, pos: Tuple[int, int], piece: Piece, 
                                 directions: List[Tuple[int, int]]) -> List[Move]:
        """Generate moves for sliding pieces (bishop, rook, queen)."""
        moves = []
        row, col = pos
        
        for row_dir, col_dir in directions:
            for distance in range(1, 8):
                new_row = row + row_dir * distance
                new_col = col + col_dir * distance
                
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                
                target = self.board.get_piece((new_row, new_col))
                
                if target is None:
                    moves.append(Move(pos, (new_row, new_col)))
                elif target.color != piece.color:
                    moves.append(Move(pos, (new_row, new_col)))
                    break
                else:
                    break
        
        return moves
    
    def _generate_bishop_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate bishop moves (diagonal)."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._generate_sliding_moves(pos, piece, directions)
    
    def _generate_rook_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate rook moves (horizontal and vertical)."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._generate_sliding_moves(pos, piece, directions)
    
    def _generate_queen_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate queen moves (combination of rook and bishop)."""
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        return self._generate_sliding_moves(pos, piece, directions)
    
    def _generate_king_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate king moves including castling."""
        moves = []
        row, col = pos
        
        # Regular king moves (one square in any direction)
        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for row_offset, col_offset in king_offsets:
            new_row = row + row_offset
            new_col = col + col_offset
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = self.board.get_piece((new_row, new_col))
                if target is None or target.color != piece.color:
                    moves.append(Move(pos, (new_row, new_col)))
        
        # Castling
        if not self.is_square_attacked(pos, piece.color):
            moves.extend(self._generate_castling_moves(pos, piece))
        
        return moves
    
    def _generate_castling_moves(self, pos: Tuple[int, int], piece: Piece) -> List[Move]:
        """Generate castling moves."""
        moves = []
        row, col = pos
        
        # Kingside castling
        if self.board.castling_rights[piece.color]['kingside']:
            if self._can_castle_kingside(row, col, piece.color):
                moves.append(Move(pos, (row, 6), is_castling=True))
        
        # Queenside castling
        if self.board.castling_rights[piece.color]['queenside']:
            if self._can_castle_queenside(row, col, piece.color):
                moves.append(Move(pos, (row, 2), is_castling=True))
        
        return moves
    
    def _can_castle_kingside(self, row: int, col: int, color: Color) -> bool:
        """Check if kingside castling is possible."""
        # Squares between king and rook must be empty
        if self.board.get_piece((row, 5)) is not None:
            return False
        if self.board.get_piece((row, 6)) is not None:
            return False
        
        # King cannot pass through or land on attacked square
        if self.is_square_attacked((row, 5), color):
            return False
        if self.is_square_attacked((row, 6), color):
            return False
        
        # Rook must be present
        rook = self.board.get_piece((row, 7))
        if not rook or rook.type != PieceType.ROOK or rook.color != color:
            return False
        
        return True
    
    def _can_castle_queenside(self, row: int, col: int, color: Color) -> bool:
        """Check if queenside castling is possible."""
        # Squares between king and rook must be empty
        if self.board.get_piece((row, 1)) is not None:
            return False
        if self.board.get_piece((row, 2)) is not None:
            return False
        if self.board.get_piece((row, 3)) is not None:
            return False
        
        # King cannot pass through or land on attacked square
        if self.is_square_attacked((row, 2), color):
            return False
        if self.is_square_attacked((row, 3), color):
            return False
        
        # Rook must be present
        rook = self.board.get_piece((row, 0))
        if not rook or rook.type != PieceType.ROOK or rook.color != color:
            return False
        
        return True
    
    def is_square_attacked(self, pos: Tuple[int, int], color: Color) -> bool:
        """
        Check if a square is attacked by the opponent.
        color: the color of the piece on this square (or would be)
        """
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        
        # Check all opponent pieces to see if they attack this square
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece((row, col))
                if piece and piece.color == opponent_color:
                    if self._can_piece_attack((row, col), piece, pos):
                        return True
        
        return False
    
    def _can_piece_attack(self, from_pos: Tuple[int, int], piece: Piece, 
                         target_pos: Tuple[int, int]) -> bool:
        """Check if a piece can attack a target square."""
        # For most pieces, check if target is in their pseudo-legal moves
        # (but without checking for check, to avoid recursion)
        
        if piece.type == PieceType.PAWN:
            return self._pawn_attacks(from_pos, piece, target_pos)
        elif piece.type == PieceType.KNIGHT:
            return self._knight_attacks(from_pos, target_pos)
        elif piece.type == PieceType.BISHOP:
            return self._bishop_attacks(from_pos, target_pos)
        elif piece.type == PieceType.ROOK:
            return self._rook_attacks(from_pos, target_pos)
        elif piece.type == PieceType.QUEEN:
            return self._queen_attacks(from_pos, target_pos)
        elif piece.type == PieceType.KING:
            return self._king_attacks(from_pos, target_pos)
        
        return False
    
    def _pawn_attacks(self, from_pos: Tuple[int, int], piece: Piece, 
                     target_pos: Tuple[int, int]) -> bool:
        """Check if pawn attacks target."""
        row, col = from_pos
        target_row, target_col = target_pos
        direction = -1 if piece.color == Color.WHITE else 1
        
        return (target_row == row + direction and 
                abs(target_col - col) == 1)
    
    def _knight_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        """Check if knight attacks target."""
        row_diff = abs(from_pos[0] - target_pos[0])
        col_diff = abs(from_pos[1] - target_pos[1])
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
    
    def _sliding_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int],
                        directions: List[Tuple[int, int]]) -> bool:
        """Check if sliding piece attacks target."""
        row, col = from_pos
        target_row, target_col = target_pos
        
        for row_dir, col_dir in directions:
            for distance in range(1, 8):
                new_row = row + row_dir * distance
                new_col = col + col_dir * distance
                
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                
                if (new_row, new_col) == target_pos:
                    return True
                
                if self.board.get_piece((new_row, new_col)) is not None:
                    break
        
        return False
    
    def _bishop_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        """Check if bishop attacks target."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._sliding_attacks(from_pos, target_pos, directions)
    
    def _rook_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        """Check if rook attacks target."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._sliding_attacks(from_pos, target_pos, directions)
    
    def _queen_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        """Check if queen attacks target."""
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        return self._sliding_attacks(from_pos, target_pos, directions)
    
    def _king_attacks(self, from_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        """Check if king attacks target."""
        row_diff = abs(from_pos[0] - target_pos[0])
        col_diff = abs(from_pos[1] - target_pos[1])
        return row_diff <= 1 and col_diff <= 1 and (row_diff + col_diff) > 0
    
    def is_legal_move(self, move: Move) -> bool:
        """
        Check if a move is legal (doesn't leave king in check).
        """
        # Make the move on a copy
        test_board = self.board.copy()
        test_board.make_move(move)
        
        # Find the king of the player who just moved
        moving_color = self.board.current_player
        king_pos = test_board.find_king(moving_color)
        
        if king_pos is None:
            return False
        
        # Check if king is in check after the move
        test_generator = MoveGenerator(test_board)
        return not test_generator.is_square_attacked(king_pos, moving_color)
    
    def is_in_check(self, color: Color) -> bool:
        """Check if the given color's king is in check."""
        king_pos = self.board.find_king(color)
        if king_pos is None:
            return False
        return self.is_square_attacked(king_pos, color)
    
    def is_checkmate(self, color: Color) -> bool:
        """Check if the given color is in checkmate."""
        if not self.is_in_check(color):
            return False
        return len(self.generate_legal_moves(color)) == 0
    
    def is_stalemate(self, color: Color) -> bool:
        """Check if the given color is in stalemate."""
        if self.is_in_check(color):
            return False
        return len(self.generate_legal_moves(color)) == 0
