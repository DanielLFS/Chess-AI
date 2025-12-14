"""Compare perft divide results with known reference."""
import numpy as np
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

def perft_divide(fen: str, depth: int):
    """Show perft for each move."""
    board = Board(fen=fen)
    moves_gen = Moves(board)
    legal_moves = moves_gen.generate()
    
    print(f"\nPerft divide depth {depth} for: {fen}")
    print(f"Total moves at depth 1: {len(legal_moves)}\n")
    
    total = 0
    for move in legal_moves:
        from_sq, to_sq, flags = decode_move(move)
        undo_info = board.make_move(move)
        count = perft(board, depth - 1)
        board.unmake_move(move, undo_info)
        print(f"{from_sq:2d}->{to_sq:2d} (f={flags}): {count:8d}")
        total += count
    
    print(f"\nTotal: {total}")
    return total

if __name__ == '__main__':
    # Kiwipete at depth 2 - reference says 2,039
    result = perft_divide("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2)
    print(f"\nExpected: 2,039")
    print(f"Got: {result}")
