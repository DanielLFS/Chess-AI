"""Debug why promotion captures aren't generated."""
import numpy as np
from engine.board import (Board, decode_move, square_to_coords, coords_to_square,
                          get_bit, WP, BP, OCCUPIED)

def debug_promotion():
    """Debug position 4 promotion."""
    board = Board(fen="r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    
    # Check a7 pawn
    a7_sq = coords_to_square(1, 0)  # Row 1 = 7th rank, col 0 = a-file
    print(f"Pawn on a7? {get_bit(board.state[WP], a7_sq)}")
    print(f"a7 square number: {a7_sq}")
    
    # Check b7 (diagonal capture target)
    b7_sq = coords_to_square(1, 1)
    print(f"\nBlack pawn on b7? {get_bit(board.state[BP], b7_sq)}")
    print(f"b7 square number: {b7_sq}")
    
    # Check all black pieces on b7
    print(f"\nPieces on b7:")
    for idx in range(6, 12):
        if get_bit(board.state[idx], b7_sq):
            piece_names = ['p', 'n', 'b', 'r', 'q', 'k']
            print(f"  Black {piece_names[idx-6]}")
    
    # Check a8 (forward target)
    a8_sq = coords_to_square(0, 0)
    print(f"\nOccupied on a8? {get_bit(board.state[OCCUPIED], a8_sq)}")
    print(f"a8 square number: {a8_sq}")
    
    # Check pseudo-legal pawn moves
    from numba.typed import List
    from engine.moves import generate_pawn_moves
    
    moves = List.empty_list(np.uint16)
    generate_pawn_moves(board.state, 0, moves)  # color=0 for white
    
    print(f"\nPseudo-legal pawn moves: {len(moves)}")
    for move in moves:
        from_sq, to_sq, flags = decode_move(move)
        from_row, from_col = square_to_coords(from_sq)
        to_row, to_col = square_to_coords(to_sq)
        flag_names = {
            0: "NORMAL", 4: "EP",
            7: "PROMO_Q", 8: "PROMO_R", 9: "PROMO_B", 10: "PROMO_N"
        }
        flag_str = flag_names.get(flags, f"FLAG_{flags}")
        print(f"  {chr(ord('a')+from_col)}{8-from_row} -> {chr(ord('a')+to_col)}{8-to_row} ({flag_str})")

if __name__ == '__main__':
    debug_promotion()
