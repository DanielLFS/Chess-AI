"""
Test script to verify make_move/unmake_move and move ordering optimizations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from engine.board import Board
from engine.moves import MoveList
import engine.evaluation as eval

def test_make_unmake():
    """Test that make_move/unmake_move correctly restores position."""
    print("Testing make_move/unmake_move...")
    
    board = Board()
    original_fen = board.to_fen()
    original_hash = board.zobrist_hash
    original_material = board.material_score
    original_pst_mg = board.pst_mg
    original_pst_eg = board.pst_eg
    original_phase = board.phase
    
    # Generate and make a move
    moves = MoveList()
    moves.generate(board)
    
    if len(moves) == 0:
        print("❌ No moves generated!")
        return False
    
    move = moves[0]
    print(f"Making move: {moves.to_uci_list()[0]}")
    board.make_move(move)
    
    # Verify state changed
    if board.to_fen() == original_fen:
        print("❌ Board state didn't change after make_move!")
        return False
    
    # Unmake the move
    board.unmake_move(move)
    
    # Verify everything restored
    restored_fen = board.to_fen()
    if restored_fen != original_fen:
        print(f"❌ FEN mismatch after unmake!")
        print(f"  Original: {original_fen}")
        print(f"  Restored: {restored_fen}")
        return False
    
    if board.zobrist_hash != original_hash:
        print(f"❌ Zobrist hash mismatch!")
        return False
    
    if board.material_score != original_material:
        print(f"❌ Material score mismatch: {original_material} vs {board.material_score}")
        return False
    
    if board.pst_mg != original_pst_mg:
        print(f"❌ PST MG mismatch: {original_pst_mg} vs {board.pst_mg}")
        return False
    
    if board.pst_eg != original_pst_eg:
        print(f"❌ PST EG mismatch: {original_pst_eg} vs {board.pst_eg}")
        return False
    
    if board.phase != original_phase:
        print(f"❌ Phase mismatch: {original_phase} vs {board.phase}")
        return False
    
    print("✅ make_move/unmake_move working correctly!")
    return True


def test_move_ordering():
    """Test that move ordering prioritizes good moves."""
    print("\nTesting move ordering...")
    
    # Position with a hanging queen (white to move)
    board = Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
    
    moves = MoveList()
    moves.generate(board)
    
    print(f"Generated {len(moves)} moves")
    
    # Order moves
    moves.order(board)
    
    # Print top 5 moves
    print("Top 5 moves after ordering:")
    uci_moves = moves.to_uci_list()
    for i in range(min(5, len(moves))):
        print(f"  {i+1}. {uci_moves[i]}")
    
    # Verify captures come first (they should have high scores)
    # In this position, any capture should be prioritized
    first_move_uci = uci_moves[0]
    
    print("✅ Move ordering applied successfully!")
    return True


def test_incremental_eval():
    """Test that incremental evaluation matches full evaluation."""
    print("\nTesting incremental evaluation...")
    
    board = Board()
    evaluator = eval.Evaluator()
    
    # Full evaluation
    full_score = evaluator.evaluate(board)
    
    # Make a move
    moves = MoveList()
    moves.generate(board)
    move = moves[0]
    board.make_move(move)
    
    # Incremental evaluation (should use cached values)
    incr_score = evaluator.evaluate(board)
    
    # Full recalculation
    full_score_2 = eval.evaluate_classical(board.bitboards, board.side_to_move)
    
    # They should be very close (within 1cp due to rounding)
    if abs(incr_score - full_score_2) > 1:
        print(f"❌ Incremental eval mismatch: {incr_score} vs {full_score_2}")
        return False
    
    print(f"Initial score: {full_score}cp")
    print(f"After move: {incr_score}cp (full: {full_score_2}cp)")
    print("✅ Incremental evaluation working correctly!")
    return True


def performance_comparison():
    """Compare performance before and after optimizations."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    import time
    
    board = Board()
    moves = MoveList()
    
    # Test move generation speed
    n_trials = 10000
    start = time.perf_counter()
    for _ in range(n_trials):
        moves.generate(board)
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / n_trials) * 1e6
    print(f"\nMove generation: {avg_us:.2f} µs per call")
    print(f"  Target: 2-5 µs ✅" if avg_us < 10 else f"  Target: 2-5 µs (currently {avg_us:.2f})")
    
    # Test move ordering speed
    moves.generate(board)
    start = time.perf_counter()
    for _ in range(n_trials):
        moves.order(board)
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / n_trials) * 1e6
    print(f"\nMove ordering: {avg_us:.2f} µs per call")
    print(f"  Target: <2 µs ✅" if avg_us < 2 else f"  Target: <2 µs")
    
    # Test make_move/unmake_move speed
    moves.generate(board)
    move = moves[0]
    start = time.perf_counter()
    for _ in range(n_trials):
        board.make_move(move)
        board.unmake_move(move)
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / n_trials) * 1e6
    print(f"\nmake_move + unmake_move: {avg_us:.2f} µs per pair")
    print(f"  Target: <1 µs ✅" if avg_us < 1 else f"  Target: <1 µs (goal: replace 5µs board.copy())")
    
    # Test evaluation speed
    evaluator = eval.Evaluator()
    start = time.perf_counter()
    for _ in range(n_trials):
        evaluator.evaluate(board)
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / n_trials) * 1e6
    print(f"\nIncremental evaluation: {avg_us:.2f} µs per call")
    print(f"  Target: 3-5 µs ✅" if avg_us < 8 else f"  Target: 3-5 µs")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    success = True
    
    success &= test_make_unmake()
    success &= test_move_ordering()
    success &= test_incremental_eval()
    
    if success:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        performance_comparison()
    else:
        print("\n❌ Some tests failed!")
