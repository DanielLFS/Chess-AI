"""
Test Reverse Futility Pruning and Principal Variation extraction.
"""

import sys
sys.path.append('.')

from engine.board import Board
from engine.search import Search


def test_pv_extraction():
    """Test PV extraction."""
    print("="*70)
    print("PRINCIPAL VARIATION EXTRACTION TEST")
    print("="*70)
    
    board = Board()
    search = Search()
    
    print("\nSearching starting position to depth 5...")
    move, score = search.search(board, depth=5)
    
    print(f"\n{search.stats}\n")
    print(f"Best move: {move:04x}")
    print(f"Score: {score}")
    
    # Extract PV
    pv = search.get_pv(board)
    pv_str = search.format_pv(pv, board)
    print(f"Principal Variation: {pv_str}")
    print(f"PV length: {len(pv)} moves")
    print(f"\n{'='*70}\n")


def test_rfp():
    """Test Reverse Futility Pruning."""
    print("="*70)
    print("REVERSE FUTILITY PRUNING TEST")
    print("="*70)
    
    # Position where one side is clearly better
    # White is up material significantly
    fen = "r3k3/8/8/8/8/8/PPPPPPPP/RNBQKBNR w KQq - 0 1"
    board = Board(fen=fen)
    
    print(f"\nPosition: {fen}")
    print("White is up significantly (2 rooks and 2 bishops)")
    
    # With RFP
    print("\n[WITH RFP]")
    search_rfp = Search(use_rfp=True)
    move, score = search_rfp.search(board, depth=5)
    print(search_rfp.stats)
    print(f"RFP prunes: {search_rfp.stats.rfp_prunes:,}")
    print(f"Nodes: {search_rfp.stats.nodes:,}")
    
    # Without RFP
    print("\n[WITHOUT RFP]")
    search_no_rfp = Search(use_rfp=False)
    move, score = search_no_rfp.search(board, depth=5)
    print(search_no_rfp.stats)
    print(f"Nodes: {search_no_rfp.stats.nodes:,}")
    
    reduction = 100 * (1 - search_rfp.stats.nodes / search_no_rfp.stats.nodes) if search_no_rfp.stats.nodes > 0 else 0
    print(f"\nNode reduction with RFP: {reduction:.1f}%")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    test_pv_extraction()
    test_rfp()
    
    print("="*70)
    print("✓ Tests complete!")
    print("="*70)
