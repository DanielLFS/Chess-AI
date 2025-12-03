"""
Flask Web Application for Chess AI
Provides web interface to play against the AI
"""

from flask import Flask, render_template, jsonify, request, session
import os
import secrets
import random
import time
from engine.board import Board, Color
from engine.moves import MoveGenerator
from engine.search import ChessEngine
from engine.evaluation import Evaluator

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Store active games in memory (in production, use Redis or database)
games = {}


def board_to_2d_array(board):
    """Convert board to 2D array for frontend."""
    result = []
    for row in range(8):
        row_pieces = []
        for col in range(8):
            piece = board.get_piece((row, col))
            if piece:
                # Return uppercase for white, lowercase for black
                symbol = piece.type.value  # P, N, B, R, Q, K from enum value
                if piece.color == Color.WHITE:
                    row_pieces.append(symbol)
                else:
                    row_pieces.append(symbol.lower())
            else:
                row_pieces.append(None)
        result.append(row_pieces)
    return result


def is_in_check(board):
    """Check if current player is in check."""
    move_gen = MoveGenerator(board)
    return move_gen.is_in_check(board.current_player)


def update_player_elo_estimate(game, move_accuracy):
    """Update estimated player ELO based on move quality."""
    # Adjust ELO estimate based on move accuracy
    accuracy_adjustments = {
        'Excellent': +5,
        'Good': +2,
        'Inaccuracy': -3,
        'Mistake': -8,
        'Blunder': -15,
        'Unknown': 0
    }
    
    adjustment = accuracy_adjustments.get(move_accuracy, 0)
    game['player_elo_estimate'] = max(400, min(2800, game['player_elo_estimate'] + adjustment))


def get_elo_from_difficulty(difficulty):
    """Convert difficulty string to ELO rating."""
    if difficulty.isdigit():
        return int(difficulty)
    
    elo_map = {
        'beginner': 800,
        'easy': 1200,
        'medium': 1600,
        'hard': 1900,
        'expert': 2400  # Increased from 2200
    }
    return elo_map.get(difficulty, 1600)


def get_ai_parameters(target_elo):
    """Get AI engine parameters based on target ELO."""
    if target_elo < 1000:
        return {'depth': 1, 'quiescence': False, 'blunder_rate': 0.15, 'max_nodes': 500}
    elif target_elo < 1400:
        return {'depth': 2, 'quiescence': False, 'blunder_rate': 0.08, 'max_nodes': 2000}
    elif target_elo < 1700:
        return {'depth': 3, 'quiescence': True, 'blunder_rate': 0.03, 'max_nodes': 10000}
    elif target_elo < 2000:
        return {'depth': 4, 'quiescence': True, 'blunder_rate': 0.01, 'max_nodes': 50000}
    elif target_elo < 2200:
        return {'depth': 5, 'quiescence': True, 'blunder_rate': 0.0, 'max_nodes': 200000}
    else:
        return {'depth': 6, 'quiescence': True, 'blunder_rate': 0.0, 'max_nodes': 500000}


def calculate_game_analysis(game):
    """Calculate post-game analysis statistics."""
    move_analysis = game['move_analysis']
    
    # Count only player moves (every other move, starting from index based on player color)
    player_is_white = game['player_color'] == 'white'
    start_index = 0 if player_is_white else 1
    player_moves = [m for i, m in enumerate(move_analysis) if i % 2 == start_index]
    
    if not player_moves:
        return {
            'total_moves': 0,
            'excellent': 0,
            'good': 0,
            'inaccuracies': 0,
            'mistakes': 0,
            'blunders': 0
        }
    
    excellent = sum(1 for m in player_moves if m['accuracy'] == 'Excellent')
    good = sum(1 for m in player_moves if m['accuracy'] == 'Good')
    inaccuracies = sum(1 for m in player_moves if m['accuracy'] == 'Inaccuracy')
    mistakes = sum(1 for m in player_moves if m['accuracy'] == 'Mistake')
    blunders = sum(1 for m in player_moves if m['accuracy'] == 'Blunder')
    
    return {
        'total_moves': len(player_moves),
        'excellent': excellent,
        'good': good,
        'inaccuracies': inaccuracies,
        'mistakes': mistakes,
        'blunders': blunders
    }


