"""Check if the failing move is en passant."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board, decode_move, FLAG_EN_PASSANT
from engine.moves import Moves

# Kiwipete
fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
board = Board.from_fen(fen)

print("Starting position:")
print(board.display())

# Move 1: a2-a4 (48->32) - should set EP square to a3 (40)
moves1 = Moves(board).generate()
move1 = None
for m in moves1:
    f, t, flags = decode_move(m)
    if f == 48 and t == 32:  # a2-a4
        move1 = m
        break

if move1:
    from_sq1, to_sq1, flags1 = decode_move(move1)
    print(f"\nMove 1: {from_sq1}->{to_sq1} (flags={flags1})")
    undo1 = board.make_move(move1)
    fen_after_move1 = board.to_fen()
    print(f"After move: {fen_after_move1}")
    
    # Check EP square
    from engine.board import unpack_ep_square
    ep_sq = unpack_ep_square(board.state[13])
    print(f"EP square: {ep_sq} (should be 40 for a3)")
    print(board.display())
    
    # Move 2: b4xa3 (33->40)
    moves2 = Moves(board).generate()
    move2 = None
    for m in moves2:
        f, t, flags = decode_move(m)
        if f == 33 and t == 40:  # b4xa3
            move2 = m
            break
    
    if move2:
        from_sq2, to_sq2, flags2 = decode_move(move2)
        print(f"\nMove 2: {from_sq2}->{to_sq2} (flags={flags2})")
        if flags2 == FLAG_EN_PASSANT:
            print("  --> THIS IS EN PASSANT!")
        else:
            print(f"  --> This is a NORMAL CAPTURE (flags should be {FLAG_EN_PASSANT} for EP)")
        
        undo2 = board.make_move(move2)
        print(f"After move: {board.to_fen()}")
        print(board.display())
        
        # Now unmake
        print("\nUnmaking move 2...")
        board.unmake_move(move2, undo2)
        fen_after_unmake2 = board.to_fen()
        print(f"After unmake: {fen_after_unmake2}")
        print(f"Expected:     {fen_after_move1}")
        if fen_after_unmake2 == fen_after_move1:
            print("  [OK] Matches!")
        else:
            print("  [ERROR] Does not match!")
            print(board.display())
    else:
        print("\nMove 2 not found!")
        print("Available moves:")
        for i, m in enumerate(moves2[:15]):
            f, t, flags = decode_move(m)
            print(f"  {f}->{t} (flags={flags})")
