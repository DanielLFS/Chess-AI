# Chess Engine Architecture Rework Plan

## Current State (Post-Optimization)

### What We've Achieved ✅
```
Test Performance: 12.54 seconds (all 34 tests passing)
Evaluation Speed: 3.2x faster (0.323s for 1000 evals)
Architecture: Numpy/Numba-based hot paths
Time Management: Fixed (test_time_limit passes)
```

### Current Architecture
```
Board:
- 2D array of Piece objects (compatibility)
- Numpy arrays (piece_array, color_array) for performance
- Hybrid: Objects for interfaces, numpy for hot paths

Moves:
- Vectorized piece finding with np.argwhere()
- Numba JIT attack detection
- Numpy direction arrays

Evaluation:
- Direct numpy array access (zero conversion overhead)
- Numba JIT position evaluation
- Vectorized material counting

Search:
- Hash-based eval cache (numba compiled)
- Alpha-beta with iterative deepening
- Killer moves and move ordering
```

## Critical Architecture Questions

### 1. Should We Go Full Bitboards?

**Current: Hybrid Object/Numpy Approach**
- Pros:
  - ✅ 3.2x evaluation speedup already achieved
  - ✅ Code remains readable
  - ✅ Easy to debug and test
  - ✅ Numpy operations are fast enough
  - ✅ All tests pass with confidence
  
- Cons:
  - ❌ Still has some Python overhead in move generation
  - ❌ Not the absolute fastest possible
  - ❌ Board representation not as compact

**Full Bitboards (12 uint64 bitboards)**
- Pros:
  - ✅ 2-5x faster than current (estimated)
  - ✅ Very compact representation (96 bytes vs ~2KB)
  - ✅ Parallel piece operations with bitwise ops
  - ✅ Industry standard for top engines
  
- Cons:
  - ❌ Complete rewrite (2-4 weeks of work)
  - ❌ Much harder to debug
  - ❌ Complex magic bitboard initialization
  - ❌ Lose all current optimizations temporarily
  - ❌ Need to rewrite ALL tests

**Recommendation:** 
- **NOT YET** - Current architecture is performing well
- Bitboards are the *ultimate* optimization but require massive rewrite
- Better to exhaust algorithmic improvements first (transposition table, better pruning)
- Current 3.2x speedup + future search improvements = competitive engine

---

### 2. What About Numba Compilation of Entire Move Generation?

**Current: Selective Numba Use**
```python
# Only hot paths compiled
@njit def _can_reach_square_sliding()
@njit def _hash_position()
```

**Full Numba Compilation**
```python
# Compile entire move generator
@njit(parallel=True)
def generate_all_moves(piece_array, color_array):
    # Pure numpy operations
    # No Python objects allowed
    pass
```

**Pros:**
- ✅ 5-10x faster move generation
- ✅ Parallel processing capability
- ✅ Near-C performance

**Cons:**
- ❌ Cannot use Python objects (Piece, Move classes)
- ❌ Need to encode moves as integers
- ❌ Lose readability
- ❌ Harder to maintain

**Recommendation:**
- **Partial Implementation** - Compile move scoring/ordering
- Keep Move objects for clarity
- Use numba for move validation loops
- Hybrid approach: objects for API, numba for computation

---

### 3. Should Transposition Table Use Numpy Arrays?

**Option A: Python Dict (Current)**
```python
self.transposition_table = {}  # hash -> (depth, score, move, flag)
```
- Pros: Easy to use, automatic memory management
- Cons: Not cache-friendly, Python overhead

**Option B: Numpy Array as Fixed-Size Cache**
```python
# Pre-allocated array, use hash % size as index
self.tt = np.zeros((2**20, 4), dtype=np.int64)  # 1M entries
```
- Pros: Cache-friendly, faster lookups, fixed memory
- Cons: Collisions, need to handle overwrites

