"""Test promotion move generation."""
import numpy as np
from engine.board import Board, decode_move, square_to_coords, get_bit, WP
from engine.moves import Moves

def test_promotion():
    """Test position 4 which has promotion."""
    # r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1
    board = Board(fen="r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    print(board.display())
    print(f"FEN: {board.to_fen()}\n")
    
    # Check white pawn positions
    print("White pawn bitboard:")
    pawns = board.state[WP]
    for sq in range(64):
        if get_bit(pawns, sq):
            row, col = square_to_coords(sq)
            print(f"  Pawn at {chr(ord('a')+col)}{8-row} (square {sq}, row={row}, col={col})")
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    print(f"\nLegal moves: {len(legal_moves)}")
    
    flag_names = {
        0: "NORMAL", 4: "EP",
        5: "CASTLE_K", 6: "CASTLE_Q",
        7: "PROMO_Q", 8: "PROMO_R", 9: "PROMO_B", 10: "PROMO_N"
    }
    
    # Print all moves
    for move in legal_moves:
        from_sq, to_sq, flags = decode_move(move)
        from_row, from_col = square_to_coords(from_sq)
        to_row, to_col = square_to_coords(to_sq)
        flag_str = flag_names.get(flags, f"FLAG_{flags}")
        
        # Check piece type
        piece_name = "?"
        for idx, name in enumerate(["P", "N", "B", "R", "Q", "K"]):
            if get_bit(board.state[idx], from_sq):
                piece_name = name
                break
        
        print(f"{piece_name} {chr(ord('a')+from_col)}{8-from_row} -> {chr(ord('a')+to_col)}{8-to_row} ({flag_str})")

if __name__ == '__main__':
    test_promotion()
