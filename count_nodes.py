"""
Calculate theoretical vs actual nodes for different search depths.
Shows the effect of alpha-beta pruning.
"""

from engine.board import Board
from engine.moves import MoveGenerator

def count_legal_moves_at_depth(board: Board, depth: int, current_depth: int = 0) -> int:
    """
    Recursively count legal positions at each depth (pure minimax, no pruning).
    
    Args:
        board: Current board position
        depth: Target depth
        current_depth: Current recursion depth
        
    Returns:
        Number of leaf nodes at target depth
    """
    if current_depth == depth:
        return 1
    
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves()
    
    if not legal_moves:
        return 1  # Terminal node (checkmate or stalemate)
    
    total_nodes = 0
    for move in legal_moves:
        board.make_move(move)
        nodes = count_legal_moves_at_depth(board, depth, current_depth + 1)
        board.unmake_move(move)
        total_nodes += nodes
    
    return total_nodes


# Starting position
board = Board()

print("Theoretical nodes (pure minimax, no pruning):")
print("=" * 60)

for depth in range(1, 6):
    nodes = count_legal_moves_at_depth(board, depth)
    print(f"Depth {depth}: {nodes:,} nodes")
    
    if depth > 1:
        branching = nodes / prev_nodes
        print(f"  Branching factor: {branching:.1f}")
    
    prev_nodes = nodes

print("\n" + "=" * 60)
print("Note: Actual search with alpha-beta pruning will visit fewer nodes")
