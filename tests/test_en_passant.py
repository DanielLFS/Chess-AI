"""Test en passant specifically."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move
from engine.moves import Moves

def test_en_passant():
    """Test en passant move generation and legality."""
    
    # Position with en passant available
    # After e2-e4, black can capture with d4 pawn
    fen = "rnbqkbnr/pppppppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    board = Board(fen=fen)
    
    print("Testing en passant")
    print("="*80)
    print(board.display())
    print(f"FEN: {board.to_fen()}\n")
    
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    # Find en passant moves
    ep_moves = []
    for move in legal_moves:
        from_sq, to_sq, flags = decode_move(move)
        if flags == 4:  # FLAG_EN_PASSANT
            ep_moves.append((from_sq, to_sq))
            print(f"Found EP: {from_sq}->{to_sq}")
    
    print(f"\nTotal en passant moves: {len(ep_moves)}")
    
    if len(ep_moves) > 0:
        # Test making and unmaking
        for from_sq, to_sq in ep_moves:
            # Find the move
            test_move = None
            for move in legal_moves:
                f, t, fl = decode_move(move)
                if f == from_sq and t == to_sq and fl == 4:
                    test_move = move
                    break
            
            if test_move:
                print(f"\nTesting EP capture {from_sq}->{to_sq}")
                undo_info = board.make_move(test_move)
                print(f"After EP: {board.to_fen()}")
                print(board.display())
                
                # Unmake
                board.unmake_move(test_move, undo_info)
                print(f"After unmake: {board.to_fen()}")
                
                # Verify it matches original
                if board.to_fen() == fen:
                    print("✓ Unmake successful")
                else:
                    print("✗ Unmake FAILED")
    
    # Check Kiwipete for any en passant
    print("\n" + "="*80)
    print("Checking Kiwipete for en passant")
    print("="*80)
    
    kiwipete = Board(fen="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    print(f"EP square in Kiwipete: {kiwipete.en_passant_target}")
    
    # Make a double pawn push to create EP opportunity
    moves = Moves(kiwipete).generate()
    # Find g2-g4
    g2g4 = None
    for move in moves:
        from_sq, to_sq, flags = decode_move(move)
        if from_sq == 54 and to_sq == 38:  # g2-g4
            g2g4 = move
            break
    
    if g2g4:
        print(f"\nMaking g2-g4...")
        undo = kiwipete.make_move(g2g4)
        print(f"FEN: {kiwipete.to_fen()}")
        print(f"EP square: {kiwipete.en_passant_target}")
        
        # Now check if black has EP captures
        black_moves = Moves(kiwipete).generate()
        black_ep = []
        for move in black_moves:
            from_sq, to_sq, flags = decode_move(move)
            if flags == 4:
                black_ep.append((from_sq, to_sq))
        
        print(f"Black EP captures available: {len(black_ep)}")
        for from_sq, to_sq in black_ep:
            print(f"  {from_sq}->{to_sq}")

if __name__ == '__main__':
    test_en_passant()
