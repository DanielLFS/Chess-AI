"""
Simple command-line demo of the chess engine.
Play against the AI in the terminal.
"""

from engine.board import Board, Color
from engine.search import ChessEngine
from engine.moves import MoveGenerator
import time


def parse_move_input(input_str: str):
    """Parse user input like 'e2e4' into from and to positions."""
    if len(input_str) != 4:
        return None
    
    try:
        from_col = ord(input_str[0].lower()) - ord('a')
        from_row = 8 - int(input_str[1])
        to_col = ord(input_str[2].lower()) - ord('a')
        to_row = 8 - int(input_str[3])
        
        if not all(0 <= x < 8 for x in [from_row, from_col, to_row, to_col]):
            return None
        
        return (from_row, from_col), (to_row, to_col)
    except:
        return None


def find_move(board: Board, from_pos, to_pos):
    """Find a legal move matching the from and to positions."""
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves()
    
    for move in legal_moves:
        if move.from_pos == from_pos and move.to_pos == to_pos:
            return move
    
    return None


def play_game():
    """Main game loop."""
    print("=" * 50)
    print("Chess AI Engine - Command Line Demo")
    print("=" * 50)
    print()
    
    # Setup
    board = Board()
    
    # Choose difficulty
    print("Select difficulty:")
    print("1. Beginner (Depth 2)")
    print("2. Intermediate (Depth 4)")
    print("3. Advanced (Depth 6)")
    
    choice = input("Enter choice (1-3): ").strip()
    depth_map = {'1': 2, '2': 4, '3': 6}
    depth = depth_map.get(choice, 4)
    
    engine = ChessEngine(max_depth=depth, use_iterative_deepening=True)
    
    # Choose color
    print("\nChoose your color:")
    print("1. White")
    print("2. Black")
    
    color_choice = input("Enter choice (1-2): ").strip()
    player_color = Color.WHITE if color_choice == '1' else Color.BLACK
    
    print(f"\nYou are playing as {'White' if player_color == Color.WHITE else 'Black'}")
    print(f"AI difficulty: Depth {depth}")
    print("\nEnter moves in format: e2e4 (from square to square)")
    print("Type 'quit' to exit\n")
    
    move_gen = MoveGenerator(board)
    move_count = 0
    
    while True:
        # Display board
        print("\n" + board.display())
        print(f"FEN: {board.to_fen()}")
        
        # Check game state
        if move_gen.is_checkmate(board.current_player):
            winner = "Black" if board.current_player == Color.WHITE else "White"
            print(f"\n🏆 Checkmate! {winner} wins!")
            break
        
        if move_gen.is_stalemate(board.current_player):
            print("\n🤝 Stalemate! Game is a draw.")
            break
        
        if move_gen.is_in_check(board.current_player):
            print("⚠️  Check!")
        
        # Player's turn
        if board.current_player == player_color:
            while True:
                user_input = input(f"\n{'White' if board.current_player == Color.WHITE else 'Black'} to move: ").strip().lower()
                
                if user_input == 'quit':
                    print("Thanks for playing!")
                    return
                
                positions = parse_move_input(user_input)
                if not positions:
                    print("Invalid format. Use: e2e4")
                    continue
                
                from_pos, to_pos = positions
                move = find_move(board, from_pos, to_pos)
                
                if move:
                    board.make_move(move)
                    move_count += 1
                    print(f"Move {move_count}: {move}")
                    break
                else:
                    print("Illegal move. Try again.")
        
        # AI's turn
        else:
            print(f"\n{'White' if board.current_player == Color.WHITE else 'Black'} (AI) is thinking...")
            
            start_time = time.time()
            move, score = engine.find_best_move(board)
            elapsed = time.time() - start_time
            
            if move is None:
                print("No legal moves available!")
                break
            
            board.make_move(move)
            move_count += 1
            
            stats = engine.stats
            print(f"Move {move_count}: {move}")
            print(f"Evaluation: {score/100:.2f} pawns")
            print(f"Time: {elapsed:.2f}s, Nodes: {stats.nodes_searched:,}, NPS: {stats.get_nodes_per_second():,.0f}")
        
        # Update move generator with new position
        move_gen = MoveGenerator(board)
    
    print("\nGame over!")
    print(f"Final position FEN: {board.to_fen()}")


if __name__ == "__main__":
    try:
        play_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
