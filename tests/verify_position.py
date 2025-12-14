"""Verify board position."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, WP, BP, get_bit, square_to_coords

fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
board = Board(fen=fen)

print("Board position verification")
print("="*80)
print(board.display())
print()

# Check specific squares
d4 = 35  # row=4, col=3
e4 = 36  # row=4, col=4
e3 = 44  # row=5, col=4

print(f"d4 (square {d4}): Black pawn = {get_bit(board.state[BP], d4)}")
print(f"e4 (square {e4}): White pawn = {get_bit(board.state[WP], e4)}")
print(f"e3 (square {e3}): Black pawn = {get_bit(board.state[BP], e3)}, White pawn = {get_bit(board.state[WP], e3)}")

# List all pieces
print("\nAll white pawns:")
wp_bb = board.state[WP]
for sq in range(64):
    if get_bit(wp_bb, sq):
        row, col = square_to_coords(sq)
        print(f"  Square {sq}: {chr(ord('a')+col)}{8-row}")

print("\nAll black pawns:")
bp_bb = board.state[BP]
for sq in range(64):
    if get_bit(bp_bb, sq):
        row, col = square_to_coords(sq)
        print(f"  Square {sq}: {chr(ord('a')+col)}{8-row}")