**Option C: Structured Numpy Array**
```python
tt_dtype = np.dtype([
    ('hash', np.uint64),
    ('depth', np.int8),
    ('score', np.int16),
    ('move_from', np.int8),
    ('move_to', np.int8),
    ('flag', np.uint8)
])
self.tt = np.zeros(2**20, dtype=tt_dtype)
```
- Pros: Best performance, type-safe, compact
- Cons: More complex to implement

**Recommendation:**
- **Option C** - Structured numpy array for TT
- Fixed size (1-2M entries) for predictable performance
- Use Zobrist hashing (numba compiled)
- Replace collisions using depth-priority

---

### 4. Move Representation: Objects vs Integers?

**Current: Move Objects**
```python
class Move:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    promotion: Optional[PieceType]
    # etc
```

**Alternative: Integer Encoding**
```python
# Pack move into 16 bits
# from_sq(6) | to_sq(6) | promotion(3) | flags(1)
move = (from_sq << 10) | (to_sq << 4) | (promotion << 1) | flag
```

**Pros of Integers:**
- ✅ 50% less memory
- ✅ Faster to copy
- ✅ Can use numpy arrays of moves
- ✅ Compatible with numba

**Cons of Integers:**
- ❌ Less readable
- ❌ Need encode/decode functions
- ❌ Harder to debug

**Recommendation:**
- **Keep Objects for Now** - readability matters
- Can add integer encoding later as optimization
- Use property methods for transparent conversion if needed

---

### 5. Should We Separate Evaluation Into Its Own Process?

**Monolithic (Current)**
```
ChessEngine (one process)
  ├── Board
  ├── MoveGenerator
  ├── Evaluator
  └── Search
```

**Distributed**
```
Search Process (coordinator)
  ↓
Evaluation Service (worker pool)
  ├── Worker 1
  ├── Worker 2
  └── Worker N
```

**Pros of Distributed:**
- ✅ Can scale to multiple cores
- ✅ Evaluation can be GPU-accelerated
- ✅ Can have multiple evaluation modes

**Cons:**
- ❌ IPC overhead (slower than direct call)
- ❌ Complex to implement
- ❌ Overkill for current scale

**Recommendation:**
- **NOT YET** - Single process is simpler and fast enough
- Multi-threading with shared memory is better option
- Consider lazy SMP (split search, not evaluation)

---

## Proposed Architecture Roadmap

### Phase 1: Algorithmic Improvements (NEXT - 1 week)
**Goal: 10-50x speedup without major rewrites**

1. **Implement Transposition Table** (2 days)
   - Structured numpy array
   - Zobrist hashing with numba
   - Depth-priority replacement
   - Expected: 10-20x speedup

2. **Improve Move Ordering** (1 day)
   - History heuristic
   - Better MVV-LVA
   - Countermove heuristic
   - Expected: 2x speedup

3. **Add Null Move Pruning** (1 day)
   - Adaptive null move
   - Verification search
   - Expected: 2x speedup

4. **Quiescence Search** (1 day)
   - Enable and tune
   - Delta pruning
   - Expected: Better tactical play

5. **Late Move Reductions** (1 day)
   - Reduce depth for unlikely moves
   - Expected: 1.5x speedup

**Expected Result: ~40x faster search (50K NPS → 2M NPS)**

---

### Phase 2: Selective Numba Compilation (1 week)
**Goal: Maximize performance while keeping code readable**

1. **Numba-compiled Move Validation** (2 days)
   ```python
   @njit
   def validate_moves_batch(board_array, color_array, moves_array):
       # Fast validation loop
       pass
   ```

2. **Vectorized Move Scoring** (1 day)
   ```python
   @njit
   def score_moves(moves, piece_array, history_table):
       # Parallel scoring
       pass
   ```

3. **Numba Zobrist Hashing** (1 day)
   ```python
   @njit
   def zobrist_hash(piece_array, color_array, castling, ep):
       # Fast incremental hash
       pass
   ```

4. **Benchmark and Tune** (2 days)
   - Profile with cProfile
   - Identify remaining bottlenecks
   - Optimize hot loops

**Expected Result: 2-3x additional speedup (2M → 5M NPS)**

---

### Phase 3: Memory Optimization (1 week)
**Goal: Reduce memory footprint, improve cache locality**

