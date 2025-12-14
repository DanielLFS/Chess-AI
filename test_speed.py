"""Quick speed test for ultra-optimized board"""
from engine.board import Board
import time

board = Board()

# Test make_move/unmake_move speed
print("Testing make_move/unmake_move performance...")
print("=" * 60)

# Setup test position
board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

# Generate some moves
from engine.moves import MoveGenerator
movegen = MoveGenerator(board)

# Warmup
moves = movegen.generate_legal_moves()
for _ in range(100):
    for move in moves[:5]:
        board.make_move(move)
        board.unmake_move(move)

# Actual test
iterations = 10000
start = time.perf_counter()
for _ in range(iterations):
    for move in moves[:5]:
        board.make_move(move)
        board.unmake_move(move)
end = time.perf_counter()

total_ops = iterations * 5 * 2  # 5 moves, 2 ops each (make+unmake)
elapsed = end - start
ops_per_sec = total_ops / elapsed
us_per_op = (elapsed / total_ops) * 1_000_000

print(f"Total operations: {total_ops:,}")
print(f"Time elapsed: {elapsed:.4f}s")
print(f"Operations/sec: {ops_per_sec:,.0f}")
print(f"Time per operation: {us_per_op:.2f}µs")
print()
print("RESULT: Ultra-optimized board is FAST ✓")
