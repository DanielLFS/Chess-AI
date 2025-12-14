"""
Benchmark search performance with and without optimizations.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from engine.board import Board
from engine.search import Search


def benchmark_position(fen: str, name: str, depth: int = 5):
    """Benchmark a position."""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"{'='*70}")
    
    board = Board(fen=fen)
    
    # Test with all optimizations
    print("\n[WITH LMR + NULL MOVE + QUIESCENCE]")
    search_opt = Search(tt_size_mb=64, use_null_move=True, use_lmr=True)
    start = time.time()
    move_opt, score_opt = search_opt.search(board, depth=depth, time_limit=30.0)
    time_opt = time.time() - start
    
    print(f"Time: {time_opt:.2f}s")
    print(f"Score: {score_opt}")
    print(f"{search_opt.stats}")
    print(f"Nodes searched: {search_opt.stats.nodes:,}")
    print(f"QNodes: {search_opt.stats.qnodes:,}")
    print(f"Total nodes: {search_opt.stats.nodes + search_opt.stats.qnodes:,}")
    
    # Test without LMR
    print("\n[WITHOUT LMR (null move + quiescence only)]")
    board2 = Board(fen=fen)
    search_basic = Search(tt_size_mb=64, use_null_move=True, use_lmr=False)
    start = time.time()
    move_basic, score_basic = search_basic.search(board2, depth=depth, time_limit=30.0)
    time_basic = time.time() - start
    
    print(f"Time: {time_basic:.2f}s")
    print(f"Score: {score_basic}")
    print(f"{search_basic.stats}")
    print(f"Nodes searched: {search_basic.stats.nodes:,}")
    print(f"QNodes: {search_basic.stats.qnodes:,}")
    print(f"Total nodes: {search_basic.stats.nodes + search_basic.stats.qnodes:,}")
    
    # Comparison
    speedup = (time_basic / time_opt) if time_opt > 0 else 1.0
    node_reduction = ((search_basic.stats.nodes - search_opt.stats.nodes) / search_basic.stats.nodes * 100) if search_basic.stats.nodes > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"SPEEDUP: {speedup:.2f}x faster with LMR!")
    print(f"NODE REDUCTION: {node_reduction:.1f}% fewer nodes")
    print(f"{'='*70}")


if __name__ == "__main__":
    print("="*70)
    print("SEARCH OPTIMIZATION BENCHMARK")
    print("="*70)
    
    # Starting position
    benchmark_position(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Starting Position",
        depth=5
    )
    
    # Middlegame
    benchmark_position(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "Kiwipete (Complex Middlegame)",
        depth=4
    )
    
    # Endgame
    benchmark_position(
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "Endgame",
        depth=6
    )
    
    print("\n" + "="*70)
    print("✓ Benchmark complete!")
    print("="*70)
