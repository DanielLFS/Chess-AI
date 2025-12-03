"""
Example: Playing a game and storing it in the database.
"""

from engine.board import Board, Color
from engine.search import ChessEngine
from engine.moves import MoveGenerator
from database.models import DatabaseManager
from datetime import datetime


def play_and_store_game():
    """Play a game between two AI engines and store it in the database."""
    
    # Initialize database
    db = DatabaseManager()
    db.create_tables()
    
    # Create board and engines
    board = Board()
    white_engine = ChessEngine(max_depth=3)
    black_engine = ChessEngine(max_depth=3)
    
    move_gen = MoveGenerator(board)
    moves_data = []
    
    print("Playing AI vs AI game...")
    print(board.display())
    
    # Game metadata
    game_data = {
        'white_player': 'Engine-Depth3',
        'black_player': 'Engine-Depth3',
        'date_played': datetime.utcnow()
    }
    
    move_count = 0
    max_moves = 100  # Limit to prevent infinite games
    
    # Play game
    while move_count < max_moves:
        # Check for game end
        if move_gen.is_checkmate(board.current_player):
            game_data['result'] = '0-1' if board.current_player == Color.WHITE else '1-0'
            print(f"\nCheckmate! {game_data['result']}")
            break
        
        if move_gen.is_stalemate(board.current_player):
            game_data['result'] = '1/2-1/2'
            print("\nStalemate!")
            break
        
        # Get move from appropriate engine
        engine = white_engine if board.current_player.value == 'white' else black_engine
        move, score = engine.find_best_move(board)
        
        if move is None:
            game_data['result'] = '1/2-1/2'
            break
        
        # Store move data
        move_data = {
            'move_number': move_count + 1,
            'side_to_move': board.current_player.value,
            'move_notation': str(move),
            'move_from': move._pos_to_notation(move.from_pos),
            'move_to': move._pos_to_notation(move.to_pos),
            'evaluation_score': score,
            'search_depth': engine.max_depth,
            'nodes_searched': engine.stats.nodes_searched,
            'time_ms': int((engine.stats.get_nodes_per_second() / max(engine.stats.nodes_searched, 1)) * 1000),
            'is_capture': move.captured_piece is not None,
            'is_check': False  # Would need to check after move
        }
        moves_data.append(move_data)
        
        # Make move
        board.make_move(move)
        move_count += 1
        move_gen = MoveGenerator(board)
        
        print(f"Move {move_count}: {move} (eval: {score/100:.2f})")
    
    # Finalize game data
    game_data['total_moves'] = move_count
    game_data['final_position'] = board.to_fen()
    
    if 'result' not in game_data:
        game_data['result'] = '1/2-1/2'  # Draw by move limit
    
    # Save to database
    print("\nSaving game to database...")
    game_id = db.save_game(game_data)
    print(f"Game saved with ID: {game_id}")
    
    # Save all moves
    for move_data in moves_data:
        move_data['game_id'] = game_id
        db.save_move(move_data)
    
    print(f"Saved {len(moves_data)} moves")
    
    print("\n" + board.display())
    print(f"\nFinal result: {game_data['result']}")
    print(f"Total moves: {move_count}")
    
    return game_id


def query_recent_games():
    """Query and display recent games from the database."""
    db = DatabaseManager()
    
    print("\nRecent games:")
    print("-" * 70)
    
    games = db.get_all_games(limit=10)
    
    for game in games:
        print(f"Game #{game.game_id}: {game.white_player} vs {game.black_player}")
        print(f"  Result: {game.result}, Moves: {game.total_moves}")
        print(f"  Date: {game.date_played}")
        print()


if __name__ == "__main__":
    # Play a game and store it
    game_id = play_and_store_game()
    
    # Query recent games
    query_recent_games()
