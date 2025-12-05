import cProfile
import pstats
from engine.board import Board
from engine.search import SearchEngine

b = Board()
s = SearchEngine(tt_size_mb=16)

profiler = cProfile.Profile()
profiler.enable()
s.search(b, depth=3)
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(30)
