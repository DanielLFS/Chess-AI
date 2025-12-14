"""Analyze perft failures in detail."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board
from engine.moves import Moves
from perft import perft_divide

# Position 4 - has promotion issues likely
print("=" * 70)
print("POSITION 4 ANALYSIS (Promotion heavy)")
print("=" * 70)
fen = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"
board = Board.from_fen(fen)
print(board.display())
print(f"\nFEN: {fen}")

# Check what moves we generate at depth 1
moves_obj = Moves(board)
legal_moves = moves_obj.generate()
print(f"\nTotal legal moves: {len(legal_moves)}")

# Expected: 6 moves at depth 1
# Let's see what they are
from engine.board import decode_move
print("\nMoves generated:")
for i, move in enumerate(legal_moves):
    from_sq, to_sq, flags = decode_move(move)
    print(f"  {i+1}. {from_sq}->{to_sq} (flags={flags})")

print("\n" + "=" * 70)
print("DIVIDE at depth 1:")
print("=" * 70)
perft_divide(board, 1)

print("\n" + "=" * 70)
print("DIVIDE at depth 2:")
print("=" * 70)
perft_divide(board, 2)

# Also test Kiwipete
print("\n\n" + "=" * 70)
print("KIWIPETE ANALYSIS")
print("=" * 70)
fen2 = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
board2 = Board.from_fen(fen2)
print(board2.display())
print(f"\nFEN: {fen2}")

moves_obj2 = Moves(board2)
legal_moves2 = moves_obj2.generate()
print(f"\nTotal legal moves: {len(legal_moves2)}")
print("Expected: 48")

print("\n" + "=" * 70)
print("DIVIDE at depth 2:")
print("=" * 70)
perft_divide(board2, 2)
