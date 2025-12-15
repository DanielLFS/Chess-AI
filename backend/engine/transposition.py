"""
Transposition table for caching position evaluations.

Runtime hash table that stores search results to avoid re-evaluating
repeated positions. Provides 10-100x speedup in search.

Structure:
- Position hash (Zobrist key)
- Evaluation score
- Best move
- Search depth
- Node type (exact/lower/upper bound)
- Age (for replacement policy)

Usage:
    from engine.tables import TranspositionTable
    
    tt = TranspositionTable(size_mb=128)
    tt.store(zobrist, score, move, depth, node_type)
    result = tt.probe(zobrist, depth, alpha, beta)
"""

import numpy as np
from numba import njit
from typing import Optional, Tuple


# Node types for alpha-beta bounds
EXACT = 0      # Exact score (PV node)
LOWER_BOUND = 1  # Beta cutoff (score >= beta)
UPPER_BOUND = 2  # Alpha cutoff (score <= alpha)


# Transposition table entry structure (packed into numpy arrays for speed)
# Each entry: [hash_key, score, best_move, depth, node_type, age]
# Using structured arrays for cache efficiency


class TranspositionTable:
    """
    Hash table for caching position evaluations.
    
    Uses Zobrist hashing with replacement scheme based on depth and age.
    """
    
    def __init__(self, size_mb: int = 128):
        """
        Initialize transposition table.
        
        Args:
            size_mb: Size in megabytes (default 128MB)
        """
        # Each entry: 8 bytes (hash) + 2 (score) + 2 (move) + 1 (depth) + 1 (type) + 1 (age) = 15 bytes
        # Round up to 16 bytes for alignment
        bytes_per_entry = 16
        self.size = (size_mb * 1024 * 1024) // bytes_per_entry
        
        # Make size a power of 2 for fast modulo (use bitwise AND instead)
        self.size = 1 << (self.size.bit_length() - 1)
        self.mask = self.size - 1
        
        # Separate arrays for each field (better cache locality)
        self.hash_keys = np.zeros(self.size, dtype=np.uint64)
        self.scores = np.zeros(self.size, dtype=np.int16)
        self.best_moves = np.zeros(self.size, dtype=np.uint16)
        self.depths = np.zeros(self.size, dtype=np.int8)
        self.node_types = np.zeros(self.size, dtype=np.uint8)
        self.ages = np.zeros(self.size, dtype=np.uint8)
        
        self.current_age = 0
        self.hits = 0
        self.collisions = 0
        self.stores = 0
        
        print(f"[TT] Initialized {self.size:,} entries ({size_mb}MB)")
    
    def clear(self):
        """Clear all entries."""
        self.hash_keys.fill(0)
        self.scores.fill(0)
        self.best_moves.fill(0)
        self.depths.fill(0)
        self.node_types.fill(0)
        self.ages.fill(0)
        self.hits = 0
        self.collisions = 0
        self.stores = 0
    
    def new_search(self):
        """Increment age for new search (helps with replacement)."""
        self.current_age = (self.current_age + 1) % 256
    
    def probe(self, zobrist: np.uint64, depth: int, alpha: int, beta: int) -> Optional[Tuple[int, np.uint16]]:
        """
        Probe transposition table for cached evaluation.
        
        Args:
            zobrist: Zobrist hash of position
            depth: Current search depth
            alpha: Alpha bound
            beta: Beta bound
        
        Returns:
            (score, best_move) if found and usable, None otherwise
        """
        index = int(zobrist & self.mask)
        
        if self.hash_keys[index] == zobrist:
            # Hash match - check if depth is sufficient
            stored_depth = self.depths[index]
            if stored_depth >= depth:
                self.hits += 1
                score = int(self.scores[index])
                node_type = self.node_types[index]
                best_move = self.best_moves[index]
                
                # Check if score is usable based on node type
                if node_type == EXACT:
                    return (score, best_move)
                elif node_type == LOWER_BOUND and score >= beta:
                    return (score, best_move)
                elif node_type == UPPER_BOUND and score <= alpha:
                    return (score, best_move)
                
                # Can't use score, but can use move for move ordering
                return (None, best_move) if best_move != 0 else None
            else:
                # Collision - hash matches but depth too shallow
                self.collisions += 1
        
        return None
    
    def store(self, zobrist: np.uint64, score: int, best_move: np.uint16, 
              depth: int, node_type: int):
        """
        Store position evaluation in transposition table.
        
        Args:
            zobrist: Zobrist hash of position
            score: Evaluation score
            best_move: Best move found
            depth: Search depth
            node_type: EXACT, LOWER_BOUND, or UPPER_BOUND
        """
        index = int(zobrist & self.mask)
        
        # Replacement scheme: always replace if:
        # 1. Empty slot (hash == 0)
        # 2. Same position (hash matches)
        # 3. Older entry (age differs and depth not significantly deeper)
        # 4. Shallower depth
        
        stored_hash = self.hash_keys[index]
        if stored_hash == 0 or stored_hash == zobrist:
            # Empty or same position - always replace
            replace = True
        else:
            # Check replacement criteria
            stored_depth = self.depths[index]
            stored_age = self.ages[index]
            
            # Replace if: new depth >= stored depth OR different age
            replace = (depth >= stored_depth) or (stored_age != self.current_age)
        
        if replace:
            self.hash_keys[index] = zobrist
            self.scores[index] = np.int16(score)
            self.best_moves[index] = best_move
            self.depths[index] = np.int8(depth)
            self.node_types[index] = np.uint8(node_type)
            self.ages[index] = np.uint8(self.current_age)
            self.stores += 1
    
    def get_stats(self) -> dict:
        """Get transposition table statistics."""
        total_probes = self.hits + self.collisions
        hit_rate = (self.hits / total_probes * 100) if total_probes > 0 else 0
        
        # Count filled entries
        filled = np.count_nonzero(self.hash_keys)
        fill_rate = filled / self.size * 100
        
        return {
            'size': self.size,
            'filled': filled,
            'fill_rate': fill_rate,
            'hits': self.hits,
            'collisions': self.collisions,
            'stores': self.stores,
            'hit_rate': hit_rate
        }
    
    def __repr__(self):
        stats = self.get_stats()
        return (f"TranspositionTable({stats['size']:,} entries, "
                f"{stats['fill_rate']:.1f}% full, "
                f"{stats['hit_rate']:.1f}% hit rate)")


