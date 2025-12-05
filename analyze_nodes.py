"""
Analyze nodes searched per depth to understand search efficiency.
"""

from engine.board import Board, Color
from engine.search import ChessEngine

# Starting position
board = Board()

# Create engine with different depths
for depth in range(1, 7):
    print(f"\n{'='*60}")
    print(f"Analyzing Depth {depth}")
    print(f"{'='*60}")
    
    engine = ChessEngine(max_depth=depth, use_iterative_deepening=False)
    engine.stats.start_time = __import__('time').time()
    
    best_move, score = engine.find_best_move(board)
    
    stats = engine.stats.to_dict()
    elapsed = __import__('time').time() - engine.stats.start_time
    
    print(f"Nodes searched: {stats['nodes_searched']:,}")
    print(f"Positions evaluated: {stats['positions_evaluated']:,}")
    print(f"Beta cutoffs: {stats['alpha_beta_cutoffs']:,}")
    print(f"Cache hits: {stats['cache_hits']:,}")
    print(f"Time: {elapsed:.2f}s")
    print(f"NPS: {stats['nodes_per_second']:,.0f}")
    print(f"Score: {score}")
    
    if depth > 1:
        prev_depth = depth - 1
        # Rough branching factor estimate
        if 'prev_nodes' in locals():
            branching = stats['nodes_searched'] / prev_nodes if prev_nodes > 0 else 0
            print(f"Branching factor from depth {prev_depth}: {branching:.1f}x")
    
    prev_nodes = stats['nodes_searched']

print(f"\n{'='*60}")
print("Analysis complete")
print(f"{'='*60}")
