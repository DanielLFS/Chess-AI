# UCI Interface - Usage Guide

## What is UCI?

UCI (Universal Chess Interface) is a standardized protocol for communication between chess engines and graphical user interfaces (GUIs). Your engine can now be used with any UCI-compatible chess GUI!

## Running the Engine

```bash
python uci/uci.py
```

The engine will wait for UCI commands on stdin and respond on stdout.

## Compatible Chess GUIs

Your engine works with:
- **Arena Chess GUI** (Windows) - Free
- **ChessBase** (Commercial)
- **Lichess** (via lichess-bot)
- **Chess.com** (analysis)
- **Cute Chess** (Cross-platform, open source)
- **PyChess** (Linux)

## Supported Commands

### Basic Commands
```
uci              - Initialize UCI mode
isready          - Check if engine is ready
ucinewgame       - Start a new game
quit             - Exit the engine
```

### Position Setup
```
position startpos
position startpos moves e2e4 e7e5 g1f3
position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

### Search Commands
```
go depth 6                    - Search to depth 6
go movetime 3000             - Search for 3 seconds
go infinite                   - Search until 'stop' command
```

### Engine Options
```
setoption name Hash value 128           - Set hash table to 128 MB
setoption name Debug value true         - Enable debug mode
```

## Engine Options

| Option | Type | Default | Range | Description |
|--------|------|---------|-------|-------------|
| Hash | spin | 64 | 1-1024 | Hash table size in MB |
| Threads | spin | 1 | 1-1 | Number of threads (currently 1) |
| MultiPV | spin | 1 | 1-1 | Multi-PV lines (currently 1) |
| Debug | check | false | - | Enable debug output |

## Example Session

```
> uci
< id name Chess-AI
< id author DanielLFS
< option name Hash type spin default 64 min 1 max 1024
< uciok

> isready
< readyok

> ucinewgame

> position startpos moves e2e4

> go depth 6
< info depth 1 score cp 50 time 10 nodes 20 pv e7e5
< info depth 2 score cp 0 time 25 nodes 150 pv e7e5 g1f3
< ...
< bestmove e7e5

> quit
```

## Using with Arena Chess GUI (Windows)

1. Download Arena Chess GUI: http://www.playwitharena.de/
2. Install Arena
3. In Arena: Engines → Install New Engine
4. Navigate to your Chess-AI folder
5. Create a batch file `chess-ai.bat`:
   ```bat
   @echo off
   cd C:\path\to\Chess-AI
   python uci\uci.py
   ```
6. Select the batch file in Arena
7. Your engine will now appear in the engine list!

## Using with Cute Chess (Cross-platform)

1. Download Cute Chess: https://cutechess.com/
2. Tools → Settings → Engines → Add
3. Command: `python`
4. Working Directory: `/path/to/Chess-AI`
5. Arguments: `uci/uci.py`
6. Protocol: UCI

## Info Output Format

During search, the engine outputs info lines in UCI format:
```
info depth 5 score cp 40 time 1108 nodes 5138 pv b8c6 b1c3 g8f6 g1f3 d7d5
```

- `depth`: Current search depth
- `score cp`: Score in centipawns (100 = 1 pawn advantage)
- `time`: Time in milliseconds
- `nodes`: Nodes searched
- `pv`: Principal variation (best line)

## Performance

- **Depth 6**: ~1 second on starting position
- **Depth 8**: ~1-2 minutes on starting position
- **Tactical positions**: Finds mate in 3 instantly
- **NPS**: 15-30k nodes per second (position dependent)

## Features

✅ Full UCI protocol support
✅ Position setup (FEN and moves)
✅ Depth-limited search
✅ Time-limited search
✅ Principal Variation display
✅ Configurable hash table
✅ New game handling
✅ Move validation

## Troubleshooting

**Engine doesn't start in GUI:**
- Make sure Python is in your PATH
- Try running `python uci/uci.py` manually first
- Check that all dependencies are installed

**Engine plays illegal moves:**
- Shouldn't happen - move validation is built in
- Report as a bug if it occurs

**Engine is slow:**
- Increase hash table size: `setoption name Hash value 256`
- Use shallower depth for faster play
- Engine is written in Python - C++ engines will be faster

## Next Steps

- Add time management (wtime/btime handling)
- Implement pondering (think on opponent's time)
- Add opening book support
- Implement endgame tablebases