# Optimized probe function (can be called from Numba JIT code)
@njit(cache=True, inline='always')
def tt_probe_fast(hash_keys: np.ndarray, scores: np.ndarray, best_moves: np.ndarray,
                  depths: np.ndarray, node_types: np.ndarray,
                  zobrist: np.uint64, mask: int, depth: int, 
                  alpha: int, beta: int) -> Tuple[bool, int, np.uint16]:
    """
    Fast transposition table probe (JIT-compiled).
    
    Returns:
        (found, score, best_move)
    """
    index = int(zobrist & mask)
    
    if hash_keys[index] == zobrist and depths[index] >= depth:
        score = int(scores[index])
        node_type = node_types[index]
        best_move = best_moves[index]
        
        if node_type == EXACT:
            return (True, score, best_move)
        elif node_type == LOWER_BOUND and score >= beta:
            return (True, score, best_move)
        elif node_type == UPPER_BOUND and score <= alpha:
            return (True, score, best_move)
        
        # Can use move but not score
        if best_move != 0:
            return (False, 0, best_move)
    
    return (False, 0, np.uint16(0))


@njit(cache=True, inline='always')
def tt_store_fast(hash_keys: np.ndarray, scores: np.ndarray, best_moves: np.ndarray,
                  depths: np.ndarray, node_types: np.ndarray, ages: np.ndarray,
                  zobrist: np.uint64, mask: int, score: int, best_move: np.uint16,
                  depth: int, node_type: int, current_age: int):
    """
    Fast transposition table store (JIT-compiled).
    """
    index = int(zobrist & mask)
    
    stored_hash = hash_keys[index]
    if stored_hash == 0 or stored_hash == zobrist:
        replace = True
    else:
        stored_depth = depths[index]
        stored_age = ages[index]
        replace = (depth >= stored_depth) or (stored_age != current_age)
    
    if replace:
        hash_keys[index] = zobrist
        scores[index] = np.int16(score)
        best_moves[index] = best_move
        depths[index] = np.int8(depth)
        node_types[index] = np.uint8(node_type)
        ages[index] = np.uint8(current_age)
