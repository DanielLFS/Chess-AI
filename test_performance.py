"""Performance test with node limits"""

from engine.board import Board
from engine.search import ChessEngine
import time

board = Board()

print("Performance Test with Node Limits")
print("=" * 70)

# Test different node limits
test_configs = [
    (3, 2000, "Medium - 1400 ELO"),
    (4, 50000, "Hard - 2000 ELO"),
    (5, 200000, "Expert - 2200 ELO"),
    (6, 500000, "Master - 2400 ELO"),
]

for depth, max_nodes, label in test_configs:
    engine = ChessEngine(max_depth=depth, use_quiescence=True, 
                        use_iterative_deepening=True, max_nodes=max_nodes)
    
    print(f"\n{label} (Depth {depth}, Max Nodes: {max_nodes:,})")
    print("-" * 70)
    
    start = time.time()
    move, score = engine.find_best_move(board, time_limit=30.0)
    elapsed = time.time() - start
    
    if move:
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        from_square = chr(ord('a') + from_col) + str(8 - from_row)
        to_square = chr(ord('a') + to_col) + str(8 - to_row)
        
        print(f"  Move: {from_square}{to_square}")
        print(f"  Score: {score:.2f}")
        print(f"  Nodes: {engine.stats.nodes_searched:,}")
        print(f"  Depth reached: {engine.stats.depth_reached}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  NPS: {int(engine.stats.nodes_searched / elapsed):,}")
        
        hit_limit = "NODE LIMIT" if engine.stats.nodes_searched >= max_nodes else "TIME LIMIT" if elapsed >= 29.5 else "COMPLETE"
        print(f"  Status: {hit_limit}")
    else:
        print("  ERROR: No move found!")

print("\n" + "=" * 70)
print("Test complete! Node limits provide consistent timing.")

for depth in range(1, 6):
    engine = ChessEngine(max_depth=depth, use_quiescence=True, use_iterative_deepening=False)
    
    start = time.time()
    move, score = engine.find_best_move(board, time_limit=None)
    elapsed = time.time() - start
    
    from_row, from_col = move.from_pos
    to_row, to_col = move.to_pos
    from_sq = chr(ord('a') + from_col) + str(8 - from_row)
    to_sq = chr(ord('a') + to_col) + str(8 - to_row)
    
    nps = engine.stats.nodes_searched / elapsed if elapsed > 0 else 0
    
    print(f"\nDepth {depth}: {from_sq}{to_sq} (score: {score:.1f})")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Nodes: {engine.stats.nodes_searched:,}")
    print(f"  NPS: {nps:,.0f}")
    print(f"  Evals: {engine.stats.positions_evaluated:,}")
    print(f"  Cutoffs: {engine.stats.alpha_beta_cutoffs:,}")
    if engine.stats.quiescence_nodes > 0:
        print(f"  Quiescence: {engine.stats.quiescence_nodes:,}")

print("\n" + "=" * 70)
print("Target: >10,000 NPS for good performance")
print("Expected: Depth 4 should complete in ~3-5 seconds")
