"""
Database Models
SQLAlchemy ORM models for chess game data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


class Game(Base):
    """Represents a chess game."""
    __tablename__ = 'games'
    
    game_id = Column(Integer, primary_key=True, autoincrement=True)
    date_played = Column(DateTime, default=datetime.utcnow)
    white_player = Column(String(50), nullable=False)
    black_player = Column(String(50), nullable=False)
    result = Column(String(10))  # '1-0', '0-1', '1/2-1/2'
    opening_eco = Column(String(5))
    opening_name = Column(String(100))
    total_moves = Column(Integer)
    final_position = Column(Text)  # FEN notation
    avg_eval_swing = Column(Float)
    engine_config_id = Column(Integer, ForeignKey('engine_configs.config_id'))
    
    # Relationships
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    statistics = relationship("SearchStatistic", back_populates="game", cascade="all, delete-orphan")
    config = relationship("EngineConfig", back_populates="games")
    
    def __repr__(self):
        return f"<Game(id={self.game_id}, {self.white_player} vs {self.black_player}, {self.result})>"


class Move(Base):
    """Represents a single move in a game."""
    __tablename__ = 'moves'
    
    move_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('games.game_id'), nullable=False)
    move_number = Column(Integer, nullable=False)
    side_to_move = Column(String(5), nullable=False)
    move_notation = Column(String(10), nullable=False)
    move_from = Column(String(2))
    move_to = Column(String(2))
    evaluation_score = Column(Float)
    search_depth = Column(Integer)
    nodes_searched = Column(Integer)
    time_ms = Column(Integer)
    principal_variation = Column(Text)
    is_capture = Column(Boolean, default=False)
    is_check = Column(Boolean, default=False)
    is_checkmate = Column(Boolean, default=False)
    
    # Relationships
    game = relationship("Game", back_populates="moves")
    statistics = relationship("SearchStatistic", back_populates="move")
    
    def __repr__(self):
        return f"<Move(game={self.game_id}, move={self.move_number}, {self.move_notation})>"


class Position(Base):
    """Represents a chess position for caching."""
    __tablename__ = 'positions'
    
    position_hash = Column(BigInteger, primary_key=True)
    fen = Column(Text, nullable=False)
    evaluation = Column(Float)
    best_move = Column(String(10))
    depth = Column(Integer)
    times_reached = Column(Integer, default=1)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Position(hash={self.position_hash}, eval={self.evaluation})>"


class SearchStatistic(Base):
    """Represents search statistics for a move."""
    __tablename__ = 'search_statistics'
    
    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('games.game_id'), nullable=False)
    move_id = Column(Integer, ForeignKey('moves.move_id'), nullable=False)
    nodes_searched = Column(Integer)
    cache_hits = Column(Integer)
    cache_misses = Column(Integer)
    alpha_beta_cutoffs = Column(Integer)
    quiescence_nodes = Column(Integer)
    search_depth = Column(Integer)
    time_ms = Column(Integer)
    nodes_per_second = Column(Float)
    
    # Relationships
    game = relationship("Game", back_populates="statistics")
    move = relationship("Move", back_populates="statistics")
    
    def __repr__(self):
        return f"<SearchStatistic(game={self.game_id}, nodes={self.nodes_searched})>"


class EngineConfig(Base):
    """Represents an engine configuration."""
    __tablename__ = 'engine_configs'
    
    config_id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(50), unique=True, nullable=False)
    search_depth = Column(Integer, default=4)
    use_quiescence = Column(Boolean, default=False)
    use_transposition_table = Column(Boolean, default=False)
    use_iterative_deepening = Column(Boolean, default=True)
    material_weight = Column(Float, default=1.0)
    positional_weight = Column(Float, default=1.0)
    mobility_weight = Column(Float, default=0.1)
    king_safety_weight = Column(Float, default=0.5)
    pawn_structure_weight = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    games = relationship("Game", back_populates="config")
    benchmarks = relationship("Benchmark", back_populates="config")
    
    def __repr__(self):
        return f"<EngineConfig(name={self.config_name}, depth={self.search_depth})>"


class OpeningStatistic(Base):
    """Represents statistics for chess openings."""
    __tablename__ = 'opening_statistics'
    
    opening_eco = Column(String(5), primary_key=True)
    opening_name = Column(String(100), nullable=False)
    times_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    avg_evaluation = Column(Float)
    
    def __repr__(self):
        return f"<OpeningStatistic({self.opening_eco}: {self.opening_name})>"


class Benchmark(Base):
    """Represents a performance benchmark."""
    __tablename__ = 'benchmarks'
    
    benchmark_id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_name = Column(String(100), nullable=False)
    engine_config_id = Column(Integer, ForeignKey('engine_configs.config_id'))
    date_run = Column(DateTime, default=datetime.utcnow)
    positions_tested = Column(Integer)
    correct_solutions = Column(Integer)
    avg_time_ms = Column(Float)
    avg_nodes_searched = Column(Float)
    avg_depth_reached = Column(Float)
    tactical_rating = Column(Integer)  # Estimated ELO
    
    # Relationships
    config = relationship("EngineConfig", back_populates="benchmarks")
    
    def __repr__(self):
        return f"<Benchmark(name={self.benchmark_name}, rating={self.tactical_rating})>"


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: str = "sqlite:///chess_ai.db"):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def execute_sql_file(self, filepath: str):
        """Execute SQL commands from a file."""
        with open(filepath, 'r') as f:
            sql_script = f.read()
        
        with self.engine.connect() as conn:
            for statement in sql_script.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            conn.commit()
    
    def save_game(self, game_data: dict) -> int:
        """
        Save a game to the database.
        
        Returns:
            game_id of the saved game
        """
        session = self.get_session()
        try:
            game = Game(**game_data)
            session.add(game)
            session.commit()
            return game.game_id
        finally:
            session.close()
    
    def save_move(self, move_data: dict) -> int:
        """
        Save a move to the database.
        
        Returns:
            move_id of the saved move
        """
        session = self.get_session()
        try:
            move = Move(**move_data)
            session.add(move)
            session.commit()
            return move.move_id
        finally:
            session.close()
    
    def save_search_stats(self, stats_data: dict) -> int:
        """
        Save search statistics to the database.
        
        Returns:
            stat_id of the saved statistics
        """
        session = self.get_session()
        try:
            stats = SearchStatistic(**stats_data)
            session.add(stats)
            session.commit()
            return stats.stat_id
        finally:
            session.close()
    
    def get_position(self, position_hash: int):
        """Get a cached position from the database."""
        session = self.get_session()
        try:
            return session.query(Position).filter_by(position_hash=position_hash).first()
        finally:
            session.close()
    
    def save_position(self, position_data: dict):
        """Save or update a position in the database."""
        session = self.get_session()
        try:
            position = session.query(Position).filter_by(
                position_hash=position_data['position_hash']
            ).first()
            
            if position:
                # Update existing
                position.times_reached += 1
                position.last_accessed = datetime.utcnow()
                if 'evaluation' in position_data:
                    position.evaluation = position_data['evaluation']
                if 'best_move' in position_data:
                    position.best_move = position_data['best_move']
            else:
                # Create new
                position = Position(**position_data)
                session.add(position)
            
            session.commit()
        finally:
            session.close()
    
    def get_engine_config(self, config_name: str):
        """Get an engine configuration by name."""
        session = self.get_session()
        try:
            return session.query(EngineConfig).filter_by(config_name=config_name).first()
        finally:
            session.close()
    
    def get_all_games(self, limit: int = 100):
        """Get recent games from the database."""
        session = self.get_session()
        try:
            return session.query(Game).order_by(Game.date_played.desc()).limit(limit).all()
        finally:
            session.close()
