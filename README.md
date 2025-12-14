# Chess Engine

A high-performance chess engine built for speed and neural network integration.

---

## 🏗️ ARCHITECTURE DECISIONS (Reference for all development)

### Core Design Choices:
1. **Board Representation**: Bitboards (12 × uint64 - one per piece type/color)
2. **State Storage**: Pure numpy array (20 × uint64 for speed)
3. **Move Encoding**: uint16 (Stockfish-style: 6 bits from + 6 bits to + 4 bits flags)
4. **Performance**: All hot paths compiled with numba (@njit cache=True)
5. **Operations**: Vectorized bit manipulation (set_bit, clear_bit, pop_count)
6. **OOP**: Minimal wrapper class (~50 lines) - all logic in numba functions
7. **Target**: Neural network MCTS engine (10,000+ evals/move)

### State Array Layout:
```python
state = np.array(dtype=np.uint64)
# Index 0-5:   White pieces [Pawn, Knight, Bishop, Rook, Queen, King]
# Index 6-11:  Black pieces [Pawn, Knight, Bishop, Rook, Queen, King]
# Index 12:    Occupied squares (all pieces combined)
# Index 13:    Metadata (castling rights, en passant, halfmove, side to move - packed)
# Index 14-19: Reserved for NN features (history planes, etc.)
```

### Implementation Strategy:
- **One file at a time** - systematic refactoring
- **All logic in numba** - zero Python overhead in hot paths
- **Minimal OOP** - thin wrapper (~30 lines) over numba functions
- **Magic bitboards** - pre-computed attack tables for sliding pieces
- **Naming convention**: Class name matches filename (board.py → Board, moves.py → Moves, etc.)

### Current Status:
- ✅ **COMPLETED**: board.py fully functional with bitboards
- ✅ Pure numpy array state (160 bytes vs 2KB+ previously - 19x smaller)
- ✅ All numba-compiled operations (zero Python overhead)
- ✅ Pre-computed attack tables (knight, king, pawn)
- ✅ Make/unmake move with all special moves (castling, en passant, promotion)
- ✅ FEN import/export working correctly
- ✅ Tested: move execution, castling rights, halfmove clock
- ✅ **COMPLETED**: moves.py rewritten with bitboard architecture
- ✅ Pure bitboard move generation (no array conversion)
- ✅ All numba-compiled functions (generate_pawn_moves, generate_knight_moves, etc.)
- ✅ Legal move filtering (removes moves leaving king in check)
- ✅ Check/checkmate/stalemate detection
- ✅ **VERIFIED**: 100% perft pass rate (6/6 positions, depths 1-5, 245s runtime)
- ✅ Fixed EN PASSANT unmake bug (captured piece restored twice)
- ✅ Move generation is PRODUCTION READY (~1.9M nps)
- ✅ **COMPLETED**: Zobrist hashing (793 keys, O(1) incremental updates, 100% hash consistency)
- ✅ **COMPLETED**: Transposition table (64MB, verified working, 10-30% hit rate)
- ✅ **COMPLETED**: search.py (negamax, TT, move ordering, iterative deepening)
- ✅ **COMPLETED**: evaluation.py (material + PST, endgame detection, @njit compiled)
- ✅ **HIGHLY OPTIMIZED**: LMR + history + futility + RFP + null move + quiescence + extensions + aspiration + PV (82-92% node reduction, 3x+ speedup!)
- ⏳ **NEXT**: Internal iterative deepening, razoring, SEE (Static Exchange Evaluation)

---

## 📊 ENGINE BENCHMARKING & METRICS PLAN

### Engine Components Overview

#### 1. **Board Representation** ✅ IMPLEMENTED
- **Current**: Bitboards (12 × uint64) + state array (20 × uint64 = 160 bytes)
- **Operations**: set_bit, clear_bit, get_bit, pop_count, lsb (all @njit)
- **Attack tables**: Pre-computed (knight, king, pawn), classical sliding (rook, bishop, queen)
- **TODO**: Magic bitboards for 5x speedup on sliding piece attacks

#### 2. **Move Generation** ✅ IMPLEMENTED & VERIFIED
- **Current**: Pure bitboard generation, all numba-compiled
- **Returns**: np.ndarray of uint16 encoded moves
- **Features**: Pseudo-legal → legal filtering, castling through check detection
- **Performance**: O(pieces) iteration, pre-computed attacks, ~1.8M nps
- **Verified**: 100% perft pass (6/6 positions at depths 1-5, including 193M nodes Kiwipete)
- **TODO**: Move ordering (MVV-LVA, killer moves, history heuristic)

