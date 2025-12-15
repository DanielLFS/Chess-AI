"""
Detailed perft analysis - check what's actually slow.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
from engine.board import Board
from engine.moves import Moves, generate_legal_moves_numba, unpack_side, META


def perft_detailed(board: Board, depth: int) -> dict:
    """Perft with detailed statistics."""
    stats = {
        'nodes': 0,
        'move_gen_time': 0,
        'make_time': 0,
        'unmake_time': 0,
        'recursion_time': 0,
        'move_gen_calls': 0,
    }
    
    def perft_recursive(board, depth, stats):
        if depth == 0:
            stats['nodes'] += 1
            return 1
        
        # Time move generation
        t0 = time.perf_counter()
        color = unpack_side(board.state[META])
        moves = generate_legal_moves_numba(board.state, color)
        t1 = time.perf_counter()
        stats['move_gen_time'] += (t1 - t0)
        stats['move_gen_calls'] += 1
        
        if depth == 1:
            stats['nodes'] += len(moves)
            return len(moves)
        
        nodes = 0
        for move in moves:
            # Time make_move
            t0 = time.perf_counter()
            undo_info = board.make_move(move)
            t1 = time.perf_counter()
            stats['make_time'] += (t1 - t0)
            
            # Recursion
            t0 = time.perf_counter()
            nodes += perft_recursive(board, depth - 1, stats)
            t1 = time.perf_counter()
            stats['recursion_time'] += (t1 - t0)
            
            # Time unmake_move
            t0 = time.perf_counter()
            board.unmake_move(move, undo_info)
            t1 = time.perf_counter()
            stats['unmake_time'] += (t1 - t0)
        
        return nodes
    
    start = time.time()
    perft_recursive(board, depth, stats)
    total_time = time.time() - start
    
    stats['total_time'] = total_time
    stats['nps'] = stats['nodes'] / total_time if total_time > 0 else 0
    
    return stats


def main():
    print("=" * 70)
    print("Detailed Perft Analysis")
    print("=" * 70)
    
    positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4),
        ("Kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4),
    ]
    
    for name, fen, depth in positions:
        print(f"\n{name} (depth {depth})")
        print("-" * 70)
        
        board = Board.from_fen(fen)
        
        # Warmup
        _ = Moves(board).generate()
        
        stats = perft_detailed(board, depth)
        
        print(f"Nodes:     {stats['nodes']:,}")
        print(f"Total time: {stats['total_time']:.3f}s")
        print(f"NPS:       {stats['nps']:,.0f}")
        print()
        
        # Time breakdown
        total = stats['total_time']
        print("Time breakdown:")
        print(f"  Move generation: {stats['move_gen_time']:.3f}s ({stats['move_gen_time']/total*100:.1f}%)")
        print(f"  Make move:       {stats['make_time']:.3f}s ({stats['make_time']/total*100:.1f}%)")
        print(f"  Unmake move:     {stats['unmake_time']:.3f}s ({stats['unmake_time']/total*100:.1f}%)")
        print(f"  Recursion+other: {stats['recursion_time']:.3f}s ({stats['recursion_time']/total*100:.1f}%)")
        print()
        
        # Per-call averages
        if stats['move_gen_calls'] > 0:
            print(f"Move generation calls: {stats['move_gen_calls']:,}")
            print(f"  Avg per call: {stats['move_gen_time']/stats['move_gen_calls']*1e6:.1f}μs")
        
        if stats['nodes'] > depth:  # Exclude leaf nodes
            make_calls = stats['nodes'] - (stats['nodes'] // (depth + 1))
            if make_calls > 0:
                print(f"Make/unmake calls: ~{make_calls:,}")
                print(f"  Avg make:   {stats['make_time']/make_calls*1e6:.1f}μs")
                print(f"  Avg unmake: {stats['unmake_time']/make_calls*1e6:.1f}μs")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
