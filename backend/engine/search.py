"""
Search Engine - Bitboard Implementation
Alpha-beta pruning with transposition table, iterative deepening, and move ordering.
"""

import time
import numpy as np
from typing import Optional, Tuple
from engine.board import (
    Board, Color, HASH, META,
    decode_move, unpack_side,
    WP, WN, WB, WR, WQ, WK,
    BP, BN, BB, BR, BQ, BK,
)
from engine.moves import Moves
from engine.transposition import TranspositionTable, EXACT, LOWER_BOUND, UPPER_BOUND
from engine.evaluation import evaluate


class SearchStats:
    """Statistics tracking for search."""
    
    def __init__(self):
        self.nodes = 0
        self.qnodes = 0
        self.tt_hits = 0
        self.tt_misses = 0
        self.cutoffs = 0
        self.null_cutoffs = 0
        self.lmr_reductions = 0
        self.lmr_researches = 0
        self.check_extensions = 0
        self.aspiration_fails = 0
        self.aspiration_researches = 0
        self.history_hits = 0
        self.futility_prunes = 0
        self.rfp_prunes = 0
        self.start_time = 0.0
        self.depth_reached = 0
    
    def reset(self):
        self.__init__()
    
    @property
    def nps(self) -> float:
        elapsed = time.time() - self.start_time
        return (self.nodes + self.qnodes) / elapsed if elapsed > 0 else 0
    
    def __str__(self) -> str:
        return (f"Nodes: {self.nodes:,} | QNodes: {self.qnodes:,} | Depth: {self.depth_reached} | "
                f"NPS: {self.nps:,.0f} | TT: {self.tt_hits:,} | Cutoffs: {self.cutoffs:,} | "
                f"Null: {self.null_cutoffs:,} | LMR: {self.lmr_reductions:,}/{self.lmr_researches:,} | "
                f"Ext: {self.check_extensions:,} | Asp: {self.aspiration_fails:,} | Fut: {self.futility_prunes:,} | RFP: {self.rfp_prunes:,}")