#### 3. **Make/Unmake** ✅ IMPLEMENTED & VERIFIED
- **Current**: make_move_numba, unmake_move_numba (100% reversible)
- **Features**: All special moves (castling, en passant, promotion)
- **Undo info**: Captured piece, old metadata, old fullmove
- **Performance**: O(1) bitboard updates, single array copy for state
- **Fixed**: EN PASSANT unmake bug (captured piece was restored twice)

#### 4. **Search** ✅ HIGHLY OPTIMIZED
- **File**: `engine/search.py` (739 lines)
- **Algorithm**: Negamax with alpha-beta pruning, iterative deepening
- **Optimizations Implemented**:
  - ✅ **Late Move Reductions (LMR)** - 16-61% node reduction ⭐
  - ✅ **History Heuristic** - 55-64% additional reduction ⭐⭐ (HUGE!)
  - ✅ **Futility Pruning** - 2k-6.5k moves pruned per position
  - ✅ **Reverse Futility Pruning** - 0-1.5k prunes (winning positions)
  - ✅ **Aspiration Windows** - 3-23% additional reduction at depth 5-6
  - ✅ **Check Extensions** - Search deeper when giving check
  - ✅ **Null move pruning** (R=2, 10-35% additional reduction)
  - ✅ **Quiescence search** (prevents horizon effect)
  - ✅ Delta pruning in qsearch (skip hopeless captures)
  - ✅ **Principal Variation (PV) extraction** - Display best line
  - ✅ Transposition table integration
  - ✅ Move ordering: TT move > captures > killers > history > others
  - ✅ Time management and mate detection
  - ✅ UCI-compatible info output
- **Performance**: 
  - **82-92% fewer nodes** vs baseline (COMBINED)
  - **Up to 3.6x speedup** with all optimizations
  - 10-40k NPS (position dependent)
  - Can search 2-3 plies deeper in same time
- **LMR Impact**: 29-864 reductions per position, 0-6.5% re-search rate
- **History Impact**: 90-15k history hits per position (exceptional ordering)
- **Futility Impact**: 2k-6.5k futile moves pruned per position
- **RFP Impact**: 0-1.5k prunes (position dependent, best in winning positions)
- **Aspiration Impact**: 1-3 re-searches per position (very efficient)
- **PV Display**: Shows thinking during search (UCI format)
- **TODO**: 
  - Internal iterative deepening (IID)
  - Razoring at pre-frontier nodes
  - Static Exchange Evaluation (SEE) for capture ordering

#### 5. **Evaluation** ✅ IMPLEMENTED
- **File**: `engine/evaluation.py` (240 lines)
- **Approach**: Material + piece-square tables (PST) with endgame detection
- **Features**:
  - Piece values: P=100, N=320, B=330, R=500, Q=900, K=20000 (centipawns)
  - PST for all piece types (white perspective, pre-flipped for black)
  - Separate king tables: middlegame (corner safety) vs endgame (centralization)
  - Endgame detection: total material < 2500 cp (roughly 2 minor pieces/side)
  - All @njit compiled for speed
- **Returns**: Score from current side's perspective (positive = good for side to move)
- **TODO**:
  - King safety (pawn shield, open files near king)
  - Pawn structure (doubled, isolated, passed pawns)
  - Mobility (legal move count, tempo)
  - Rook on open/semi-open files
  - Bishop pair bonus
  - Knight outposts
  - Optional: NNUE evaluation (neural network)

#### 6. **Zobrist Hashing** ✅ IMPLEMENTED & VERIFIED
- **Purpose**: Fast position hashing for transposition table
- **Implementation**: 793 uint64 keys (768 piece + 16 castling + 8 EP + 1 side)
- **Features**:
  - Incremental hash updates in make/unmake (XOR operations)
  - Store hash in state[14] (reserved slot)
  - Deterministic seed=0 for debugging
  - O(1) hash updates, verified with perft
- **Verified**: 100% hash consistency (make/unmake preserves hash, 8902 nodes tested)
- **Status**: Ready for transposition table implementation

#### 7. **Transposition Table (TT)** ✅ IMPLEMENTED
- **Implementation**: Hash table using Zobrist keys for position caching
- **Structure**: 16 bytes per entry (hash + move + depth + score + bound + age)
- **Size**: Configurable (16MB - 4GB), power-of-2 for fast indexing
- **Replacement**: Depth-preferred + age-based eviction
- **Features**:
  - probe() - retrieve cached results (with alpha/beta bounds)
  - store() - cache search results  
  - Fast JIT-compiled numba versions (tt_probe_fast, tt_store_fast)
  - Statistics tracking (hit rate, collisions, fill rate)
