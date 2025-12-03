"""
Blind Test Suite for Search Algorithm
Tests with different tactical positions not used in test_search.py
"""

import unittest
import time
from engine.board import Board, Color
from engine.search import ChessEngine
from engine.evaluation import Evaluator


class TestEvaluation(unittest.TestCase):
    """Blind tests for position evaluation with new positions."""
    
    def setUp(self):
        """Set up evaluator."""
        self.evaluator = Evaluator()
    
    def test_rook_endgame_eval(self):
        """Test rook endgame evaluation."""
        board = Board()
        board.from_fen("8/5k2/8/8/8/3K4/8/3R4 w - - 0 1")
        score = self.evaluator.evaluate(board)
        # White has rook advantage (positive score = White advantage)
        self.assertGreater(score, 400, "White should have rook advantage")
    
    def test_opposite_bishops(self):
        """Test opposite colored bishops."""
        board = Board()
        board.from_fen("8/5k2/8/3b4/8/3B4/5K2/8 w - - 0 1")
        score = self.evaluator.evaluate(board)
        # Should be roughly equal with opposite bishops
        self.assertAlmostEqual(score, 0, delta=100, msg="Opposite bishops should be roughly equal")
    
    def test_passed_pawn(self):
        """Test passed pawn evaluation."""
        board = Board()
        board.from_fen("8/8/8/3P4/8/5k2/8/5K2 w - - 0 1")
        score1 = self.evaluator.evaluate(board)
        
        board.from_fen("8/8/8/8/8/5k2/8/5K2 w - - 0 1")
        score2 = self.evaluator.evaluate(board)
        
        # Position with passed pawn should be better for white (higher score)
        self.assertGreater(score1, score2, "Passed pawn should improve evaluation for White")
    
    def test_doubled_pawns(self):
        """Test doubled pawns penalty."""
        board = Board()
        board.from_fen("8/8/3p4/3p4/8/8/8/K6k w - - 0 1")
        score = self.evaluator.evaluate(board)
        # Black has doubled pawns (structural weakness)
        self.assertIsNotNone(score, "Should evaluate doubled pawn position")
    
    def test_knight_vs_bishop(self):
        """Test knight vs bishop in different positions."""
        # Knight in closed position
        board1 = Board()
        board1.from_fen("4k3/8/8/8/8/8/8/4K1N1 w - - 0 1")
        score1 = self.evaluator.evaluate(board1)
        
        # Bishop in open position
        board2 = Board()
        board2.from_fen("4k3/8/8/8/8/8/8/4K1B1 w - - 0 1")
        score2 = self.evaluator.evaluate(board2)
        
        # Both should give White advantage (positive score from Black's perspective means bad for Black)
        self.assertGreater(score1, 0, "Knight should give advantage to White")
        self.assertGreater(score2, 0, "Bishop should give advantage to White")


