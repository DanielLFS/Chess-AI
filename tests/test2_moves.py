"""
Blind Test Suite for Move Generation
Tests with different positions not used in test_moves.py
"""

import unittest
import time
from engine.board import Board, PieceType, Color
from engine.moves import MoveGenerator


class TestMoveGeneration(unittest.TestCase):
    """Blind tests for move generation with new positions."""
    
    def setUp(self):
        """Set up test board."""
        self.board = Board()
        self.move_gen = MoveGenerator(self.board)
    
    def test_mid_game_position_moves(self):
        """Test move generation in a mid-game position."""
        board = Board()
        # Sicilian Defense, Najdorf variation position
        board.from_fen("r1bqkb1r/1p2pppp/p1np1n2/8/3NP3/2N1B3/PPP2PPP/R2QKB1R w KQkq - 0 7")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        self.assertGreater(len(moves), 25, "Mid-game position should have many moves")
    
    def test_rook_endgame(self):
        """Test rook endgame position."""
        board = Board()
        board.from_fen("8/5k2/8/8/8/3K4/8/3R4 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        self.assertGreater(len(moves), 15, "Rook and king should have multiple moves")
    
    def test_blocked_pawns(self):
        """Test blocked pawn structure."""
        board = Board()
        board.from_fen("4k3/4p3/4P3/8/8/8/8/4K3 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        # King has moves, but pawn is blocked
        pawn_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.PAWN]
        self.assertEqual(len(pawn_moves), 0, "Blocked pawn should have no moves")
    
    def test_knight_corner(self):
        """Test knight in corner has fewer moves."""
        board = Board()
        board.from_fen("N6k/8/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        knight_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.KNIGHT]
        self.assertEqual(len(knight_moves), 2, "Knight in corner should have 2 moves")
    
    def test_bishop_trapped(self):
        """Test trapped bishop."""
        board = Board()
        board.from_fen("7k/ppp5/8/8/8/8/1B6/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        bishop_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.BISHOP]
        # Bishop should still have some moves along diagonal
        self.assertGreater(len(bishop_moves), 0, "Bishop should have at least one move")
    
    def test_queen_fork(self):
        """Test queen can attack multiple pieces."""
        board = Board()
        board.from_fen("r7/8/8/3Q4/8/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        queen_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.QUEEN]
        # Queen gives check, so only has a few legal moves (king in check means limited moves)
        self.assertGreater(len(queen_moves), 0, "Queen should have moves")
    
    def test_king_cannot_castle_through_check(self):
        """Test that king cannot castle through check."""
        board = Board()
        board.from_fen("r3k2r/8/8/8/8/5b2/8/R3K2R w KQkq - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        castling_moves = [m for m in moves if m.is_castling]
        # King cannot castle kingside (f1 is attacked by bishop)
        self.assertLess(len(castling_moves), 2, "Cannot castle through check")
    
    def test_queenside_castling(self):
        """Test queenside castling."""
        board = Board()
        board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.BLACK)
        castling_moves = [m for m in moves if m.is_castling]
        self.assertEqual(len(castling_moves), 2, "Should have both castling options")
    
    def test_en_passant_both_sides(self):
        """Test en passant available on both sides."""
        board = Board()
        board.from_fen("8/8/8/1pP5/8/8/8/k6K w - b6 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        en_passant_moves = [m for m in moves if m.is_en_passant]
        self.assertEqual(len(en_passant_moves), 1, "Should have en passant capture")
    
    def test_promotion_with_capture(self):
        """Test pawn promotion with capture."""
        board = Board()
        board.from_fen("1n5k/P7/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        promotion_moves = [m for m in moves if m.promotion]
        # 4 promotions forward + 4 promotions capturing
        self.assertEqual(len(promotion_moves), 8, "Should have 8 promotion options (4 forward + 4 capture)")
    
    def test_discovered_check(self):
        """Test position with discovered check possibility."""
        board = Board()
        board.from_fen("4k3/8/8/8/8/3N4/8/3RK3 w - - 0 1")
        move_gen = MoveGenerator(board)
        in_check = move_gen.is_in_check(Color.BLACK)
        self.assertFalse(in_check, "Black should not be in check initially")
        
        # After knight moves, rook gives check
        moves = move_gen.generate_legal_moves(Color.WHITE)
        self.assertGreater(len(moves), 0, "White should have moves")
    
    def test_back_rank_mate(self):
        """Test back rank checkmate pattern."""
        board = Board()
        board.from_fen("6k1/5ppp/8/8/8/8/8/R6K w - - 0 1")
        move_gen = MoveGenerator(board)
        # Move rook to back rank
        moves = [m for m in move_gen.generate_legal_moves(Color.WHITE) 
                if m.to_pos[0] == 0 and board.get_piece(m.from_pos).type == PieceType.ROOK]
        self.assertGreater(len(moves), 0, "Rook should be able to move to back rank")
    
    def test_smothered_mate_position(self):
        """Test smothered mate pattern."""
        board = Board()
        board.from_fen("6rk/6pp/8/8/8/8/8/5N1K w - - 0 1")
        move_gen = MoveGenerator(board)
        # Knight can potentially deliver checkmate
        knight_moves = [m for m in move_gen.generate_legal_moves(Color.WHITE)
                       if board.get_piece(m.from_pos).type == PieceType.KNIGHT]
        self.assertGreater(len(knight_moves), 0, "Knight should have moves")
    
    def test_king_in_center_danger(self):
        """Test king in center under attack."""
        board = Board()
        board.from_fen("r6r/8/8/8/3k4/8/8/4K3 w - - 0 1")
        move_gen = MoveGenerator(board)
        in_check = move_gen.is_in_check(Color.BLACK)
        self.assertFalse(in_check, "Black king should not be in check")


class TestPerft(unittest.TestCase):
    """Perft tests with different positions."""
    
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
    
    def test_perft_position_2_depth_1(self):
        """Perft test: Position 2, depth 1."""
        board = Board()
        board.from_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 48, "Perft(1) should be 48")
    
    def test_perft_position_3_depth_1(self):
        """Perft test: Position 3, depth 1."""
        board = Board()
        board.from_fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 14, "Perft(1) should be 14")
    
    def test_perft_position_3_depth_2(self):
        """Perft test: Position 3, depth 2."""
        board = Board()
        board.from_fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
        nodes = self.perft(board, 2)
        self.assertEqual(nodes, 191, "Perft(2) should be 191")
    
    def test_perft_position_4_depth_1(self):
        """Perft test: Position 4, depth 1."""
        board = Board()
        board.from_fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 6, "Perft(1) should be 6")


class TestComplexPositions(unittest.TestCase):
    """Test complex board states."""
    
    def test_complex_fen_parsing(self):
        """Test parsing of complex FEN position."""
        fen = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/4P3/2PP1N2/PP1NBPPP/R1BQ1RK1 w - - 0 10"
        board = Board()
        board.from_fen(fen)
        generated_fen = board.to_fen()
        self.assertEqual(generated_fen, fen, "Complex FEN should be preserved")
    
    def test_position_after_captures(self):
        """Test position state after multiple captures."""
        board = Board()
        board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        move_gen = MoveGenerator(board)
        
        # Make a few moves and captures
        moves = move_gen.generate_legal_moves()
        if moves:
            board_copy = board.copy()
            board_copy.make_move(moves[0])
            
            # Verify board is still valid
            self.assertIsNotNone(board_copy.to_fen(), "Board should be valid after move")
    
    def test_symmetric_position(self):
        """Test symmetric position evaluation."""
        board = Board()
        board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        move_gen = MoveGenerator(board)
        white_moves = move_gen.generate_legal_moves(Color.WHITE)
        
        # Symmetric position, so both sides should have same number of moves
        self.assertEqual(len(white_moves), 20, "Symmetric position should have 20 moves")


if __name__ == '__main__':
    unittest.main()