- **Status**: Ready for search integration (10-100x speedup potential)

#### 8. **Time Management** ⏳ TODO
- **Features needed**:
  - Time per move calculation
  - Hard/soft time limits
  - Increment handling
  - Move overhead compensation
  - Time saved in winning positions
  - Panic mode when low on time

#### 9. **UCI Protocol** ⏳ TODO
- **Commands**: uci, isready, ucinewgame, position, go, stop, quit
- **Info output**: depth, nodes, time, pv, score cp/mate, nps, hashfull
- **Options**: Hash, Threads, Ponder, MultiPV
- **Integration**: Allows use with GUIs (Arena, ChessBase, Lichess)

#### 10. **Opening Book** ⏳ OPTIONAL
- **Format**: Polyglot .bin or custom
- **Features**: Move selection (best, random, weighted)
- **Size**: 100KB-10MB typical
- **Performance**: Instant moves in opening

#### 11. **Endgame Tablebases** ⏳ OPTIONAL
- **Formats**: Syzygy (compressed), Gaviota
- **Probing**: WDL (win/draw/loss) or DTZ (distance to zero)
- **Storage**: 7-piece = ~19GB, 6-piece = ~1.2GB
- **Performance**: Perfect endgame play

---

### Key Metrics to Track

#### **A. CORRECTNESS** (Gate metrics - must pass)
1. **Perft Accuracy**
   - `perft(5)` from starting position = 4,865,609 nodes
   - Kiwipete `perft(5)` = 193,491,423 nodes
   - Endgame position `perft(6)` = verify
   - **Goal**: 100% match with reference (Stockfish perft)

2. **Move Legality**
   - No illegal moves generated
   - All legal moves found
   - Castling rules correct (not through check, rights tracking)
   - En passant correct (capture square, timing)
   - Promotion handling

3. **Position Integrity**
   - Make/unmake reversibility (state identical after unmake)
   - Zobrist hash consistency
   - FEN import/export round-trip

#### **B. SPEED** (Performance metrics)
1. **Nodes Per Second (NPS) - PERFT**
   - **Current**: ~2.0M nps (Python + Numba JIT)
   - **Status**: ✅ **TOP TIER for Python** (1-5M typical ceiling)
   - **Breakdown**: 74% move generation, 15% make/unmake, 11% overhead
   - **Optimized with**: Bitboards, magic attacks, pre-computed tables, Numba JIT
   
   **Performance Context:**
   - Pure Python: 50k-200k nps
   - Python + Numba (us): 2M nps ← **You are here**
   - C/C++/Rust: 10-100M nps
   - Stockfish (highly optimized C++): 50M+ nps
   
   **To reach 10-100M nps:** Rewrite core move generation in C/Rust with Python bindings
   - Cython: Helps ~20-50%, but still Python-limited (3-5M nps max)
   - C/Rust extension: Full speed, but requires rewrite (10-100M nps)
   - **Recommendation**: Current speed is excellent; focus on search quality over raw NPS

2. **Search Nodes Per Second** (with eval + TT)
   - Measure during alpha-beta search
   - **Expected**: 500k-1.5M nps (slower than perft due to eval overhead)
   - **Note**: Search NPS less important than effective branching factor reduction

3. **Move Generation Speed**
   - **Current**: 11-23μs per call (measured via profiling)
   - Simple positions: 11μs, Complex (Kiwipete): 23μs
   - **Already optimized**: Pre-computed tables, magic attacks, Numba JIT

4. **Make/Unmake Speed**
   - **Current**: ~100ns per operation (0.1μs, measured)
   - **Status**: ✅ Near-optimal (negligible overhead)

#### **C. STRENGTH** (Playing ability)
1. **Fixed-Depth ELO**
   - Test at depth 4, 5, 6
   - Play 100+ games vs rated opponents
   - **Baseline**: ~1200-1500 ELO (current)
   - **Target**: 2000+ ELO (with TT + better eval)

2. **Fixed-Time ELO**
   - 1s, 5s, 10s per move
   - More realistic than fixed-depth
   - Compare to engines at same time control

3. **CCRL Equivalent**
   - Standard testing conditions (40/4 time control)
   - Compare to engines on CCRL rating list