1. **Compact Move Representation** (2 days)
   - Move objects with `__slots__`
   - Optional integer encoding
   - Move pool/recycling

2. **Optimized Board Copy** (2 days)
   - Copy-on-write numpy arrays
   - Minimize allocation
   - Reuse buffers

3. **Cache-Friendly Data Structures** (2 days)
   - Align data structures
   - Reduce indirection
   - Benchmark cache misses

**Expected Result: 1.5x speedup from better cache usage**

---

### Phase 4: Consider Bitboards (2-4 weeks)
**Goal: Maximum performance, competitive with top engines**

**Only if:**
- ✅ Completed Phase 1-3
- ✅ Still need more performance
- ✅ Have 2-4 weeks dedicated time
- ✅ Comprehensive test suite in place

**Steps:**
1. Research modern bitboard implementations
2. Implement magic bitboard generation
3. Rewrite board representation
4. Rewrite move generation
5. Port all tests
6. Benchmark comparison

**Expected Result: 2-5x additional speedup (5M → 25M NPS)**

---

## Architecture Decision Matrix

| Optimization | Speedup | Effort | Complexity | Priority |
|--------------|---------|--------|------------|----------|
| Transposition Table | 10-20x | Medium | Medium | **CRITICAL** |
| Move Ordering | 2x | Low | Low | **HIGH** |
| Null Move Pruning | 2x | Low | Medium | **HIGH** |
| Quiescence Search | Better tactics | Low | Medium | **HIGH** |
| LMR | 1.5x | Medium | Medium | **MEDIUM** |
| Numba Move Gen | 2-3x | Medium | High | **MEDIUM** |
| Compact Moves | 1.2x | Low | Low | **LOW** |
| Cache Optimization | 1.5x | High | High | **LOW** |
| **Bitboards** | 2-5x | **VERY HIGH** | **VERY HIGH** | **FUTURE** |

---

## Recommended Implementation Order

### Week 1: Search Improvements
```
Day 1-2: Transposition Table (BIGGEST IMPACT)
Day 3:   History Heuristic + Better Move Ordering
Day 4:   Null Move Pruning
Day 5:   Tune Quiescence Search
```

### Week 2: Numba Optimization
```
Day 1-2: Compile move validation loops
Day 3:   Zobrist hashing with numba
Day 4:   Vectorized move scoring
Day 5:   Profile and benchmark
```

### Week 3: Memory & Polish
```
Day 1-2: Optimize move representation
Day 3:   Improve board copy performance
Day 4-5: Comprehensive benchmarking
```

### Week 4+: Optional Bitboards
```
Only if needed and time permits
Complete rewrite of board/moves
```

---

## Key Architectural Principles

1. **Hybrid is Good** - Objects for clarity, numpy/numba for speed
2. **Measure Everything** - Profile before optimizing
3. **Incremental Improvement** - Small changes, verify correctness
4. **Algorithm > Implementation** - Smart search > fast move gen
5. **Readability Matters** - Can optimize hot paths without ruining everything

## Success Metrics

### Current State:
- NPS: ~50K-100K (estimated)
- Depth: ~4-5 in 1 second
- Tests: 34/34 passing

### Target (After Phase 1-2):
- NPS: **2-5M** (20-50x improvement)
- Depth: **6-8** in 1 second
- Tests: **34/34 passing**
- Playing strength: **~1800-2000 ELO**

### Ultimate Goal (After Bitboards):
- NPS: **10-25M**
- Depth: **8-10** in 1 second
- Playing strength: **~2200-2400 ELO**
- Competitive with commercial engines

---

## Conclusion

**Don't rewrite everything yet!**

The current numpy/numba hybrid architecture is solid. Focus on:
1. Transposition table (HUGE win)
2. Better search algorithms (null move, LMR)
3. Selective numba compilation

Bitboards are the endgame, not the starting point. Get to 2-5M NPS first with algorithmic improvements, THEN consider the bitboard rewrite if needed.

**Current architecture is 80% of the way there. Don't throw it away!**
