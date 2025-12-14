"""Focus on where the divergence starts."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board
from perft import perft, perft_divide

# Kiwipete - error starts at depth 3
print("=" * 70)
print("KIWIPETE - Testing depths 1-3")
print("=" * 70)
fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
board = Board.from_fen(fen)

for depth in [1, 2, 3]:
    nodes = perft(board, depth)
    expected = [48, 2039, 97862, 4085603][depth - 1] if depth <= 4 else 0
    match = "✓" if nodes == expected else "✗"
    diff = nodes - expected if expected > 0 else 0
    print(f"Depth {depth}: {nodes:,} nodes (expected {expected:,}) {match} (diff: {diff:+,})")

print("\n" + "=" * 70)
print("Let's check a few moves from depth 2 divide to see where it diverges")
print("=" * 70)

# Test specific moves that might have issues
test_moves = [
    ("d5d6", "d5-d6 - pawn push"),
    ("d5e6", "d5xe6 - pawn capture (en passant target?)"),
    ("e5d7", "Nxd7 - knight capture"),
    ("e1g1", "O-O - kingside castle"),
    ("e1c1", "O-O-O - queenside castle"),
]

for move_str, description in test_moves:
    # Parse move
    from_sq = (ord(move_str[0]) - ord('a')) + (8 - int(move_str[1])) * 8
    to_sq = (ord(move_str[2]) - ord('a')) + (8 - int(move_str[3])) * 8
    
    # Make move
    from engine.moves import Moves
    from engine.board import encode_move, FLAG_NORMAL
    
    moves_obj = Moves(board)
    legal_moves = moves_obj.generate()
    
    # Find the move
    found_move = None
    for m in legal_moves:
        from engine.board import decode_move
        f, t, flags = decode_move(m)
        if f == from_sq and t == to_sq:
            found_move = m
            break
    
    if found_move is not None:
        undo_info = board.make_move(found_move)
        nodes_after = perft(board, 2)
        board.unmake_move(found_move, undo_info)
        print(f"{move_str}: {nodes_after:,} nodes at depth 2 - {description}")
    else:
        print(f"{move_str}: NOT FOUND - {description}")

print("\n" + "=" * 70)
print("POSITION 3 - Testing depths 1-4")
print("=" * 70)
fen3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
board3 = Board.from_fen(fen3)

expected_vals = [14, 191, 2812, 43238]
for depth in [1, 2, 3, 4]:
    nodes = perft(board3, depth)
    expected = expected_vals[depth - 1]
    match = "✓" if nodes == expected else "✗"
    diff = nodes - expected
    print(f"Depth {depth}: {nodes:,} nodes (expected {expected:,}) {match} (diff: {diff:+,})")