#### **D. TACTICAL PERFORMANCE**
1. **Tactical Puzzle Score**
   - Lichess puzzle database (mate in 1, 2, 3)
   - WAC (Win At Chess) test suite - 300 positions
   - **Goal**: 90%+ solved at reasonable depth

2. **Mate Finding**
   - Mate in 2: 100% at depth 4
   - Mate in 3: 100% at depth 6
   - Mate in 5: 80%+ at depth 10

3. **Sacrifice Recognition**
   - Find correct sacrifices (queen sac, exchange sac)
   - Avoid bad sacrifices
   - Track false positive/negative rate

#### **E. GAME QUALITY DIAGNOSTICS**
1. **Blunder Rate**
   - Moves losing >200cp (centipawns)
   - **Target**: <5% at depth 5+

2. **Average Centipawn Loss (ACPL)**
   - Compared to depth+2 analysis
   - **Target**: <30cp per move

3. **Move Agreement with Stockfish**
   - Top move match rate
   - Top-3 move match rate
   - **Target**: 60%+ top move at depth 5

4. **Draw Recognition**
   - Avoid drawn positions when winning
   - Accept draws when losing
   - Fifty-move rule handling

---

### Benchmarking Plan

#### **Level 1: Perft Gate** (Correctness - run on every change)
```python
# Fast, deterministic, catches bugs immediately
perft(starting_position, depth=5)  # ~5M nodes, <1 sec target
perft(kiwipete, depth=4)           # ~4M nodes
perft(endgame_pos, depth=5)        # ~10M nodes
# MUST match reference exactly (0 tolerance)
```

#### **Level 2: Deterministic Bench** (Speed - run daily)
```python
# Fixed-depth search on standard positions
positions = [starting, kiwipete, middle_game_1, middle_game_2, endgame_1]
for pos in positions:
    search(pos, depth=6)
    log(nodes, nps, time, pv)
# Compare metrics over time (regression detection)
```

#### **Level 3: Fast Self-Play** (Strength - run weekly)
```python
# Quick validation of playing strength
play_matches(
    engine_v1 vs engine_v2,
    games=50,
    time_control="1s per move",
    opening_book=standard
)
# Track win/draw/loss and ELO difference
```

#### **Level 4: Slower Confirmation** (Tournament - run before release)
```python
# Thorough strength test
play_tournament(
    opponents=[stockfish_level_3, gnuchess, crafty],
    games=100 per opponent,
    time_control="5+0.05",
    positions=diversified_opening_set
)
# Calculate ELO rating with confidence interval
```

---

### Logging Requirements (Fair Comparisons)

#### **System Configuration**
```yaml
hardware:
  cpu: "Intel i7-12700K" / "AMD Ryzen 9 5950X" / etc.
  cores: 8
  threads: 16
  ram: "32GB DDR4-3200"
  os: "Windows 11" / "Ubuntu 22.04" / etc.

engine_config:
  version: "v1.2.0"
  commit_hash: "a3f8d91"
  compilation_flags: "-O3 -march=native"
  python_version: "3.11.5"
  numba_version: "0.58.1"

search_config:
  threads: 1  # Single-threaded for baseline
  hash_size_mb: 256
  use_tablebase: false
  use_opening_book: false
  
time_control:
  type: "fixed_time" / "fixed_depth" / "tournament"
  base_time_sec: 300
  increment_sec: 3
  moves_to_go: 40  # for classical time controls
  
test_conditions:
  opening_set: "standard_20_positions"
  opponent: "stockfish_15.1_level_5"
  games_count: 100
  adjudication: "tb_3fold_50move"
```

#### **Per-Game Logging**
```python
game_log = {
    "game_id": "uuid",
    "white": "ChessAI-v1.2.0",
    "black": "Stockfish-15.1-L5",
    "result": "1-0",  # 1-0, 0-1, 1/2-1/2
    "termination": "checkmate" / "time" / "adjudication",
    "moves": "e2e4 e7e5 Ng1f3...",
    "final_position_fen": "...",
    "total_moves": 42,
    "white_time_used_ms": 145230,
    "black_time_used_ms": 152100,
}
```

#### **Per-Search Logging**
```python
search_stats = {
    "position_fen": "...",
    "depth_reached": 8,
    "nodes_searched": 1_234_567,
    "time_ms": 1500,
    "nps": 823_045,
    "best_move": "e2e4",
    "pv": ["e2e4", "e7e5", "Ng1f3", "Nb8c6"],
    "score_cp": 25,
    "tt_hits": 45_231,
    "tt_cutoffs": 12_445,
    "beta_cutoffs": 78_901,
    "qsearch_nodes": 234_567,
}
```

