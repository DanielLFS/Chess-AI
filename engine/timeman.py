"""
Time management for chess search.

Allocates search time per move based on:
- Total time remaining
- Increment per move
- Game phase (opening/middlegame/endgame)
- Move complexity

Prevents timeouts while maximizing thinking time.

Usage:
    tm = TimeManager(total_time_ms=60000, increment_ms=1000)
    allocated_time = tm.allocate_time(moves_played=15)
    
    # During search
    if tm.should_stop():
        break
"""

import time
from typing import Optional


class TimeManager:
    """
    Intelligent time allocation for search.
    
    Balances between:
    - Not timing out
    - Using time effectively
    - Adapting to game phase
    """
    
    def __init__(self, 
                 total_time_ms: int,
                 increment_ms: int = 0,
                 moves_to_go: Optional[int] = None,
                 overhead_ms: int = 50):
        """
        Initialize time manager.
        
        Args:
            total_time_ms: Total time remaining (milliseconds)
            increment_ms: Time added per move (Fischer increment)
            moves_to_go: Moves until time control (None = sudden death)
            overhead_ms: Safety margin for network/processing lag
        """
        self.total_time_ms = total_time_ms
        self.increment_ms = increment_ms
        self.moves_to_go = moves_to_go
        self.overhead_ms = overhead_ms
        
        self.allocated_time_ms = 0
        self.max_time_ms = 0
        self.start_time = 0
        self.nodes_searched = 0
        
        # Time allocation parameters
        self.default_move_fraction = 1.0 / 30.0  # Assume ~30 moves remaining
        self.opening_move_fraction = 1.0 / 40.0  # More conservative in opening
        self.endgame_move_fraction = 1.0 / 20.0  # More aggressive in endgame
        
        # Time extension multipliers
        self.max_time_multiplier = 3.0  # Can use up to 3x allocated time if critical
    
    def allocate_time(self, 
                     moves_played: int = 0,
                     is_opening: bool = False,
                     is_endgame: bool = False) -> int:
        """
        Calculate how much time to allocate for this move.
        
        Args:
            moves_played: Number of moves played so far
            is_opening: Whether we're in opening phase
            is_endgame: Whether we're in endgame phase
        
        Returns:
            Allocated time in milliseconds
        """
        # Available time (after overhead)
        available = max(0, self.total_time_ms - self.overhead_ms)
        
        # Determine moves remaining
        if self.moves_to_go is not None:
            # Fixed move time control (e.g., 40 moves in 90 minutes)
            expected_moves = self.moves_to_go
        else:
            # Sudden death - estimate based on game phase
            if is_opening:
                expected_moves = 40  # Conservative
            elif is_endgame:
                expected_moves = 20  # Fewer moves expected
            else:
                expected_moves = 30  # Standard middlegame
        
        # Base allocation: available time / expected moves
        base_allocation = available / expected_moves
        
        # Add increment (we'll get this back after our move)
        base_allocation += self.increment_ms * 0.8  # Use 80% of increment
        
        # Adjust for game phase
        if is_opening:
            # Spend less time in opening (can be book/theory)
            phase_multiplier = 0.7
        elif is_endgame:
            # Spend more time in endgame (critical calculation)
            phase_multiplier = 1.3
        else:
            # Standard middlegame
            phase_multiplier = 1.0
        
        self.allocated_time_ms = int(base_allocation * phase_multiplier)
        
        # Maximum time we can use (for critical positions)
        # Allow up to 3x allocated time, but not more than 20% of remaining
        self.max_time_ms = min(
            int(self.allocated_time_ms * self.max_time_multiplier),
            int(available * 0.2)
        )
        
        # Ensure we don't allocate more than available
        self.allocated_time_ms = min(self.allocated_time_ms, available)
        self.max_time_ms = min(self.max_time_ms, available)
        
        return self.allocated_time_ms
    
    def start_search(self):
        """Mark search start time."""
        self.start_time = time.perf_counter()
        self.nodes_searched = 0
    
    def elapsed_ms(self) -> int:
        """Get elapsed time since search start (milliseconds)."""
        if self.start_time == 0:
            return 0
        return int((time.perf_counter() - self.start_time) * 1000)
    
    def should_stop(self, is_critical: bool = False) -> bool:
        """
        Check if we should stop searching.
        
        Args:
            is_critical: Whether position is critical (allows time extension)
        
        Returns:
            True if we should stop search
        """
        elapsed = self.elapsed_ms()
        
        # Never exceed max time (hard limit)
        if elapsed >= self.max_time_ms:
            return True
        
        # Normal stop at allocated time (unless critical)
        if not is_critical and elapsed >= self.allocated_time_ms:
            return True
        
        return False
    
    def update_nodes(self, nodes: int):
        """Update node count (for NPS calculation)."""
        self.nodes_searched = nodes
    
    def get_nps(self) -> int:
        """Get nodes per second."""
        elapsed = self.elapsed_ms()
        if elapsed == 0:
            return 0
        return int((self.nodes_searched * 1000) / elapsed)
    
    def get_stats(self) -> dict:
        """Get time management statistics."""
        return {
            'allocated_ms': self.allocated_time_ms,
            'max_ms': self.max_time_ms,
            'elapsed_ms': self.elapsed_ms(),
            'remaining_ms': max(0, self.total_time_ms - self.elapsed_ms()),
            'nps': self.get_nps(),
            'nodes': self.nodes_searched
        }
    
    def is_time_critical(self) -> bool:
        """Check if we're running low on time."""
        return self.total_time_ms < 10000  # Less than 10 seconds
    
    def should_extend_time(self, 
                          score_drop: int = 0,
                          best_move_changed: bool = False) -> bool:
        """
        Determine if we should extend thinking time.
        
        Args:
            score_drop: How much score dropped from previous iteration
            best_move_changed: Whether best move changed this iteration
        
        Returns:
            True if we should extend search time
        """
        elapsed = self.elapsed_ms()
        
        # Already past allocated time
        if elapsed >= self.allocated_time_ms:
            return False
        
        # Don't extend if we're already near max time
        if elapsed >= self.max_time_ms * 0.8:
            return False
        
        # Extend on large score drop (position got worse)
        if score_drop > 100:  # More than 1 pawn worse
            return True
        
        # Extend if best move keeps changing (unstable position)
        if best_move_changed:
            return True
        
        return False


