"""
Comprehensive depth tests:
1. Starting position depth 8
2. Tactical mate in 3 position depth 10
3. Kiwipete complex middlegame depth 7-8
4. Simple endgame depth 12-15
"""

import sys
import time
sys.path.append('.')

from engine.board import Board
from engine.search import Search


def format_time(seconds):
    """Format seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def test_position(name, fen, target_depth, description):
    """Test a single position."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Description: {description}")
    print(f"FEN: {fen}")
    print(f"Target Depth: {target_depth}\n")
    
    board = Board(fen=fen)
    search = Search()
    
    start_time = time.time()
    move, score = search.search(board, depth=target_depth)
    elapsed = time.time() - start_time
    
    total_nodes = search.stats.nodes + search.stats.qnodes
    nps = total_nodes / elapsed if elapsed > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"RESULTS - {name}")
    print(f"{'='*70}")
    print(f"Time: {format_time(elapsed)}")
    print(f"Best move: {move:04x}")
    print(f"Score: {score} cp")
    print(f"\nNodes: {search.stats.nodes:,}")
    print(f"QNodes: {search.stats.qnodes:,}")
    print(f"Total nodes: {total_nodes:,}")
    print(f"NPS: {nps:,.0f}")
    print(f"\nDepth reached: {search.stats.depth_reached}")
    print(f"TT hits: {search.stats.tt_hits:,}")
    print(f"Cutoffs: {search.stats.cutoffs:,}")
    print(f"Null move cutoffs: {search.stats.null_cutoffs:,}")
    print(f"LMR: {search.stats.lmr_reductions:,} reductions, {search.stats.lmr_researches:,} researches")
    print(f"Check extensions: {search.stats.check_extensions:,}")
    print(f"Futility prunes: {search.stats.futility_prunes:,}")
    print(f"RFP prunes: {search.stats.rfp_prunes:,}")
    print(f"History hits: {search.stats.history_hits:,}")
    print(f"Aspiration fails: {search.stats.aspiration_fails:,}")
    
    # Extract and show PV
    pv = search.get_pv(board, max_depth=10)
    pv_str = search.format_pv(pv, board)
    print(f"\nPrincipal Variation: {pv_str}")
    print(f"PV length: {len(pv)} moves")
    
    return {
        'name': name,
        'depth': target_depth,
        'time': elapsed,
        'nodes': total_nodes,
        'nps': nps,
        'score': score,
        'move': move,
    }


if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE DEPTH TESTS")
    print("="*70)
    
    results = []
    
    # Test 1: Starting position depth 8
    results.append(test_position(
        "Starting Position - Depth 8",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        8,
        "Benchmark test - balanced opening position"
    ))
    
    # Test 2: Tactical mate in 3 - depth 10
    results.append(test_position(
        "Mate in 3 - Depth 10",
        "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1",
        10,
        "Tests tactical sharpness - should find Qxf7# mate sequence"
    ))
    
    # Test 3: Kiwipete complex middlegame depth 7
    results.append(test_position(
        "Kiwipete - Depth 7",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        7,
        "Complex middlegame with many captures and tactics"
    ))
    
    # Test 4: Endgame depth 12
    results.append(test_position(
        "Endgame - Depth 12",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        12,
        "Simple endgame - tests deep search capability"
    ))
    
    # Summary
    print(f"\n\n{'='*70}")
    print("COMPREHENSIVE SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"{'Test':<30} {'Depth':<8} {'Time':<12} {'Nodes':<15} {'NPS':<12}")
    print("-"*77)
    for r in results:
        print(f"{r['name']:<30} {r['depth']:<8} {format_time(r['time']):<12} "
              f"{r['nodes']:<15,} {r['nps']:<12,.0f}")
    
    total_time = sum(r['time'] for r in results)
    total_nodes = sum(r['nodes'] for r in results)
    avg_nps = total_nodes / total_time if total_time > 0 else 0
    
    print("-"*77)
    print(f"{'TOTAL':<30} {'':<8} {format_time(total_time):<12} "
          f"{total_nodes:<15,} {avg_nps:<12,.0f}")
    
    print(f"\n{'='*70}")
    print("✓ All depth tests complete!")
    print(f"{'='*70}")
