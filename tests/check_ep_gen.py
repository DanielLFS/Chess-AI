"""Check if EP moves are generated but filtered out."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move
from engine.moves import Moves, generate_pseudo_legal_moves

def check_ep_filtering():
    fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    board = Board(fen=fen)
    
    print(f"FEN: {fen}\n")
    
    # Get pseudo-legal moves
    pseudo = generate_pseudo_legal_moves(board.state, 1)  # color=1 for black
    print(f"Pseudo-legal moves: {len(pseudo)}")
    
    # Find EP moves in pseudo-legal
    ep_pseudo = []
    for move in pseudo:
        from_sq, to_sq, flags = decode_move(move)
        if flags == 7:  # FLAG_EN_PASSANT = 7
            ep_pseudo.append((from_sq, to_sq))
            print(f"  Pseudo EP: {from_sq}->{to_sq}")
    
    # Get legal moves
    legal = Moves(board).generate()
    print(f"\nLegal moves: {len(legal)}")
    
    # Find EP moves in legal
    ep_legal = []
    for move in legal:
        from_sq, to_sq, flags = decode_move(move)
        if flags == 7:  # FLAG_EN_PASSANT = 7
            ep_legal.append((from_sq, to_sq))
            print(f"  Legal EP: {from_sq}->{to_sq}")
    
    if len(ep_pseudo) > 0 and len(ep_legal) == 0:
        print("\n✗ EP moves are generated but filtered out as illegal!")
    elif len(ep_pseudo) == 0:
        print("\n✗ EP moves are NOT being generated at all!")
    else:
        print(f"\n✓ EP moves: {len(ep_legal)}")

if __name__ == '__main__':
    check_ep_filtering()
