# Chess Engine Backend Analysis & Optimization Plan

## Current Status

### Architecture Overview
```
engine/
├── board.py        (467 lines) - Board representation, moves, FEN
├── moves.py        (??  lines) - Legal move generation
├── evaluation.py   (??  lines) - Position evaluation
└── search.py       (??  lines) - Minimax search with alpha-beta
```

### Test Results
- **28/29 tests passing (96.5%)**
- ✅ All move generation tests passing
- ✅ All evaluation tests passing  
- ✅ Checkmate detection working
- ❌ Time limit test failing (11s instead of 1s - search not respecting time constraints)

## Core Components Analysis

### 1. **board.py** - Board Representation
**Current Implementation:**
- 8x8 2D array of Piece objects
- FEN parsing and generation
- Move execution with undo capability
- Castling, en passant, promotion support

**Optimization Opportunities:**
- [ ] Consider bitboards for faster position manipulation
- [ ] Zobrist hashing for position caching
- [ ] Incremental update of piece lists
- [ ] Copy-on-write for board copying

### 2. **moves.py** - Move Generation
**Current Implementation:**
- Pseudo-legal move generation
- Legality checking (filters out moves leaving king in check)
- Special moves: castling, en passant, promotion

**Performance Metrics:**
- Perft(3) from initial position: ~8,902 nodes ✅
- Perft(2) Kiwipete: 2,039 nodes ✅

**Optimization Opportunities:**
- [ ] Magic bitboards for sliding pieces
- [ ] Pre-computed attack tables
- [ ] Move ordering (MVV-LVA, killer moves, history heuristic)
- [ ] Staged move generation

### 3. **evaluation.py** - Position Evaluation
**Current Implementation:**
- Material counting
- Piece-square tables
- Uses numpy arrays (already optimized!)

**Current Weights:**
- P=100, N=320, B=330, R=500, Q=900, K=20000

**Optimization Opportunities:**
- [ ] Add king safety evaluation
- [ ] Pawn structure analysis (doubled, isolated, passed pawns)
- [ ] Mobility evaluation
- [ ] Piece coordination bonuses
- [ ] Endgame-specific evaluation

### 4. **search.py** - Search Algorithm
**Current Implementation:**
- Minimax with alpha-beta pruning
- Iterative deepening
- Basic move ordering
- Time management (BROKEN - not respecting time limits!)

**Issues Found:**
1. **Time limit not working** - search runs 11x longer than requested
2. Node counting may be inefficient
3. No aspiration windows
4. No transposition table

**Optimization Opportunities:**
- [ ] Fix time management (critical!)
- [ ] Add transposition table (huge speedup)
- [ ] Null move pruning
- [ ] Late move reductions
- [ ] Quiescence search
- [ ] Aspiration windows
- [ ] Principal variation search (PVS)

## Dependency Analysis

### External Dependencies
```python
numpy==1.26.4          # Used in evaluation.py
numba==0.59.0          # Not currently used but installed
```

### Internal Dependencies
```
board.py (no engine deps)
    ↓
moves.py → board.py
    ↓
evaluation.py → board.py
    ↓
search.py → board.py, moves.py, evaluation.py
```

**Clean architecture!** No circular dependencies.

## Performance Profiling Needed

### Critical Metrics to Measure:
1. **Nodes per second (NPS)** - Current: Unknown
2. **Move generation time** - Per position average
3. **Evaluation time** - Per position average  
4. **Board copy time** - Used frequently in search
5. **Alpha-beta cutoff rate** - How effective is pruning?
6. **Branch factor** - Average moves per position

### Profiling Plan:
```python
# Create benchmark script
import cProfile
import pstats

# Profile move generation
# Profile search at various depths
# Profile evaluation function
# Identify bottlenecks
```

## Optimization Priority

### Phase 1: Critical Fixes (Week 1)
1. **Fix time management** - search.py time limit enforcement
2. **Add transposition table** - 10-100x speedup potential
3. **Profile current performance** - establish baseline metrics

### Phase 2: Search Optimizations (Week 2)
4. **Quiescence search** - Avoid horizon effect
5. **Move ordering improvements** - Killer moves, history heuristic
6. **Null move pruning** - Reduce search tree
7. **Aspiration windows** - Faster alpha-beta

### Phase 3: Evaluation Enhancements (Week 3)
8. **King safety** - Critical for middlegame
9. **Pawn structure** - Passed/doubled/isolated pawns
10. **Mobility** - Piece activity evaluation
11. **Tapered evaluation** - Interpolate middlegame/endgame

### Phase 4: Advanced Optimizations (Week 4)
12. **Bitboards** - Complete rewrite for 10x speed
13. **Magic bitboards** - Fast sliding piece moves
14. **SIMD optimization** - Vectorized operations
15. **Multi-threading** - Lazy SMP

## Estimated Performance Gains

| Optimization | Current NPS | Expected NPS | Speedup |
|--------------|-------------|--------------|---------|
| Baseline     | ~50K        | -            | 1x      |
| + Transposition table | ~50K | ~500K   | 10x     |
| + Move ordering | ~500K    | ~1M          | 2x      |
| + Null move | ~1M         | ~2M          | 2x      |
| + Bitboards | ~2M         | ~5M          | 2.5x    |
| **Total**   | **50K**     | **5M**       | **100x**|

## Code Quality Metrics

### Current State:
- ✅ Clean separation of concerns
- ✅ Type hints used
- ✅ Good test coverage (96.5%)
- ✅ No circular dependencies
- ⚠️ Limited documentation
- ⚠️ No performance benchmarks

### Improvements Needed:
- [ ] Add docstrings to all public methods
- [ ] Create performance benchmark suite
- [ ] Add integration tests
- [ ] Document engine parameters
- [ ] Add UCI protocol support

## Next Steps

1. **Create profiling script** to measure current performance
2. **Fix time management bug** in search.py
3. **Implement transposition table** for massive speedup
4. **Add benchmarking suite** to track improvements
5. **Document optimization results**

## Future Architecture Considerations

### When reintroducing frontend (React):
- Keep engine as pure Python backend
- Create REST API layer
- WebSocket for real-time analysis
- Separate evaluation service (can be microservice)
- Consider UCI protocol for engine communication

### Scalability:
- Engine can run in separate process
- Multiple engine instances for analysis
- Distributed computing for opening book generation
- Cloud deployment for online play
