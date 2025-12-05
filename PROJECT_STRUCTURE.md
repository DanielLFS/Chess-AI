# Chess Engine - Project Structure

## Directory Layout

```
Chess-AI/
├── engine/              # Core chess engine
│   ├── board.py         # Bitboard board representation
│   ├── moves.py         # Move generation (magic bitboards)
│   ├── evaluation.py    # Position evaluation
│   ├── search.py        # Alpha-beta search with pruning
│   ├── transposition.py # Transposition table
│   ├── movepicker.py    # Move ordering heuristics
│   ├── timeman.py       # Time management
│   └── tables/          # Pre-computed lookup tables (11KB)
│       ├── *.npy        # Binary NumPy arrays
│       └── generation/  # Table generation scripts
│
├── tests/               # Test suite
├── uci/                 # UCI protocol (placeholder)
├── neural/              # NNUE evaluation (placeholder)
└── count_nodes.py       # Node counting utility
```

## Performance Metrics

**Theoretical nodes (pure minimax):**
- Depth 5: 4,865,652 nodes

**With alpha-beta pruning:**
- Depth 5: 276,856 nodes (94% reduction)

**With full optimizations (TT + move ordering):**
- Depth 5: ~6,000 nodes (99.9% reduction)
- Speed: 2,500-10,000 NPS

## Key Features

✅ Bitboard representation (12 bitboards)  
✅ Magic bitboard move generation  
✅ Alpha-beta pruning with quiescence  
✅ Transposition table (128MB default)  
✅ Move ordering (killers, history, countermoves)  
✅ Incremental zobrist hashing  
✅ Tapered evaluation (midgame/endgame)  
✅ Time management  

## Future Work

- UCI protocol implementation
- NNUE neural network evaluation
- Search extensions (null move, LMR, etc.)
- Opening book
- Endgame tablebases