@app.route('/')
def index():
    """Render the main chess game interface."""
    return render_template('index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new chess game."""
    data = request.json
    game_mode = data.get('game_mode', 'player-vs-ai')
    player_color = data.get('color', 'white').lower()
    difficulty = data.get('difficulty', 'medium')
    
    # For AI vs AI mode
    white_difficulty = data.get('white_difficulty', 'expert')
    black_difficulty = data.get('black_difficulty', 'medium')
    
    # Create game session
    game_id = secrets.token_hex(8)
    session['game_id'] = game_id
    
    # Initialize board
    board = Board()
    
    # Set up based on game mode
    if game_mode == 'ai-vs-ai':
        # AI vs AI mode: create engines for both sides
        white_elo = get_elo_from_difficulty(white_difficulty)
        black_elo = get_elo_from_difficulty(black_difficulty)
        
        white_params = get_ai_parameters(white_elo)
        black_params = get_ai_parameters(black_elo)
        
        white_engine = ChessEngine(max_depth=white_params['depth'], use_quiescence=white_params['quiescence'], 
                                   use_iterative_deepening=True, max_nodes=white_params['max_nodes'])
        black_engine = ChessEngine(max_depth=black_params['depth'], use_quiescence=black_params['quiescence'],
                                   use_iterative_deepening=True, max_nodes=black_params['max_nodes'])
        
        games[game_id] = {
            'board': board,
            'game_mode': 'ai-vs-ai',
            'player_color': None,
            'white_ai_engine': white_engine,
            'black_ai_engine': black_engine,
            'white_elo': white_elo,
            'black_elo': black_elo,
            'white_blunder_rate': white_params['blunder_rate'],
            'black_blunder_rate': black_params['blunder_rate'],
            'move_history': [],
            'move_analysis': [],
            'captured_pieces': {'white': [], 'black': []},
            'player_elo_estimate': None,
            'position_evaluations': []
        }
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'board': board_to_2d_array(board),
            'fen': board.to_fen(),
            'game_mode': 'ai-vs-ai',
            'player_color': None,
            'current_turn': 'white',
            'is_player_turn': False,
            'in_check': is_in_check(board),
            'game_over': False,
            'status': 'Game started (AI vs AI)',
            'move_history': [],
            'captured_pieces': {'white': [], 'black': []},
            'white_elo': white_elo,
            'black_elo': black_elo,
            'evaluation': 0.0
        })
    
    # Player vs AI mode (existing logic)
    
    # Create game session
    game_id = secrets.token_hex(8)
    session['game_id'] = game_id
    
    # Initialize board
    board = Board()
    
    # Set AI difficulty based on ELO or preset
    if difficulty.isdigit():
        # Direct ELO input (e.g., "1500")
        target_elo = int(difficulty)
    else:
        # Preset difficulty levels with ELO equivalents
        elo_map = {
            'beginner': 800,
            'easy': 1200,
            'medium': 1600,
            'hard': 1900,
            'expert': 2200
        }
        target_elo = elo_map.get(difficulty, 1600)
    
    # Get AI parameters using the helper function
    ai_params = get_ai_parameters(target_elo)
    
    # Create persistent engine instance
    ai_engine = ChessEngine(max_depth=ai_params['depth'], use_quiescence=ai_params['quiescence'], 
                           use_iterative_deepening=True, max_nodes=ai_params['max_nodes'])
    
    # Store game state
    games[game_id] = {
        'board': board,
        'player_color': player_color,
        'ai_depth': ai_params['depth'],
        'ai_engine': ai_engine,
        'target_elo': target_elo,
        'blunder_rate': ai_params['blunder_rate'],
        'move_history': [],
        'move_analysis': [],  # Store move quality analysis
        'captured_pieces': {'white': [], 'black': []},
        'player_elo_estimate': 1500,  # Starting estimate
        'position_evaluations': []  # Track evaluation after each move
    }
    
    # If player is black, make AI move first
    ai_move_data = None
    if player_color == 'black':
        ai_move_data = make_ai_move(game_id)
    
    return jsonify({
        'success': True,
        'game_id': game_id,
        'board': board_to_2d_array(board),
        'fen': board.to_fen(),
        'player_color': player_color,
        'current_turn': 'white' if board.current_player == Color.WHITE else 'black',
        'is_player_turn': (player_color == 'white' and board.current_player == Color.WHITE) or 
                         (player_color == 'black' and board.current_player == Color.BLACK),
        'in_check': is_in_check(board),
        'game_over': False,
        'status': 'Game started',
        'move_history': [],
        'captured_pieces': {'white': [], 'black': []},
        'ai_elo': target_elo,
        'player_elo': 1500,
        'evaluation': 0.0,  # Initial position is equal
        'ai_move': ai_move_data
    })


