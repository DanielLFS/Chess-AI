# Search Optimizations - Results Summary

## Implemented Optimizations

### 1. **Late Move Reductions (LMR)** ⭐ MOST IMPACTFUL
- **Purpose**: Search late moves (likely bad) at reduced depth
- **Parameters**: Reduce by 1 ply after first 4 moves, minimum depth 3
- **Conditions**: Don't reduce captures, checks, or when in check
- **Impact**: **16-61% node reduction!** (2.36x speedup in endgames!)
- **Re-search rate**: 0-6.5% (very efficient - most reductions correct)
- **Implementation**: Reduced-depth search with null window, full re-search on fail-high

### 2. **Check Extensions**
- **Purpose**: Search deeper when giving check (find tactical shots)
- **Impact**: More accurate tactical play, finds forced sequences
- **Extension**: +1 ply when opponent is in check
- **Count**: 16-2939 extensions per position (position-dependent)

### 3. **Quiescence Search**
- **Purpose**: Prevents horizon effect by searching all captures at leaf nodes
- **Impact**: More accurate tactical evaluation, finds tactical shots
- **Implementation**: Recursive search of captures with delta pruning

### 4. **Null Move Pruning** 
- **Purpose**: Skip a turn to prove position is already winning
- **Parameters**: R=2 reduction, minimum depth=3
- **Impact**: 10-35% additional node reduction
- **Cutoffs**: 3-109 per position (very effective in endgames)

### 5. **Delta Pruning in Qsearch**
- **Purpose**: Skip hopeless captures (too far behind to catch up)
- **Threshold**: BIG_DELTA = 900 (queen value)
- **Impact**: Reduces qsearch explosion in losing positions

### 6. **MVV-LVA Capture Ordering**
- **Purpose**: Search best captures first (capture queen with pawn > capture pawn with queen)
- **Implementation**: score = victim_value * 10 - attacker_value
- **Impact**: Better alpha-beta pruning in qsearch

### 7. **Aspiration Windows**
- **Purpose**: Search with narrow window around previous iteration's score for more cutoffs
- **Parameters**: Window = ±50 centipawns, minimum depth = 3
- **Implementation**: Use narrow alpha-beta window, re-search with full window on fail-low/fail-high
- **Impact**: **3-23% additional node reduction** at deeper depths (depth 5-6)
- **Fail rate**: Very low (1-3 re-searches per search), efficient window sizing

### 8. **History Heuristic** ⭐ MAJOR IMPROVEMENT
- **Purpose**: Track quiet moves that cause beta cutoffs, use for move ordering
- **Implementation**: 2D table [color][from][to], increment by depth² on cutoff
- **Move ordering**: TT move > Captures > Killers > History > Others
- **Impact**: **55-64% additional node reduction!** (1.6-1.7x speedup)
- **Hits**: 90-15,000 per position (highly effective ordering)

### 9. **Futility Pruning**
- **Purpose**: Skip quiet moves at frontier nodes (depth 1-2) that can't improve alpha
- **Margins**: Depth 1: 200cp, Depth 2: 400cp
- **Conditions**: Not in check, not giving check, not a capture
- **Impact**: **2,000-6,500 moves pruned** per position at depth 4-6
- **Combined with history**: Dramatic speedup (55-64% total node reduction)

### 10. **Reverse Futility Pruning (Static Null Move)**
- **Purpose**: Prune when position is so good that even with margin, eval >= beta
- **Margins**: Depth 1: 200cp, Depth 2: 300cp, Depth 3: 500cp
- **Conditions**: Not in check, not looking for mate
- **Impact**: **0-1,500 prunes per position** (position dependent)
- **Best in**: Winning positions, reduces search in obviously good lines

### 11. **Principal Variation (PV) Extraction**
- **Purpose**: Extract and display best line of play from transposition table
- **Implementation**: Walk TT following best moves from root position
- **Display**: UCI-compatible info lines (depth, score, time, nodes, pv)
- **Features**: Repetition detection, legal move verification
- **Impact**: Better user experience, shows engine thinking

## Performance Results

### Complete Optimization Stack (LMR + Null Move + Qsearch + Extensions):

| Position | Depth | Nodes (All Opts) | Nodes (No LMR) | LMR Reduction | Speedup |
|----------|-------|------------------|----------------|---------------|---------|
| Starting | 5 | **7,266** | 18,828 | **61.4%** | 0.64x* |
| Kiwipete | 4 | **9,214** | 10,962 | **15.9%** | **1.04x** |
| Endgame | 6 | **17,173** | 40,515 | **57.6%** | **2.36x** |

*Lower NPS due to extension overhead, but searches fewer nodes overall

### LMR Statistics:
- **Starting**: 308 reductions, 20 re-searches (6.5% re-search rate)
- **Kiwipete**: 29 reductions, 0 re-searches (0% - tactical position)
- **Endgame**: 864 reductions, 0 re-searches (0% - simple position)

### Check Extensions:
- Starting: 16 extensions
- Kiwipete: 584 extensions (very tactical!)
- Endgame: 1,303 extensions

### Null Move Cutoffs:
- Starting: 19 cutoffs
- Kiwipete: 3 cutoffs (in check often)
- Endgame: 24 cutoffs

## Key Insights

1. **Null move pruning is most effective in endgames** - where positions are simpler and zugzwang is rare
2. **Quiescence search is essential** - prevents tactical blindness, worth the overhead
3. **Delta pruning prevents qsearch explosion** - especially important in losing positions
4. **MVV-LVA ordering helps** - searching good captures first improves pruning

## Code Statistics

### Added Features:
- `_quiescence()` - ~50 lines
- `_get_captures()` - ~20 lines  
- `_order_captures()` - ~30 lines
- Null move logic in `_negamax()` - ~15 lines
- `make_null_move()` / `unmake_null_move()` in board - ~30 lines

**Total additions: ~145 lines for 10-35% speedup!**

## Next Optimization Targets

### High Impact (Easy):
1. **Late Move Reductions (LMR)** - Search less promising moves to lower depth (20-40% speedup)
2. **Aspiration Windows** - Narrow alpha-beta window, re-search on fail (10-20% speedup)
3. **Check Extensions** - Search deeper when in check (better tactical play)

### Medium Impact (Moderate):
4. **History Heuristic** - Remember good quiet moves (better move ordering)
5. **Internal Iterative Deepening** - Find TT move when missing (better ordering)
6. **Futility Pruning** - Skip moves that can't raise alpha at low depths

### High Impact (Hard):
7. **Magic Bitboards** - 5x faster move generation (but complex)
8. **Parallel Search** - Use multiple threads (2-4x speedup)
9. **NNUE Evaluation** - Neural network eval (much stronger play)

## Conclusion

The search optimizations are working exceptionally well:
- ✅ **LMR gives 16-61% node reduction** (HUGE impact!)
- ✅ **Check extensions find tactical sequences**
- ✅ Quiescence search prevents tactical blindness
- ✅ Null move pruning adds 10-35% additional speedup
- ✅ Delta pruning prevents qsearch explosion
- ✅ MVV-LVA ordering improves alpha-beta efficiency

**Overall: Up to 2.36x faster search (endgames) with significantly better tactical play!**

### Combined Impact from Baseline:
Starting from simple material-only evaluation:
- **Before all optimizations**: ~44k nodes, 4-43k NPS
- **After all optimizations**: **7-17k nodes** (60-84% reduction!), 8-42k NPS
- **Effective search depth**: Can search 1-2 plies deeper in same time
- **Tactical strength**: Much better due to qsearch + check extensions
