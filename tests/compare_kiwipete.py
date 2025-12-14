"""Compare our perft divide with known reference values for Kiwipete.

Reference values from https://www.chessprogramming.org/Perft_Results
Kiwipete position: r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -

Known perft divide at depth 1 (from Stockfish):
a2a3: 43
a2a4: 44
b2b3: 44
b2b4: 44
c3b1: 44
c3a4: 44
c3b5: 44
c3d1: 44
d2c1: 44
d2e3: 45
d2f4: 44
d2g5: 44
d2h6: 44
d5d6: 43
d5e6: 48
e1c1: 43
e1d1: 43
e1f1: 42
e2a6: 43
e2b5: 44
e2c4: 44
e2d1: 39
e2d3: 44
e2f1: 44
e5c4: 41
e5c6: 44
e5d3: 40
e5d7: 46
e5f7: 45
e5g4: 42
e5g6: 44
f3d3: 44
f3e3: 46
f3f4: 45
f3f5: 51
f3f6: 46
f3g3: 47
f3g4: 46
f3h3: 50
f3h5: 48
g2g3: 42
g2g4: 41
g2h3: 44
h1f1: 43
h1g1: 44
e1g1: 46
Total: 2039
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move, square_to_coords
from engine.moves import Moves

# Reference from Stockfish
REFERENCE = {
    'a2a3': 43, 'a2a4': 44, 'b2b3': 44, 'b2b4': 44,
    'c3b1': 44, 'c3a4': 44, 'c3b5': 44, 'c3d1': 44,
    'd2c1': 44, 'd2e3': 45, 'd2f4': 44, 'd2g5': 44, 'd2h6': 44,
    'd5d6': 43, 'd5e6': 48,
    'e1c1': 43, 'e1d1': 43, 'e1f1': 42, 'e1g1': 46,
    'e2a6': 43, 'e2b5': 44, 'e2c4': 44, 'e2d1': 39, 'e2d3': 44, 'e2f1': 44,
    'e5c4': 41, 'e5c6': 44, 'e5d3': 40, 'e5d7': 46, 'e5f7': 45, 'e5g4': 42, 'e5g6': 44,
    'f3d3': 44, 'f3e3': 46, 'f3f4': 45, 'f3f5': 51, 'f3f6': 46,
    'f3g3': 47, 'f3g4': 46, 'f3h3': 50, 'f3h5': 48,
    'g2g3': 42, 'g2g4': 41, 'g2h3': 44,
    'h1f1': 43, 'h1g1': 44,
}

def perft(board: Board, depth: int) -> int:
    """Count leaf nodes."""
    if depth == 0:
        return 1
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    if depth == 1:
        return len(legal_moves)
    
    nodes = 0
    for move in legal_moves:
        undo_info = board.make_move(move)
        nodes += perft(board, depth - 1)
        board.unmake_move(move, undo_info)
    
    return nodes

def main():
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = Board(fen=fen)
    
    print("Comparing Kiwipete perft divide (depth 1) with reference")
    print("="*80)
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    our_results = {}
    discrepancies = []
    
    for move in legal_moves:
        from_sq, to_sq, flags = decode_move(move)
        from_row, from_col = square_to_coords(from_sq)
        to_row, to_col = square_to_coords(to_sq)
        
        move_str = f"{chr(ord('a')+from_col)}{8-from_row}{chr(ord('a')+to_col)}{8-to_row}"
        
        undo_info = board.make_move(move)
        count = len(Moves(board).generate())
        board.unmake_move(move, undo_info)
        
        our_results[move_str] = count
        
        if move_str in REFERENCE:
            expected = REFERENCE[move_str]
            if count != expected:
                discrepancies.append((move_str, count, expected))
                print(f"✗ {move_str}: {count} (expected {expected}, diff={count-expected})")
        else:
            print(f"? {move_str}: {count} (not in reference)")
    
    # Check for missing moves
    for ref_move in REFERENCE:
        if ref_move not in our_results:
            print(f"✗ MISSING: {ref_move} (expected {REFERENCE[ref_move]})")
    
    print(f"\n{'='*80}")
    print(f"Our total: {sum(our_results.values())}")
    print(f"Reference total: {sum(REFERENCE.values())}")
    print(f"Discrepancies: {len(discrepancies)}")
    
    if discrepancies:
        print(f"\nTotal difference: {sum(c - e for _, c, e in discrepancies)}")

if __name__ == '__main__':
    main()
