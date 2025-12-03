# Chess AI Engine

A high-performance chess engine built from scratch in Python with optional C++ extensions, featuring comprehensive analytics, SQL database integration, and a web-based interface.

## 🎯 Project Goals

- **Scientific Exploration**: Analyze AI decision-making and chess strategy through data
- **Performance Optimization**: Scalable architecture supporting competitive play
- **Data Analytics**: SQL-based game storage and analysis for research insights
- **CV-Ready**: Demonstrates full-stack development, algorithms, databases, and optimization

## 🚀 Features

### Core Engine
- ♟️ **Complete Chess Rules**: All piece moves, castling, en passant, promotion
- 🧠 **Advanced AI Search**: Minimax with alpha-beta pruning, iterative deepening
- 📊 **Position Evaluation**: Material counting + piece-square tables + positional factors
- ⚡ **Performance**: Configurable depth (1-20+ ply), optimized move ordering
- 🎯 **Scalable Strength**: From beginner (ELO ~1000) to advanced (2000+)

### Database & Analytics
- 📁 **SQL Database**: Store games, moves, positions, and performance metrics
- 📈 **Rich Analytics**: Opening statistics, blunder detection, search efficiency
- 🔍 **Position Caching**: Transposition table for repeated positions
- 📊 **Performance Tracking**: Nodes/second, cache hit rates, alpha-beta cutoffs

### Web Interface
- 🌐 **Web-based UI**: Play against AI via browser (Flask backend)
- 📱 **Real-time Analysis**: Live evaluation scores and principal variations
- 🎮 **Adjustable Difficulty**: Multiple engine configurations
- 📉 **Visualization**: Move-by-move evaluation graphs

## 📂 Project Structure

```
Chess-AI/
├── engine/              # Core chess engine
│   ├── board.py        # Board representation, FEN, move application
│   ├── moves.py        # Legal move generation
│   ├── evaluation.py   # Position evaluation function
│   └── search.py       # Minimax + alpha-beta search
├── database/           # SQL database layer
│   ├── models.py       # SQLAlchemy ORM models
│   ├── schema.sql      # Database schema
│   └── queries.py      # Analytics queries
├── web/                # Web interface
│   ├── app.py          # Flask application
│   ├── static/         # JavaScript, CSS
│   └── templates/      # HTML templates
├── analysis/           # Analytics and visualization
│   ├── game_analyzer.py
│   ├── metrics.py
│   └── visualizations.py
├── tests/              # Test suite
│   ├── test_moves.py   # Move generation tests
## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DanielLFS/Chess-AI.git
   cd Chess-AI
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

**Start the application:**
```bash
python run.py
```

Then open your browser and navigate to: **http://127.0.0.1:5000**

## How to Play

1. Click "Start New Game"
2. Choose your color (White, Black, or Random)
3. Make moves by:
   - **Click** on a piece, then click on a destination square
   - **Drag and drop** pieces to move them
4. The evaluation bar shows who has the advantage
5. Watch your ELO rating update based on move quality
6. Use the action buttons to:
   - Flip the board view
   - Export the game as PGN
   - Load a position from FEN
   - Analyze the game moves

## Technologies Used

- **Backend**: Python 3.13, Flask 3.0
- **Frontend**: Vanilla JavaScript (ES6), HTML5, CSS3
- **Chess Engine**: Custom implementation with numpy/numba optimization
- **Styling**: Modern CSS with gradients, animations, and responsive design

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_moves.py

# Run with coverage
python -m pytest --cov=engine tests/
```

### Code Structure

- **engine/board.py**: Handles board state, piece positions, move execution
- **engine/moves.py**: Legal move generation, check/checkmate detection
- **engine/evaluation.py**: Position evaluation using piece values and position tables
- **web/app.py**: Flask routes and game state management
- **web/static/js/chess.js**: Frontend game logic and UI interactions

## Future Enhancements (Roadmap)

- [ ] Add AI opponents with various difficulty levels
- [ ] Online multiplayer support
- [ ] Game database for storing and replaying games
- [ ] Opening book integration
- [ ] Endgame tablebases
- [ ] Advanced analysis features
- [ ] Chess puzzles
- [ ] User accounts and rating history

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

- GitHub: [@DanielLFS](https://github.com/DanielLFS)
- Repository: [Chess-AI](https://github.com/DanielLFS/Chess-AI)

---

**Enjoy playing chess!** ♟️
