"""
Perft (Performance Test) - Move Generation Validation
Tests move generation correctness by counting leaf nodes at various depths.
Reference: https://www.chessprogramming.org/Perft
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from engine.board import Board
from engine.moves import Moves


def perft(board: Board, depth: int, verbose: bool = False) -> int:
    """
    Count all leaf nodes at given depth.
    
    Args:
        board: Current board position
        depth: Depth to search (0 = current position)
        verbose: Print move breakdown at depth 1
        
    Returns:
        Total number of leaf nodes
    """
    if depth == 0:
        return 1
    
    moves_gen = Moves(board)
    moves = moves_gen.generate()
    
    if depth == 1:
        return len(moves)
    
    nodes = 0
    for move in moves:
        undo_info = board.make_move(move)
        nodes += perft(board, depth - 1, False)
        board.unmake_move(move, undo_info)
    
    return nodes


def perft_divide(board: Board, depth: int):
    """
    Perft with move-by-move breakdown (divide).
    Useful for debugging - shows which moves have wrong counts.
    """
    moves_gen = Moves(board)
    moves = moves_gen.generate()
    
    total_nodes = 0
    print(f"\nPerft divide at depth {depth}:")
    print("-" * 50)
    
    for move in moves:
        from_sq, to_sq, flags = move & 0x3F, (move >> 6) & 0x3F, (move >> 12) & 0xF
        from_row, from_col = from_sq // 8, from_sq % 8
        to_row, to_col = to_sq // 8, to_sq % 8
        
        # Convert to algebraic notation
        from_str = f"{chr(ord('a') + from_col)}{8 - from_row}"
        to_str = f"{chr(ord('a') + to_col)}{8 - to_row}"
        
        undo_info = board.make_move(move)
        count = perft(board, depth - 1, False)
        board.unmake_move(move, undo_info)
        
        total_nodes += count
        print(f"{from_str}{to_str}: {count:,}")
    
    print("-" * 50)
    print(f"Total: {total_nodes:,}")
    return total_nodes


def run_perft_suite():
    """Run standard perft test suite with known positions."""
    
    test_positions = [
        {
            "name": "Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "depths": {
                1: 20,
                2: 400,
                3: 8_902,
                4: 197_281,
                5: 4_865_609,
                6: 119_060_324,
            }
        },
        {
            "name": "Kiwipete",
            "fen": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "depths": {
                1: 48,
                2: 2_039,
                3: 97_862,
                4: 4_085_603,
                5: 193_690_690,  # Corrected from chessprogramming.org
            }
        },
        {
            "name": "Position 3",
            "fen": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "depths": {
                1: 14,
                2: 191,
                3: 2_812,
                4: 43_238,
                5: 674_624,
                6: 11_030_083,
            }
        },
        {
            "name": "Position 4",
            "fen": "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
            "depths": {
                1: 6,
                2: 264,
                3: 9_467,
                4: 422_333,
                5: 15_833_292,
            }
        },
        {
            "name": "Position 5",
            "fen": "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
            "depths": {
                1: 44,
                2: 1_486,
                3: 62_379,
                4: 2_103_487,
                5: 89_941_194,
            }
        },
        {
            "name": "Position 6",
            "fen": "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
            "depths": {
                1: 46,
                2: 2_079,
                3: 89_890,
                4: 3_894_594,
                5: 164_075_551,
            }
        }
    ]
    
    print("=" * 70)
    print("PERFT TEST SUITE")
    print("=" * 70)
    
    all_passed = True
    total_time = 0
    
    for pos in test_positions:
        print(f"\n{pos['name']}")
        print(f"FEN: {pos['fen']}")
        print("-" * 70)
        
        board = Board.from_fen(pos['fen'])
        
        for depth, expected in pos['depths'].items():
            if depth > 5:  # Skip depth 6 for now (too slow without optimizations)
                continue
                
            start = time.time()
            result = perft(board, depth)
            elapsed = time.time() - start
            total_time += elapsed
            
            status = "✓ PASS" if result == expected else "✗ FAIL"
            nps = int(result / elapsed) if elapsed > 0 else 0
            
            print(f"Depth {depth}: {result:>12,} nodes | {elapsed:>6.3f}s | {nps:>10,} nps | {status}")
            
            if result != expected:
                print(f"         Expected: {expected:,}")
                all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print(f"Total time: {total_time:.2f}s")
    print("=" * 70)
    
    return all_passed


def quick_perft_test():
    """Quick validation test - just starting position up to depth 4."""
    print("\n" + "=" * 50)
    print("QUICK PERFT TEST (Starting Position)")
    print("=" * 50)
    
    board = Board()
    expected = {1: 20, 2: 400, 3: 8_902, 4: 197_281}
    
    for depth in range(1, 5):
        start = time.time()
        result = perft(board, depth)
        elapsed = time.time() - start
        
        status = "✓" if result == expected[depth] else "✗"
        nps = int(result / elapsed) if elapsed > 0 else 0
        
        print(f"Depth {depth}: {result:>8,} | Expected: {expected[depth]:>8,} | "
              f"{elapsed:>6.3f}s | {nps:>8,} nps | {status}")
    
    print("=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_perft_test()
        elif sys.argv[1] == "divide":
            depth = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            board = Board()
            perft_divide(board, depth)
        elif sys.argv[1] == "fen":
            fen = sys.argv[2]
            depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4
            board = Board.from_fen(fen)
            print(f"Perft({depth}) from position:")
            print(board.display())
            start = time.time()
            result = perft(board, depth)
            elapsed = time.time() - start
            nps = int(result / elapsed) if elapsed > 0 else 0
            print(f"\nNodes: {result:,}")
            print(f"Time: {elapsed:.3f}s")
            print(f"NPS: {nps:,}")
    else:
        # Default: run full suite
        run_perft_suite()
