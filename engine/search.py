"""
Search Module
Implements minimax with alpha-beta pruning and iterative deepening.
"""

import time
from typing import Optional, Tuple, List
from engine.board import Board, Move, Color
from engine.moves import MoveGenerator
from engine.evaluation import Evaluator


class SearchStats:
    """Tracks statistics during search."""
    
    def __init__(self):
        self.nodes_searched = 0
        self.positions_evaluated = 0
        self.alpha_beta_cutoffs = 0
        self.quiescence_nodes = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = 0
        self.depth_reached = 0
    
    def reset(self):
        """Reset all statistics."""
        self.__init__()
    
    def get_nodes_per_second(self) -> float:
        """Calculate nodes per second."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.nodes_searched / elapsed
        return 0
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            'nodes_searched': self.nodes_searched,
            'positions_evaluated': self.positions_evaluated,
            'alpha_beta_cutoffs': self.alpha_beta_cutoffs,
            'quiescence_nodes': self.quiescence_nodes,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'depth_reached': self.depth_reached,
            'nodes_per_second': self.get_nodes_per_second()
        }


class ChessEngine:
    """Main chess engine with search capabilities."""
    
    # Constants for evaluation
    CHECKMATE_SCORE = 100000
    STALEMATE_SCORE = 0
    
    def __init__(self, max_depth: int = 4, use_iterative_deepening: bool = True,
                 use_quiescence: bool = False, max_nodes: int = None):
        """
        Initialize the chess engine.
        
        Args:
            max_depth: Maximum search depth
            use_iterative_deepening: Whether to use iterative deepening
            use_quiescence: Whether to use quiescence search
            max_nodes: Maximum nodes to search (None = unlimited)
        """
        self.max_depth = max_depth
        self.use_iterative_deepening = use_iterative_deepening
        self.use_quiescence = use_quiescence
        self.max_nodes = max_nodes
        self.evaluator = Evaluator()
        self.stats = SearchStats()
        self.time_limit = None  # Time limit in seconds (None = no limit)
        self.should_stop = False
        
        # Transposition table (position hash -> (depth, score, best_move, node_type))
        self.transposition_table = {}
        
        # Killer moves (depth -> [move1, move2])
        self.killer_moves = {}
        
        # Evaluation cache (FEN -> score) - simple caching
        self.eval_cache = {}
    
    def find_best_move(self, board: Board, time_limit: Optional[float] = None) -> Tuple[Move, float]:
        """
        Find the best move for the current position.
        
        Returns:
            Tuple of (best_move, evaluation_score)
        """
        self.stats.reset()
        self.stats.start_time = time.time()
        self.time_limit = time_limit
        self.should_stop = False
        
        # Clear eval cache to prevent memory issues (keep transposition table)
        self.eval_cache.clear()
        
        move_gen = MoveGenerator(board)
        legal_moves = move_gen.generate_legal_moves()
        
        if not legal_moves:
            return None, 0
        
        if len(legal_moves) == 1:
            # Only one legal move, return it immediately
            return legal_moves[0], 0
        
        best_move = None
        best_score = float('-inf')
        
        if self.use_iterative_deepening:
            # Iterative deepening: search progressively deeper
            for depth in range(1, self.max_depth + 1):
                if self.should_stop:
                    break
                
                self.stats.depth_reached = depth
                move, score = self._search_depth(board, depth, legal_moves)
                
                if move is not None:
                    best_move = move
                    best_score = score
                
                # If we found a checkmate, no need to search deeper
                if abs(score) >= self.CHECKMATE_SCORE - 100:
                    break
        else:
            # Single depth search
            self.stats.depth_reached = self.max_depth
            best_move, best_score = self._search_depth(board, self.max_depth, legal_moves)
        
        return best_move, best_score
    
    def _search_depth(self, board: Board, depth: int, moves: List[Move]) -> Tuple[Move, float]:
        """Search at a specific depth."""
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        # Determine if we're maximizing (white) or minimizing (black)
        is_maximizing = (board.current_player == Color.WHITE)
        
        # Initialize best_score based on who's turn it is
        if is_maximizing:
            best_score = float('-inf')
        else:
            best_score = float('inf')
        
        # Order moves for better pruning
        moves = self._order_moves(board, moves, depth)
        
        for move in moves:
            if self.should_stop:
                break
            
            # Make move
            board_copy = board.copy()
            board_copy.make_move(move)
            
            # Search this move
            score = self._alpha_beta(board_copy, depth - 1, alpha, beta, not is_maximizing)
            
            # Update best move
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                # For black (minimizing), we want the LOWEST score
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)
        
        return best_move, best_score
    
    def _alpha_beta(self, board: Board, depth: int, alpha: float, beta: float, 
                   is_maximizing: bool) -> float:
        """
        Alpha-beta pruning search.
        
        Args:
            board: Current board state
            depth: Remaining search depth
            alpha: Best score for maximizing player
            beta: Best score for minimizing player
            is_maximizing: True if maximizing player's turn
        
        Returns:
            Evaluation score for the position
        """
        self.stats.nodes_searched += 1
        
        # Check node limit first (hard cap)
        if self.max_nodes and self.stats.nodes_searched >= self.max_nodes:
            self.should_stop = True
            return 0
        
        # Check time limit only every 1000 nodes for performance
        if self.time_limit and self.stats.nodes_searched % 1000 == 0:
            if (time.time() - self.stats.start_time) > self.time_limit:
                self.should_stop = True
                return 0
        
        # Terminal node or depth limit reached
        if depth == 0:
            if self.use_quiescence:
                return self._quiescence_search(board, alpha, beta, is_maximizing)
            else:
                self.stats.positions_evaluated += 1
                
                # Check evaluation cache
                fen = board.to_fen()
                if fen in self.eval_cache:
                    score = self.eval_cache[fen]
                else:
                    score = self.evaluator.evaluate(board)
                    self.eval_cache[fen] = score
                
                # Evaluator returns from Black's perspective (positive = good for Black)
                # When White is maximizing, we need to negate it
                return -score if is_maximizing else score
        
        move_gen = MoveGenerator(board)
        legal_moves = move_gen.generate_legal_moves()
        
        # Checkmate or stalemate
        if not legal_moves:
            if move_gen.is_in_check(board.current_player):
                # Checkmate - the current player is mated
                # Return a score from the searcher's perspective
                # If maximizing and Black is mated (good for White) → large positive
                # If minimizing and White is mated (good for Black) → large negative
                mate_score = self.CHECKMATE_SCORE - (self.max_depth - depth)
                if is_maximizing:
                    return mate_score if board.current_player == Color.BLACK else -mate_score
                else:
                    return -mate_score if board.current_player == Color.WHITE else mate_score
            else:
                # Stalemate
                return self.STALEMATE_SCORE
        
        # Order moves
        legal_moves = self._order_moves(board, legal_moves, depth)
        
        if is_maximizing:
            max_score = float('-inf')
            for move in legal_moves:
                board_copy = board.copy()
                board_copy.make_move(move)
                score = self._alpha_beta(board_copy, depth - 1, alpha, beta, False)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                
                if beta <= alpha:
                    self.stats.alpha_beta_cutoffs += 1
                    self._store_killer_move(move, depth)
                    break  # Beta cutoff
            
            return max_score
        else:
            min_score = float('inf')
            for move in legal_moves:
                board_copy = board.copy()
                board_copy.make_move(move)
                score = self._alpha_beta(board_copy, depth - 1, alpha, beta, True)
                min_score = min(min_score, score)
                beta = min(beta, score)
                
                if beta <= alpha:
                    self.stats.alpha_beta_cutoffs += 1
                    self._store_killer_move(move, depth)
                    break  # Alpha cutoff
            
            return min_score
    
    def _quiescence_search(self, board: Board, alpha: float, beta: float, 
                          is_maximizing: bool, max_depth: int = 5) -> float:
        """
        Quiescence search to avoid horizon effect.
        Only searches captures and checks to find quiet positions.
        """
        self.stats.quiescence_nodes += 1
        
        # Stand-pat score (current position evaluation) with caching
        fen = board.to_fen()
        if fen in self.eval_cache:
            stand_pat = self.eval_cache[fen]
        else:
            stand_pat = self.evaluator.evaluate(board)
            self.eval_cache[fen] = stand_pat
            
        if not is_maximizing:
            stand_pat = -stand_pat
        
        if max_depth == 0:
            self.stats.positions_evaluated += 1
            return stand_pat
        
        if is_maximizing:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)
        
        # Generate only tactical moves (captures)
        move_gen = MoveGenerator(board)
        all_moves = move_gen.generate_legal_moves()
        tactical_moves = [move for move in all_moves if self._is_tactical_move(board, move)]
        
        if not tactical_moves:
            self.stats.positions_evaluated += 1
            return stand_pat
        
        # Search tactical moves
        tactical_moves = self._order_captures(board, tactical_moves)
        
        if is_maximizing:
            max_score = stand_pat
            for move in tactical_moves:
                board_copy = board.copy()
                board_copy.make_move(move)
                score = self._quiescence_search(board_copy, alpha, beta, False, max_depth - 1)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                
                if beta <= alpha:
                    break
            
            return max_score
        else:
            min_score = stand_pat
            for move in tactical_moves:
                board_copy = board.copy()
                board_copy.make_move(move)
                score = self._quiescence_search(board_copy, alpha, beta, True, max_depth - 1)
                min_score = min(min_score, score)
                beta = min(beta, score)
                
                if beta <= alpha:
                    break
            
            return min_score
    
    def _is_tactical_move(self, board: Board, move: Move) -> bool:
        """Check if a move is tactical (capture, promotion, or check)."""
        # Check if it's a capture
        if move.captured_piece or move.is_en_passant:
            return True
        
        # Check if it's a promotion
        if move.promotion:
            return True
        
        # Could also check for checks, but that requires making the move
        # For now, just captures and promotions
        return False
    
    def _order_moves(self, board: Board, moves: List[Move], depth: int) -> List[Move]:
        """
        Order moves for better alpha-beta pruning.
        Move ordering heuristics:
        1. Captures (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
        2. Killer moves
        3. Other moves
        """
        def move_priority(move: Move) -> int:
            priority = 0
            
            # Captures (higher priority for capturing valuable pieces)
            if move.captured_piece:
                victim_value = self.evaluator.PIECE_VALUES.get(move.captured_piece.type, 0)
                attacker = board.get_piece(move.from_pos)
                attacker_value = self.evaluator.PIECE_VALUES.get(attacker.type, 0) if attacker else 0
                priority += 10000 + victim_value - attacker_value
            
            # Promotions
            if move.promotion:
                priority += 9000
            
            # Killer moves
            if depth in self.killer_moves:
                if move in self.killer_moves[depth]:
                    priority += 8000
            
            # Castling
            if move.is_castling:
                priority += 100
            
            return priority
        
        return sorted(moves, key=move_priority, reverse=True)
    
    def _order_captures(self, board: Board, moves: List[Move]) -> List[Move]:
        """Order capture moves by MVV-LVA."""
        def capture_priority(move: Move) -> int:
            if move.captured_piece:
                victim_value = self.evaluator.PIECE_VALUES.get(move.captured_piece.type, 0)
                attacker = board.get_piece(move.from_pos)
                attacker_value = self.evaluator.PIECE_VALUES.get(attacker.type, 0) if attacker else 0
                return victim_value - attacker_value
            return 0
        
        return sorted(moves, key=capture_priority, reverse=True)
    
    def _store_killer_move(self, move: Move, depth: int):
        """Store a killer move for a given depth."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        # Keep only the two most recent killer moves per depth
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()
    
    def get_principal_variation(self, board: Board, depth: int) -> List[Move]:
        """
        Get the principal variation (best line of play).
        """
        pv = []
        board_copy = board.copy()
        
        for _ in range(depth):
            move, _ = self.find_best_move(board_copy)
            if move is None:
                break
            pv.append(move)
            board_copy.make_move(move)
        
        return pv
