"""Manually trace through EP generation logic."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import (Board, unpack_ep_square, META, coords_to_square, 
                          square_to_coords, get_bit, BP, clear_bit, lsb)
import numpy as np

def manual_ep_check():
    fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    board = Board(fen=fen)
    
    print("Manual EP generation trace")
    print("="*80)
    
    # Get black pawns
    pawns_bb = board.state[BP]
    print(f"Black pawn bitboard: {bin(pawns_bb)}")
    
    # Get EP square
    ep_square = unpack_ep_square(board.state[META])
    print(f"EP square: {ep_square}")
    
    # Get opponent pieces (white)
    opponent_pieces = np.uint64(0)
    for i in range(6):
        opponent_pieces |= board.state[i]  # WP, WN, WB, WR, WQ, WK
    
    print(f"\nChecking each black pawn:")
    temp_pawns = pawns_bb
    pawn_count = 0
    while temp_pawns:
        from_sq = lsb(temp_pawns)
        temp_pawns = clear_bit(temp_pawns, from_sq)
        
        row, col = square_to_coords(from_sq)
        print(f"\n  Pawn #{pawn_count+1} at square {from_sq} (row={row}, col={col})")
        
        # Check captures
        for cap_offset in [-1, 1]:
            cap_col = col + cap_offset
            if 0 <= cap_col < 8:
                # Black captures: row + 1
                cap_row = row + 1
                cap_sq = coords_to_square(cap_row, cap_col)
                
                print(f"    Capture offset {cap_offset:+d}: cap_sq={cap_sq} (row={cap_row}, col={cap_col})")
                
                has_opponent = get_bit(opponent_pieces, cap_sq)
                print(f"      Has opponent piece: {has_opponent}")
                
                if ep_square >= 0:
                    matches_ep = (cap_sq == ep_square)
                    print(f"      EP available: yes, matches: {matches_ep}")
                    
                    if not has_opponent and matches_ep:
                        print(f"      ✓ SHOULD GENERATE EP MOVE!")
                else:
                    print(f"      EP available: no")
        
        pawn_count += 1

if __name__ == '__main__':
    manual_ep_check()
