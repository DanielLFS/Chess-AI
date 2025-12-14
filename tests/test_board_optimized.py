"""
Test suite for optimized board.py (MINIMAL OOP version)
Tests both individual numba functions and the Board class integration.
NO Piece/Move classes - working with raw values only!
"""

import pytest
import numpy as np
from engine.board import (
    Board, PieceType, Color,
    make_move_fast, unmake_move_fast, update_castling_rights, decode_move,
    CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ, CASTLE_ALL,
    FLAG_NORMAL, FLAG_PROMOTION_QUEEN, FLAG_CASTLING_KINGSIDE, 
    FLAG_CASTLING_QUEENSIDE, FLAG_EN_PASSANT
)


# ============================================================================
# PART 1: Test Individual Numba Functions
# ============================================================================

class TestNumbaFunctions:
    """Test individual numba-compiled functions in isolation."""
    
    def test_decode_move(self):
        """Test move encoding/decoding."""
        # Encode a move from e2 to e4
        encoded = np.uint16((FLAG_NORMAL << 12) | (28 << 6) | 52)  # e2(52) -> e4(28)
        from_sq, to_sq, flags = decode_move(encoded)
        
        assert from_sq == 52  # e2
        assert to_sq == 28    # e4
        assert flags == FLAG_NORMAL
    
    def test_make_move_fast_normal(self):
        """Test make_move_fast for normal moves."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # Place white pawn on e2
        pieces[6, 4] = PieceType.PAWN
        colors[6, 4] = Color.WHITE
        
        # Move to e4
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 6, 4, 4, 4, FLAG_NORMAL
        )
        
        # Check piece moved
        assert pieces[6, 4] == 0
        assert colors[6, 4] == 0
        assert pieces[4, 4] == PieceType.PAWN
        assert colors[4, 4] == Color.WHITE
        
        # Check no capture
        assert captured == 0
        assert captured_color == 0
    
    def test_make_move_fast_capture(self):
        """Test make_move_fast with capture."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # White pawn on e4, black pawn on d5
        pieces[4, 4] = PieceType.PAWN
        colors[4, 4] = Color.WHITE
        pieces[3, 3] = PieceType.PAWN
        colors[3, 3] = Color.BLACK
        
        # Capture d5
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 4, 4, 3, 3, FLAG_NORMAL
        )
        
        # Check capture info
        assert captured == PieceType.PAWN
        assert captured_color == Color.BLACK
        
        # Check position
        assert pieces[4, 4] == 0
        assert pieces[3, 3] == PieceType.PAWN
        assert colors[3, 3] == Color.WHITE
    
    def test_make_move_fast_castling_kingside(self):
        """Test kingside castling."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # White king on e1, rook on h1
        pieces[7, 4] = PieceType.KING
        colors[7, 4] = Color.WHITE
        pieces[7, 7] = PieceType.ROOK
        colors[7, 7] = Color.WHITE
        
        # Castle kingside
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 7, 4, 7, 6, FLAG_CASTLING_KINGSIDE
        )
        
        # Check king moved to g1
        assert pieces[7, 6] == PieceType.KING
        assert colors[7, 6] == Color.WHITE
        
        # Check rook moved to f1
        assert pieces[7, 5] == PieceType.ROOK
        assert colors[7, 5] == Color.WHITE
        
        # Check old positions empty
        assert pieces[7, 4] == 0
        assert pieces[7, 7] == 0
    
    def test_make_move_fast_castling_queenside(self):
        """Test queenside castling."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # White king on e1, rook on a1
        pieces[7, 4] = PieceType.KING
        colors[7, 4] = Color.WHITE
        pieces[7, 0] = PieceType.ROOK
        colors[7, 0] = Color.WHITE
        
        # Castle queenside
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 7, 4, 7, 2, FLAG_CASTLING_QUEENSIDE
        )
        
        # Check king moved to c1
        assert pieces[7, 2] == PieceType.KING
        assert colors[7, 2] == Color.WHITE
        
        # Check rook moved to d1
        assert pieces[7, 3] == PieceType.ROOK
        assert colors[7, 3] == Color.WHITE
        
        # Check old positions empty
        assert pieces[7, 4] == 0
        assert pieces[7, 0] == 0
    
    def test_make_move_fast_en_passant(self):
        """Test en passant capture."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # White pawn on e5, black pawn on d5
        pieces[3, 4] = PieceType.PAWN
        colors[3, 4] = Color.WHITE
        pieces[3, 3] = PieceType.PAWN
        colors[3, 3] = Color.BLACK
        
        # En passant capture to d6
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 3, 4, 2, 3, FLAG_EN_PASSANT
        )
        
        # Check white pawn moved to d6
        assert pieces[2, 3] == PieceType.PAWN
        assert colors[2, 3] == Color.WHITE
        
        # Check black pawn captured (on d5, same row as moving pawn)
        assert pieces[3, 3] == 0
        assert ep_cap == PieceType.PAWN
        assert ep_cap_color == Color.BLACK
    
    def test_make_move_fast_promotion(self):
        """Test pawn promotion."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # White pawn on e7
        pieces[1, 4] = PieceType.PAWN
        colors[1, 4] = Color.WHITE
        
        # Promote to queen on e8
        captured, captured_color, ep_cap, ep_cap_color = make_move_fast(
            pieces, colors, 1, 4, 0, 4, FLAG_PROMOTION_QUEEN
        )
        
        # Check promoted to queen
        assert pieces[0, 4] == PieceType.QUEEN
        assert colors[0, 4] == Color.WHITE
        assert pieces[1, 4] == 0
    
    def test_unmake_move_fast_normal(self):
        """Test unmake_move_fast for normal moves."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # After move: pawn on e4
        pieces[4, 4] = PieceType.PAWN
        colors[4, 4] = Color.WHITE
        
        # Unmake move from e2
        unmake_move_fast(pieces, colors, 6, 4, 4, 4, FLAG_NORMAL, 0, 0, 0, 0)
        
        # Check restored
        assert pieces[6, 4] == PieceType.PAWN
        assert colors[6, 4] == Color.WHITE
        assert pieces[4, 4] == 0
    
    def test_unmake_move_fast_capture(self):
        """Test unmake_move_fast with capture."""
        pieces = np.zeros((8, 8), dtype=np.int8)
        colors = np.zeros((8, 8), dtype=np.int8)
        
        # After capture: white pawn on d5
        pieces[3, 3] = PieceType.PAWN
        colors[3, 3] = Color.WHITE
        
        # Unmake - restore black pawn
        unmake_move_fast(pieces, colors, 4, 4, 3, 3, FLAG_NORMAL,
                        PieceType.PAWN, Color.BLACK, 0, 0)
        
        # Check both pieces restored
        assert pieces[4, 4] == PieceType.PAWN
        assert colors[4, 4] == Color.WHITE
        assert pieces[3, 3] == PieceType.PAWN
        assert colors[3, 3] == Color.BLACK
    
    def test_update_castling_rights_king_move(self):
        """Test castling rights update when king moves."""
        rights = CASTLE_ALL
        
        # White king moves
        new_rights = update_castling_rights(
            rights, PieceType.KING, Color.WHITE, 4, 7, 5, 0
        )
        
        # White should lose both castling rights
        assert not (new_rights & CASTLE_WK)
        assert not (new_rights & CASTLE_WQ)
        assert (new_rights & CASTLE_BK)  # Black keeps rights
        assert (new_rights & CASTLE_BQ)
    
    def test_update_castling_rights_rook_move(self):
        """Test castling rights update when rook moves."""
        rights = CASTLE_ALL
        
        # White kingside rook moves from h1
        new_rights = update_castling_rights(
            rights, PieceType.ROOK, Color.WHITE, 7, 7, 6, 0
        )
        
        # Only white kingside should be lost
        assert not (new_rights & CASTLE_WK)
        assert (new_rights & CASTLE_WQ)
        assert (new_rights & CASTLE_BK)
        assert (new_rights & CASTLE_BQ)
    
    def test_update_castling_rights_rook_captured(self):
        """Test castling rights when rook is captured."""
        rights = CASTLE_ALL
        
        # Capture black queenside rook on a8
        new_rights = update_castling_rights(
            rights, PieceType.KNIGHT, Color.WHITE, 1, 0, 0, PieceType.ROOK
        )
        
        # Black queenside should be lost
        assert (new_rights & CASTLE_WK)
        assert (new_rights & CASTLE_WQ)
        assert (new_rights & CASTLE_BK)
        assert not (new_rights & CASTLE_BQ)


# ============================================================================
# PART 2: Test Board Class Integration
# ============================================================================

class TestBoardIntegration:
    """Test Board class using the optimized functions."""
    
    def test_board_initialization(self):
        """Test board starts in correct position."""
        board = Board()
        
        # Check starting position
        assert board.piece_array[0, 0] == PieceType.ROOK  # Black rook a8
        assert board.piece_array[0, 4] == PieceType.KING  # Black king e8
        assert board.piece_array[7, 4] == PieceType.KING  # White king e1
        assert board.piece_array[6, 4] == PieceType.PAWN  # White pawn e2
        
        # Check colors
        assert board.color_array[0, 0] == Color.BLACK
        assert board.color_array[7, 0] == Color.WHITE
        
        # Check game state
        assert board.current_player == Color.WHITE
        assert board.castling_rights == CASTLE_ALL
        assert board.halfmove_clock == 0
        assert board.fullmove_number == 1
    
    def test_board_fen_export(self):
        """Test FEN export."""
        board = Board()
        fen = board.to_fen()
        
        expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert fen == expected
    
    def test_board_fen_import(self):
        """Test FEN import."""
        board = Board()
        fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 3"
        board.from_fen(fen)
        
        # Check some pieces
        assert board.piece_array[2, 5] == PieceType.KNIGHT  # White knight f6
        assert board.piece_array[5, 5] == PieceType.KNIGHT  # Black knight f3
        
        # Check game state
        assert board.current_player == Color.WHITE
        assert board.castling_rights == CASTLE_ALL
        assert board.halfmove_clock == 4
        assert board.fullmove_number == 3
    
    def test_make_unmake_normal_move(self):
        """Test making and unmaking a normal move (e2-e4)."""
        board = Board()
        
        # e2-e4 using raw coordinates
        success = board.make_move(6, 4, 4, 4, FLAG_NORMAL)
        
        assert success
        assert board.piece_array[4, 4] == PieceType.PAWN
        assert board.piece_array[6, 4] == 0
        assert board.current_player == Color.BLACK
        
        # Unmake
        board.unmake_move(6, 4, 4, 4, FLAG_NORMAL)
        
        assert board.piece_array[6, 4] == PieceType.PAWN
        assert board.piece_array[4, 4] == 0
        assert board.current_player == Color.WHITE
    
    def test_make_unmake_capture(self):
        """Test capture and unmake."""
        board = Board()
        # Pawn takes pawn: e4xd5
        board.from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        
        board.make_move(4, 4, 3, 3, FLAG_NORMAL)
        
        # Check capture happened
        assert board.piece_array[3, 3] == PieceType.PAWN
        assert board.color_array[3, 3] == Color.WHITE
        
        # Unmake
        board.unmake_move(4, 4, 3, 3, FLAG_NORMAL)
        
        # Check restored
        assert board.piece_array[4, 4] == PieceType.PAWN
        assert board.color_array[4, 4] == Color.WHITE
        assert board.piece_array[3, 3] == PieceType.PAWN
        assert board.color_array[3, 3] == Color.BLACK
    
    def test_make_unmake_castling_kingside(self):
        """Test kingside castling (O-O)."""
        board = Board()
        board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1")
        
        # O-O
        board.make_move(7, 4, 7, 6, FLAG_CASTLING_KINGSIDE)
        
        # Check castled position
        assert board.piece_array[7, 6] == PieceType.KING
        assert board.piece_array[7, 5] == PieceType.ROOK
        assert board.piece_array[7, 4] == 0
        assert board.piece_array[7, 7] == 0
        
        # Check castling rights lost
        assert not (board.castling_rights & CASTLE_WK)
        assert not (board.castling_rights & CASTLE_WQ)
        
        # Unmake
        board.unmake_move(7, 4, 7, 6, FLAG_CASTLING_KINGSIDE)
        
        # Check restored
        assert board.piece_array[7, 4] == PieceType.KING
        assert board.piece_array[7, 7] == PieceType.ROOK
        assert board.piece_array[7, 6] == 0
        assert board.piece_array[7, 5] == 0
    
    def test_make_unmake_en_passant(self):
        """Test en passant capture (e5xd6 e.p.)."""
        board = Board()
        board.from_fen("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
        
        # e5xd6 e.p.
        board.make_move(3, 4, 2, 3, FLAG_EN_PASSANT)
        
        # Check capture
        assert board.piece_array[2, 3] == PieceType.PAWN
        assert board.color_array[2, 3] == Color.WHITE
        assert board.piece_array[3, 3] == 0  # Captured pawn removed
        
        # Unmake
        board.unmake_move(3, 4, 2, 3, FLAG_EN_PASSANT)
        
        # Check restored
        assert board.piece_array[3, 4] == PieceType.PAWN
        assert board.color_array[3, 4] == Color.WHITE
        assert board.piece_array[3, 3] == PieceType.PAWN
        assert board.color_array[3, 3] == Color.BLACK
    
    def test_make_unmake_promotion(self):
        """Test pawn promotion (e7-e8=Q)."""
        board = Board()
        board.from_fen("8/4P3/8/8/8/8/4k3/4K3 w - - 0 1")
        
        # e7-e8=Q
        board.make_move(1, 4, 0, 4, FLAG_PROMOTION_QUEEN)
        
        # Check promoted
        assert board.piece_array[0, 4] == PieceType.QUEEN
        assert board.color_array[0, 4] == Color.WHITE
        
        # Unmake
        board.unmake_move(1, 4, 0, 4, FLAG_PROMOTION_QUEEN)
        
        # Check restored as pawn
        assert board.piece_array[1, 4] == PieceType.PAWN
        assert board.color_array[1, 4] == Color.WHITE
        assert board.piece_array[0, 4] == 0
    
    def test_castling_rights_updates(self):
        """Test castling rights update correctly when king moves."""
        board = Board()
        
        # Move white king (e1-f1)
        board.make_move(7, 4, 7, 5, FLAG_NORMAL)
        
        # Check white lost castling
        assert not (board.castling_rights & CASTLE_WK)
        assert not (board.castling_rights & CASTLE_WQ)
        assert (board.castling_rights & CASTLE_BK)
        assert (board.castling_rights & CASTLE_BQ)
    
    def test_en_passant_target_updates(self):
        """Test en passant target is set correctly on double pawn push."""
        board = Board()
        
        # e2-e4 (double pawn push)
        board.make_move(6, 4, 4, 4, FLAG_NORMAL)
        
        # Check en passant target set
        assert board.en_passant_target == (5, 4)  # e3
        
        # Next move should clear it
        board.make_move(1, 0, 2, 0, FLAG_NORMAL)  # Random black move
        
        assert board.en_passant_target is None
    
    def test_halfmove_clock_updates(self):
        """Test halfmove clock increments and resets."""
        board = Board()
        
        # Knight move (clock increments) - Nb1-c3
        board.make_move(7, 1, 5, 2, FLAG_NORMAL)
        assert board.halfmove_clock == 1
        
        # Another knight move - Nb8-c6
        board.make_move(0, 1, 2, 2, FLAG_NORMAL)
        assert board.halfmove_clock == 2
        
        # Pawn move (clock resets) - a2-a4
        board.make_move(6, 0, 4, 0, FLAG_NORMAL)
        assert board.halfmove_clock == 0
    
    def test_fullmove_number_updates(self):
        """Test fullmove number increments after black's move."""
        board = Board()
        
        assert board.fullmove_number == 1
        
        # White move - e2-e4
        board.make_move(6, 4, 4, 4, FLAG_NORMAL)
        assert board.fullmove_number == 1  # Still 1
        
        # Black move - e7-e5
        board.make_move(1, 4, 3, 4, FLAG_NORMAL)
        assert board.fullmove_number == 2  # Now 2
    
    def test_player_switches(self):
        """Test current player switches correctly."""
        board = Board()
        
        assert board.current_player == Color.WHITE
        
        board.make_move(6, 4, 4, 4, FLAG_NORMAL)
        
        assert board.current_player == Color.BLACK
        
        board.unmake_move(6, 4, 4, 4, FLAG_NORMAL)
        
        assert board.current_player == Color.WHITE
    
    def test_king_position_cache(self):
        """Test king position is cached correctly."""
        board = Board()
        
        assert board.king_positions[Color.WHITE] == (7, 4)
        assert board.king_positions[Color.BLACK] == (0, 4)
        
        # Move white king (e1-f1)
        board.make_move(7, 4, 7, 5, FLAG_NORMAL)
        
        assert board.king_positions[Color.WHITE] == (7, 5)
        
        # Unmake
        board.unmake_move(7, 4, 7, 5, FLAG_NORMAL)
        
        assert board.king_positions[Color.WHITE] == (7, 4)