---

### Internal Instrumentation Counters

#### **Search Diagnostics**
```python
counters = {
    # Core metrics
    "nodes_searched": 0,           # Total nodes visited
    "qsearch_nodes": 0,            # Quiescence nodes
    "leaf_nodes": 0,               # Evaluation calls
    
    # Pruning efficiency
    "beta_cutoffs": 0,             # Alpha-beta cutoffs
    "beta_cutoffs_first_move": 0,  # First move caused cutoff
    "null_move_cutoffs": 0,        # Null move pruning success
    "lmr_reductions": 0,           # Late move reductions applied
    
    # Transposition table
    "tt_probes": 0,                # TT lookups
    "tt_hits": 0,                  # TT hit rate
    "tt_cutoffs": 0,               # TT caused cutoff
    "tt_overwrites": 0,            # Collisions/replacements
    
    # Move ordering
    "hash_move_first": 0,          # Hash move tried first
    "mvv_lva_applied": 0,          # MVV-LVA ordering used
    "killer_move_cutoffs": 0,      # Killer move success
    "history_move_cutoffs": 0,     # History heuristic success
    
    # Extensions
    "check_extensions": 0,         # Check extensions applied
    "pawn_extensions": 0,          # Passed pawn to 7th rank
    "recapture_extensions": 0,     # Recapture extensions
    
    # Time management
    "time_checks": 0,              # How often time checked
    "time_aborts": 0,              # Search aborted due to time
}

# Calculate derived metrics
def analyze_counters(c):
    return {
        "branching_factor": c["nodes_searched"] / max(1, c["leaf_nodes"]),
        "tt_hit_rate": c["tt_hits"] / max(1, c["tt_probes"]),
        "beta_cutoff_rate": c["beta_cutoffs"] / max(1, c["nodes_searched"]),
        "first_move_cutoff_rate": c["beta_cutoffs_first_move"] / max(1, c["beta_cutoffs"]),
        "qsearch_ratio": c["qsearch_nodes"] / max(1, c["nodes_searched"]),
    }
```

---

### Implementation Checklist

#### **Phase 1: Correctness Foundation** ✅ PARTIALLY COMPLETE
- [x] Perft test suite with standard positions
- [x] Move generation correctness (all legal moves found)
- [x] Make/unmake reversibility test
- [ ] FEN import/export round-trip validation
- [ ] Zobrist hashing implementation

#### **Phase 2: Speed Optimization** ⏳ IN PROGRESS
- [x] Bitboard representation
- [x] Numba compilation for hot paths
- [ ] Magic bitboards for sliding pieces
- [ ] Attack table pre-computation
- [ ] SIMD vectorization where applicable

#### **Phase 3: Search Enhancements** ⏳ TODO
- [ ] Transposition table (Zobrist hashing)
- [ ] Move ordering (hash move, MVV-LVA, killers, history)
- [ ] Iterative deepening
- [ ] Aspiration windows
- [ ] Null move pruning
- [ ] Late move reductions (LMR)
- [ ] Quiescence search

#### **Phase 4: Evaluation Improvements** ⏳ TODO
- [ ] King safety evaluation
- [ ] Pawn structure analysis
- [ ] Mobility and center control
- [ ] Piece coordination
- [ ] Optional: Neural network (NNUE)

#### **Phase 5: Integration & Testing** ⏳ TODO
- [ ] UCI protocol implementation
- [ ] Time management system
- [ ] Opening book integration (optional)
- [ ] Tablebase probing (optional)
- [ ] Automated benchmarking pipeline
- [ ] Continuous ELO tracking

---

## Architecture Overview

The chess engine is composed of several independent components that work together:

```
Chess Engine
│
├─► Board Representation (engine/board.py)
│   └─ 8x8 board state, piece positions, move execution
│
├─► Move Generation (engine/moves.py)
│   └─ Generates all legal moves, checks rules
│
├─► Position Evaluation (engine/evaluation.py)  
│   └─ Calculates position score (winning/losing bar)
│
└─► Search Algorithm (engine/search.py)
    └─ Looks ahead to find the best move
```

## Component Breakdown

