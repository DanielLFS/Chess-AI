"""Test EP with simplest possible position."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board
from engine.moves import Moves

# Simple EP position: just kings and pawns
# White pawn on e5, black pawn on d5, white just played e2-e4 (so d5 can capture e.p. on e3)
# Actually, let's use: white just played d2-d4, black pawn on e4 can capture on d3

fen1 = "8/8/8/8/3Pp3/8/8/4K2k b - d3 0 1"
board1 = Board(fen=fen1)
print("Position 1: Black pawn on e4, EP on d3")
print(board1.display())
print(f"FEN: {board1.to_fen()}")
moves1 = Moves(board1).generate()
print(f"Legal moves: {len(moves1)}\n")

# The original failing position
fen2 = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
board2 = Board(fen=fen2)
print("Position 2: Full board, black pawn on d4, EP on e3")
print(f"Legal moves: {len(Moves(board2).generate())}\n")

# Try white EP
fen3 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 1"
board3 = Board(fen=fen3)
print("Position 3: White pawn on e4, EP on e6")
print(f"Legal moves: {len(Moves(board3).generate())}\n")
