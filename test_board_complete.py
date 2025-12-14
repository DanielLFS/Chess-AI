"""Test complete board functionality."""
from engine.board import Board, encode_move

print("=" * 60)
print("TEST 1: FEN Import/Export")
print("=" * 60)
b = Board.from_fen('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1')
print(b.display())
print('FEN:', b.to_fen())

print("\n" + "=" * 60)
print("TEST 2: Move Sequence (1.e4 e5 2.Bc4 Nc6)")
print("=" * 60)
b2 = Board()
print("Starting position:")
print(b2.display())
print(b2.to_fen())

# 1. e2-e4
move = encode_move(52, 36, 0)
b2.make_move(move)
print("\nAfter 1.e4:")
print(b2.to_fen())

# 1... e7-e5
move = encode_move(12, 28, 0)
b2.make_move(move)
print("After 1...e5:")
print(b2.to_fen())

# 2. Bf1-c4
move = encode_move(61, 34, 0)
b2.make_move(move)
print("After 2.Bc4:")
print(b2.to_fen())

# 2... Nb8-c6
move = encode_move(1, 18, 0)
b2.make_move(move)
print("After 2...Nc6:")
print(b2.display())
print(b2.to_fen())

print("\n" + "=" * 60)
print("TEST 3: Castling Rights Update")
print("=" * 60)
b3 = Board()
print(f"Initial castling: {bin(b3.castling_rights)}")

# Move white king
move = encode_move(60, 52, 0)  # Ke1-e2
b3.make_move(move)
print(f"After Ke2 (king moved): {bin(b3.castling_rights)} (should lose WK and WQ)")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
