"""Test AI move quality to diagnose issues"""

from engine.board import Board
from engine.search import ChessEngine
from engine.moves import MoveGenerator

# Test with a fresh game
board = Board()

print("Testing AI at different depths from starting position...")
print("=" * 60)

for depth in range(1, 7):
    engine = ChessEngine(max_depth=depth, use_quiescence=True, use_iterative_deepening=False)
    
    print(f"\nDepth {depth}:")
    move, score = engine.find_best_move(board, time_limit=None)  # NO TIME LIMIT
    
    if move:
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        from_square = chr(ord('a') + from_col) + str(8 - from_row)
        to_square = chr(ord('a') + to_col) + str(8 - to_row)
        
        print(f"  Best move: {from_square}{to_square}")
        print(f"  Score: {score:.2f}")
        print(f"  Nodes searched: {engine.stats.nodes_searched}")
        print(f"  Time: {engine.stats.nodes_searched / max(engine.stats.get_nodes_per_second(), 1):.2f}s")
    else:
        print("  ERROR: No move found!")

print("\n" + "=" * 60)
print("Expected good opening moves: e2e4, d2d4, g1f3, b1c3")
print("Bad moves that indicate issues: a2a3, b2b3, c2c3, h2h3")
