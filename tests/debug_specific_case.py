"""Debug the specific failing case."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board, decode_move
from engine.moves import Moves
import numpy as np

# Start from Kiwipete
fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
board = Board.from_fen(fen)

print("=" * 70)
print("DEBUGGING SPECIFIC FAILING SEQUENCE")
print("=" * 70)
print("\nStarting position:")
print(board.display())
print(f"FEN: {board.to_fen()}\n")

# Move 1: a2a3 (square 48 -> 32)
moves1 = Moves(board).generate()
move1 = None
for m in moves1:
    f, t, flags = decode_move(m)
    if f == 48 and t == 40:  # a2-a3
        move1 = m
        break

print(f"Move 1: Looking for 48->40 (a2-a3)")
if move1:
    from_sq1, to_sq1, flags1 = decode_move(move1)
    print(f"  Found: {from_sq1}->{to_sq1} (flags={flags1})")
    undo1 = board.make_move(move1)
    print(f"  After move: {board.to_fen()}")
    print(board.display())
else:
    print("  NOT FOUND - trying alternative squares")
    # List all pawn moves
    for m in moves1:
        f, t, flags = decode_move(m)
        from engine.board import get_piece_at
        piece_type, color = get_piece_at(board.state, f)
        if piece_type == 0:  # Pawn
            print(f"  Pawn move: {f}->{t} (flags={flags})")
    
    # Let me check square numbers
    # a2 = col 0, row 6 = 6*8 + 0 = 48
    # a3 = col 0, row 5 = 5*8 + 0 = 40
    # a4 = col 0, row 4 = 4*8 + 0 = 32
    
    print("\nSquare reference:")
    print("  a2 = 48, a3 = 40, a4 = 32")
    print("  b4 = row 4, col 1 = 4*8+1 = 33")
    
    # Try a2-a4 double push
    print("\nLooking for a2-a4 (48->32) double push...")
    for m in moves1:
        f, t, flags = decode_move(m)
        if f == 48 and t == 32:
            move1 = m
            print(f"  Found: 48->32 (a2-a4 double push, flags={flags})")
            undo1 = board.make_move(move1)
            print(f"  After move: {board.to_fen()}")
            print(board.display())
            break

if not move1:
    print("ERROR: Could not find move 1")
    sys.exit(1)

# Move 2: b4xa3 (square 33 -> 40)
print(f"\nMove 2: Looking for 33->40 (b4xa3)")
moves2 = Moves(board).generate()
move2 = None
for m in moves2:
    f, t, flags = decode_move(m)
    if f == 33 and t == 40:
        move2 = m
        break

if move2:
    from_sq2, to_sq2, flags2 = decode_move(move2)
    print(f"  Found: {from_sq2}->{to_sq2} (flags={flags2})")
    state_before_move2 = board.state.copy()
    undo2 = board.make_move(move2)
    print(f"  After move: {board.to_fen()}")
    print(board.display())
    
    # Now unmake move 2
    print(f"\nUnmaking move 2...")
    print(f"  undo_info: {undo2}")
    board.unmake_move(move2, undo2)
    print(f"  After unmake: {board.to_fen()}")
    print(board.display())
    
    # Check if state matches
    if np.array_equal(board.state, state_before_move2):
        print("  ✓ State matches!")
    else:
        print("  ✗ State DOES NOT match!")
        print(f"  Expected FEN: {Board.from_state(state_before_move2, 1).to_fen()}")
    
    # Now unmake move 1
    print(f"\nUnmaking move 1...")
    board.unmake_move(move1, undo1)
    print(f"  After unmake: {board.to_fen()}")
    print(board.display())
    
    # Check if we're back to start
    original_board = Board.from_fen(fen)
    if np.array_equal(board.state, original_board.state):
        print("  ✓ Back to original state!")
    else:
        print("  ✗ NOT back to original!")
        print(f"  Expected: {fen}")

else:
    print("  NOT FOUND")
    print(f"  Available moves from this position:")
    for i, m in enumerate(moves2[:10]):  # Show first 10
        f, t, flags = decode_move(m)
        print(f"    {i+1}. {f}->{t} (flags={flags})")