# ============================================================================
# PART 3: Integration and Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and complex scenarios."""
    
    def test_multiple_moves_sequence(self):
        """Test a sequence of moves and unmake all."""
        board = Board()
        moves = [
            (6, 4, 4, 4, FLAG_NORMAL),  # e4
            (1, 4, 3, 4, FLAG_NORMAL),  # e5
            (7, 6, 5, 5, FLAG_NORMAL),  # Nf3
            (0, 1, 2, 2, FLAG_NORMAL),  # Nc6
        ]
        
        for from_r, from_c, to_r, to_c, flags in moves:
            board.make_move(from_r, from_c, to_r, to_c, flags)
        
        # Unmake all
        for from_r, from_c, to_r, to_c, flags in reversed(moves):
            board.unmake_move(from_r, from_c, to_r, to_c, flags)
        
        # Should be back to starting position
        fen = board.to_fen()
        assert fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    def test_fen_roundtrip(self):
        """Test FEN import/export roundtrip."""
        test_fens = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 3",
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
        ]
        
        for fen in test_fens:
            board = Board()
            board.from_fen(fen)
            exported = board.to_fen()
            assert exported == fen, f"FEN mismatch: {fen} != {exported}"
    
    def test_board_copy(self):
        """Test board copying."""
        board1 = Board()
        board1.make_move(6, 4, 4, 4, FLAG_NORMAL)
        
        board2 = board1.copy()
        
        # Should be equal
        assert np.array_equal(board1.piece_array, board2.piece_array)
        assert np.array_equal(board1.color_array, board2.color_array)
        
        # Modify board2
        board2.make_move(1, 4, 3, 4, FLAG_NORMAL)
        
        # board1 should be unchanged
        assert not np.array_equal(board1.piece_array, board2.piece_array)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