class FixedTimeManager(TimeManager):
    """
    Simplified time manager for fixed time per move.
    
    Useful for testing and analysis.
    """
    
    def __init__(self, time_per_move_ms: int):
        """
        Initialize with fixed time per move.
        
        Args:
            time_per_move_ms: Fixed time allocation per move
        """
        super().__init__(total_time_ms=time_per_move_ms * 100, increment_ms=0)
        self.fixed_time = time_per_move_ms
        # Pre-allocate time
        self.allocated_time_ms = self.fixed_time
        self.max_time_ms = self.fixed_time
    
    def allocate_time(self, moves_played: int = 0, 
                     is_opening: bool = False,
                     is_endgame: bool = False) -> int:
        """Always return fixed time."""
        self.allocated_time_ms = self.fixed_time
        self.max_time_ms = self.fixed_time
        return self.fixed_time


class DepthOnlyManager(TimeManager):
    """
    Time manager that never stops (for fixed-depth search).
    
    Used when depth limit is primary constraint.
    """
    
    def __init__(self):
        """Initialize infinite time manager."""
        super().__init__(total_time_ms=999_999_999, increment_ms=0)
    
    def should_stop(self, is_critical: bool = False) -> bool:
        """Never stop based on time."""
        return False
    
    def allocate_time(self, moves_played: int = 0,
                     is_opening: bool = False,
                     is_endgame: bool = False) -> int:
        """Return infinite time."""
        self.allocated_time_ms = 999_999_999
        self.max_time_ms = 999_999_999
        return 999_999_999
