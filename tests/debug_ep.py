"""Debug en passant square calculation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, unpack_ep_square, META, square_to_coords, coords_to_square
from engine.moves import Moves

def debug_ep():
    # Black to move, e3 is EP target
    fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    board = Board(fen=fen)
    
    print(f"FEN: {fen}")
    print(board.display())
    
    # Check EP square from metadata
    ep_sq = unpack_ep_square(board.state[META])
    print(f"\nEP square from metadata: {ep_sq}")
    
    if ep_sq >= 0:
        row, col = square_to_coords(ep_sq)
        print(f"EP coords: row={row}, col={col}")
        print(f"EP algebraic: {chr(ord('a')+col)}{8-row}")
    
    # e3 should be square 44 (row=5, col=4)
    e3_sq = coords_to_square(5, 4)
    print(f"\ne3 square number: {e3_sq}")
    
    # Check black pawn on d4
    d4_sq = coords_to_square(4, 3)
    print(f"d4 square number: {d4_sq}")
    
    from engine.board import BP, get_bit
    has_pawn = get_bit(board.state[BP], d4_sq)
    print(f"Black pawn on d4: {has_pawn}")
    
    # Manually calculate where the capture should go
    # Black pawn on d4 (row=4, col=3) capturing to e3 (row=5, col=4)
    from_row, from_col = 4, 3
    # For black (color=1), capture is row + 1, col ± 1
    cap_row = from_row + 1
    cap_col_right = from_col + 1  # = 4 (e-file)
    cap_sq = coords_to_square(cap_row, cap_col_right)
    print(f"\nCalculated capture square for d4 pawn: {cap_sq}")
    print(f"Capture coords: row={cap_row}, col={cap_col_right}")
    print(f"Matches e3? {cap_sq == e3_sq}")
    print(f"Matches EP square? {cap_sq == ep_sq}")
    
    # Now check what moves are generated
    moves = Moves(board).generate()
    print(f"\nTotal moves: {len(moves)}")
    
    # Manually call generate_pawn_moves to see what happens
    from numba.typed import List
    import numpy as np
    from engine.moves import generate_pawn_moves
    
    pawn_moves = List.empty_list(np.uint16)
    generate_pawn_moves(board.state, 1, pawn_moves)  # color=1 for black
    
    print(f"Pawn moves generated: {len(pawn_moves)}")
    
    from engine.board import decode_move
    for move in pawn_moves:
        from_sq, to_sq, flags = decode_move(move)
        print(f"  {from_sq}->{to_sq} (flags={flags})")

if __name__ == '__main__':
    debug_ep()
