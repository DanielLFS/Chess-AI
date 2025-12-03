# Chess Engine

A chess engine built from scratch in Python with complete move generation, position evaluation, and search algorithms.

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

### 1. **board.py** - The Chessboard 🎲
**What it does:**
- Represents the 8x8 chess board as a 2D array
- Stores where all pieces are located
- Executes moves and updates the board
- Handles special rules (castling, en passant, promotion)
- Converts to/from FEN notation
- Tracks game state (whose turn, castling rights, etc.)

**What it does NOT do:**
- Does not decide which moves are legal
- Does not calculate who's winning
- Does not pick moves to play

**Key methods:**
- `make_move(move)` - Execute a move on the board
- `copy()` - Create a copy for trying moves
- `to_fen()` / `load_from_fen()` - FEN import/export
- `get_piece(position)` - Get piece at a square

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

**Built with ❤️ for learning and exploration**