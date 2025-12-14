"""Test if unmake is truly reversible in all cases."""
import sys
sys.path.insert(0, 'c:/Users/narut/OneDrive/Documents/GitHub/Chess-AI')

from engine.board import Board
from engine.moves import Moves
import numpy as np

def test_unmake_reversibility(fen, depth=2):
    """Recursively test that make/unmake is perfectly reversible."""
    board = Board.from_fen(fen)
    errors = []
    
    def recurse(depth_left, path=[]):
        if depth_left == 0:
            return
        
        # Save state
        original_state = board.state.copy()
        original_fen = board.to_fen()
        
        moves_obj = Moves(board)
        legal_moves = moves_obj.generate()
        
        for i, move in enumerate(legal_moves):
            from engine.board import decode_move
            from_sq, to_sq, flags = decode_move(move)
            
            # Make move
            undo_info = board.make_move(move)
            
            # Recurse
            recurse(depth_left - 1, path + [f"{from_sq}->{to_sq}"])
            
            # Unmake move
            board.unmake_move(move, undo_info)
            
            # Check if state is restored
            if not np.array_equal(board.state, original_state):
                errors.append({
                    'path': path + [f"{from_sq}->{to_sq}"],
                    'original_fen': original_fen,
                    'after_unmake_fen': board.to_fen(),
                    'move': f"{from_sq}->{to_sq} (flags={flags})"
                })
                print(f"X UNMAKE ERROR after path: {' -> '.join(path + [f'{from_sq}->{to_sq}'])}")
                print(f"  Original FEN: {original_fen}")
                print(f"  After unmake: {board.to_fen()}")
                
                # Restore state to continue testing
                board.state = original_state.copy()
    
    recurse(depth)
    return errors

print("=" * 70)
print("TESTING UNMAKE REVERSIBILITY")
print("=" * 70)

# Test Kiwipete
print("\n1. Testing Kiwipete at depth 2...")
fen1 = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
errors1 = test_unmake_reversibility(fen1, depth=2)
if not errors1:
    print("   [OK] All unmakes are reversible!")
else:
    print(f"   [ERROR] Found {len(errors1)} unmake errors")

# Test Position 3
print("\n2. Testing Position 3 at depth 2...")
fen2 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
errors2 = test_unmake_reversibility(fen2, depth=2)
if not errors2:
    print("   [OK] All unmakes are reversible!")
else:
    print(f"   [ERROR] Found {len(errors2)} unmake errors")

# Test Position 4
print("\n3. Testing Position 4 at depth 2...")
fen3 = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"
errors3 = test_unmake_reversibility(fen3, depth=2)
if not errors3:
    print("   [OK] All unmakes are reversible!")
else:
    print(f"   [ERROR] Found {len(errors3)} unmake errors")

print("\n" + "=" * 70)
if not errors1 and not errors2 and not errors3:
    print("[OK] ALL TESTS PASSED - Unmake is fully reversible")
    print("The perft discrepancies must be due to something else...")
else:
    print("[ERROR] UNMAKE HAS BUGS - This explains the perft discrepancies")
