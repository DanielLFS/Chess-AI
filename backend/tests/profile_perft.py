"""
Profile perft to find bottlenecks.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import cProfile
import pstats
from io import StringIO
from engine.board import Board
from engine.moves import Moves


def perft(board: Board, depth: int) -> int:
    """Perft function to profile."""
    if depth == 0:
        return 1
    
    moves_gen = Moves(board)
    moves = moves_gen.generate()
    
    if depth == 1:
        return len(moves)
    
    nodes = 0
    for move in moves:
        undo_info = board.make_move(move)
        nodes += perft(board, depth - 1)
        board.unmake_move(move, undo_info)
    
    return nodes


def main():
    print("Profiling perft performance...\n")
    
    # Use starting position depth 4 (197K nodes)
    board = Board()
    
    print("Warming up JIT...")
    _ = perft(board, 3)
    
    print("Running profiled perft depth 4...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    start = time.time()
    nodes = perft(board, 4)
    elapsed = time.time() - start
    
    profiler.disable()
    
    print(f"Nodes: {nodes:,}")
    print(f"Time: {elapsed:.3f}s")
    print(f"NPS: {nodes/elapsed:,.0f}")
    
    # Print profile stats
    print("\n" + "=" * 80)
    print("Top 30 time-consuming functions:")
    print("=" * 80)
    
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(30)
    
    print(s.getvalue())
    
    print("\n" + "=" * 80)
    print("Top 20 by number of calls:")
    print("=" * 80)
    
    s2 = StringIO()
    stats2 = pstats.Stats(profiler, stream=s2)
    stats2.strip_dirs()
    stats2.sort_stats('calls')
    stats2.print_stats(20)
    
    print(s2.getvalue())


if __name__ == "__main__":
    main()
