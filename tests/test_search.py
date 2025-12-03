"""
Test Suite for Search Algorithm
"""

import unittest
from engine.board import Board, Color
from engine.search import ChessEngine
from engine.evaluation import Evaluator


class TestEvaluation(unittest.TestCase):
    """Test position evaluation."""
    
    def setUp(self):
        """Set up evaluator."""
        self.evaluator = Evaluator()
    
    def test_initial_position_eval(self):
        """Test that initial position is roughly equal."""
        board = Board()
        score = self.evaluator.evaluate(board)
        self.assertAlmostEqual(score, 0, delta=50, msg="Initial position should be roughly equal")
    
    def test_material_advantage(self):
        """Test that material advantage is detected."""
        board = Board()
        board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1")  # White missing rook
        score = self.evaluator.evaluate(board)
        self.assertLess(score, -400, "White should be down material")
    
    def test_queen_vs_pawns(self):
        """Test queen vs pawns evaluation."""
        board = Board()
        board.from_fen("4k3/8/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")  # White has 8 pawns
        score1 = self.evaluator.evaluate(board)
        
        board.from_fen("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")  # White has queen
        score2 = self.evaluator.evaluate(board)
        
        self.assertGreater(score2, score1, "Queen should be worth more than 8 pawns")


class TestSearch(unittest.TestCase):
    """Test search algorithm."""
    
    def test_find_checkmate_in_one(self):
        """Test that engine finds checkmate in one move."""
        board = Board()
        board.from_fen("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=2)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Engine should find a move")
        # Check if it's checkmate (move to f7 which is row 1, col 5)
        self.assertEqual(move.to_pos, (1, 5), "Engine should play Qxf7# or Bxf7# checkmate")
    
    def test_avoid_hanging_piece(self):
        """Test that engine doesn't hang pieces."""
        board = Board()
        # Position where white can capture a free queen at e3
        board.from_fen("rnb1kbnr/pppppppp/8/8/8/4q3/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        # Engine should see a huge material advantage
        # Score should be very positive (at least +8 pawns = 800 centipawns)
        self.assertGreater(score, 700, "Engine should recognize large material advantage")
    
    def test_search_statistics(self):
        """Test that search statistics are tracked."""
        board = Board()
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        stats = engine.stats.to_dict()
        self.assertGreater(stats['nodes_searched'], 0, "Should have searched nodes")
        self.assertGreater(stats['positions_evaluated'], 0, "Should have evaluated positions")
    
    def test_time_limit(self):
        """Test that search respects time limit."""
        import time
        board = Board()
        engine = ChessEngine(max_depth=10)  # Very deep
        
        start = time.time()
        move, score = engine.find_best_move(board, time_limit=0.5)  # 500ms limit
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 1.0, "Search should respect time limit")
        self.assertIsNotNone(move, "Should still return a move")


if __name__ == '__main__':
    unittest.main()
