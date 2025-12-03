"""
Test unmake_move functionality
"""
import unittest
from engine.board import Board, PieceType, Color
from engine.moves import MoveGenerator


class TestUnmakeMove(unittest.TestCase):
    """Test cases for unmake_move functionality."""
    
    def test_unmake_regular_move(self):
        """Test undoing a regular move."""
        board = Board()
        gen = MoveGenerator(board)
        
        # Get initial FEN
        initial_fen = board.to_fen()
        
        # Make a move (e2-e4)
        moves = gen.generate_legal_moves()
        e2e4 = next(m for m in moves if m.from_pos == (6, 4) and m.to_pos == (4, 4))
        board.make_move(e2e4)
        
        # Undo the move
        board.unmake_move(e2e4)
        
        # Should be back to initial position
        self.assertEqual(board.to_fen(), initial_fen)
    
    def test_unmake_capture(self):
        """Test undoing a capture."""
        # Position with a capture available
        board = Board()
        board.from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
        gen = MoveGenerator(board)
        
        initial_fen = board.to_fen()
        
        # Make capture e4xd5
        moves = gen.generate_legal_moves()
        capture = next(m for m in moves if m.from_pos == (4, 4) and m.to_pos == (3, 3))
        self.assertIsNotNone(capture.captured_piece)
        
        board.make_move(capture)
        board.unmake_move(capture)
        
        self.assertEqual(board.to_fen(), initial_fen)
    
    def test_unmake_castling(self):
        """Test undoing castling."""
        # Position where white can castle kingside
        board = Board()
        board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        gen = MoveGenerator(board)
        
        initial_fen = board.to_fen()
        
        # Castle kingside
        moves = gen.generate_legal_moves()
        castle = next(m for m in moves if m.is_castling and m.to_pos == (7, 6))
        
        board.make_move(castle)
        board.unmake_move(castle)
        
        self.assertEqual(board.to_fen(), initial_fen)
    
    def test_unmake_en_passant(self):
        """Test undoing en passant."""
        # Position where en passant is available
        board = Board()
        board.from_fen("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3")
        gen = MoveGenerator(board)
        
        initial_fen = board.to_fen()
        
        # En passant capture
        moves = gen.generate_legal_moves()
        en_passant = next(m for m in moves if m.is_en_passant)
        
        board.make_move(en_passant)
        board.unmake_move(en_passant)
        
        self.assertEqual(board.to_fen(), initial_fen)
    
    def test_unmake_sequence(self):
        """Test undoing a sequence of moves."""
        board = Board()
        
        initial_fen = board.to_fen()
        moves_made = []
        
        # Make 5 moves
        for _ in range(5):
            gen = MoveGenerator(board)
            legal_moves = gen.generate_legal_moves()
            move = legal_moves[0]
            board.make_move(move)
            moves_made.append(move)
        
        # Undo all 5 moves
        for move in reversed(moves_made):
            board.unmake_move(move)
        
        # Should be back to initial position
        self.assertEqual(board.to_fen(), initial_fen)


if __name__ == '__main__':
    unittest.main()
