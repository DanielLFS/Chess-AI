"""
Test search performance from starting position at depths 1-6.
Shows nodes searched, time, NPS, and all optimization statistics.
"""

import sys
import time
sys.path.append('.')

from engine.board import Board
from engine.search import Search


def test_depth_scaling():
    """Test search from depth 1 to 6 on starting position."""
    print("="*70)
    print("SEARCH PERFORMANCE TEST - STARTING POSITION")
    print("="*70)
    
    board = Board()
    search = Search()
    
    print("\nPosition: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    print(f"\nSearching depths 1-6...\n")
    
    results = []
    
    for depth in range(1, 7):
        print(f"{'='*70}")
        print(f"Depth {depth}")
        print(f"{'='*70}")
        
        # Reset stats for this depth
        search.stats.reset()
        search.stats.start_time = time.time()
        
        # Search
        start = time.time()
        move, score = search.search(board, depth=depth)
        elapsed = time.time() - start
        
        # Get stats
        total_nodes = search.stats.nodes + search.stats.qnodes
        nps = total_nodes / elapsed if elapsed > 0 else 0
        
        # Store results
        results.append({
            'depth': depth,
            'nodes': search.stats.nodes,
            'qnodes': search.stats.qnodes,
            'total': total_nodes,
            'time': elapsed,
            'nps': nps,
            'score': score,
            'move': move,
            'tt_hits': search.stats.tt_hits,
            'cutoffs': search.stats.cutoffs,
            'null_cutoffs': search.stats.null_cutoffs,
            'lmr_reductions': search.stats.lmr_reductions,
            'lmr_researches': search.stats.lmr_researches,
            'check_extensions': search.stats.check_extensions,
            'aspiration_fails': search.stats.aspiration_fails,
            'futility_prunes': search.stats.futility_prunes,
            'rfp_prunes': search.stats.rfp_prunes,
            'history_hits': search.stats.history_hits,
        })
        
        print(f"\nTime: {elapsed:.3f}s")
        print(f"Score: {score}")
        print(f"Best move: {move:04x}")
        print(f"\n{search.stats}")
        print(f"\nTotal nodes: {total_nodes:,}")
        print(f"NPS: {nps:,.0f}\n")
    
    # Summary table
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}\n")
    
    print(f"{'Depth':<8} {'Nodes':<12} {'QNodes':<12} {'Total':<12} {'Time':<10} {'NPS':<12}")
    print("-"*70)
    for r in results:
        print(f"{r['depth']:<8} {r['nodes']:<12,} {r['qnodes']:<12,} {r['total']:<12,} "
              f"{r['time']:<10.3f} {r['nps']:<12,.0f}")
    
    # Detailed optimization stats
    print(f"\n{'='*70}")
    print("OPTIMIZATION STATISTICS")
    print(f"{'='*70}\n")
    
    print(f"{'Depth':<8} {'TT Hits':<10} {'Cutoffs':<10} {'Null':<8} {'LMR':<12} {'Ext':<8} {'Fut':<8} {'RFP':<8} {'Hist':<10}")
    print("-"*110)
    for r in results:
        lmr_str = f"{r['lmr_reductions']}/{r['lmr_researches']}"
        print(f"{r['depth']:<8} {r['tt_hits']:<10,} {r['cutoffs']:<10,} {r['null_cutoffs']:<8,} "
              f"{lmr_str:<12} {r['check_extensions']:<8,} {r['futility_prunes']:<8,} "
              f"{r['rfp_prunes']:<8,} {r['history_hits']:<10,}")
    
    print(f"\n{'='*70}")
    print("✓ Performance test complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_depth_scaling()
