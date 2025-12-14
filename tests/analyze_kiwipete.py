"""Deep dive into Kiwipete to find the 1,770 extra nodes at depth 3."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board, decode_move, square_to_coords
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

def perft_divide(board: Board, depth: int):
    """Show perft for each move."""
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    results = []
    total = 0
    for move in legal_moves:
        from_sq, to_sq, flags = decode_move(move)
        undo_info = board.make_move(move)
        count = perft(board, depth - 1)
        board.unmake_move(move, undo_info)
        
        results.append((from_sq, to_sq, flags, count))
        total += count
    
    return results, total

def main():
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = Board(fen=fen)
    
    print("Kiwipete Depth 2 Analysis")
    print("="*80)
    
    results, total = perft_divide(board, 2)
    print(f"Total: {total} (expected: 2,039)")
    print()
    
    # Now check depth 3 for each move that might be suspicious
    print("Kiwipete Depth 3 Analysis - Finding moves with wrong counts")
    print("="*80)
    
    # Known good reference for depth 3 per move (from Stockfish/other engines)
    # We need to find which moves at depth 1 lead to wrong counts at depth 2
    
    moves_gen = Moves(board)
    moves_d1 = moves_gen.generate()
    
    suspicious_moves = []
    
    for move in moves_d1:
        from_sq, to_sq, flags = decode_move(move)
        from_row, from_col = square_to_coords(from_sq)
        to_row, to_col = square_to_coords(to_sq)
        
        # Make the move
        undo_info = board.make_move(move)
        
        # Get move count at depth 2 from this position
        count_d2 = perft(board, 2)
        
        # Unmake
        board.unmake_move(move, undo_info)
        
        # Store for later analysis
        move_str = f"{chr(ord('a')+from_col)}{8-from_row}{chr(ord('a')+to_col)}{8-to_row}"
        suspicious_moves.append((move_str, from_sq, to_sq, flags, count_d2))
    
    # Sort by count to see outliers
    suspicious_moves.sort(key=lambda x: x[4], reverse=True)
    
    print("\nAll moves at depth 1 with their depth-2 counts:")
    print(f"{'Move':<8} {'From':<5} {'To':<5} {'Flags':<6} {'Depth-2 Count':<15}")
    print("-"*50)
    for move_str, from_sq, to_sq, flags, count in suspicious_moves:
        print(f"{move_str:<8} {from_sq:<5} {to_sq:<5} {flags:<6} {count:<15}")
    
    # Now let's check castling moves specifically
    print("\n" + "="*80)
    print("Checking castling moves specifically:")
    print("="*80)
    
    for move_str, from_sq, to_sq, flags, count in suspicious_moves:
        if flags == 5 or flags == 6:  # Castling flags
            flag_name = "O-O" if flags == 5 else "O-O-O"
            print(f"\n{flag_name}: {move_str} -> depth-2 count = {count}")
            
            # Make this castling move and examine the resulting position
            board2 = Board(fen=fen)
            move = None
            for m in Moves(board2).generate():
                f, t, fl = decode_move(m)
                if f == from_sq and t == to_sq and fl == flags:
                    move = m
                    break
            
            if move:
                undo_info = board2.make_move(move)
                print(f"After {flag_name}:")
                print(board2.display())
                print(f"FEN: {board2.to_fen()}")
                
                # Check if position is correct
                moves_after = Moves(board2).generate()
                print(f"Legal moves after {flag_name}: {len(moves_after)}")

if __name__ == '__main__':
    main()
