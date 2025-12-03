"""
Third Round Blind Test Suite for Move Generation
Includes edge cases and positions that previously revealed test design issues
"""

import unittest
import time
from engine.board import Board, PieceType, Color
from engine.moves import MoveGenerator


class TestMoveGeneration(unittest.TestCase):
    """Third round of blind tests focusing on edge cases."""
    
    def setUp(self):
        """Set up test board."""
        self.board = Board()
        self.move_gen = MoveGenerator(self.board)
    
    def test_queen_on_open_board(self):
        """Test queen has maximum moves on truly open board."""
        board = Board()
        # Queen in center with no other pieces blocking
        board.from_fen("8/8/8/3Q4/8/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        queen_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.QUEEN]
        # Queen in center should have 27 moves (8 files + 8 ranks + 13 diagonals - 2 occupied)
        self.assertGreater(len(queen_moves), 25, "Queen on open board should have 25+ moves")
    
    def test_rook_on_edge(self):
        """Test rook on board edge."""
        board = Board()
        board.from_fen("R6k/8/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        rook_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.ROOK]
        # Rook on a8 has 13 moves (6 on rank to g8 + 7 on file, can capture king on h8)
        self.assertEqual(len(rook_moves), 13, "Rook on edge should have 13 moves")
    
    def test_bishop_on_corner(self):
        """Test bishop trapped in corner."""
        board = Board()
        board.from_fen("B6k/8/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        bishop_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.BISHOP]
        # Bishop on a8 has 7 diagonal moves
        self.assertEqual(len(bishop_moves), 7, "Bishop in corner should have 7 moves")
    
    def test_knight_on_edge(self):
        """Test knight on board edge."""
        board = Board()
        board.from_fen("8/8/8/N7/8/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        knight_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.KNIGHT]
        # Knight on a5 has 4 moves
        self.assertEqual(len(knight_moves), 4, "Knight on edge should have 4 moves")
    
    def test_pawn_chains(self):
        """Test interlocking pawn chains."""
        board = Board()
        board.from_fen("8/8/8/2ppp3/3PPP2/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        pawn_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.PAWN]
        # White pawns are blocked or can capture
        self.assertGreater(len(pawn_moves), 0, "Should have some pawn moves or captures")
    
    def test_multiple_checks_impossible(self):
        """Test that engine doesn't allow moves that leave king in check."""
        board = Board()
        # White king on e1, Black rooks on e8 and a1
        board.from_fen("4r3/8/8/8/8/8/8/r3K3 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        # King must escape, can't move to squares attacked by rooks
        self.assertGreater(len(moves), 0, "King should have escape moves")
        self.assertLess(len(moves), 8, "Not all king moves should be legal")
    
    def test_absolute_pin(self):
        """Test piece absolutely pinned to king."""
        board = Board()
        # White knight on e2 pinned by Black rook on e8
        board.from_fen("4r3/8/8/8/8/8/4N3/4K2k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        knight_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.KNIGHT]
        # Knight is pinned and cannot move
        self.assertEqual(len(knight_moves), 0, "Pinned knight should have no legal moves")
    
    def test_discovery_escape_check(self):
        """Test moving pinned piece when it gives discovered check."""
        board = Board()
        # White bishop on d3, Black king on h7, White rook on d1
        board.from_fen("7k/8/8/8/8/3B4/8/3R3K w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        bishop_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.BISHOP]
        # Bishop can move (not pinned), and may give discovered check
        self.assertGreater(len(bishop_moves), 0, "Bishop should be able to move")
    
    def test_en_passant_discovery(self):
        """Test en passant when it would expose king."""
        board = Board()
        # White king on e5, White pawn on d5, Black pawn just moved to c5
        board.from_fen("8/8/8/2pPK3/8/8/8/7k w - c6 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        en_passant_moves = [m for m in moves if m.is_en_passant]
        # En passant is legal here (no discovered check)
        self.assertGreater(len(en_passant_moves), 0, "En passant should be legal")
    
    def test_castling_while_rook_attacked(self):
        """Test castling when rook is attacked (should be legal)."""
        board = Board()
        # Rook on h1 attacked by Black rook on h8
        board.from_fen("7r/8/8/8/8/8/8/4K2R w K - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        castling_moves = [m for m in moves if m.is_castling]
        # Castling is legal even if rook is attacked
        self.assertEqual(len(castling_moves), 1, "Should be able to castle when rook is attacked")
    
    def test_castling_after_rook_moved(self):
        """Test no castling after rook has moved."""
        board = Board()
        # Position looks like castling is possible but rights say no
        board.from_fen("4k3/8/8/8/8/8/8/R3K2R w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        castling_moves = [m for m in moves if m.is_castling]
        # No castling rights
        self.assertEqual(len(castling_moves), 0, "Should not be able to castle without rights")
    
    def test_promotion_under_attack(self):
        """Test pawn promotion even when promotion square is attacked."""
        board = Board()
        # White pawn on g7 can promote to g8 (attacked by Black rook on h8) or capture h8
        board.from_fen("7r/6P1/8/8/8/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        promotion_moves = [m for m in moves if m.promotion]
        # Promotion is legal: 4 advancing to g8 + 4 capturing rook on h8 = 8 total
        self.assertEqual(len(promotion_moves), 8, "Should have 8 promotion options")
    
    def test_stalemate_with_many_pieces(self):
        """Test stalemate detection with multiple pieces on board."""
        board = Board()
        # Black king on a8, White queen on b6, White king on c6
        board.from_fen("k7/8/1QK5/8/8/8/8/8 b - - 0 1")
        move_gen = MoveGenerator(board)
        is_stalemate = move_gen.is_stalemate(Color.BLACK)
        self.assertTrue(is_stalemate, "Should detect stalemate")
    
    def test_checkmate_with_minor_pieces(self):
        """Test checkmate with two bishops."""
        board = Board()
        # Black king on a8, White bishops on b6 and c6, White king on c7
        board.from_fen("k7/2K5/1BB5/8/8/8/8/8 b - - 0 1")
        move_gen = MoveGenerator(board)
        is_checkmate = move_gen.is_checkmate(Color.BLACK)
        # This is actually checkmate
        self.assertTrue(is_checkmate, "Should detect checkmate")


class TestPerft(unittest.TestCase):
    """Additional Perft tests for validation."""
    
    def perft(self, board: Board, depth: int) -> int:
        """Count leaf nodes at given depth."""
        if depth == 0:
            return 1
        
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves()
        
        nodes = 0
        for move in moves:
            board_copy = board.copy()
            board_copy.make_move(move)
            nodes += self.perft(board_copy, depth - 1)
        
        return nodes
    
    def test_perft_position_5_depth_1(self):
        """Perft test: Position 5, depth 1."""
        board = Board()
        board.from_fen("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 44, "Perft(1) should be 44")
    
    def test_perft_position_6_depth_1(self):
        """Perft test: Position 6, depth 1."""
        board = Board()
        board.from_fen("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 46, "Perft(1) should be 46")


class TestSpecialMoveValidation(unittest.TestCase):
    """Test edge cases in special moves."""
    
    def test_en_passant_removes_correct_pawn(self):
        """Test that en passant removes the correct pawn."""
        board = Board()
        board.from_fen("8/8/8/3pP3/8/8/8/K6k w - d6 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        en_passant_move = [m for m in moves if m.is_en_passant][0]
        
        # Execute en passant
        board.make_move(en_passant_move)
        
        # Check that Black pawn on d5 is removed
        self.assertIsNone(board.get_piece((3, 3)), "Captured pawn should be removed")
        # Check that White pawn is on d6
        white_pawn = board.get_piece((2, 3))
        self.assertIsNotNone(white_pawn, "White pawn should be on d6")
        self.assertEqual(white_pawn.type, PieceType.PAWN, "Should be a pawn")
    
    def test_castling_moves_both_pieces(self):
        """Test that castling moves both king and rook."""
        board = Board()
        board.from_fen("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        kingside_castle = [m for m in moves if m.is_castling and m.to_pos == (7, 6)][0]
        
        # Execute castling
        board.make_move(kingside_castle)
        
        # Check king is on g1
        king = board.get_piece((7, 6))
        self.assertIsNotNone(king, "King should be on g1")
        self.assertEqual(king.type, PieceType.KING, "Should be a king")
        
        # Check rook is on f1
        rook = board.get_piece((7, 5))
        self.assertIsNotNone(rook, "Rook should be on f1")
        self.assertEqual(rook.type, PieceType.ROOK, "Should be a rook")
        
        # Check original positions are empty
        self.assertIsNone(board.get_piece((7, 4)), "e1 should be empty")
        self.assertIsNone(board.get_piece((7, 7)), "h1 should be empty")
    
    def test_promotion_changes_piece_type(self):
        """Test that promotion actually changes the piece type."""
        board = Board()
        board.from_fen("8/P6k/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        queen_promotion = [m for m in moves if m.promotion == PieceType.QUEEN][0]
        
        # Execute promotion
        board.make_move(queen_promotion)
        
        # Check that a8 now has a queen
        promoted_piece = board.get_piece((0, 0))
        self.assertIsNotNone(promoted_piece, "Should have piece on a8")
        self.assertEqual(promoted_piece.type, PieceType.QUEEN, "Should be a queen")
        self.assertEqual(promoted_piece.color, Color.WHITE, "Should be White's queen")
    
    def test_double_pawn_push_sets_en_passant(self):
        """Test that double pawn push correctly sets en passant square."""
        board = Board()
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        
        # Find e2-e4 move
        e2e4 = [m for m in moves if m.from_pos == (6, 4) and m.to_pos == (4, 4)][0]
        
        # Execute double pawn push
        board.make_move(e2e4)
        
        # Check en passant target square is set
        self.assertEqual(board.en_passant_target, (5, 4), "En passant square should be e3")
    
    def test_capture_clears_target_square(self):
        """Test that captures properly remove captured piece."""
        board = Board()
        board.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        
        # Black plays d5, White captures exd5
        board.from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        
        # Find exd5
        capture = [m for m in moves if m.from_pos == (4, 4) and m.to_pos == (3, 3)][0]
        
        # Execute capture
        board.make_move(capture)
        
        # Check that d5 has White pawn
        piece = board.get_piece((3, 3))
        self.assertIsNotNone(piece, "Should have piece on d5")
        self.assertEqual(piece.color, Color.WHITE, "Should be White's piece")
        self.assertEqual(piece.type, PieceType.PAWN, "Should be a pawn")


if __name__ == '__main__':
    unittest.main()
