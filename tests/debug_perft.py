"""Debug perft failures."""
import numpy as np
from engine.board import Board, decode_move
from engine.moves import Moves

def check_duplicate_moves(fen: str):
    """Check if we're generating duplicate moves."""
    print(f"\nChecking: {fen}")
    board = Board(fen=fen)
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    print(f"Total legal moves: {len(legal_moves)}")
    
    # Check for duplicates
    unique_moves = set(legal_moves)
    if len(unique_moves) != len(legal_moves):
        print(f"WARNING: Found duplicates! Unique: {len(unique_moves)}, Total: {len(legal_moves)}")
        # Find duplicates
        seen = {}
        for move in legal_moves:
            if move in seen:
                seen[move] += 1
            else:
                seen[move] = 1
        
        for move, count in seen.items():
            if count > 1:
                from_sq, to_sq, flags = decode_move(move)
                print(f"  Duplicate: {from_sq}->{to_sq} (flags={flags}) x{count}")
    else:
        print("No duplicates found")
    
    return len(legal_moves)

if __name__ == '__main__':
    # Test positions that are failing
    check_duplicate_moves("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")  # Position 3
    check_duplicate_moves("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")  # Kiwipete
    check_duplicate_moves("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")  # Position 4
    check_duplicate_moves("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8")  # Position 5

