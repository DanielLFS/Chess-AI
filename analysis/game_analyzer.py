"""
Analysis Module
Game analyzer for post-game analysis and insights.
"""

from typing import List, Dict, Any
from engine.board import Board
from engine.moves import MoveGenerator
from engine.evaluation import Evaluator
from database.models import DatabaseManager, Game, Move


class GameAnalyzer:
    """Analyzes chess games for insights."""
    
    def __init__(self):
        self.evaluator = Evaluator()
        self.db = DatabaseManager()
    
    def analyze_game(self, game_id: int) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a game.
        
        Returns:
            Dictionary with analysis results
        """
        session = self.db.get_session()
        try:
            game = session.query(Game).filter_by(game_id=game_id).first()
            if not game:
                return None
            
            moves = session.query(Move).filter_by(game_id=game_id).order_by(Move.move_number).all()
            
            analysis = {
                'game_id': game_id,
                'players': f"{game.white_player} vs {game.black_player}",
                'result': game.result,
                'total_moves': len(moves),
                'blunders': self._find_blunders(moves),
                'evaluation_graph': self._get_evaluation_graph(moves),
                'critical_moments': self._find_critical_moments(moves),
                'accuracy': self._calculate_accuracy(moves),
                'average_depth': sum(m.search_depth for m in moves if m.search_depth) / len(moves) if moves else 0
            }
            
            return analysis
        finally:
            session.close()
    
    def _find_blunders(self, moves: List[Move], threshold: float = 200) -> List[Dict]:
        """Find moves that resulted in large evaluation swings."""
        blunders = []
        
        for i in range(1, len(moves)):
            if moves[i-1].evaluation_score is None or moves[i].evaluation_score is None:
                continue
            
            prev_eval = moves[i-1].evaluation_score
            curr_eval = moves[i].evaluation_score
            
            # Adjust for side to move
            if moves[i].side_to_move == 'black':
                prev_eval = -prev_eval
                curr_eval = -curr_eval
            
            eval_drop = prev_eval - curr_eval
            
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
    
    def _get_evaluation_graph(self, moves: List[Move]) -> List[float]:
        """Get list of evaluations for graphing."""
        return [m.evaluation_score / 100.0 for m in moves if m.evaluation_score is not None]
    
    def _find_critical_moments(self, moves: List[Move], top_n: int = 5) -> List[Dict]:
        """Find moves with largest evaluation changes."""
        moments = []
        
        for i in range(1, len(moves)):
            if moves[i-1].evaluation_score is None or moves[i].evaluation_score is None:
                continue
            
            eval_change = abs(moves[i].evaluation_score - moves[i-1].evaluation_score)
            
            moments.append({
                'move_number': moves[i].move_number,
                'move': moves[i].move_notation,
                'eval_change': eval_change,
                'eval_before': moves[i-1].evaluation_score,
                'eval_after': moves[i].evaluation_score
            })
        
        return sorted(moments, key=lambda x: x['eval_change'], reverse=True)[:top_n]
    
    def _calculate_accuracy(self, moves: List[Move]) -> Dict[str, float]:
        """
        Calculate move accuracy (how close moves were to best evaluation).
        """
        white_accuracy = []
        black_accuracy = []
        
        for i in range(1, len(moves)):
            if moves[i].evaluation_score is None:
                continue
            
            # Simple accuracy: inverse of evaluation drop
            # Perfect move = 100%, large blunder = 0%
            eval_change = abs(moves[i].evaluation_score - moves[i-1].evaluation_score)
            accuracy = max(0, 100 - (eval_change / 10))  # Scale appropriately
            
            if moves[i].side_to_move == 'white':
                white_accuracy.append(accuracy)
            else:
                black_accuracy.append(accuracy)
        
        return {
            'white': sum(white_accuracy) / len(white_accuracy) if white_accuracy else 0,
            'black': sum(black_accuracy) / len(black_accuracy) if black_accuracy else 0
        }
    
    def compare_games(self, game_ids: List[int]) -> Dict[str, Any]:
        """Compare multiple games."""
        comparisons = []
        
        for game_id in game_ids:
            analysis = self.analyze_game(game_id)
            if analysis:
                comparisons.append(analysis)
        
        return {
            'games': comparisons,
            'summary': {
                'avg_moves': sum(g['total_moves'] for g in comparisons) / len(comparisons) if comparisons else 0,
                'total_blunders': sum(len(g['blunders']) for g in comparisons),
                'avg_depth': sum(g['average_depth'] for g in comparisons) / len(comparisons) if comparisons else 0
            }
        }
    
    def generate_report(self, game_id: int) -> str:
        """Generate a text report for a game."""
        analysis = self.analyze_game(game_id)
        
        if not analysis:
            return "Game not found."
        
        report = []
        report.append("=" * 60)
        report.append(f"Game Analysis Report - Game #{game_id}")
        report.append("=" * 60)
        report.append(f"\nPlayers: {analysis['players']}")
        report.append(f"Result: {analysis['result']}")
        report.append(f"Total Moves: {analysis['total_moves']}")
        report.append(f"Average Search Depth: {analysis['average_depth']:.1f}")
        
        report.append(f"\n{'Accuracy:':<20}")
        report.append(f"  White: {analysis['accuracy']['white']:.1f}%")
        report.append(f"  Black: {analysis['accuracy']['black']:.1f}%")
        
        if analysis['blunders']:
            report.append(f"\nBlunders Found: {len(analysis['blunders'])}")
            for blunder in analysis['blunders'][:5]:  # Top 5
                report.append(f"  Move {blunder['move_number']} ({blunder['side']}): {blunder['move']}")
                report.append(f"    Eval drop: {blunder['eval_drop']:.0f} centipawns")
        else:
            report.append("\nNo major blunders found!")
        
        if analysis['critical_moments']:
            report.append(f"\nCritical Moments:")
            for moment in analysis['critical_moments'][:3]:
                report.append(f"  Move {moment['move_number']}: {moment['move']}")
                report.append(f"    Eval change: {moment['eval_change']:.0f} centipawns")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    analyzer = GameAnalyzer()
    
    # Analyze most recent game
    db = DatabaseManager()
    games = db.get_all_games(limit=1)
    
    if games:
        report = analyzer.generate_report(games[0].game_id)
        print(report)
    else:
        print("No games found in database. Play a game first!")
