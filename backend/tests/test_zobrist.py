"""
Test Zobrist hashing correctness.
Verifies:
1. Make/unmake preserves hash
2. Same position gets same hash
3. Different positions get different hashes
4. Hash consistency during perft
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.board import Board, HASH
from engine.moves import Moves


def test_make_unmake_hash():
    """Test that make/unmake preserves hash."""
    print("Testing make/unmake hash preservation...")
    
    board = Board()
    moves_gen = Moves(board)
    
    positions_tested = 0
    hash_mismatches = 0
    
    # Test from starting position
    original_hash = board.state[HASH]
    legal_moves = moves_gen.generate()
    
    for move in legal_moves:
        undo = board.make_move(move)
        
        # Make another move to go deeper
        inner_moves = Moves(board).generate()
        if len(inner_moves) > 0:
            inner_move = inner_moves[0]
            inner_undo = board.make_move(inner_move)
            board.unmake_move(inner_move, inner_undo)
        
        # Unmake and verify hash
        board.unmake_move(move, undo)
        restored_hash = board.state[HASH]
        
        positions_tested += 1
        if restored_hash != original_hash:
            hash_mismatches += 1
            print(f"  FAIL: Move {move:04x} - hash mismatch!")
            print(f"    Original: {original_hash}")
            print(f"    Restored: {restored_hash}")
    
    print(f"  Tested {positions_tested} move sequences")
    if hash_mismatches == 0:
        print(f"  ✓ All hashes preserved correctly!")
    else:
        print(f"  ✗ {hash_mismatches} hash mismatches found")
    
    return hash_mismatches == 0


def test_same_position_same_hash():
    """Test that same position gets same hash."""
    print("\nTesting same position -> same hash...")
    
    # Create two boards from same FEN
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    board1 = Board.from_fen(fen)
    board2 = Board.from_fen(fen)
    
    hash1 = board1.state[HASH]
    hash2 = board2.state[HASH]
    
    if hash1 == hash2:
        print(f"  ✓ Same position gets same hash: {hash1}")
        return True
    else:
        print(f"  ✗ Hash mismatch!")
        print(f"    Board 1: {hash1}")
        print(f"    Board 2: {hash2}")
        return False


def test_different_positions_different_hashes():
    """Test that different positions get different hashes."""
    print("\nTesting different positions -> different hashes...")
    
    fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
    ]
    
    hashes = []
    for fen in fens:
        board = Board.from_fen(fen)
        hash_val = board.state[HASH]
        hashes.append(hash_val)
        print(f"  Position {len(hashes)}: {hash_val}")
    
    # Check for collisions
    unique_hashes = len(set(hashes))
    if unique_hashes == len(hashes):
        print(f"  ✓ All {len(hashes)} positions have unique hashes")
        return True
    else:
        print(f"  ✗ Collision detected! {len(hashes)} positions, {unique_hashes} unique hashes")
        return False


def test_perft_hash_consistency(depth=3):
    """Test hash consistency during perft traversal."""
    print(f"\nTesting hash consistency during perft (depth {depth})...")
    
    board = Board()
    nodes = 0
    errors = 0
    
    def perft_with_hash_check(board, depth, original_hash):
        nonlocal nodes, errors
        
        if depth == 0:
            nodes += 1
            return
        
        moves_gen = Moves(board)
        legal_moves = moves_gen.generate()
        
        for move in legal_moves:
            before_hash = board.state[HASH]
            undo = board.make_move(move)
            
            perft_with_hash_check(board, depth - 1, original_hash)
            
            board.unmake_move(move, undo)
            after_hash = board.state[HASH]
            
            if before_hash != after_hash:
                errors += 1
    
    original_hash = board.state[HASH]
    perft_with_hash_check(board, depth, original_hash)
    
    print(f"  Traversed {nodes:,} nodes")
    if errors == 0:
        print(f"  ✓ All hashes consistent!")
    else:
        print(f"  ✗ {errors} hash errors found")
    
    return errors == 0


def main():
    print("=" * 60)
    print("Zobrist Hash Consistency Tests")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Make/unmake preservation", test_make_unmake_hash()))
    results.append(("Same position -> same hash", test_same_position_same_hash()))
    results.append(("Different positions -> different hashes", test_different_positions_different_hashes()))
    results.append(("Perft hash consistency", test_perft_hash_consistency(depth=3)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Zobrist hash tests PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
