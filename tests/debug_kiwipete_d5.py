"""Debug Kiwipete depth 5 discrepancy."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board, decode_move
from engine.moves import Moves
from perft import perft, perft_divide

# Kiwipete position
fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
board = Board.from_fen(fen)

print("=" * 70)
print("KIWIPETE DEPTH 5 INVESTIGATION")
print("=" * 70)
print(f"\nFEN: {fen}")
print()

# Test each depth
for depth in range(1, 6):
    nodes = perft(board, depth)
    expected = [48, 2039, 97862, 4085603, 193491423][depth - 1]
    diff = nodes - expected
    pct = (diff / expected * 100) if expected > 0 else 0
    status = "PASS" if diff == 0 else "FAIL"
    print(f"Depth {depth}: {nodes:>12,} nodes | Expected: {expected:>12,} | Diff: {diff:>+9,} ({pct:>+6.3f}%) | {status}")

print("\n" + "=" * 70)
print("DIVIDE AT DEPTH 4 - Looking for moves with wrong counts")
print("=" * 70)

# Get divide at depth 4 to see which moves might have issues
import time
from collections import defaultdict

moves_obj = Moves(board)
legal_moves = moves_obj.generate()

print(f"\nAnalyzing {len(legal_moves)} moves at depth 4...\n")

move_counts = []
for move in legal_moves:
    from_sq, to_sq, flags = decode_move(move)
    
    undo_info = board.make_move(move)
    count = perft(board, 4)
    board.unmake_move(move, undo_info)
    
    move_counts.append((from_sq, to_sq, flags, count))

# Sort by count descending to see largest contributors
move_counts.sort(key=lambda x: x[3], reverse=True)

print("Top 10 moves by node count:")
for i, (f, t, flags, count) in enumerate(move_counts[:10], 1):
    print(f"  {i:2d}. {f:2d}->{t:2d} (flags={flags}): {count:>10,} nodes")

print(f"\nTotal from divide: {sum(c for _, _, _, c in move_counts):,} nodes")
print(f"Expected depth 5:  {193491423:,} nodes")
print(f"Difference:        {sum(c for _, _, _, c in move_counts) - 193491423:+,} nodes")

# Check for any suspicious patterns
print("\n" + "=" * 70)
print("CHECKING FOR SUSPICIOUS PATTERNS")
print("=" * 70)

# Group by flag type
from collections import Counter
flag_counts = Counter(flags for _, _, flags, _ in move_counts)
print(f"\nMoves by flag type:")
for flag, count in sorted(flag_counts.items()):
    flag_names = {0: "NORMAL", 1: "PROMO_Q", 2: "PROMO_R", 3: "PROMO_B", 4: "PROMO_N", 
                  5: "CASTLE_K", 6: "CASTLE_Q", 7: "EN_PASSANT"}
    print(f"  Flag {flag} ({flag_names.get(flag, 'UNKNOWN')}): {count} moves")

# Check for duplicate moves
move_signatures = [(f, t, flags) for f, t, flags, _ in move_counts]
if len(move_signatures) != len(set(move_signatures)):
    print("\n[WARNING] DUPLICATE MOVES DETECTED!")
    seen = set()
    for sig in move_signatures:
        if sig in seen:
            print(f"  Duplicate: {sig}")
        seen.add(sig)
else:
    print("\n[OK] No duplicate moves detected")

# Check if any moves leave king in check (shouldn't happen with legal move gen)
print("\n" + "=" * 70)
print("VERIFYING ALL MOVES ARE LEGAL")
print("=" * 70)

illegal_count = 0
for f, t, flags, _ in move_counts:
    from engine.board import encode_move
    move = encode_move(f, t, flags)
    undo_info = board.make_move(move)
    
    # Check if our king is in check (would be illegal)
    from engine.board import unpack_side
    current_side = unpack_side(board.state[13])
    opponent_side = 1 - current_side
    
    # Find our king (the side that just moved)
    from engine.moves import find_king_square, is_square_attacked
    our_king_sq = find_king_square(board.state, opponent_side)
    
    if is_square_attacked(board.state, our_king_sq, current_side):
        illegal_count += 1
        print(f"[ERROR] Illegal move: {f}->{t} (flags={flags}) leaves king in check!")
    
    board.unmake_move(move, undo_info)

if illegal_count == 0:
    print("[OK] All moves are legal")
else:
    print(f"[ERROR] Found {illegal_count} illegal moves!")
