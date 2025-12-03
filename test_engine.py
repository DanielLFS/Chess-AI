"""
Quick test script to verify the engine works correctly.
"""

from engine.board import Board, Color
from engine.search import ChessEngine
from engine.moves import MoveGenerator
from engine.evaluation import Evaluator
import time


def test_basic_functionality():
    """Test basic engine functionality."""
    print("Chess AI Engine - Quick Test Suite")
    print("=" * 50)
    
    # Test 1: Board setup
    print("\n1. Testing board setup...")
    board = Board()
    assert board.to_fen() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("   ✓ Board initialized correctly")
    
    # Test 2: Move generation
    print("\n2. Testing move generation...")
    move_gen = MoveGenerator(board)
    moves = move_gen.generate_legal_moves(Color.WHITE)
    assert len(moves) == 20, f"Expected 20 moves, got {len(moves)}"
    print(f"   ✓ Generated {len(moves)} legal moves from starting position")
    
    # Test 3: Evaluation
    print("\n3. Testing position evaluation...")
    evaluator = Evaluator()
    score = evaluator.evaluate(board)
    assert abs(score) < 100, "Initial position should be roughly equal"
    print(f"   ✓ Initial position evaluation: {score/100:.2f} pawns")
    
    # Test 4: Search
    print("\n4. Testing AI search...")
    engine = ChessEngine(max_depth=3)
    start = time.time()
    move, score = engine.find_best_move(board)
    elapsed = time.time() - start
    
    assert move is not None, "Engine should find a move"
    print(f"   ✓ Found move: {move}")
    print(f"   ✓ Evaluation: {score/100:.2f} pawns")
    print(f"   ✓ Time: {elapsed:.3f}s")
    print(f"   ✓ Nodes: {engine.stats.nodes_searched:,}")
    print(f"   ✓ NPS: {engine.stats.get_nodes_per_second():,.0f}")
    
    # Test 5: Make move
    print("\n5. Testing move execution...")
    board.make_move(move)
    new_fen = board.to_fen()
    assert new_fen != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("   ✓ Move executed successfully")
    print(f"   ✓ New FEN: {new_fen}")
    
    # Test 6: Checkmate detection
    print("\n6. Testing checkmate detection...")
    checkmate_board = Board()
    checkmate_board.from_fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1")
    move_gen = MoveGenerator(checkmate_board)
    assert move_gen.is_checkmate(Color.WHITE)
    print("   ✓ Checkmate detected correctly")
    
    # Test 7: Stalemate detection
    print("\n7. Testing stalemate detection...")
    stalemate_board = Board()
    stalemate_board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    move_gen = MoveGenerator(stalemate_board)
    assert move_gen.is_stalemate(Color.BLACK)
    print("   ✓ Stalemate detected correctly")
    
    # Test 8: Tactical position
    print("\n8. Testing tactical position (Scholar's Mate)...")
    tactical_board = Board()
    tactical_board.from_fen("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    engine = ChessEngine(max_depth=2)
    move, score = engine.find_best_move(tactical_board)
    # Should find a checkmate move to f7
    # f7 is row 1, col 5 (0-indexed from top, 8th rank = row 0)
    is_checkmate_move = (move.to_pos[0] == 1 and move.to_pos[1] == 5)  # f7 square
    assert is_checkmate_move, f"Should find checkmate on f7 (1,5), found {move} to position {move.to_pos}"
    print(f"   ✓ Found checkmate: {move}")
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


def benchmark_performance():
    """Benchmark engine performance at different depths."""
    print("\n\nPerformance Benchmark")
    print("=" * 50)
    
    board = Board()
    
    for depth in [2, 3, 4, 5]:
        engine = ChessEngine(max_depth=depth, use_iterative_deepening=False)
        
        print(f"\nDepth {depth}:")
        start = time.time()
        move, score = engine.find_best_move(board)
        elapsed = time.time() - start
        
        stats = engine.stats
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Nodes: {stats.nodes_searched:,}")
        print(f"  NPS: {stats.get_nodes_per_second():,.0f}")
        print(f"  Best move: {move}")
        print(f"  Eval: {score/100:.2f}")


def test_special_moves():
    """Test special moves (castling, en passant, promotion)."""
    print("\n\nSpecial Moves Test")
    print("=" * 50)
    
    # Castling
    print("\n1. Testing castling...")
    board = Board()
    board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    move_gen = MoveGenerator(board)
    moves = move_gen.generate_legal_moves()
    castling_moves = [m for m in moves if m.is_castling]
    print(f"   ✓ Found {len(castling_moves)} castling moves")
    
    # En passant
    print("\n2. Testing en passant...")
    board = Board()
    board.from_fen("8/8/8/pP6/8/8/8/8 w - a6 0 1")
    move_gen = MoveGenerator(board)
    moves = move_gen.generate_legal_moves()
    ep_moves = [m for m in moves if m.is_en_passant]
    print(f"   ✓ Found {len(ep_moves)} en passant move")
    
    # Promotion
    print("\n3. Testing pawn promotion...")
    board = Board()
    board.from_fen("8/P7/8/8/8/8/8/8 w - - 0 1")
    move_gen = MoveGenerator(board)
    moves = move_gen.generate_legal_moves()
    promo_moves = [m for m in moves if m.promotion]
    print(f"   ✓ Found {len(promo_moves)} promotion moves")


if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_special_moves()
        
        print("\n\nRun performance benchmark? (may take ~30 seconds)")
        response = input("Enter 'y' to run: ").strip().lower()
        
        if response == 'y':
            benchmark_performance()
        
        print("\n✅ All tests completed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
