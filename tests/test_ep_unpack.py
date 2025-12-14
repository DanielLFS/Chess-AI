"""Test EP unpacking."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, META, unpack_ep_square
import numpy as np

fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
board = Board(fen=fen)

meta = board.state[META]
print(f"META value: {meta}")
print(f"META binary: {bin(meta)}")

ep = unpack_ep_square(meta)
print(f"\nUnpacked EP square: {ep}")
print(f"Expected: 44 (e3)")
print(f"Match: {ep == 44}")

# Also check that it's a numpy int, not Python int
print(f"\nType of ep: {type(ep)}")
print(f"ep >= 0: {ep >= 0}")
print(f"ep == 44: {ep == 44}")

# Test the condition used in generate_pawn_moves
cap_sq = 44
condition = ep >= 0 and cap_sq == ep
print(f"\nCondition (ep >= 0 and cap_sq == ep): {condition}")
