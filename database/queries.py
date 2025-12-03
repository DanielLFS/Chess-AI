"""
Database Queries Module
Complex analytical queries for chess game analysis.
"""

from sqlalchemy import func, and_, or_, desc, text
from database.models import Game, Move, SearchStatistic, EngineConfig, OpeningStatistic, Benchmark
from typing import List, Dict, Any


class AnalyticsQueries:
    """Complex analytical queries for game analysis."""
    
    def __init__(self, session):
        self.session = session
    
    def get_game_statistics(self, game_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a game."""
        game = self.session.query(Game).filter_by(game_id=game_id).first()
        if not game:
            return None
        
        moves = self.session.query(Move).filter_by(game_id=game_id).all()
        
        stats = {
            'game_id': game.game_id,
            'players': f"{game.white_player} vs {game.black_player}",
            'result': game.result,
            'total_moves': len(moves),
            'opening': f"{game.opening_eco}: {game.opening_name}" if game.opening_eco else "Unknown",
            'evaluations': [m.evaluation_score for m in moves if m.evaluation_score],
            'avg_depth': sum(m.search_depth for m in moves if m.search_depth) / len(moves) if moves else 0,
            'total_nodes': sum(m.nodes_searched for m in moves if m.nodes_searched),
            'captures': sum(1 for m in moves if m.is_capture),
            'checks': sum(1 for m in moves if m.is_check)
        }
        
        return stats
    
    def get_player_performance(self, player_name: str) -> Dict[str, Any]:
        """Get performance statistics for a player."""
        # Games as white
        white_games = self.session.query(Game).filter_by(white_player=player_name).all()
        # Games as black
        black_games = self.session.query(Game).filter_by(black_player=player_name).all()
        
        total_games = len(white_games) + len(black_games)
        
        wins = sum(1 for g in white_games if g.result == '1-0') + \
               sum(1 for g in black_games if g.result == '0-1')
        draws = sum(1 for g in white_games + black_games if g.result == '1/2-1/2')
        losses = total_games - wins - draws
        
        return {
            'player': player_name,
            'total_games': total_games,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': wins / total_games if total_games > 0 else 0,
            'games_as_white': len(white_games),
            'games_as_black': len(black_games)
        }
    
    def get_opening_performance(self, opening_eco: str = None) -> List[Dict[str, Any]]:
        """Get performance statistics for openings."""
        if opening_eco:
            stats = self.session.query(OpeningStatistic).filter_by(opening_eco=opening_eco).first()
            return [self._format_opening_stat(stats)] if stats else []
        else:
            stats = self.session.query(OpeningStatistic).order_by(
                desc(OpeningStatistic.times_played)
            ).limit(20).all()
            return [self._format_opening_stat(s) for s in stats]
    
    def _format_opening_stat(self, stat: OpeningStatistic) -> Dict[str, Any]:
        """Format opening statistic for display."""
        total = stat.wins + stat.draws + stat.losses
        return {
            'eco': stat.opening_eco,
            'name': stat.opening_name,
            'games': total,
            'wins': stat.wins,
            'draws': stat.draws,
            'losses': stat.losses,
            'win_rate': stat.wins / total if total > 0 else 0,
            'avg_eval': stat.avg_evaluation
        }
    
    def get_engine_performance_comparison(self) -> List[Dict[str, Any]]:
        """Compare performance of different engine configurations."""
        configs = self.session.query(EngineConfig).all()
        
        results = []
        for config in configs:
            games = self.session.query(Game).filter_by(engine_config_id=config.config_id).all()
            
            if games:
                total_games = len(games)
                wins = sum(1 for g in games if g.result == '1-0')
                
                # Average search statistics
                avg_nodes = self.session.query(func.avg(SearchStatistic.nodes_searched)).filter(
                    SearchStatistic.game_id.in_([g.game_id for g in games])
                ).scalar() or 0
                
                avg_time = self.session.query(func.avg(SearchStatistic.time_ms)).filter(
                    SearchStatistic.game_id.in_([g.game_id for g in games])
                ).scalar() or 0
                
                results.append({
                    'config_name': config.config_name,
                    'search_depth': config.search_depth,
                    'total_games': total_games,
                    'wins': wins,
                    'win_rate': wins / total_games,
                    'avg_nodes_per_move': avg_nodes,
                    'avg_time_per_move_ms': avg_time
                })
        
        return sorted(results, key=lambda x: x['win_rate'], reverse=True)
    
    def get_position_evaluation_history(self, fen: str) -> List[Dict[str, Any]]:
        """Get evaluation history for a specific position."""
        # This would track how the engine's evaluation of a position changed over time
        # Useful for analyzing evaluation function improvements
        
        moves = self.session.query(Move, Game).join(Game).filter(
            Move.move_notation.like(f'%{fen}%')  # Simplified - would need better FEN matching
        ).order_by(Game.date_played).all()
        
        return [{
            'date': game.date_played,
            'evaluation': move.evaluation_score,
            'depth': move.search_depth,
            'game_id': game.game_id
        } for move, game in moves]
    
    def get_tactical_motif_statistics(self) -> Dict[str, int]:
        """Get statistics on tactical motifs found."""
        # Count different types of tactical moves
        total_moves = self.session.query(func.count(Move.move_id)).scalar()
        captures = self.session.query(func.count(Move.move_id)).filter(Move.is_capture == True).scalar()
        checks = self.session.query(func.count(Move.move_id)).filter(Move.is_check == True).scalar()
        checkmates = self.session.query(func.count(Move.move_id)).filter(Move.is_checkmate == True).scalar()
        
        return {
            'total_moves': total_moves,
            'captures': captures,
            'checks': checks,
            'checkmates': checkmates,
            'capture_rate': captures / total_moves if total_moves > 0 else 0,
            'check_rate': checks / total_moves if total_moves > 0 else 0
        }
    
    def get_search_efficiency_trends(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get search efficiency metrics over time."""
        stats = self.session.query(
            SearchStatistic,
            Game.date_played
        ).join(Game).order_by(desc(Game.date_played)).limit(limit).all()
        
        return [{
            'date': game_date,
            'nodes_searched': stat.nodes_searched,
            'nodes_per_second': stat.nodes_per_second,
            'alpha_beta_cutoffs': stat.alpha_beta_cutoffs,
            'cutoff_rate': stat.alpha_beta_cutoffs / stat.nodes_searched if stat.nodes_searched > 0 else 0
        } for stat, game_date in stats]
    
    def get_average_game_length_by_opening(self) -> List[Dict[str, Any]]:
        """Get average game length grouped by opening."""
        results = self.session.query(
            Game.opening_eco,
            Game.opening_name,
            func.avg(Game.total_moves).label('avg_moves'),
            func.count(Game.game_id).label('games_count')
        ).filter(
            Game.opening_eco.isnot(None)
        ).group_by(
            Game.opening_eco, Game.opening_name
        ).having(
            func.count(Game.game_id) >= 3  # At least 3 games
        ).order_by(
            desc('avg_moves')
        ).all()
        
        return [{
            'opening_eco': r.opening_eco,
            'opening_name': r.opening_name,
            'avg_moves': round(r.avg_moves, 1),
            'games_count': r.games_count
        } for r in results]
    
    def get_blunder_analysis(self, game_id: int, threshold: float = 200) -> List[Dict[str, Any]]:
        """
        Identify blunders in a game (evaluation drops by more than threshold centipawns).
        """
        moves = self.session.query(Move).filter_by(game_id=game_id).order_by(Move.move_number).all()
        
        blunders = []
        for i in range(1, len(moves)):
            prev_eval = moves[i-1].evaluation_score
            curr_eval = moves[i].evaluation_score
            
            if prev_eval is not None and curr_eval is not None:
                eval_drop = abs(curr_eval - prev_eval)
                if eval_drop >= threshold:
                    blunders.append({
                        'move_number': moves[i].move_number,
                        'move': moves[i].move_notation,
                        'side': moves[i].side_to_move,
                        'eval_before': prev_eval,
                        'eval_after': curr_eval,
                        'eval_drop': eval_drop
                    })
        
        return blunders