### 1. **board.py** - The Chessboard 🎲 (BITBOARD IMPLEMENTATION)
**Architecture:**
- **Bitboards**: 12 × uint64 (one per piece type/color) + occupied bitboard
- **State**: Pure numpy array (20 × uint64 = 160 bytes total)
- **Metadata**: Packed into single uint64 (castling | ep_square | halfmove | side)
- **All numba**: Every function compiled with @njit for zero Python overhead
- **Minimal OOP**: Board class is just a 50-line wrapper around numba functions

**What it does:**
- Represents board as bitboards (64-bit integers, 1 bit per square)
- Vectorized bit operations (set_bit, clear_bit, pop_count, lsb)
- Pre-computed attack tables for non-sliding pieces (knight, king, pawn)
- Classical sliding piece attacks (rook, bishop, queen) - magic bitboards coming
- Executes moves with pure numba functions (make_move/unmake_move)
- Handles special rules (castling, en passant, promotion)
- State copy is single array copy (~160 bytes)

**Performance characteristics:**
- **State size**: 160 bytes (19x smaller than old implementation)
- **Copy speed**: O(1) - single numpy array copy
- **Bit operations**: O(1) - inlined numba, ~1-2 CPU cycles
- **Attack generation**: O(rays) - ~10ns per piece (classical), ~2ns with magic
- **SIMD ready**: Numpy arrays support vectorization

**Key design principles:**
1. **Zero Python overhead**: All hot paths in numba
2. **Cache-friendly**: Contiguous memory (20 × 8 bytes)
3. **Vectorized**: Bit manipulation instead of loops
4. **NN-ready**: Easy to add history planes (indices 14-19 reserved)

**Key methods:**
- `Board()` - Create starting position (or empty board)
- `copy()` - O(1) deep copy
- `display()` - ASCII visualization
- Properties: `current_player`, `castling_rights`, `en_passant_target`, `halfmove_clock`

---

### 2. **moves.py** - The Move Generator ♟️
**What it does:**
- Generates all pseudo-legal moves for each piece type
- Filters out moves that would leave king in check
- Detects check, checkmate, and stalemate
- Validates move legality
- Implements piece-specific movement patterns

**What it does NOT do:**
- Does not evaluate if moves are "good" or "bad"
- Does not pick which move to play
- Does not search ahead

**Key methods:**
- `generate_legal_moves()` - Get all legal moves in position
- `is_in_check(color)` - Check if king is in check
- `is_checkmate()` / `is_stalemate()` - Game over detection

**Performance:**
- Generates ~20-50 moves per position on average
- Perft(3) from initial position: 8,902 nodes ✓
- Critical for engine speed - optimizing this gives major gains

---

### 3. **evaluation.py** - The Evaluator 📊
**What it does:**
- **Calculates the winning/losing evaluation bar**
- Counts material (piece values: P=100, N=320, B=330, R=500, Q=900)
- Uses piece-square tables (rewards good piece placement)
- Returns a score where:
  - Positive score = White is winning
  - Negative score = Black is winning
  - 0 = Equal position
  - +500 = White is up ~5 pawns worth of material

**What it does NOT do:**
- Does not pick moves
- Does not look ahead at future positions
- Just evaluates the CURRENT position

**Key methods:**
- `evaluate(board)` - Returns position score
- `material_eval(board)` - Count piece material
- `positional_eval(board)` - Piece-square table bonus

**Current implementation:**
- Uses numpy arrays for speed
- Piece-square tables for positional understanding
- Can be extended with king safety, pawn structure, mobility, etc.

---

### 4. **search.py** - The Chess Engine (The Brain) 🚀
**What it does:**
- **THIS IS THE ACTUAL ENGINE - picks the best move to play**
- Looks ahead multiple moves into the future (depth 4-6 typically)
- Uses minimax algorithm with alpha-beta pruning
- Evaluates each possible move by:
  1. Making the move
  2. Recursively searching opponent's responses
  3. Using the evaluator to score leaf positions
  4. Backing up the best score
- Returns the move with the highest evaluation

**Algorithm (Minimax with Alpha-Beta):**
```
For each possible move:
  1. Make the move
  2. Search opponent's best response (recursive)
  3. Then our counter-response (recursive)
  4. Continue for 'depth' moves ahead
  5. At the end, use evaluator to score position
  6. Back up the score through the tree
Pick the move with the best score
```

**What it does NOT do:**
- Does not directly calculate evaluation scores (uses evaluation.py)
- Does not generate moves (uses moves.py)