class Search:
    """
    Chess search engine with alpha-beta pruning.
    
    Features:
    - Iterative deepening
    - Transposition table
    - Move ordering (TT move, captures, killers)
    - Alpha-beta pruning
    """
    
    MATE_SCORE = 30000  # Fits in int16, leaves room for mate distance
    DRAW_SCORE = 0
    
    # Piece values for MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    PIECE_VALUES = np.array([100, 320, 330, 500, 900, 20000], dtype=np.int32)  # P,N,B,R,Q,K
    
    # Search parameters
    NULL_MOVE_REDUCTION = 2  # R=2 is standard
    NULL_MOVE_MIN_DEPTH = 3  # Don't try null move at shallow depths
    
    # Late Move Reduction (LMR) parameters
    LMR_MIN_DEPTH = 3  # Minimum depth to apply LMR
    LMR_FULL_DEPTH_MOVES = 4  # Search first N moves at full depth
    LMR_REDUCTION = 1  # Reduce depth by this amount for late moves
    
    # Aspiration window parameters
    ASPIRATION_WINDOW = 50  # Initial window size (in centipawns)
    ASPIRATION_MIN_DEPTH = 3  # Minimum depth to use aspiration windows
    
    # Futility pruning parameters (margins at frontier nodes)
    FUTILITY_MARGIN = {
        1: 200,  # At depth 1, skip if position + 200cp < alpha
        2: 400,  # At depth 2, skip if position + 400cp < alpha
    }
    
    # Reverse Futility Pruning (Static Null Move) parameters
    REVERSE_FUTILITY_MARGIN = {
        1: 200,  # At depth 1, prune if eval - 200cp >= beta
        2: 300,  # At depth 2, prune if eval - 300cp >= beta
        3: 500,  # At depth 3, prune if eval - 500cp >= beta
    }
    
    def __init__(self, tt_size_mb: int = 64, max_depth: int = 64, use_null_move: bool = True, use_lmr: bool = True, use_aspiration: bool = True, use_futility: bool = True, use_rfp: bool = True):
        """
        Initialize search engine.
        
        Args:
            tt_size_mb: Transposition table size in megabytes
            max_depth: Maximum search depth
            use_null_move: Enable null move pruning
            use_lmr: Enable late move reductions
        """
        self.tt = TranspositionTable(size_mb=tt_size_mb)
        self.max_depth = max_depth
        self.stats = SearchStats()
        self.killer_moves = {}  # depth -> [move1, move2]
        self.history_table = np.zeros((2, 64, 64), dtype=np.int32)  # [color][from][to]
        self.stop_search = False
        self.time_limit = None
        self.use_null_move = use_null_move
        self.use_lmr = use_lmr
        self.use_aspiration = use_aspiration
        self.use_futility = use_futility
        self.use_rfp = use_rfp
        self.null_move_active = False  # Track if we're in null move search
    
    def search(self, board: Board, depth: int = 5, time_limit: float = None) -> Tuple[Optional[np.uint16], int]:
        """
        Find best move using iterative deepening.
        
        Args:
            board: Current position
            depth: Maximum depth to search
            time_limit: Time limit in seconds (None = no limit)
        
        Returns:
            (best_move, score) or (None, 0) if no moves
        """
        self.stats.reset()
        self.stats.start_time = time.time()
        self.stop_search = False
        self.time_limit = time_limit
        self.tt.new_search()
        
        moves_gen = Moves(board)
        legal_moves = moves_gen.generate()
        
        if len(legal_moves) == 0:
            return None, 0
        
        if len(legal_moves) == 1:
            return legal_moves[0], 0
        
        best_move = legal_moves[0]
        best_score = -self.MATE_SCORE
        
        # Iterative deepening with aspiration windows
        for current_depth in range(1, min(depth, self.max_depth) + 1):
            if self.stop_search:
                break
            
            self.stats.depth_reached = current_depth
            
            # Use aspiration windows for deeper searches
            if self.use_aspiration and current_depth >= self.ASPIRATION_MIN_DEPTH and abs(best_score) < self.MATE_SCORE - 100:
                alpha = best_score - self.ASPIRATION_WINDOW
                beta = best_score + self.ASPIRATION_WINDOW
                
                move, score = self._search_root_aspiration(board, current_depth, legal_moves, alpha, beta)
                
                # Re-search with wider window if we failed high/low
                if score <= alpha:  # Fail low
                    self.stats.aspiration_fails += 1
                    self.stats.aspiration_researches += 1
                    move, score = self._search_root(board, current_depth, legal_moves)
                elif score >= beta:  # Fail high
                    self.stats.aspiration_fails += 1
                    self.stats.aspiration_researches += 1
                    move, score = self._search_root(board, current_depth, legal_moves)
            else:
                # Full window search for shallow depths or after mate score
                move, score = self._search_root(board, current_depth, legal_moves)
            
            if move is not None:
                best_move = move
                best_score = score
                
                # Extract and display PV
                pv = self.get_pv(board, max_depth=10)
                pv_str = self.format_pv(pv, board)
                elapsed = time.time() - self.stats.start_time
                print(f"info depth {current_depth} score cp {score} time {int(elapsed * 1000)} nodes {self.stats.nodes} pv {pv_str}")
            
            # Stop if we found mate
            if abs(score) >= self.MATE_SCORE - 100:
                break
            
            # Check time
            if self.time_limit and (time.time() - self.stats.start_time) >= self.time_limit:
                break
        
        return best_move, best_score
    
    def _search_root(self, board: Board, depth: int, moves: np.ndarray) -> Tuple[Optional[np.uint16], int]:
        """Search root position with all legal moves."""
        alpha = -self.MATE_SCORE
        beta = self.MATE_SCORE
        best_move = None
        best_score = -self.MATE_SCORE
        
        # Try TT move first
        tt_entry = self.tt.probe(np.uint64(board.state[HASH]), depth, alpha, beta)
        tt_move = tt_entry[1] if tt_entry else None
        
        # Order moves
        ordered_moves = self._order_moves(board, moves, depth, tt_move)
        
        for move in ordered_moves:
            undo = board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.unmake_move(move, undo)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
        
        # Store in TT
        if best_move is not None:
            self.tt.store(np.uint64(board.state[HASH]), best_score, best_move, depth, EXACT)
        
        return best_move, best_score
    
    def _search_root_aspiration(self, board: Board, depth: int, moves: np.ndarray, alpha: int, beta: int) -> Tuple[Optional[np.uint16], int]:
        """Search root position with aspiration window (alpha-beta bounds)."""
        best_move = None
        best_score = -self.MATE_SCORE
        
        # Try TT move first
        tt_entry = self.tt.probe(np.uint64(board.state[HASH]), depth, alpha, beta)
        tt_move = tt_entry[1] if tt_entry else None
        
        # Order moves
        ordered_moves = self._order_moves(board, moves, depth, tt_move)
        
        for move in ordered_moves:
            undo = board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.unmake_move(move, undo)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            if score >= beta:
                # Fail high - score is too good
                return best_move, best_score
            
            alpha = max(alpha, score)
        
        # Store in TT (only if we didn't fail high/low)
        if best_move is not None and best_score > alpha:
            self.tt.store(np.uint64(board.state[HASH]), best_score, best_move, depth, EXACT)
        
        return best_move, best_score
    
    def _negamax(self, board: Board, depth: int, alpha: int, beta: int) -> int:
        """
        Negamax search with alpha-beta pruning.
        
        Returns score from current side's perspective.
        """
        self.stats.nodes += 1
        
        # Check time limit
        if self.time_limit and self.stats.nodes % 1000 == 0:
            if (time.time() - self.stats.start_time) >= self.time_limit:
                self.stop_search = True
                return 0
        
        # Probe transposition table
        zobrist = np.uint64(board.state[HASH])
        tt_entry = self.tt.probe(zobrist, depth, alpha, beta)
        
        if tt_entry and tt_entry[0] is not None:
            self.stats.tt_hits += 1
            return tt_entry[0]
        else:
            self.stats.tt_misses += 1
        
        # Terminal depth - enter quiescence search
        if depth <= 0:
            return self._quiescence(board, alpha, beta)
        
        # Generate moves
        moves_gen = Moves(board)
        legal_moves = moves_gen.generate()
        in_check = moves_gen.is_check()
        
        # Checkmate or stalemate
        if len(legal_moves) == 0:
            if in_check:
                return -self.MATE_SCORE + (self.max_depth - depth)  # Mate in N plies
            else:
                return self.DRAW_SCORE  # Stalemate
        
        # Reverse Futility Pruning (Static Null Move)
        # If position is so good that even with a margin, eval >= beta, prune
        if (self.use_rfp and
            depth in self.REVERSE_FUTILITY_MARGIN and
            not in_check and
            abs(beta) < self.MATE_SCORE - 100):
            
            static_eval = self._evaluate(board)
            if static_eval - self.REVERSE_FUTILITY_MARGIN[depth] >= beta:
                self.stats.rfp_prunes += 1
                return static_eval
        
        # Null move pruning (only if not in check and not already in null move)
        if (self.use_null_move and 
            not self.null_move_active and 
            not in_check and 
            depth >= self.NULL_MOVE_MIN_DEPTH and
            beta < self.MATE_SCORE - 100):  # Don't null move when looking for mate
            
            # Make null move (skip turn)
            self.null_move_active = True
            undo = board.make_null_move()
            
            # Search with reduced depth
            score = -self._negamax(board, depth - 1 - self.NULL_MOVE_REDUCTION, -beta, -beta + 1)
            
            # Unmake null move
            board.unmake_null_move(undo)
            self.null_move_active = False
            
            # If null move fails high, we can prune (opponent can do better than our best)
            if score >= beta:
                self.stats.null_cutoffs += 1
                return beta
        
        # Order moves
        tt_move = tt_entry[1] if tt_entry else None
        ordered_moves = self._order_moves(board, legal_moves, depth, tt_move)
        
        best_score = -self.MATE_SCORE
        best_move = None
        moves_searched = 0
        
        # Futility pruning - evaluate position for frontier nodes
        futility_base = None
        if (self.use_futility and 
            depth in self.FUTILITY_MARGIN and 
            not in_check and 
            abs(alpha) < self.MATE_SCORE - 100):
            futility_base = self._evaluate(board)
        
        for move in ordered_moves:
            # Check if this move is a capture (before making the move)
            is_capture = self._is_capture(move, board)
            
            # Futility pruning: skip quiet moves at frontier nodes that can't improve alpha
            if (futility_base is not None and 
                not is_capture and 
                moves_searched > 0 and  # Don't prune the first move
                futility_base + self.FUTILITY_MARGIN[depth] <= alpha):
                self.stats.futility_prunes += 1
                continue
            
            undo = board.make_move(move)
            
            # Check if we're in check after the move (opponent in check)
            moves_gen_new = Moves(board)
            gives_check = moves_gen_new.is_check()
            
            # Determine new depth (with extensions/reductions)
            new_depth = depth - 1
            
            # Check extension - search deeper when giving check
            if gives_check:
                new_depth += 1
                self.stats.check_extensions += 1
            
            # Late Move Reduction (LMR)
            # Reduce depth for moves searched late in the list (likely bad)
            do_full_search = True
            if (self.use_lmr and 
                moves_searched >= self.LMR_FULL_DEPTH_MOVES and
                depth >= self.LMR_MIN_DEPTH and
                not in_check and  # Don't reduce when in check
                not gives_check and  # Don't reduce checks
                not is_capture):  # Don't reduce captures
                
                # Search with reduced depth
                self.stats.lmr_reductions += 1
                score = -self._negamax(board, new_depth - self.LMR_REDUCTION, -alpha - 1, -alpha)
                
                # If reduced search fails high, do full search
                if score > alpha:
                    self.stats.lmr_researches += 1
                    score = -self._negamax(board, new_depth, -beta, -alpha)
                    do_full_search = False
                else:
                    do_full_search = False
            
            # Normal full-depth search
            if do_full_search:
                score = -self._negamax(board, new_depth, -beta, -alpha)
            
            board.unmake_move(move, undo)
            moves_searched += 1
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            
            # Beta cutoff
            if alpha >= beta:
                self.stats.cutoffs += 1
                
                # Update history heuristic for quiet moves (not captures)
                if not is_capture:
                    side = unpack_side(board.state[META])
                    from_sq = move & 0x3F
                    to_sq = (move >> 6) & 0x3F
                    # Bonus = depth^2 (deeper searches get higher priority)
                    self.history_table[side, from_sq, to_sq] += depth * depth
                    self._store_killer(move, depth)
                
                break
        
        # Store in transposition table
        if best_move is not None:
            bound = EXACT if alpha < beta else LOWER_BOUND
            self.tt.store(zobrist, best_score, best_move, depth, bound)
        
        return best_score
    
    def _evaluate(self, board: Board) -> int:
        """
        Evaluate position using piece-square tables.
        Returns score from current side's perspective.
        """
        return evaluate(board.state)
    
    def _quiescence(self, board: Board, alpha: int, beta: int) -> int:
        """
        Quiescence search - search only captures to avoid horizon effect.
        This prevents the engine from missing tactical shots.
        """
        self.stats.qnodes += 1
        
        # Check time limit periodically
        if self.time_limit and self.stats.qnodes % 1000 == 0:
            if (time.time() - self.stats.start_time) >= self.time_limit:
                self.stop_search = True
                return 0
        
        # Stand pat score (what if we don't capture anything?)
        stand_pat = self._evaluate(board)
        
        # Beta cutoff - position is already too good
        if stand_pat >= beta:
            return beta
        
        # Update alpha
        if stand_pat > alpha:
            alpha = stand_pat
        
        # Delta pruning - if we're too far behind, skip captures that can't help
        # Even capturing a queen (900) won't save us
        BIG_DELTA = 900
        if stand_pat < alpha - BIG_DELTA:
            return alpha
        
        # Generate and search only captures
        moves_gen = Moves(board)
        captures = self._get_captures(board, moves_gen.generate())
        
        if len(captures) == 0:
            return stand_pat
        
        # Order captures by MVV-LVA
        captures = self._order_captures(board, captures)
        
        for move in captures:
            undo = board.make_move(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.unmake_move(move, undo)
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        
        return alpha
    
    def _get_captures(self, board: Board, moves: np.ndarray) -> np.ndarray:
        """Filter only capture moves."""
        if len(moves) == 0:
            return moves
        
        side = unpack_side(board.state[META])
        opponent_start = BP if side == 0 else WP
        
        captures = []
        for move in moves:
            to_sq = (move >> 6) & 0x3F
            
            # Check if destination is occupied by opponent
            is_capture = False
            for piece_idx in range(6):
                if board.state[opponent_start + piece_idx] & (np.uint64(1) << to_sq):
                    is_capture = True
                    break
            
            # Also include en passant captures
            flags = (move >> 12) & 0xF
            if flags == 5:  # EP_CAPTURE flag
                is_capture = True
            
            if is_capture:
                captures.append(move)
        
        return np.array(captures, dtype=np.uint16)
    
    def _order_captures(self, board: Board, captures: np.ndarray) -> np.ndarray:
        """Order captures by MVV-LVA."""
        if len(captures) <= 1:
            return captures
        
        scores = np.zeros(len(captures), dtype=np.int32)
        side = unpack_side(board.state[META])
        opponent_start = BP if side == 0 else WP
        piece_start = WP if side == 0 else BP
        
        for i, move in enumerate(captures):
            from_sq = move & 0x3F
            to_sq = (move >> 6) & 0x3F
            
            # Find captured piece value
            captured_value = 100  # Default (en passant pawn)
            for piece_idx in range(6):
                if board.state[opponent_start + piece_idx] & (np.uint64(1) << to_sq):
                    captured_value = int(self.PIECE_VALUES[piece_idx])
                    break
            
            # Find moving piece value
            moving_value = 100  # Default pawn
            for piece_idx in range(6):
                if board.state[piece_start + piece_idx] & (np.uint64(1) << from_sq):
                    moving_value = int(self.PIECE_VALUES[piece_idx])
                    break
            
            # MVV-LVA score
            scores[i] = captured_value * 10 - moving_value
        
        sorted_indices = np.argsort(-scores)
        return captures[sorted_indices]
    
    def _is_capture(self, move: np.uint16, board: Board) -> bool:
        """Check if a move is a capture."""
        to_sq = (move >> 6) & 0x3F
        side = unpack_side(board.state[META])
        opponent_start = BP if side == 0 else WP
        
        # Check if destination is occupied by opponent
        for piece_idx in range(6):
            if board.state[opponent_start + piece_idx] & (np.uint64(1) << to_sq):
                return True
        
        # Check for en passant
        flags = (move >> 12) & 0xF
        if flags == 5:  # EP_CAPTURE
            return True
        
        return False
    
    def _order_moves(self, board: Board, moves: np.ndarray, depth: int, tt_move: Optional[np.uint16]) -> np.ndarray:
        """
        Order moves for better alpha-beta pruning.
        
        Priority:
        1. TT move (from transposition table)
        2. Captures (MVV-LVA)
        3. Killer moves
        4. Other moves
        """
        if len(moves) <= 1:
            return moves
        
        scores = np.zeros(len(moves), dtype=np.int32)
        
        for i, move in enumerate(moves):
            # TT move gets highest priority
            if tt_move is not None and move == tt_move:
                scores[i] = 1000000
                continue
            
            # Decode move
            from_sq, to_sq, flags = move & 0x3F, (move >> 6) & 0x3F, (move >> 12) & 0xF
            
            # Check if capture (destination square occupied by opponent)
            side = unpack_side(board.state[META])
            opponent_start = BP if side == 0 else WP
            
            captured_value = 0
            for piece_idx in range(6):
                if board.state[opponent_start + piece_idx] & (np.uint64(1) << to_sq):
                    captured_value = self.PIECE_VALUES[piece_idx]
                    break
            
            if captured_value > 0:
                # MVV-LVA: prefer capturing valuable pieces with cheap pieces
                # Find moving piece value
                piece_start = WP if side == 0 else BP
                moving_value = 100  # default pawn
                for piece_idx in range(6):
                    if board.state[piece_start + piece_idx] & (np.uint64(1) << from_sq):
                        moving_value = self.PIECE_VALUES[piece_idx]
                        break
                
                scores[i] = 10000 + captured_value - (moving_value // 10)
            else:
                # Quiet moves: killers > history heuristic
                if depth in self.killer_moves and move in self.killer_moves[depth]:
                    scores[i] = 2000
                else:
                    # History heuristic score
                    history_score = self.history_table[side, from_sq, to_sq]
                    scores[i] = history_score
                    if history_score > 0:
                        self.stats.history_hits += 1
        
        # Sort moves by score (descending)
        sorted_indices = np.argsort(-scores)
        return moves[sorted_indices]
    
    def _store_killer(self, move: np.uint16, depth: int):
        """Store killer move for this depth."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()
    
    def get_pv(self, board: Board, max_depth: int = 10) -> list:
        """
        Extract Principal Variation from transposition table.
        
        Args:
            board: Current board position
            max_depth: Maximum PV depth to extract
            
        Returns:
            List of moves in PV line
        """
        pv = []
        seen_positions = set()
        temp_board = Board(fen=board.to_fen())
        
        for _ in range(max_depth):
            # Get hash
            zobrist = np.uint64(temp_board.state[HASH])
            
            # Avoid repetition
            if zobrist in seen_positions:
                break
            seen_positions.add(zobrist)
            
            # Probe TT for best move
            tt_entry = self.tt.probe(zobrist, 0, -self.MATE_SCORE, self.MATE_SCORE)
            if tt_entry is None or tt_entry[1] == 0:
                break
            
            move = tt_entry[1]
            
            # Verify move is legal
            moves_gen = Moves(temp_board)
            legal_moves = moves_gen.generate()
            if move not in legal_moves:
                break
            
            pv.append(move)
            
            # Make move on temporary board
            undo = temp_board.make_move(move)
            
            # If checkmate, stop
            moves_gen_new = Moves(temp_board)
            if len(moves_gen_new.generate()) == 0:
                break
        
        return pv
    
    def format_pv(self, pv: list, board: Board) -> str:
        """
        Format PV line as readable move sequence.
        
        Args:
            pv: List of moves
            board: Starting board position
            
        Returns:
            String representation of PV (e.g., "e2e4 e7e5 Nf3")
        """
        if not pv:
            return ""
        
        moves_str = []
        temp_board = Board(fen=board.to_fen())
        
        for move in pv:
            from_sq, to_sq, flags = decode_move(move)
            from_notation = chr(ord('a') + (from_sq % 8)) + str(from_sq // 8 + 1)
            to_notation = chr(ord('a') + (to_sq % 8)) + str(to_sq // 8 + 1)
            moves_str.append(f"{from_notation}{to_notation}")
            
            # Make move for next iteration
            undo = temp_board.make_move(move)
        
        return " ".join(moves_str)


# Example usage
if __name__ == "__main__":
    print("Testing bitboard search engine\n")
    
    # Starting position
    board = Board()
    search = Search(tt_size_mb=64, max_depth=10)
    
    print("Searching starting position...")
    move, score = search.search(board, depth=5, time_limit=5.0)
    
    if move:
        from_sq, to_sq, flags = decode_move(move)
        print(f"Best move: {from_sq} -> {to_sq}")
        print(f"Score: {score}")
    
    print(f"\n{search.stats}")
    
    # TT stats
    tt_stats = search.tt.get_stats()
    print(f"\nTT: {tt_stats['stores']:,} stores, {tt_stats['fill_rate']:.1f}% full")
