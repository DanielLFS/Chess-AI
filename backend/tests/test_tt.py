"""
Simple test to verify TT integration basics.
Tests TT with bitboard API independently.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.board import Board, HASH
from engine.transposition import TranspositionTable, EXACT, LOWER_BOUND, UPPER_BOUND
from engine.moves import Moves


def test_tt_with_bitboards():
    """Test that TT works with bitboard positions."""
    print("=" * 60)
    print("Testing Transposition Table with Bitboards")
    print("=" * 60)
    
    tt = TranspositionTable(size_mb=64)
    board = Board()
    
    print("\nTest 1: Store and probe position")
    zobrist = board.state[HASH]
    print(f"  Starting position hash: {zobrist}")
    
    # Store a result
    tt.store(zobrist, score=100, best_move=np.uint16(0x1234), depth=5, node_type=EXACT)
    print(f"  Stored: depth=5, score=100, move=0x1234")
    
    # Probe it back
    result = tt.probe(zobrist, depth=5, alpha=-1000, beta=1000)
    if result:
        score, move = result
        print(f"  Probed: score={score}, move={move:04x}")
        if score == 100 and move == 0x1234:
            print("  ✓ Store/probe works!")
        else:
            print(f"  ✗ Mismatch!")
    else:
        print("  ✗ Probe failed!")
    
    print("\nTest 2: Hash changes after moves")
    original_hash = board.state[HASH]
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    if len(legal_moves) > 0:
        move = legal_moves[0]
        undo = board.make_move(move)
        new_hash = board.state[HASH]
        
        print(f"  Original hash: {original_hash}")
        print(f"  After move hash: {new_hash}")
        
        if new_hash != original_hash:
            print("  ✓ Hash changed after move")
        else:
            print("  ✗ Hash didn't change!")
        
        # Unmake and verify hash restored
        board.unmake_move(move, undo)
        restored_hash = board.state[HASH]
        
        if restored_hash == original_hash:
            print(f"  ✓ Hash restored after unmake")
        else:
            print(f"  ✗ Hash not restored! ({restored_hash} != {original_hash})")
    
    print("\nTest 3: TT with multiple positions")
    positions_tested = 0
    tt_hits = 0
    
    for move in legal_moves[:5]:  # Test first 5 moves
        undo = board.make_move(move)
        pos_hash = board.state[HASH]
        
        # Store position
        tt.store(pos_hash, score=positions_tested, best_move=np.uint16(0), depth=1, node_type=EXACT)
        
        # Immediately probe it
        result = tt.probe(pos_hash, depth=1, alpha=-1000, beta=1000)
        if result and result[0] == positions_tested:
            tt_hits += 1
        
        board.unmake_move(move, undo)
        positions_tested += 1
    
    print(f"  Tested {positions_tested} positions")
    print(f"  TT hits: {tt_hits}/{positions_tested}")
    
    if tt_hits == positions_tested:
        print("  ✓ All positions stored and retrieved correctly!")
    else:
        print(f"  ✗ Some positions failed")
    
    # Get stats
    print("\nTransposition Table Statistics:")
    tt_stats = tt.get_stats()
    print(f"  Size: {tt_stats['size']:,} entries")
    print(f"  Filled: {tt_stats['filled']:,} ({tt_stats['fill_rate']:.1f}%)")
    print(f"  Stores: {tt_stats['stores']:,}")
    print(f"  Hits: {tt_stats['hits']:,}")
    print(f"  Hit rate: {tt_stats['hit_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✓ All TT bitboard tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_tt_with_bitboards()