**Key methods:**
- `find_best_move(board, time_limit)` - Main entry point, returns best move
- `_alpha_beta(board, depth, alpha, beta)` - Recursive search
- `_order_moves(moves)` - Sort moves for better pruning

**Current capabilities:**
- Searches 4-6 ply (half-moves) deep
- Alpha-beta pruning for efficiency
- Iterative deepening (search depth 1, then 2, then 3...)
- Node limit to prevent excessive computation

**Performance bottlenecks:**
- Board copying (done for each move tried)
- No transposition table (re-evaluates same positions)
- Time management needs fixing
- Move ordering could be better

---

## How They Work Together

When you ask the engine to find a move:

```python
# 1. Create the engine
engine = ChessEngine(depth=4)

# 2. Find best move (this is the entry point)
best_move, score = engine.find_best_move(board)

# Inside find_best_move():
#   3. Get all legal moves
moves = MoveGenerator(board).generate_legal_moves()  # moves.py

#   4. Try each move
for move in moves:
    #   5. Make the move
    board_copy = board.copy()  # board.py
    board_copy.make_move(move)  # board.py
    
    #   6. Search deeper (recursive minimax)
    #      This tries opponent's moves, then our responses, etc.
    score = search_recursively(board_copy, depth - 1)
    
    #   7. At depth 0, evaluate the position
    eval_score = Evaluator().evaluate(board_copy)  # evaluation.py
    
    #   8. Back up the score through the tree

#   9. Return the move with the best score
return best_move
```

---

## Project Structure

```
Chess-AI/
├── engine/                 # Core chess engine
│   ├── board.py           # Board representation (467 lines)
│   ├── moves.py           # Legal move generation
│   ├── evaluation.py      # Position evaluation (evaluation bar)
│   └── search.py          # Search algorithm (picks best move)
└── tests/                 # Unit tests (28/29 passing)
    ├── test_moves.py      # Move generation tests
    └── test_search.py     # Search algorithm tests
```

---

## Current Status

**Test Results:** 28/29 tests passing (96.5%)
- ✅ All move generation tests passing
- ✅ All evaluation tests passing
- ✅ Checkmate detection working
- ❌ Time limit test failing (needs fix)

**Performance:**
- ~50K nodes per second (estimated)
- Searches 4-6 ply deep
- Playing strength: ~1500 ELO (estimated)

---

## What Each File Does (Quick Reference)

| File | Purpose | What it Returns | Used By |
|------|---------|-----------------|---------|
| **board.py** | Board state | Current position | All modules |
| **moves.py** | Legal moves | List of moves | search.py |
| **evaluation.py** | Position score | +/- number | search.py |
| **search.py** | Best move | Move to play | Your app |

---

## Key Optimization Opportunities

1. **Transposition Table** (search.py)
   - Cache position evaluations
   - 10-100x speedup potential
   - Currently re-evaluating same positions

2. **Better Move Ordering** (search.py)
   - Try best moves first
   - Better alpha-beta cutoffs
   - 2-3x speedup

3. **Bitboards** (board.py rewrite)
   - Represent board as 64-bit integers
   - Much faster move generation
   - 10x speedup potential

4. **Enhanced Evaluation** (evaluation.py)
   - Add king safety
   - Pawn structure analysis
   - Mobility evaluation
   - +200-300 ELO improvement

---

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

### Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/DanielLFS/Chess-AI.git
   cd Chess-AI
   ```

2. **Create virtual environment** (recommended)
   ```powershell
### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/DanielLFS/Chess-AI.git
   cd Chess-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Example

```python
from engine.board import Board
from engine.search import ChessEngine
from engine.moves import MoveGenerator

# Create a new game
board = Board()
engine = ChessEngine(max_depth=4)

# Get best move
move, score = engine.find_best_move(board)
print(f"Best move: {move}, Evaluation: {score/100:.2f}")

# Make the move
board.make_move(move)
print(board.display())
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_moves.py

# Run with coverage
python -m pytest --cov=engine tests/
```

## Testing & Validation

**Test Results:** 28/29 tests passing (96.5%)

**Perft Tests** (validates move generation):
- Initial position Perft(3) = 8,902 nodes ✓
- Kiwipete Perft(2) = 2,039 nodes ✓

## Contributing

This is an educational project. Contributions and suggestions welcome!

## License

MIT License

## Author