@app.route('/api/get_legal_moves', methods=['POST'])
def get_legal_moves():
    """Get legal moves for a piece."""
    data = request.json
    game_id = data.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    
    square = data.get('square')  # e.g., "e2"
    from_pos = square
    if not from_pos:
        return jsonify({'error': 'Missing from position'}), 400
    
    # Convert algebraic notation to coordinates
    col = ord(from_pos[0]) - ord('a')
    row = 8 - int(from_pos[1])
    
    piece = board.get_piece((row, col))
    if not piece:
        return jsonify({'legal_moves': []})
    
    # Generate legal moves
    move_gen = MoveGenerator(board)
    all_moves = move_gen.generate_legal_moves(piece.color)
    
    # Filter moves for this piece
    piece_moves = [m for m in all_moves if m.from_pos == (row, col)]
    
    # Convert to algebraic notation (return simple array of square names)
    legal_moves = []
    for move in piece_moves:
        to_row, to_col = move.to_pos
        to_square = chr(ord('a') + to_col) + str(8 - to_row)
        legal_moves.append(to_square)
    
    return jsonify({'legal_moves': legal_moves})


@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Make a player move and get AI response."""
    data = request.json
    game_id = data.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    
    from_square = data.get('from')  # e.g., "e2"
    to_square = data.get('to')      # e.g., "e4"
    promotion = data.get('promotion', 'Q')  # For pawn promotion
    
    if not from_square or not to_square:
        return jsonify({'error': 'Missing move data'}), 400
    
    # Convert to coordinates
    from_col = ord(from_square[0]) - ord('a')
    from_row = 8 - int(from_square[1])
    to_col = ord(to_square[0]) - ord('a')
    to_row = 8 - int(to_square[1])
    
    # Find the matching legal move
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves(board.current_player)
    
    matching_move = None
    for move in legal_moves:
        if move.from_pos == (from_row, from_col) and move.to_pos == (to_row, to_col):
            # Handle promotion
            if move.promotion:
                from engine.board import PieceType
                promo_map = {'Q': PieceType.QUEEN, 'R': PieceType.ROOK, 
                            'B': PieceType.BISHOP, 'N': PieceType.KNIGHT}
                if move.promotion == promo_map.get(promotion):
                    matching_move = move
                    break
            else:
                matching_move = move
                break
    
    if not matching_move:
        return jsonify({'error': 'Illegal move'}), 400
    
    # Evaluate position before move for analysis
    evaluator = Evaluator()
    pre_move_eval = evaluator.evaluate(board)
    
    # Make the move
    board.make_move(matching_move)
    
    # Evaluate position after move
    post_move_eval = evaluator.evaluate(board)
    
    # Simple move quality assessment based on eval change
    # (Proper analysis would require checking engine's best move, but that's expensive)
    eval_change = abs(post_move_eval - pre_move_eval)
    
    if eval_change < 0.5:
        accuracy = 'Excellent'
    elif eval_change < 1.0:
        accuracy = 'Good'
    elif eval_change < 2.0:
        accuracy = 'Inaccuracy'
    elif eval_change < 4.0:
        accuracy = 'Mistake'
    else:
        accuracy = 'Blunder'
    
    # Record move history
    move_notation = from_square + to_square
    if matching_move.promotion:
        move_notation += promotion
    game['move_history'].append(move_notation)
    
    # Store move analysis
    game['move_analysis'].append({
        'move': move_notation,
        'pre_eval': pre_move_eval,
        'post_eval': post_move_eval,
        'accuracy': accuracy
    })
    
    # Update player ELO estimate based on move quality
    update_player_elo_estimate(game, accuracy)
    
    # Track captured pieces
    if matching_move.captured_piece:
        piece_color = 'black' if board.current_player == Color.WHITE else 'white'
        # Store piece type as string (P, N, B, R, Q, K)
        piece_type = matching_move.captured_piece.type.value
        game['captured_pieces'][piece_color].append(piece_type)
    
    # Check game status AFTER player move (before AI responds)
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves(board.current_player)
    
    game_over = False
    status = 'Game in progress'
    
    if not legal_moves:
        game_over = True
        if move_gen.is_in_check(board.current_player):
            winner = 'White' if board.current_player == Color.BLACK else 'Black'
            status = f'Checkmate! {winner} wins!'
        else:
            status = 'Stalemate!'
    elif move_gen.is_in_check(board.current_player):
        status = 'Check!'
    
    # Return board state AFTER player move but BEFORE AI move
    return jsonify({
        'success': True,
        'board': board_to_2d_array(board),
        'fen': board.to_fen(),
        'move_history': game['move_history'],
        'captured_pieces': game['captured_pieces'],
        'current_turn': 'white' if board.current_player == Color.WHITE else 'black',
        'is_player_turn': (game['player_color'] == 'white' and board.current_player == Color.WHITE) or 
                         (game['player_color'] == 'black' and board.current_player == Color.BLACK),
        'in_check': move_gen.is_in_check(board.current_player),
        'game_over': game_over,
        'status': status,
        'should_ai_move': not game_over,
        'player_elo': game['player_elo_estimate'],
        'ai_elo': game['target_elo'],
        'last_move_accuracy': game['move_analysis'][-1]['accuracy'] if game['move_analysis'] else 'Unknown',
        'evaluation': post_move_eval,
        'game_analysis': calculate_game_analysis(game) if game_over else None
    })


def make_ai_move(game_id):
    """Make an AI move."""
    game = games[game_id]
    board = game['board']
    
    # Determine which engine to use
    if game.get('game_mode') == 'ai-vs-ai':
        # AI vs AI: select engine based on whose turn it is
        if board.current_player == Color.WHITE:
            engine = game['white_ai_engine']
            blunder_rate = game['white_blunder_rate']
            elo = game['white_elo']
        else:
            engine = game['black_ai_engine']
            blunder_rate = game['black_blunder_rate']
            elo = game['black_elo']
        print(f"\n{'White' if board.current_player == Color.WHITE else 'Black'} to move (ELO {elo}, depth {engine.max_depth}, blunder rate {blunder_rate*100:.1f}%)")
    else:
        # Player vs AI: use single AI engine
        engine = game['ai_engine']
        blunder_rate = game['blunder_rate']
        elo = game['target_elo']
    
    # Potentially add blunders for lower ELO
    is_blunder = random.random() < blunder_rate
    if is_blunder:
        print(f"  → Making intentional blunder (random move)")
        # Make a random legal move instead of best move
        move_gen = MoveGenerator(board)
        legal_moves = move_gen.generate_legal_moves(board.current_player)
        if legal_moves:
            move = random.choice(legal_moves)
            score = 0  # Don't evaluate blunders
        else:
            move = None
    else:
        # Find best move normally with time limit (but node limit is primary)
        # Time limit is just a safety fallback
        time_limit = 30.0  # Generous time limit since node limit controls speed
        print(f"  → Searching depth {engine.max_depth} with max {engine.max_nodes} nodes...")
        start_time = time.time()
        move, score = engine.find_best_move(board, time_limit=time_limit)
        elapsed = time.time() - start_time
        print(f"  → Found move in {elapsed:.2f}s, score: {score:.2f}, nodes: {engine.stats.nodes_searched}")
    
    if not move:
        return None
    
    # Convert move to algebraic notation
    from_row, from_col = move.from_pos
    to_row, to_col = move.to_pos
    from_square = chr(ord('a') + from_col) + str(8 - from_row)
    to_square = chr(ord('a') + to_col) + str(8 - to_row)
    
    # Make the move
    board.make_move(move)
    
    # Record move
    move_notation = from_square + to_square
    if move.promotion:
        move_notation += str(move.promotion).split('.')[-1][0]
    game['move_history'].append(move_notation)
    
    # Track captured pieces
    if move.captured_piece:
        piece_color = 'white' if board.current_player == Color.WHITE else 'black'
        # Store piece type as string (P, N, B, R, Q, K)
        piece_type = move.captured_piece.type.value
        game['captured_pieces'][piece_color].append(piece_type)
    
    # Check game status
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves(board.current_player)
    
    game_over = False
    result = None
    
    if not legal_moves:
        game_over = True
        if move_gen.is_in_check(board.current_player):
            result = 'checkmate'
        else:
            result = 'stalemate'
    
    return {
        'from': from_square,
        'to': to_square,
        'fen': board.to_fen(),
        'score': score,
        'game_over': game_over,
        'result': result
    }


@app.route('/api/get_game_state', methods=['GET'])
def get_game_state():
    """Get current game state."""
    game_id = request.args.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves(board.current_player)
    
    game_over = False
    status = 'Game in progress'
    
    if not legal_moves:
        game_over = True
        if move_gen.is_in_check(board.current_player):
            winner = 'Black' if board.current_player == Color.WHITE else 'White'
            status = f'Checkmate! {winner} wins!'
        else:
            status = 'Stalemate!'
    
    return jsonify({
        'board': board_to_2d_array(board),
        'fen': board.to_fen(),
        'move_history': game['move_history'],
        'captured_pieces': game['captured_pieces'],
        'player_color': game['player_color'],
        'current_turn': 'white' if board.current_player == Color.WHITE else 'black',
        'is_player_turn': (game['player_color'] == 'white' and board.current_player == Color.WHITE) or 
                         (game['player_color'] == 'black' and board.current_player == Color.BLACK),
        'in_check': move_gen.is_in_check(board.current_player),
        'game_over': game_over,
        'status': status
    })


@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    """Trigger AI to make a move."""
    data = request.json
    game_id = data.get('game_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    
    # Make AI move
    ai_move_data = make_ai_move(game_id)
    
    if not ai_move_data:
        return jsonify({'error': 'No legal moves for AI'}), 400
    
    # Get updated game state after AI move
    move_gen = MoveGenerator(board)
    legal_moves = move_gen.generate_legal_moves(board.current_player)
    
    game_over = ai_move_data.get('game_over', False)
    status = 'Game in progress'
    
    if not legal_moves:
        game_over = True
        if move_gen.is_in_check(board.current_player):
            winner = 'Black' if board.current_player == Color.WHITE else 'White'
            status = f'Checkmate! {winner} wins!'
        else:
            status = 'Stalemate!'
    elif move_gen.is_in_check(board.current_player):
        status = 'Check!'
    
    return jsonify({
        'success': True,
        'board': board_to_2d_array(board),
        'fen': board.to_fen(),
        'move_history': game['move_history'],
        'captured_pieces': game['captured_pieces'],
        'current_turn': 'white' if board.current_player == Color.WHITE else 'black',
        'is_player_turn': (game['player_color'] == 'white' and board.current_player == Color.WHITE) or 
                         (game['player_color'] == 'black' and board.current_player == Color.BLACK),
        'in_check': move_gen.is_in_check(board.current_player),
        'game_over': game_over,
        'status': status,
        'ai_move': ai_move_data,
        'evaluation': Evaluator().evaluate(board),
        'game_analysis': calculate_game_analysis(game) if game_over else None
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
