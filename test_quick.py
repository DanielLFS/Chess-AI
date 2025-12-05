from engine.board import Board
from engine.search import SearchEngine

# Quick performance test
b = Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
s = SearchEngine()
best_move, score, info = s.search(b, depth=5)

print(f'\nResult: Best move={best_move}, Score={score}')
print(f'Nodes: {info["nodes"]}, NPS: {info["nps"]}')
print(f'Beta cutoffs: {info["beta_cutoffs"]}')
print(f'TT hits: {info["tt_hits"]}')
