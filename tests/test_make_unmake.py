"""Test make/unmake consistency."""
import numpy as np
from engine.board import Board
from engine.moves import Moves

def test_make_unmake():
    """Test that make/unmake properly restores state."""
    board = Board(fen="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    original_fen = board.to_fen()
    print(f"Original: {original_fen}")
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    print(f"\nTesting {len(legal_moves)} moves...")
    
    for i, move in enumerate(legal_moves):
        from engine.board import decode_move
        from_sq, to_sq, flags = decode_move(move)
        
        # Make move
        undo_info = board.make_move(move)
        after_fen = board.to_fen()
        
        # Unmake move
        board.unmake_move(move, undo_info)
        restored_fen = board.to_fen()
        
        # Check if restored
        if restored_fen != original_fen:
            print(f"\n✗ Move {i+1}: {from_sq}->{to_sq} (flags={flags})")
            print(f"  Original:  {original_fen}")
            print(f"  After:     {after_fen}")
            print(f"  Restored:  {restored_fen}")
            print(f"  MISMATCH!")
            return False
    
    print(f"✓ All {len(legal_moves)} moves correctly unmade")
    return True

if __name__ == '__main__':
    test_make_unmake()
