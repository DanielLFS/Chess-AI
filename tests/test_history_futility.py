"""
Benchmark history heuristic + futility pruning specifically.
"""

import sys
import time
sys.path.append('.')

from engine.board import Board
from engine.search import Search


def test_position(fen: str, name: str, depth: int):
    """Test a position with/without history + futility."""
    print(f"\n{'='*70}")
    print(f"{name} (Depth {depth})")
    print(f"{'='*70}\n")
    
    board = Board(fen=fen)
    
    # Test WITH history + futility
    print("[WITH HISTORY HEURISTIC + FUTILITY PRUNING]")
    search_opt = Search(use_futility=True)
    start = time.time()
    move_opt, score_opt = search_opt.search(board, depth=depth)
    elapsed_opt = time.time() - start
    print(f"Time: {elapsed_opt:.2f}s")
    print(f"Score: {score_opt}")
    print(search_opt.stats)
    print(f"Nodes searched: {search_opt.stats.nodes:,}")
    print(f"Futility prunes: {search_opt.stats.futility_prunes:,}")
    print(f"History hits: {search_opt.stats.history_hits:,}")
    print(f"Total nodes: {search_opt.stats.nodes + search_opt.stats.qnodes:,}")
    
    # Test WITHOUT history + futility
    print(f"\n[WITHOUT HISTORY + FUTILITY]")
    search_base = Search(use_futility=False)
    search_base.history_table.fill(0)  # Disable history by clearing table
    start = time.time()
    move_base, score_base = search_base.search(board, depth=depth)
    elapsed_base = time.time() - start
    print(f"Time: {elapsed_base:.2f}s")
    print(f"Score: {score_base}")
    print(search_base.stats)
    print(f"Nodes searched: {search_base.stats.nodes:,}")
    print(f"Total nodes: {search_base.stats.nodes + search_base.stats.qnodes:,}")
    
    # Calculate improvement
    speedup = elapsed_base / elapsed_opt if elapsed_opt > 0 else 0
    node_reduction = 100 * (1 - search_opt.stats.nodes / search_base.stats.nodes) if search_base.stats.nodes > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"SPEEDUP: {speedup:.2f}x faster with history + futility!")
    print(f"NODE REDUCTION: {node_reduction:.1f}% fewer nodes")
    print(f"{'='*70}")


if __name__ == "__main__":
    print("="*70)
    print("HISTORY HEURISTIC + FUTILITY PRUNING BENCHMARK")
    print("="*70)
    
    # Test positions
    test_position(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Starting Position",
        depth=5
    )
    
    test_position(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "Kiwipete (Complex Middlegame)",
        depth=4
    )
    
    test_position(
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "Endgame",
        depth=6
    )
    
    print(f"\n{'='*70}")
    print("✓ Benchmark complete!")
    print(f"{'='*70}")
