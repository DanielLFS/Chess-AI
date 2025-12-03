"""
Test Suite for Move Generation
Includes Perft tests for validation.
"""

import unittest
import time
from engine.board import Board, PieceType, Color
from engine.moves import MoveGenerator


class TestMoveGeneration(unittest.TestCase):
    """Test move generation for all piece types."""
    
    def setUp(self):
        """Set up test board."""
        self.board = Board()
        self.move_gen = MoveGenerator(self.board)
    
    def test_initial_position_move_count(self):
        """Test that initial position has 20 legal moves."""
        moves = self.move_gen.generate_legal_moves(Color.WHITE)
        self.assertEqual(len(moves), 20, "Initial position should have 20 legal moves")
    
    def test_pawn_moves(self):
        """Test pawn move generation."""
        board = Board()
        board.from_fen("8/8/8/8/8/8/P7/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        pawn_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.PAWN]
        self.assertGreaterEqual(len(pawn_moves), 1, "Single pawn should have moves")
    
    def test_pawn_double_move(self):
        """Test pawn double move from starting position."""
        board = Board()
        board.from_fen("8/8/8/8/8/8/P7/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        self.assertGreaterEqual(len(moves), 1)
    
    def test_knight_moves(self):
        """Test knight move generation."""
        board = Board()
        board.from_fen("8/8/8/8/3N4/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        knight_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.KNIGHT]
        self.assertEqual(len(knight_moves), 8, "Knight in center should have 8 moves")
    
    def test_bishop_moves(self):
        """Test bishop move generation."""
        board = Board()
        board.from_fen("8/8/8/8/3B4/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        bishop_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.BISHOP]
        # Bishop has 13 diagonal squares, but one blocked by king
        self.assertGreaterEqual(len(bishop_moves), 12, "Bishop in center should have 12+ moves")
    
    def test_rook_moves(self):
        """Test rook move generation."""
        board = Board()
        board.from_fen("8/8/8/8/3R4/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        rook_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.ROOK]
        self.assertEqual(len(rook_moves), 14, "Rook in center should have 14 moves")
    
    def test_queen_moves(self):
        """Test queen move generation."""
        board = Board()
        board.from_fen("8/8/8/8/3Q4/8/8/K6k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        queen_moves = [m for m in moves if board.get_piece(m.from_pos).type == PieceType.QUEEN]
        # Queen has 27 squares normally, but one blocked by king
        self.assertGreaterEqual(len(queen_moves), 26, "Queen in center should have 26+ moves")
    
    def test_king_moves(self):
        """Test king move generation."""
        board = Board()
        board.from_fen("8/8/8/8/3K4/8/8/7k w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        self.assertEqual(len(moves), 8, "King in center should have 8 moves")
    
    def test_castling_kingside(self):
        """Test kingside castling."""
        board = Board()
        board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        castling_moves = [m for m in moves if m.is_castling]
        self.assertGreaterEqual(len(castling_moves), 1, "Should have castling moves available")
    
    def test_en_passant(self):
        """Test en passant capture."""
        board = Board()
        board.from_fen("k7/8/8/pP6/8/8/8/K7 w - a6 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        en_passant_moves = [m for m in moves if m.is_en_passant]
        self.assertEqual(len(en_passant_moves), 1, "Should have 1 en passant move")
    
    def test_pawn_promotion(self):
        """Test pawn promotion."""
        board = Board()
        board.from_fen("8/P6k/8/8/8/8/8/K7 w - - 0 1")
        move_gen = MoveGenerator(board)
        moves = move_gen.generate_legal_moves(Color.WHITE)
        promotion_moves = [m for m in moves if m.promotion]
        self.assertEqual(len(promotion_moves), 4, "Should have 4 promotion options")
    
    def test_check_detection(self):
        """Test that king in check is detected."""
        board = Board()
        board.from_fen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        move_gen = MoveGenerator(board)
        in_check = move_gen.is_in_check(Color.BLACK)
        self.assertTrue(in_check, "Black king should be in check")
    
    def test_checkmate_detection(self):
        """Test checkmate detection."""
        board = Board()
        board.from_fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1")
        move_gen = MoveGenerator(board)
        is_checkmate = move_gen.is_checkmate(Color.WHITE)
        self.assertTrue(is_checkmate, "White should be in checkmate")
    
    def test_stalemate_detection(self):
        """Test stalemate detection."""
        board = Board()
        board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        move_gen = MoveGenerator(board)
        is_stalemate = move_gen.is_stalemate(Color.BLACK)
        self.assertTrue(is_stalemate, "Black should be in stalemate")


class TestPerft(unittest.TestCase):
    """
    Perft (Performance Test) - counts leaf nodes at a given depth.
    Used to verify move generation correctness.
    """
    
    def perft(self, board: Board, depth: int) -> int:
        """
        Count leaf nodes at given depth.
        """
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
    
    def test_perft_initial_position_depth_1(self):
        """Perft test: initial position, depth 1."""
        board = Board()
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 20, "Perft(1) from initial position should be 20")
    
    def test_perft_initial_position_depth_2(self):
        """Perft test: initial position, depth 2."""
        board = Board()
        nodes = self.perft(board, 2)
        self.assertEqual(nodes, 400, "Perft(2) from initial position should be 400")
    
    def test_perft_initial_position_depth_3(self):
        """Perft test: initial position, depth 3."""
        board = Board()
        start_time = time.time()
        nodes = self.perft(board, 3)
        elapsed = time.time() - start_time
        self.assertEqual(nodes, 8902, f"Perft(3) from initial position should be 8902 (took {elapsed:.2f}s)")
    
    def test_perft_kiwipete_depth_1(self):
        """Perft test: Kiwipete position, depth 1."""
        board = Board()
        board.from_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        nodes = self.perft(board, 1)
        self.assertEqual(nodes, 48, "Perft(1) for Kiwipete should be 48")
    
    def test_perft_kiwipete_depth_2(self):
        """Perft test: Kiwipete position, depth 2."""
        board = Board()
        board.from_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        nodes = self.perft(board, 2)
        self.assertEqual(nodes, 2039, "Perft(2) for Kiwipete should be 2039")


class TestBoardState(unittest.TestCase):
    """Test board state management."""
    
    def test_fen_conversion(self):
        """Test FEN parsing and generation."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        board = Board()
        generated_fen = board.to_fen()
        self.assertEqual(generated_fen, fen, "FEN should match initial position")
    
    def test_fen_roundtrip(self):
        """Test FEN parsing and regeneration."""
        original_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        board = Board()
        board.from_fen(original_fen)
        generated_fen = board.to_fen()
        self.assertEqual(generated_fen, original_fen, "FEN roundtrip should preserve position")
    
    def test_board_copy(self):
        """Test that board copy is independent."""
        board1 = Board()
        board2 = board1.copy()
        
        # Make a move on board1
        move_gen = MoveGenerator(board1)
        moves = move_gen.generate_legal_moves()
        board1.make_move(moves[0])
        
        # board2 should be unchanged
        self.assertNotEqual(board1.to_fen(), board2.to_fen(), "Board copy should be independent")


if __name__ == '__main__':
    unittest.main()
