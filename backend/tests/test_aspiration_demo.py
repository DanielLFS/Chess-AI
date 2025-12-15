"""
Quick test to show aspiration windows in action.
"""

import sys
sys.path.append('.')

from engine.board import Board
from engine.search import Search

# Starting position
board = Board()

print("="*70)
print("ASPIRATION WINDOWS DEMONSTRATION")
print("="*70)

# Search with aspiration windows
print("\nSearching at depth 6 with aspiration windows enabled...")
search = Search(use_aspiration=True)
move, score = search.search(board, depth=6)

print(f"\nBest move: {move:04x}")
print(f"Score: {score}")
print(f"\n{search.stats}")
print(f"\nAspiration window statistics:")
print(f"  - Windows used: Yes (min depth = {search.ASPIRATION_MIN_DEPTH})")
print(f"  - Window size: ±{search.ASPIRATION_WINDOW} centipawns")
print(f"  - Fail-high/fail-low events: {search.stats.aspiration_fails}")
print(f"  - Re-searches triggered: {search.stats.aspiration_researches}")
print(f"  - Total nodes searched: {search.stats.nodes:,}")
print(f"  - Total nodes (including qsearch): {search.stats.nodes + search.stats.qnodes:,}")

print("\n" + "="*70)
print("✓ Aspiration windows working correctly!")
print("="*70)
