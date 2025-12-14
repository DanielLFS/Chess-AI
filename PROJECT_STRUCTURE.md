# Chess Engine - Project Structure

## Directory Layout

```
Chess-AI/
├── engine/              # Core chess engine
│   ├── board.py         # ✅ Bitboard board representation (1009 lines)
│   ├── moves.py         # ✅ Move generation (422 lines, perft verified)
│   ├── evaluation.py    # ✅ Material + PST evaluation (240 lines)
│   ├── search.py        # ✅ Negamax with alpha-beta pruning (321 lines)
│   ├── transposition.py # ✅ Hash table with Zobrist keys (258 lines)
│   └── tables/          # Pre-computed lookup tables
│
├── tests/               # Test suite
│   ├── perft.py         # ✅ Move generation verification (100% pass)
│   ├── profile_perft.py # ✅ Performance profiling
│   ├── analyze_perft.py # ✅ Detailed timing analysis
│   ├── test_zobrist.py  # ✅ Hash consistency tests
│   ├── test_tt.py       # ✅ Transposition table tests
│   └── test_search.py   # ✅ Search engine tests
│
├── uci/                 # UCI protocol (TODO)
├── neural/              # NNUE evaluation (TODO)
├── README.md            # Full documentation
└── requirements.txt     # Dependencies (numpy, numba)
```

## Performance Metrics

**Move Generation (perft):**
- Kiwipete depth 5: 193,690,690 nodes in 102s (~2.0M nps)
- Position 6 depth 5: 164,075,551 nodes in 87s (~1.9M nps)
- **Status**: ✅ 100% pass rate (6/6 positions, depths 1-5)

**Search with Evaluation:**
- Starting position: e2e4, 70 cp, 4.5k NPS (depth 5)
- After 1.e4: b8c6, 90 cp, 38k NPS (depth 5)
- Kiwipete: e2a6, 50 cp, 22k NPS (depth 4)
- Endgame: b4f4, -20 cp, 43k NPS (depth 6)
- **NPS varies by position complexity (4-43k typical)**

**Transposition Table:**
- Size: 64MB (configurable)
- Hit rate: 10-30% typical in search
- Entry: 16 bytes (hash + move + depth + score + bound + age)

## Implementation Status

### ✅ COMPLETED

**Core Engine:**
- Bitboard representation (12 × uint64 for pieces)
- Pure numpy state array (20 × uint64 = 160 bytes)
- Move generation (all piece types, castling, en passant, promotion)
- Make/unmake moves (100% reversible, tested with perft)
- Legal move filtering (removes moves leaving king in check)
- Check/checkmate/stalemate detection

**Zobrist Hashing:**
- 793 uint64 keys (768 piece + 16 castling + 8 EP + 1 side)
- Incremental updates (O(1) XOR operations)
- 100% hash consistency verified

**Transposition Table:**
- Hash table with depth-preferred + age-based replacement
- Supports EXACT, LOWER_BOUND, UPPER_BOUND entries
- Fast probe/store with JIT compilation

**Search Engine:**
- Negamax with alpha-beta pruning
- Iterative deepening (depth 1 to max)
- Move ordering: TT move > MVV-LVA captures > killer moves
- Time management with early exit
- Mate distance scoring

**Evaluation:**
- Material values (P=100, N=320, B=330, R=500, Q=900, K=20000 cp)
- Piece-square tables (PST) for all pieces
- Endgame detection (< 2500 cp total material)
- Separate king tables: middlegame (corner) vs endgame (center)
- Numba JIT compiled for speed

### 🚧 TODO

**Search Improvements:**
- Null move pruning (big speedup)
- Late move reductions (LMR)
- Quiescence search (tactical stability)
- Aspiration windows
- Check extensions
- Principal variation (PV) extraction

**Evaluation Improvements:**
- King safety (pawn shield, open files)
- Pawn structure (doubled, isolated, passed)
- Mobility (legal move count)
- Rook on open files
- Bishop pair bonus
- Knight outposts

**Infrastructure:**
- Magic bitboards (5x faster sliding attacks)
- UCI protocol implementation
- Opening book
- Endgame tablebases
- NNUE neural network evaluation
