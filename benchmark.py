"""
Benchmark script to measure search performance improvements
"""
import time
from engine.board import Board
from engine.search import ChessEngine


def benchmark_position(fen: str, depth: int, description: str):
    """Benchmark a position at given depth."""
    board = Board()
    board.from_fen(fen)
    engine = ChessEngine(max_depth=depth)
    
    print(f"\n{description}")
    print(f"FEN: {fen}")
    print(f"Depth: {depth}")
    
    start = time.time()
    move, score = engine.find_best_move(board)
    elapsed = time.time() - start
    
    print(f"Best move: {move}")
    print(f"Score: {score}")
    print(f"Time: {elapsed:.3f}s")
    print(f"Nodes: {engine.stats.nodes_searched:,}")
    print(f"NPS: {engine.stats.nodes_searched / elapsed:,.0f}")
    print(f"Cutoffs: {engine.stats.alpha_beta_cutoffs:,}")
    
    return elapsed, engine.stats.nodes_searched


def main():
    """Run performance benchmarks."""
    print("=" * 60)
    print("Chess Engine Performance Benchmark")
    print("=" * 60)
    
    positions = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4, "Initial Position (depth 4)"),
        ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, "Kiwipete Position (depth 4)"),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, "Endgame Position (depth 5)"),
    ]
    
    total_time = 0
    total_nodes = 0
    
    for fen, depth, desc in positions:
        elapsed, nodes = benchmark_position(fen, depth, desc)
        total_time += elapsed
        total_nodes += nodes
    
    print("\n" + "=" * 60)
    print(f"Total time: {total_time:.3f}s")
    print(f"Total nodes: {total_nodes:,}")
    print(f"Average NPS: {total_nodes / total_time:,.0f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
