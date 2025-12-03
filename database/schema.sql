"""
Database Schema
SQL schema for storing games, moves, positions, and analytics.
"""

# SQL Schema for Chess AI Database

SCHEMA_SQL = """
-- Games played by the engine
CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    white_player VARCHAR(50) NOT NULL,
    black_player VARCHAR(50) NOT NULL,
    result VARCHAR(10),  -- '1-0', '0-1', '1/2-1/2'
    opening_eco VARCHAR(5),
    opening_name VARCHAR(100),
    total_moves INTEGER,
    final_position TEXT,  -- FEN notation
    avg_eval_swing REAL,
    engine_config_id INTEGER,
    FOREIGN KEY (engine_config_id) REFERENCES engine_configs(config_id)
);

-- Every move with rich metadata
CREATE TABLE IF NOT EXISTS moves (
    move_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    move_number INTEGER NOT NULL,
    side_to_move VARCHAR(5) NOT NULL,  -- 'white' or 'black'
    move_notation VARCHAR(10) NOT NULL,  -- e.g., 'e2e4', 'e7e8q'
    move_from VARCHAR(2),  -- e.g., 'e2'
    move_to VARCHAR(2),    -- e.g., 'e4'
    evaluation_score REAL,  -- In centipawns
    search_depth INTEGER,
    nodes_searched INTEGER,
    time_ms INTEGER,
    principal_variation TEXT,  -- Best line of play
    is_capture BOOLEAN,
    is_check BOOLEAN,
    is_checkmate BOOLEAN,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE
);

-- Cache evaluated positions
CREATE TABLE IF NOT EXISTS positions (
    position_hash BIGINT PRIMARY KEY,
    fen TEXT NOT NULL,
    evaluation REAL,
    best_move VARCHAR(10),
    depth INTEGER,
    times_reached INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track AI performance metrics per move
CREATE TABLE IF NOT EXISTS search_statistics (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    nodes_searched INTEGER,
    cache_hits INTEGER,
    cache_misses INTEGER,
    alpha_beta_cutoffs INTEGER,
    quiescence_nodes INTEGER,
    search_depth INTEGER,
    time_ms INTEGER,
    nodes_per_second REAL,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES moves(move_id) ON DELETE CASCADE
);

-- Configuration profiles for experimentation
CREATE TABLE IF NOT EXISTS engine_configs (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name VARCHAR(50) UNIQUE NOT NULL,
    search_depth INTEGER DEFAULT 4,
    use_quiescence BOOLEAN DEFAULT 0,
    use_transposition_table BOOLEAN DEFAULT 0,
    use_iterative_deepening BOOLEAN DEFAULT 1,
    material_weight REAL DEFAULT 1.0,
    positional_weight REAL DEFAULT 1.0,
    mobility_weight REAL DEFAULT 0.1,
    king_safety_weight REAL DEFAULT 0.5,
    pawn_structure_weight REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Opening book performance
CREATE TABLE IF NOT EXISTS opening_statistics (
    opening_eco VARCHAR(5) PRIMARY KEY,
    opening_name VARCHAR(100) NOT NULL,
    times_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    avg_evaluation REAL
);

-- Performance benchmarks
CREATE TABLE IF NOT EXISTS benchmarks (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_name VARCHAR(100) NOT NULL,
    engine_config_id INTEGER,
    date_run TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    positions_tested INTEGER,
    correct_solutions INTEGER,
    avg_time_ms REAL,
    avg_nodes_searched REAL,
    avg_depth_reached REAL,
    tactical_rating INTEGER,  -- Estimated ELO from tactical tests
    FOREIGN KEY (engine_config_id) REFERENCES engine_configs(config_id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_moves_game_id ON moves(game_id);
CREATE INDEX IF NOT EXISTS idx_moves_move_number ON moves(move_number);
CREATE INDEX IF NOT EXISTS idx_search_stats_game_id ON search_statistics(game_id);
CREATE INDEX IF NOT EXISTS idx_positions_fen ON positions(fen);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(date_played);
CREATE INDEX IF NOT EXISTS idx_games_result ON games(result);
"""

# Default engine configuration
DEFAULT_CONFIG_SQL = """
INSERT OR IGNORE INTO engine_configs 
    (config_name, search_depth, use_quiescence, use_transposition_table, 
     use_iterative_deepening, material_weight, positional_weight)
VALUES 
    ('default', 4, 0, 0, 1, 1.0, 1.0),
    ('aggressive', 5, 1, 1, 1, 1.2, 0.8),
    ('positional', 4, 0, 1, 1, 0.9, 1.3),
    ('tactical', 6, 1, 1, 1, 1.1, 0.9),
    ('beginner', 2, 0, 0, 0, 1.0, 0.5);
"""
