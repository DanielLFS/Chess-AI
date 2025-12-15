"""
Test aspiration windows specifically at deeper depths (6-8) where they're most effective.
"""

import sys
import time
sys.path.append('.')

from engine.board import Board
from engine.search import Search


def test_position(fen: str, name: str, depth: int):
    """Test a position at specified depth with/without aspiration windows."""
    print(f"\n{'='*70}")
    print(f"{name} (Depth {depth})")
    print(f"{'='*70}\n")
    
    board = Board(fen=fen)
    
    # Test WITH aspiration windows
    print("[WITH ASPIRATION WINDOWS]")
    search_asp = Search(use_aspiration=True)
    start = time.time()
    move_asp, score_asp = search_asp.search(board, depth=depth)
    elapsed_asp = time.time() - start
    print(f"Time: {elapsed_asp:.2f}s")
    print(f"Score: {score_asp}")
    print(search_asp.stats)
    print(f"Nodes searched: {search_asp.stats.nodes:,}")
    print(f"Aspiration fails: {search_asp.stats.aspiration_fails}")
    print(f"Aspiration researches: {search_asp.stats.aspiration_researches}")
    print(f"Total nodes: {search_asp.stats.nodes + search_asp.stats.qnodes:,}")
    
    # Test WITHOUT aspiration windows
    print(f"\n[WITHOUT ASPIRATION WINDOWS]")
    search_no_asp = Search(use_aspiration=False)
    start = time.time()
    move_no_asp, score_no_asp = search_no_asp.search(board, depth=depth)
    elapsed_no_asp = time.time() - start
    print(f"Time: {elapsed_no_asp:.2f}s")
    print(f"Score: {score_no_asp}")
    print(search_no_asp.stats)
    print(f"Nodes searched: {search_no_asp.stats.nodes:,}")
    print(f"Total nodes: {search_no_asp.stats.nodes + search_no_asp.stats.qnodes:,}")
    
    # Calculate improvement
    speedup = elapsed_no_asp / elapsed_asp if elapsed_asp > 0 else 0
    node_reduction = 100 * (1 - search_asp.stats.nodes / search_no_asp.stats.nodes) if search_no_asp.stats.nodes > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"SPEEDUP: {speedup:.2f}x faster with aspiration windows!")
    print(f"NODE REDUCTION: {node_reduction:.1f}% fewer nodes")
    print(f"{'='*70}")


if __name__ == "__main__":
    print("="*70)
    print("ASPIRATION WINDOW BENCHMARK")
    print("="*70)
    
    # Test positions at deeper depths where aspiration windows shine
    test_position(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Starting Position",
        depth=6
    )
    
    test_position(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "Kiwipete (Complex Middlegame)",
        depth=5
    )
    
    test_position(
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "Endgame",
        depth=8
    )
    
    print(f"\n{'='*70}")
    print("✓ Benchmark complete!")
    print(f"{'='*70}")
