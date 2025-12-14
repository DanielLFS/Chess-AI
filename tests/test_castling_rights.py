"""Find specific positions where move generation differs from expected."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move
from engine.moves import Moves

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

def find_castling_bug():
    """Check if castling rights are being updated correctly."""
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = Board(fen=fen)
    
    print("Testing castling rights updates")
    print("="*80)
    print(f"Initial FEN: {board.to_fen()}")
    print(f"Initial castling rights: {bin(board.castling_rights)}")
    
    # Test 1: After white castles kingside, black should still have both castling rights
    board1 = Board(fen=fen)
    moves = Moves(board1).generate()
    
    # Find O-O move
    oo_move = None
    for m in moves:
        from_sq, to_sq, flags = decode_move(m)
        if from_sq == 60 and to_sq == 62 and flags == 5:  # e1-g1, kingside
            oo_move = m
            break
    
    if oo_move:
        print(f"\nMaking white O-O...")
        undo_info = board1.make_move(oo_move)
        print(f"After O-O: {board1.to_fen()}")
        print(f"Castling rights: {bin(board1.castling_rights)} (should be kq = 0b1100)")
        
        # Now check black's moves
        black_moves = Moves(board1).generate()
        print(f"Black has {len(black_moves)} legal moves")
        
        # Find black's castling moves
        black_castles = []
        for m in black_moves:
            from_sq, to_sq, flags = decode_move(m)
            if flags == 5 or flags == 6:
                black_castles.append((from_sq, to_sq, flags))
        
        print(f"Black castling moves: {black_castles}")
        if len(black_castles) == 2:
            print("✓ Black can still castle both sides")
        else:
            print(f"✗ BLACK CASTLING BUG: Should have 2 castling moves, got {len(black_castles)}")
    
    # Test 2: Check if we're allowing castling when pieces moved and came back
    print("\n" + "="*80)
    print("Test 2: Moving rook and back (should lose castling)")
    print("="*80)
    
    board2 = Board(fen=fen)
    moves2 = Moves(board2).generate()
    
    # Find h1-g1 (rook move)
    rook_move = None
    for m in moves2:
        from_sq, to_sq, flags = decode_move(m)
        if from_sq == 63 and to_sq == 62:  # h1-g1
            rook_move = m
            break
    
    if rook_move:
        print(f"Moving H1 rook to G1...")
        undo1 = board2.make_move(rook_move)
        print(f"FEN: {board2.to_fen()}")
        print(f"Castling rights: {bin(board2.castling_rights)} (should lose K = white kingside)")
        
        # Black moves something
        black_moves2 = Moves(board2).generate()
        any_black_move = black_moves2[0]
        undo2 = board2.make_move(any_black_move)
        
        # White moves rook back
        white_moves3 = Moves(board2).generate()
        rook_back = None
        for m in white_moves3:
            from_sq, to_sq, flags = decode_move(m)
            if from_sq == 62 and to_sq == 63:  # g1-h1
                rook_back = m
                break
        
        if rook_back:
            undo3 = board2.make_move(rook_back)
            print(f"After moving rook back: {board2.to_fen()}")
            print(f"Castling rights: {bin(board2.castling_rights)} (should still NOT have K)")
            
            # It's black's turn now, so make a black move first
            black_moves4 = Moves(board2).generate()
            any_black_move2 = black_moves4[0]
            undo4 = board2.make_move(any_black_move2)
            
            print(f"After black moves: {board2.to_fen()}")
            
            # NOW check if white can castle (it's white's turn)
            white_moves5 = Moves(board2).generate()
            white_castles = []
            for m in white_moves5:
                from_sq, to_sq, flags = decode_move(m)
                if flags == 5 and from_sq == 60:  # Kingside castle from e1
                    white_castles.append(m)
                    print(f"  Found WHITE kingside castle: {from_sq}->{to_sq}")
            
            if len(white_castles) == 0:
                print("✓ Correctly prevents castling after rook moved")
            else:
                print(f"✗ BUG: Allows WHITE castling after rook moved! {len(white_castles)} moves")

if __name__ == '__main__':
    find_castling_bug()