**Daniel**
- GitHub: [@DanielLFS](https://github.com/DanielLFS)
- Repository: [Chess-AI](https://github.com/DanielLFS/Chess-AI)

---

**Built for learning chess engine architecture and optimization techniques.**
- [x] Move generation
- [x] Basic evaluation
- [x] Minimax + alpha-beta
- [x] Database schema

### Phase 2: Web Interface (In Progress)
- [ ] Flask backend API
- [ ] Interactive chessboard UI
- [ ] Real-time game analysis
- [ ] Move history and replay

### Phase 3: Advanced Features
- [ ] Transposition table
- [ ] Quiescence search
- [ ] Opening book
- [ ] Endgame tablebases
- [ ] Time management

### Phase 4: Optimization
- [ ] C++ move generation
- [ ] Bitboard representation
- [ ] Parallel search
- [ ] Neural network evaluation

### Phase 5: Analytics Dashboard
- [ ] Performance visualization
- [ ] Opening repertoire analysis
- [ ] AI vs AI tournaments
- [ ] ELO rating system

## 📈 Key Metrics for CV

- **Lines of Code**: 3,000+ (Python core)
- **Test Coverage**: 80%+ target
- **Database Tables**: 7 tables with relationships
- **Algorithms Implemented**: Minimax, alpha-beta, iterative deepening, MVV-LVA
- **Performance**: Configurable strength (ELO 1000-2200+)

## 🤝 Contributing

This is a portfolio project, but suggestions and feedback are welcome!

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

**Daniel**
- GitHub: [@DanielLFS](https://github.com/DanielLFS)

## 🙏 Acknowledgments

- Chess programming community for algorithms and techniques
- Stockfish for reference implementation ideas
- UCI protocol for standard chess engine interface

---

## 📚 Technical Documentation

### Move Generation Algorithm
The engine uses a pseudo-legal move generator followed by legality checking:
1. Generate all pseudo-legal moves for each piece
2. Filter moves that would leave king in check
3. Apply move ordering for better alpha-beta efficiency

### Evaluation Function
```
Evaluation = Material + Position + Mobility + King Safety + Pawn Structure

Material: Piece values (P=100, N=320, B=330, R=500, Q=900)
Position: Piece-square tables reward good piece placement
```

### Search Algorithm
```
function alpha_beta(position, depth, α, β, maximizing):
    if depth = 0 or terminal:
        return evaluate(position)
    
    if maximizing:
        for each move in ordered_moves(position):
            score = alpha_beta(make_move(move), depth-1, α, β, false)
            α = max(α, score)
            if β ≤ α: break  # Beta cutoff
        return α
```

## 🔬 Research & Analysis

### SQL Analytics Queries

**Opening Performance**:
```sql
SELECT opening_eco, opening_name, 
       AVG(total_moves) as avg_length,
       COUNT(*) as games_played
FROM games
GROUP BY opening_eco
ORDER BY games_played DESC;
```

**Search Efficiency Over Time**:
```sql
SELECT date_played, 
       AVG(nodes_searched) as avg_nodes,
       AVG(alpha_beta_cutoffs) as avg_cutoffs
FROM search_statistics
JOIN games ON search_statistics.game_id = games.game_id
GROUP BY DATE(date_played);
```

### Performance Metrics Tracked
- Nodes per second (NPS)
- Alpha-beta cutoff efficiency
- Transposition table hit rate
- Average branching factor
- Evaluation accuracy vs tactical puzzles

---

## 📁 File Overview

### Core Engine (engine/)
| File | Lines | Description | Status |
|------|-------|-------------|--------|
| `board.py` | 1044 | Bitboard representation, make/unmake moves, null moves | ✅ Complete |
| `moves.py` | 422 | Move generation (perft verified) | ✅ Complete |
| `evaluation.py` | 240 | Material + PST evaluation | ✅ Complete |
| `search.py` | 739 | LMR + history + futility + RFP + aspiration + PV | ✅ Highly Optimized |
| `transposition.py` | 258 | Zobrist hash table | ✅ Complete |

### Tests (tests/)
| File | Description | Status |
|------|-------------|--------|
| `perft.py` | Move generation verification (100% pass) | ✅ Passing |
| `test_search.py` | Search engine tests (4 positions) | ✅ Passing |
| `test_tt.py` | Transposition table tests | ✅ Passing |
| `test_zobrist.py` | Hash consistency tests | ✅ Passing |
| `profile_perft.py` | Performance profiling | ✅ Working |
| `analyze_perft.py` | Detailed timing analysis | ✅ Working |

**Total engine code: ~2,437 lines**  
**Total test code: ~500 lines** (including benchmarks)

---

**Built with ❤️ for learning and exploration**