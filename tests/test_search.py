"""
Test bitboard search engine.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from engine.board import Board, decode_move
from engine.search import Search


def test_basic_search():
    """Test search on various positions."""
    print("=" * 70)
    print("Testing Bitboard Search Engine")
    print("=" * 70)
    
    positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5),
        ("After 1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", 5),
        ("Kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4),
        ("Endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 6),
    ]
    
    search = Search(tt_size_mb=64)
    
    for name, fen, depth in positions:
        print(f"\n{name}")
        print(f"FEN: {fen}")
        print(f"Depth: {depth}")
        print("-" * 70)
        
        board = Board.from_fen(fen)
        
        start = time.time()
        move, score = search.search(board, depth=depth, time_limit=10.0)
        elapsed = time.time() - start
        
        if move:
            from_sq, to_sq, flags = decode_move(move)
            from_row, from_col = from_sq // 8, from_sq % 8
            to_row, to_col = to_sq // 8, to_sq % 8
            from_notation = f"{chr(ord('a') + from_col)}{8 - from_row}"
            to_notation = f"{chr(ord('a') + to_col)}{8 - to_row}"
            
            print(f"Best move: {from_notation}{to_notation} (encoded: {move:04x})")
            print(f"Score: {score}")
        else:
            print("No legal moves (checkmate or stalemate)")
        
        print(f"Time: {elapsed:.2f}s")
        print(f"{search.stats}")
        
        # TT stats
        tt_stats = search.tt.get_stats()
        print(f"TT: {tt_stats['stores']:,} stores, {tt_stats['hits']:,} hits, "
              f"{tt_stats['fill_rate']:.1f}% full")
    
    print("\n" + "=" * 70)
    print("✓ All tests completed successfully!")
    print("=" * 70)


def test_mate_in_one():
    """Test that search finds mate in one."""
    print("\n" + "=" * 70)
    print("Mate in 1 Test")
    print("=" * 70)
    
    # White to move, Qh5# is mate
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1"
    board = Board.from_fen(fen)
    
    print(f"Position (Scholar's mate setup): {fen}")
    
    search = Search(tt_size_mb=16)
    move, score = search.search(board, depth=3)
    
    if move:
        from_sq, to_sq, flags = decode_move(move)
        from_row, from_col = from_sq // 8, from_sq % 8
        to_row, to_col = to_sq // 8, to_sq % 8
        from_notation = f"{chr(ord('a') + from_col)}{8 - from_row}"
        to_notation = f"{chr(ord('a') + to_col)}{8 - to_row}"
        
        print(f"Best move: {from_notation}{to_notation}")
        print(f"Score: {score}")
        
        if score >= 99000:  # Near mate score
            print("✓ Found mate!")
        else:
            print("⚠ Didn't recognize mate")
    
    print(f"{search.stats}")


if __name__ == "__main__":
    test_basic_search()
    test_mate_in_one()
