"""
Move ordering heuristics for alpha-beta search.

Implements killer moves, history heuristic, and countermove heuristic
to dramatically improve search efficiency (10-50x speedup).

Move ordering priority:
1. Hash move (from transposition table)
2. Winning captures (MVV-LVA)
3. Killer moves (non-captures that caused beta cutoffs)
4. Countermoves (refutation moves)
5. History heuristic (moves that historically caused cutoffs)
6. Losing captures
7. Remaining quiet moves

Usage:
    picker = MovePicker()
    moves = picker.order_moves(board, moves, ply, hash_move)
"""

import numpy as np
from numba import njit
from typing import Optional


# Move ordering scores (higher = search first)
HASH_MOVE_SCORE = 10_000_000
WINNING_CAPTURE_BASE = 1_000_000
KILLER_MOVE_SCORE_1 = 900_000  # Primary killer
KILLER_MOVE_SCORE_2 = 800_000  # Secondary killer
COUNTERMOVE_SCORE = 700_000
HISTORY_SCORE_BASE = 0  # 0 to 100_000 based on history
LOSING_CAPTURE_BASE = -1_000_000

# Killer move slots per ply
MAX_KILLERS = 2
MAX_PLY = 128


@njit(cache=True)
def mvv_lva_score(move: np.uint16, board_state: np.ndarray) -> int:
    """
    Most Valuable Victim - Least Valuable Attacker scoring.
    
    Args:
        move: Move in format (from_sq | (to_sq << 6) | (flags << 12))
        board_state: Bitboards array [12, 64] - for victim detection
    
    Returns:
        Score where higher = better capture
    """
    to_sq = (move >> 6) & 0x3F
    from_sq = move & 0x3F
    
    # Piece values for MVV-LVA (victim values * 10)
    piece_values = np.array([100, 320, 330, 500, 900, 20000,  # White pieces
                             100, 320, 330, 500, 900, 20000], dtype=np.int32)  # Black pieces
    
    # Find victim (piece on to_sq)
    victim_value = 0
    for piece_type in range(12):
        if (board_state[piece_type] >> to_sq) & 1:
            victim_value = piece_values[piece_type]
            break
    
    # Find attacker (piece on from_sq)
    attacker_value = 0
    for piece_type in range(12):
        if (board_state[piece_type] >> from_sq) & 1:
            attacker_value = piece_values[piece_type]
            break
    
    # MVV-LVA: prioritize valuable victims, deprioritize valuable attackers
    return (victim_value * 10) - attacker_value


@njit(cache=True)
def is_capture(move: np.uint16, board_state: np.ndarray) -> bool:
    """Check if move is a capture."""
    to_sq = (move >> 6) & 0x3F
    flags = (move >> 12) & 0xF
    
    # En passant is always a capture
    if flags == 5:  # EP_CAPTURE flag
        return True
    
    # Check if destination square has enemy piece
    for piece_type in range(12):
        if (board_state[piece_type] >> to_sq) & 1:
            return True
    
    return False


