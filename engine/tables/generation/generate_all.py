"""
Generate all lookup tables for chess engine.

This script pre-computes and saves all tables to .npy files.
Run this to regenerate tables with different parameters or after tuning.

Usage:
    python -m engine.tables.generate_all [--seed 42]
"""

import argparse
from . import zobrist_keys, magic_tables, pst_tables


def generate_all(seed: int = 42):
    """
    Generate all tables and save to .npy files.
    
    Args:
        seed: Random seed for Zobrist keys
    """
    print("=" * 60)
    print("GENERATING ALL LOOKUP TABLES")
    print("=" * 60)
    print()
    
    # Zobrist keys
    print("[1/3] Zobrist Keys")
    print("-" * 60)
    zobrist_keys.save_zobrist_keys(seed)
    print()
    
    # Magic bitboards
    print("[2/3] Magic Bitboards")
    print("-" * 60)
    magic_tables.save_magic_tables()
    print()
    
    # Piece-Square Tables
    print("[3/3] Piece-Square Tables")
    print("-" * 60)
    pst_tables.save_pst_tables()
    print()
    
    print("=" * 60)
    print("✅ ALL TABLES GENERATED")
    print("=" * 60)
    
    # Calculate total size
    import numpy as np
    from pathlib import Path
    
    table_dir = Path(__file__).parent.parent  # Go up to tables/ directory
    npy_files = list(table_dir.glob("*.npy"))
    total_size = sum(f.stat().st_size for f in npy_files)
    
    print(f"\nTotal storage: {total_size // 1024}KB ({len(npy_files)} files)")
    print("\nFiles:")
    for f in sorted(npy_files):
        size = f.stat().st_size
        unit = "KB" if size >= 1024 else "B"
        size_val = size // 1024 if size >= 1024 else size
        print(f"  - {f.name:30s} {size_val:5d} {unit}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate chess engine lookup tables")
    parser.add_argument('--seed', type=int, default=42, help='Random seed for Zobrist keys')
    args = parser.parse_args()
    
    generate_all(args.seed)
