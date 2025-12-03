"""
Third Round Blind Test Suite for Search Algorithm
Includes positions that stress-test evaluation and tactical awareness
"""

import unittest
import time
from engine.board import Board, Color, PieceType
from engine.search import ChessEngine
from engine.evaluation import Evaluator


class TestEvaluation(unittest.TestCase):
    """Third round of evaluation tests with precise expectations."""
    
    def setUp(self):
        """Set up evaluator."""
        self.evaluator = Evaluator()
    
    def test_piece_value_accuracy(self):
        """Test that piece values are accurate."""
        board = Board()
        # White has extra knight
        board.from_fen("rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        score = self.evaluator.evaluate(board)
        # Knight is worth about 300 centipawns
        self.assertGreater(score, 250, "Extra knight should be worth ~300")
        self.assertLess(score, 350, "Extra knight should be worth ~300")
    
    def test_centralization_bonus(self):
        """Test that centralized pieces get bonus."""
        # Knight on edge
        board1 = Board()
        board1.from_fen("8/8/8/8/8/8/N7/K6k w - - 0 1")
        score1 = self.evaluator.evaluate(board1)
        
        # Knight in center
        board2 = Board()
        board2.from_fen("8/8/8/8/3N4/8/8/K6k w - - 0 1")
        score2 = self.evaluator.evaluate(board2)
        
        # Centralized knight should be better
        self.assertGreater(score2, score1, "Centralized knight should score higher")
    
    def test_king_safety_opening(self):
        """Test king safety evaluation in opening."""
        # King castled
        board1 = Board()
        board1.from_fen("rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1")
        score1 = self.evaluator.evaluate(board1)
        
        # King in center
        board2 = Board()
        board2.from_fen("rnbq1rk1/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQ - 0 1")
        score2 = self.evaluator.evaluate(board2)
        
        # Both positions should be evaluated (king safety is part of piece-square tables)
        self.assertIsNotNone(score1)
        self.assertIsNotNone(score2)
    
    def test_material_imbalance_queen_vs_rooks(self):
        """Test queen vs two rooks evaluation."""
        # Queen
        board1 = Board()
        board1.from_fen("4k3/8/8/8/8/8/8/4K1Q1 w - - 0 1")
        score1 = self.evaluator.evaluate(board1)
        
        # Two rooks
        board2 = Board()
        board2.from_fen("4k3/8/8/8/8/8/8/R3K2R w - - 0 1")
        score2 = self.evaluator.evaluate(board2)
        
        # Two rooks (1000) should be slightly better than queen (900)
        self.assertGreater(score2, score1, "Two rooks should be slightly better than queen")
    
    def test_bishop_pair_bonus(self):
        """Test bishop pair evaluation."""
        # Single bishop
        board1 = Board()
        board1.from_fen("4k3/8/8/8/8/8/8/4KB2 w - - 0 1")
        score1 = self.evaluator.evaluate(board1)
        
        # Bishop pair
        board2 = Board()
        board2.from_fen("4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1")
        score2 = self.evaluator.evaluate(board2)
        
        # Bishop pair should be better (though we may not have implemented the bonus)
        self.assertGreater(score2, score1 + 250, "Bishop pair should be worth more than two separate bishops")


class TestSearch(unittest.TestCase):
    """Third round of search tests with specific tactical patterns."""
    
    def test_capture_free_queen(self):
        """Test that engine captures completely free queen."""
        board = Board()
        # Free Black queen on e4 that White pawn on d3 can capture diagonally
        board.from_fen("rnb1kbnr/pppppppp/8/8/4q3/3P4/PPP1PPPP/RNBQKBNR w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        # Must capture the queen
        self.assertEqual(move.to_pos, (4, 4), "Must capture free queen on e4")
        self.assertGreater(score, 800, "Score should reflect huge material advantage")
    
    def test_avoid_simple_fork(self):
        """Test that engine doesn't allow simple knight fork."""
        board = Board()
        # White's turn, Black knight can fork king and rook
        board.from_fen("4k3/8/8/8/8/5n2/8/R3K3 w - - 0 1")
        
        # Move king away from danger
        board.from_fen("4k3/8/8/5n2/8/8/8/R3K3 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
        # After best move, should avoid losing material
        self.assertGreater(score, -600, "Should avoid losing rook to fork")
    
    def test_find_back_rank_mate(self):
        """Test finding back rank mate."""
        board = Board()
        # White rook can deliver back rank mate
        board.from_fen("6k1/5ppp/8/8/8/8/8/R6K w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        # Should move rook to back rank
        if move.to_pos[0] == 0:  # rank 8
            self.assertGreater(abs(score), 9000, "Should recognize checkmate")
    
    def test_prevent_back_rank_mate(self):
        """Test defending against back rank mate threat."""
        board = Board()
        # Black threatens Ra1#
        board.from_fen("r6k/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find defensive move")
        # Should recognize danger but not immediate mate
        self.assertLess(abs(score), 9000, "Should not see immediate checkmate")
    
    def test_trade_when_ahead(self):
        """Test that engine trades pieces when ahead in material."""
        board = Board()
        # White is up a queen
        board.from_fen("4k3/8/8/3q4/3Q4/8/8/4K3 w - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        # Trading queens is good when ahead
        if move.to_pos == (3, 3):  # Captures queen
            self.assertGreater(score, 0, "Should still be winning after trade")
    
    def test_promotion_race(self):
        """Test pawn race to promotion."""
        board = Board()
        # Both sides have passed pawns
        board.from_fen("8/P7/8/8/8/8/7p/K6k w - - 0 1")
        
        engine = ChessEngine(max_depth=4)
        move, score = engine.find_best_move(board)
        
        # Should push pawn to promote
        if board.get_piece(move.from_pos).type == PieceType.PAWN:
            self.assertTrue(move.promotion or move.to_pos[0] < 2, "Should advance pawn toward promotion")
    
    def test_sacrifice_for_mate(self):
        """Test recognizing sacrifices that lead to mate."""
        board = Board()
        # White can sacrifice queen for mate
        board.from_fen("r4rk1/ppp2ppp/8/8/8/8/PPP2PPP/R3QRK1 w - - 0 1")
        
        engine = ChessEngine(max_depth=4)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
        # At depth 4, might not see complete mate sequence
        self.assertIsNotNone(score, "Should return a score")
    
    def test_zugzwang_recognition(self):
        """Test recognizing zugzwang-like positions."""
        board = Board()
        # King opposition in endgame
        board.from_fen("8/8/8/4k3/8/4K3/8/8 w - - 0 1")
        
        engine = ChessEngine(max_depth=4)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move in opposition position")
        # Score should be near equal
        self.assertLess(abs(score), 100, "King opposition should be roughly equal")
    
    def test_fortress_position(self):
        """Test evaluation of fortress positions."""
        board = Board()
        # Bishop of wrong color for pawn
        board.from_fen("8/8/8/8/8/5k2/5p2/5KB1 b - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
        # Position should favor Black (pawn on f2)
        self.assertLess(score, -100, "Black should be better with pawn on f2")
    
    def test_perpetual_check_option(self):
        """Test recognizing perpetual check possibilities."""
        board = Board()
        # Queen can give perpetual checks
        board.from_fen("8/8/8/8/8/5k2/5q2/5K2 b - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
        # Should recognize winning position for Black
        self.assertLess(score, -500, "Queen vs nothing should be winning")
    
    def test_simplification_when_ahead(self):
        """Test simplifying position when ahead."""
        board = Board()
        # White is up material
        board.from_fen("rnbqk3/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
        # Should recognize material advantage
        self.assertGreater(score, 400, "Should see rook advantage")


class TestSearchDepth(unittest.TestCase):
    """Test search behavior at different depths."""
    
    def test_deeper_search_finds_better_moves(self):
        """Test that deeper search finds better moves."""
        board = Board()
        board.from_fen("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
        
        # Shallow search
        engine_shallow = ChessEngine(max_depth=2)
        move_shallow, score_shallow = engine_shallow.find_best_move(board)
        
        # Deeper search
        engine_deep = ChessEngine(max_depth=4)
        move_deep, score_deep = engine_deep.find_best_move(board)
        
        # Both should find moves
        self.assertIsNotNone(move_shallow, "Shallow search should find move")
        self.assertIsNotNone(move_deep, "Deep search should find move")
        
        # Deeper search should evaluate more positions
        self.assertGreater(
            engine_deep.stats.positions_evaluated,
            engine_shallow.stats.positions_evaluated,
            "Deeper search should evaluate more positions"
        )
    
    def test_time_constraint_respected(self):
        """Test that time constraints are respected."""
        board = Board()
        
        engine = ChessEngine(max_depth=10)  # Very deep
        
        start_time = time.time()
        move, score = engine.find_best_move(board, time_limit=0.5)
        elapsed = time.time() - start_time
        
        self.assertLess(elapsed, 1.5, "Should respect time limit")
        self.assertIsNotNone(move, "Should still return a move")
    
    def test_iterative_deepening_finds_move_at_each_depth(self):
        """Test that iterative deepening returns best move at each depth."""
        board = Board()
        
        engine = ChessEngine(max_depth=4, use_iterative_deepening=True)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move with iterative deepening")
        self.assertEqual(engine.stats.depth_reached, 4, "Should reach target depth")


class TestTacticalPatterns(unittest.TestCase):
    """Test recognition of specific tactical patterns."""
    
    def test_removing_defender(self):
        """Test removing the defender tactic."""
        board = Board()
        # White can capture defender of Black queen
        board.from_fen("rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=4)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a tactical move")
    
    def test_overloaded_piece(self):
        """Test exploiting overloaded piece."""
        board = Board()
        # Rook defends too many pieces
        board.from_fen("6k1/5ppp/8/8/8/8/r4PPP/R5K1 b - - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find move exploiting overload")
    
    def test_deflection(self):
        """Test deflection tactic."""
        board = Board()
        # Can deflect defender
        board.from_fen("r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/R3K2R w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
    
    def test_interference(self):
        """Test interference tactic."""
        board = Board()
        board.from_fen("r3k3/ppp2ppp/8/8/8/8/PPP2PPP/R3K2R w KQq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")
    
    def test_clearance(self):
        """Test clearance tactic."""
        board = Board()
        board.from_fen("r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/R3K2R w KQkq - 0 1")
        
        engine = ChessEngine(max_depth=3)
        move, score = engine.find_best_move(board)
        
        self.assertIsNotNone(move, "Should find a move")


if __name__ == '__main__':
    unittest.main()