class MovePicker:
    """
    Advanced move ordering using multiple heuristics.
    
    Dramatically improves alpha-beta pruning efficiency by searching
    likely-good moves first.
    """
    
    def __init__(self):
        """Initialize move ordering tables."""
        # Killer moves: best non-capture moves per ply [ply][killer_slot]
        self.killers = np.zeros((MAX_PLY, MAX_KILLERS), dtype=np.uint16)
        
        # History heuristic: [piece_type][to_square] -> success count
        self.history = np.zeros((12, 64), dtype=np.int32)
        
        # Countermoves: [from_square][to_square] -> best response move
        self.countermoves = np.zeros((64, 64), dtype=np.uint16)
        
        # Statistics
        self.killer_hits = 0
        self.history_hits = 0
        self.counter_hits = 0
    
    def clear(self):
        """Clear all heuristic tables (call between games)."""
        self.killers.fill(0)
        self.history.fill(0)
        self.countermoves.fill(0)
        self.killer_hits = 0
        self.history_hits = 0
        self.counter_hits = 0
    
    def clear_for_search(self):
        """Clear killers for new search (keep history)."""
        self.killers.fill(0)
    
    def update_killer(self, move: np.uint16, ply: int):
        """
        Add move to killer moves for this ply.
        
        Args:
            move: The move that caused a beta cutoff
            ply: Current search ply (distance from root)
        """
        if ply >= MAX_PLY:
            return
        
        # Don't duplicate - if already primary killer, don't demote
        if self.killers[ply, 0] == move:
            return
        
        # Shift killers: primary -> secondary, new -> primary
        self.killers[ply, 1] = self.killers[ply, 0]
        self.killers[ply, 0] = move
    
    def update_history(self, move: np.uint16, piece_type: int, depth: int, cutoff: bool):
        """
        Update history heuristic based on search results.
        
        Args:
            move: The move that was tried
            piece_type: Piece type that moved (0-11)
            depth: Remaining depth when move was tried
            cutoff: Whether move caused beta cutoff (good move)
        """
        to_sq = (move >> 6) & 0x3F
        
        # Bonus/penalty scales with depth (deeper = more important)
        delta = depth * depth
        
        if cutoff:
            # Good move - increase history score
            self.history[piece_type, to_sq] += delta
        else:
            # Bad move - decrease history score
            self.history[piece_type, to_sq] -= delta
        
        # Aging: prevent overflow and keep scores recent
        # Scale down if any entry gets too large
        if np.abs(self.history[piece_type, to_sq]) > 10_000:
            self.history //= 2
    
    def update_countermove(self, opponent_move: np.uint16, response_move: np.uint16):
        """
        Record that response_move is a good response to opponent_move.
        
        Args:
            opponent_move: The move opponent just played
            response_move: Our move that refuted it (caused beta cutoff)
        """
        if opponent_move == 0:
            return
        
        from_sq = opponent_move & 0x3F
        to_sq = (opponent_move >> 6) & 0x3F
        self.countermoves[from_sq, to_sq] = response_move
    
    def get_history_score(self, move: np.uint16, piece_type: int) -> int:
        """Get history score for move (0 to HISTORY_SCORE_BASE range)."""
        to_sq = (move >> 6) & 0x3F
        history_val = self.history[piece_type, to_sq]
        
        # Normalize to 0-100k range
        max_history = 10_000
        normalized = min(max(history_val, 0), max_history)
        return (normalized * 100_000) // max_history
    
    def order_moves(self, board, moves: np.ndarray, ply: int, 
                   hash_move: Optional[np.uint16] = None,
                   prev_move: Optional[np.uint16] = None) -> np.ndarray:
        """
        Order moves for optimal alpha-beta pruning.
        
        Args:
            board: Board object (for capture detection)
            moves: Array of moves to order
            ply: Current search ply
            hash_move: Best move from transposition table (if any)
            prev_move: Opponent's previous move (for countermove)
        
        Returns:
            Moves sorted by descending priority
        """
        if len(moves) == 0:
            return moves
        
        scores = np.zeros(len(moves), dtype=np.int32)
        
        # Get board state for capture detection
        board_state = board.bitboards
        
        for i, move in enumerate(moves):
            # 1. Hash move (from TT)
            if hash_move is not None and move == hash_move:
                scores[i] = HASH_MOVE_SCORE
                continue
            
            # Get move info
            from_sq = move & 0x3F
            to_sq = (move >> 6) & 0x3F
            
            # Find piece type
            piece_type = -1
            for pt in range(12):
                if (board_state[pt] >> from_sq) & 1:
                    piece_type = pt
                    break
            
            # 2. Captures
            if is_capture(move, board_state):
                mvv_score = mvv_lva_score(move, board_state)
                if mvv_score >= 0:
                    # Winning or equal capture
                    scores[i] = WINNING_CAPTURE_BASE + mvv_score
                else:
                    # Losing capture (queen takes pawn)
                    scores[i] = LOSING_CAPTURE_BASE + mvv_score
                continue
            
            # 3. Killer moves (non-captures)
            if ply < MAX_PLY:
                if move == self.killers[ply, 0]:
                    scores[i] = KILLER_MOVE_SCORE_1
                    continue
                elif move == self.killers[ply, 1]:
                    scores[i] = KILLER_MOVE_SCORE_2
                    continue
            
            # 4. Countermove
            if prev_move is not None and prev_move != 0:
                prev_from = prev_move & 0x3F
                prev_to = (prev_move >> 6) & 0x3F
                if move == self.countermoves[prev_from, prev_to]:
                    scores[i] = COUNTERMOVE_SCORE
                    continue
            
            # 5. History heuristic
            if piece_type != -1:
                scores[i] = HISTORY_SCORE_BASE + self.get_history_score(move, piece_type)
        
        # Sort moves by score (descending)
        sorted_indices = np.argsort(-scores)  # Negative for descending
        return moves[sorted_indices]
    
    def get_stats(self) -> dict:
        """Get move ordering statistics."""
        return {
            'killer_hits': self.killer_hits,
            'history_hits': self.history_hits,
            'counter_hits': self.counter_hits,
            'max_history': int(np.max(np.abs(self.history))),
            'active_killers': int(np.count_nonzero(self.killers))
        }