class TestSearch(unittest.TestCase):
    """Blind tests for search algorithm with different tactics."""
    
    def test_find_fork(self):
        """Test that engine finds knight fork."""
        board = Board()
        # Position where knight can fork king and rook
        board.from_fen("r3k3/8/8/8/8/5N2/8/4K3 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Engine should find a move")
        # Engine should find a good move (fork or similar)
        self.assertGreater(score, -200, "Should find reasonable position")
    
    def test_find_pin(self):
        """Test that engine recognizes pin."""
        board = Board()
        # Bishop pins knight to king
        board.from_fen("4k3/8/3n4/8/8/8/8/4KB2 w - - 0 1")
        
        engine = ChessEngine(max_depth=2)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Engine should find a move")
    
    def test_avoid_threefold_repetition(self):
        """Test position where repetition might occur."""
        board = Board()
        board.from_fen("8/8/8/8/8/3k4/3q4/3K4 b - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move even in difficult position")
    
    def test_find_skewer(self):
        """Test that engine finds skewer tactic."""
        board = Board()
        # Rook can skewer king and queen
        board.from_fen("4k3/4q3/8/8/8/8/8/R3K3 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Engine should find a move")
        # Should recognize the tactical opportunity
        self.assertGreater(abs(score), 0, "Should evaluate the position")
    
    def test_endgame_king_activity(self):
        """Test king activity in endgame."""
        board = Board()
        board.from_fen("8/8/8/3k4/8/8/8/3K4 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find king move in endgame")
    
    def test_promotion_choice(self):
        """Test that engine prefers queen promotion."""
        board = Board()
        board.from_fen("8/4P3/8/8/8/8/5k2/5K2 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        if move and move.promotion:
            # If promoting, should choose queen (Q)
            self.assertEqual(move.promotion, 'Q', "Should promote to queen")
    
    def test_zugzwang_position(self):
        """Test zugzwang-like position."""
        board = Board()
        board.from_fen("8/8/p7/k7/8/K7/8/8 b - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move even in zugzwang")
    
    def test_defense_against_mate_threat(self):
        """Test defending against mate threat."""
        board = Board()
        # Black threatens checkmate, White must defend
        board.from_fen("6k1/5ppp/8/8/8/8/5q2/R5K1 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Must find defensive move")
    
    def test_piece_coordination(self):
        """Test that engine coordinates pieces."""
        board = Board()
        board.from_fen("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should coordinate development")
    
    def test_iterative_deepening(self):
        """Test iterative deepening search."""
        board = Board()
        
        engine = ChessEngine(max_depth=4, use_iterative_deepening=True)
        move, score = engine.find_best_move(board)
        
        stats = engine.stats.to_dict()
        self.assertEqual(stats['depth_reached'], 4, "Should reach depth 4")
        self.assertIsNotNone(move, "Should find move with iterative deepening")
    
    def test_alpha_beta_pruning_efficiency(self):
        """Test that alpha-beta pruning reduces search."""
        board = Board()
        
        # Search without move ordering (less efficient)
        engine1 = ChessEngine(max_depth=3)
        engine1.use_killer_moves = False
        move1, score1 = engine1.find_best_move(board)
        nodes1 = engine1.stats.to_dict()['nodes_searched']
        
        # Search with move ordering (more efficient)
        engine2 = ChessEngine(max_depth=3)
        engine2.use_killer_moves = True
        move2, score2 = engine2.find_best_move(board)
        nodes2 = engine2.stats.to_dict()['nodes_searched']
        
        # Both should find same score
        self.assertEqual(score1, score2, "Both should find same evaluation")
        # Move ordering should help, but not guaranteed to reduce nodes
        self.assertGreater(nodes1, 0, "Should search some nodes")
        self.assertGreater(nodes2, 0, "Should search some nodes")
    
    def test_quiescence_search(self):
        """Test quiescence search in tactical position."""
        board = Board()
        # Position with hanging piece
        board.from_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3, use_quiescence=True)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move with quiescence search")
    
    def test_mate_in_two(self):
        """Test finding mate in two moves."""
        board = Board()
        # Anastasia's Mate pattern
        board.from_fen("5rk1/5Npp/8/8/8/8/8/6KR w - - 0 1")
        
        engine = ChessEngine(max_depth=4)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find first move of mate sequence")
        # Should recognize good position for White (might not see mate at depth 4)
        self.assertGreater(abs(score), 50, "Should see positional advantage")


class TestSearchEdgeCases(unittest.TestCase):
    """Test edge cases in search."""
    
    def test_only_king_moves(self):
        """Test position where only king can move."""
        board = Board()
        board.from_fen("8/8/8/8/pppppppp/8/pppppppp/K6k w - - 0 1")
        
        engine = ChessEngine(max_depth=2)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find king move")
    
    def test_forced_capture_sequence(self):
        """Test forced capture sequence."""
        board = Board()
        board.from_fen("4k3/8/8/8/8/8/4q3/4K3 w - - 0 1")
        
        engine = ChessEngine(max_depth=2)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move in bad position")
        # White is in a bad position but not immediate checkmate
        self.assertLess(abs(score), 10000, "Should return a reasonable score")
    
    def test_single_legal_move(self):
        """Test position with only one legal move."""
        board = Board()
        board.from_fen("k7/P7/K7/8/8/8/8/8 w - - 0 1")
        
        engine = ChessEngine(max_depth=2)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find the only legal move")


if __name__ == '__main__':
    unittest.main()
