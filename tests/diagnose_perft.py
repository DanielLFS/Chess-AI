"""Diagnose perft failures by comparing move counts at each depth."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move
from engine.moves import Moves

def perft(board: Board, depth: int) -> int:
    """Count leaf nodes."""
    if depth == 0:
        return 1
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    if depth == 1:
        return len(legal_moves)
    
    nodes = 0
    for move in legal_moves:
        undo_info = board.make_move(move)
        nodes += perft(board, depth - 1)
        board.unmake_move(move, undo_info)
    
    return nodes

def compare_position(fen: str, expected_depth_2: int, expected_depth_3: int):
    """Compare our perft with expected values and show differences."""
    print(f"\n{'='*80}")
    print(f"Position: {fen}")
    print(f"{'='*80}")
    
    board = Board(fen=fen)
    
    # Depth 1
    moves_gen = Moves(board)
    moves_d1 = moves_gen.generate()
    count_d1 = len(moves_d1)
    print(f"Depth 1: {count_d1} moves")
    
    # Depth 2
    count_d2 = perft(board, 2)
    match_d2 = "✓" if count_d2 == expected_depth_2 else f"✗ (expected {expected_depth_2})"
    print(f"Depth 2: {count_d2} nodes {match_d2}")
    
    if count_d2 != expected_depth_2:
        # Show move breakdown at depth 1
        print("\nMove breakdown at depth 2:")
        for move in moves_d1:
            undo_info = board.make_move(move)
            count = len(Moves(board).generate())
            board.unmake_move(move, undo_info)
            
            from_sq, to_sq, flags = decode_move(move)
            print(f"  {from_sq:2d}->{to_sq:2d} (f={flags}): {count:3d} moves")
    
    # Depth 3
    count_d3 = perft(board, 3)
    match_d3 = "✓" if count_d3 == expected_depth_3 else f"✗ (expected {expected_depth_3})"
    print(f"Depth 3: {count_d3} nodes {match_d3}")
    
    return count_d2 == expected_depth_2 and count_d3 == expected_depth_3

if __name__ == '__main__':
    all_pass = True
    
    # Kiwipete - fails at depth 3
    all_pass &= compare_position(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        2039, 97862
    )
    
    # Position 3 - fails at depth 4 (check depth 2 and 3)
    all_pass &= compare_position(
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        191, 2812
    )
    
    # Position 4 - fails at depth 4 (check depth 2 and 3)
    all_pass &= compare_position(
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        264, 9467
    )
    
    print(f"\n{'='*80}")
    if all_pass:
        print("✓ All positions match expected values")
    else:
        print("✗ Some positions have discrepancies")
    print(f"{'='*80}\n")
