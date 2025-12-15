"""
UCI (Universal Chess Interface) Protocol Implementation

Handles communication between the chess engine and UCI-compatible GUIs.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.board import Board
from engine.search import Search
from engine.moves import Moves


class UCIEngine:
    """UCI protocol handler for the chess engine."""
    
    def __init__(self):
        self.board = Board()
        self.search = Search(tt_size_mb=64, max_depth=64)
        self.debug = False
        self.running = True
        
    def send(self, message: str):
        """Send message to GUI."""
        print(message, flush=True)
        if self.debug:
            print(f"[DEBUG] Sent: {message}", file=sys.stderr, flush=True)
    
    def uci(self):
        """Respond to 'uci' command."""
        self.send("id name Chess-AI")
        self.send("id author DanielLFS")
        
        # Engine options
        self.send("option name Hash type spin default 64 min 1 max 1024")
        self.send("option name Threads type spin default 1 min 1 max 1")
        self.send("option name MultiPV type spin default 1 min 1 max 1")
        self.send("option name Debug type check default false")
        
        self.send("uciok")
    
    def isready(self):
        """Respond to 'isready' command."""
        self.send("readyok")
    
    def ucinewgame(self):
        """Start a new game."""
        self.board = Board()
        self.search.tt.clear()
        self.search.killer_moves = {}
        self.search.history_table.fill(0)
    
    def position(self, args: list):
        """
        Set up position.
        
        Format:
        - position startpos
        - position startpos moves e2e4 e7e5
        - position fen <fen> moves ...
        """
        if not args:
            return
        
        idx = 0
        
        # Parse position type
        if args[idx] == "startpos":
            self.board = Board()
            idx += 1
        elif args[idx] == "fen":
            # Collect FEN string (next 6 tokens)
            idx += 1
            fen_parts = []
            while idx < len(args) and args[idx] != "moves":
                fen_parts.append(args[idx])
                idx += 1
            fen = " ".join(fen_parts)
            self.board = Board(fen=fen)
        
        # Parse moves
        if idx < len(args) and args[idx] == "moves":
            idx += 1
            while idx < len(args):
                move_str = args[idx]
                self._make_move(move_str)
                idx += 1
    
    def _make_move(self, move_str: str):
        """
        Make a move in UCI format (e.g., 'e2e4', 'e7e8q').
        
        Args:
            move_str: Move in UCI format
        """
        if len(move_str) < 4:
            return
        
        from_sq = (ord(move_str[0]) - ord('a')) + (int(move_str[1]) - 1) * 8
        to_sq = (ord(move_str[2]) - ord('a')) + (int(move_str[3]) - 1) * 8
        
        # Get promotion piece if any
        promotion = 0
        if len(move_str) == 5:
            promo_char = move_str[4].lower()
            promo_map = {'q': 4, 'r': 3, 'b': 2, 'n': 1}
            promotion = promo_map.get(promo_char, 0)
        
        # Find matching legal move
        moves_gen = Moves(self.board)
        legal_moves = moves_gen.generate()
        
        for move in legal_moves:
            move_from = move & 0x3F
            move_to = (move >> 6) & 0x3F
            move_promo = (move >> 12) & 0xF
            
            # Check for promotion flag (8)
            is_promotion = (move_promo & 8) != 0
            
            if move_from == from_sq and move_to == to_sq:
                if is_promotion:
                    # Extract promotion piece type (bits 0-2)
                    promo_piece = move_promo & 0x7
                    if promo_piece == promotion:
                        self.board.make_move(move)
                        return
                else:
                    self.board.make_move(move)
                    return
    
    def go(self, args: list):
        """
        Start searching.
        
        Format:
        - go depth 6
        - go movetime 3000
        - go wtime 60000 btime 60000 winc 1000 binc 1000
        - go infinite
        """
        depth = 6  # Default depth
        movetime = None
        
        # Parse arguments
        i = 0
        while i < len(args):
            if args[i] == "depth":
                depth = int(args[i + 1])
                i += 2
            elif args[i] == "movetime":
                movetime = int(args[i + 1]) / 1000.0  # Convert ms to seconds
                i += 2
            elif args[i] == "infinite":
                depth = 64  # Max depth for infinite
                i += 1
            elif args[i] in ["wtime", "btime", "winc", "binc", "movestogo"]:
                # TODO: Implement time management
                i += 2
            else:
                i += 1
        
        # Search
        best_move, score = self.search.search(self.board, depth=depth, time_limit=movetime)
        
        # Format and send best move
        if best_move is not None:
            move_str = self._format_move(best_move)
            self.send(f"bestmove {move_str}")
        else:
            self.send("bestmove 0000")
    
    def _format_move(self, move: int) -> str:
        """
        Format move as UCI string.
        
        Args:
            move: Encoded move (uint16)
            
        Returns:
            UCI format string (e.g., 'e2e4', 'e7e8q')
        """
        from_sq = move & 0x3F
        to_sq = (move >> 6) & 0x3F
        flags = (move >> 12) & 0xF
        
        from_file = chr(ord('a') + (from_sq % 8))
        from_rank = str((from_sq // 8) + 1)
        to_file = chr(ord('a') + (to_sq % 8))
        to_rank = str((to_sq // 8) + 1)
        
        move_str = f"{from_file}{from_rank}{to_file}{to_rank}"
        
        # Check for promotion (bit 3 set)
        if flags & 8:
            promo_piece = flags & 0x7
            promo_chars = ['n', 'b', 'r', 'q']
            if promo_piece < 4:
                move_str += promo_chars[promo_piece]
        
        return move_str
    
    def setoption(self, args: list):
        """
        Set engine option.
        
        Format: setoption name <name> value <value>
        """
        if len(args) < 4 or args[0] != "name":
            return
        
        # Find 'value' keyword
        try:
            value_idx = args.index("value")
            name = " ".join(args[1:value_idx])
            value = " ".join(args[value_idx + 1:])
        except ValueError:
            return
        
        # Handle options
        if name.lower() == "hash":
            try:
                hash_size = int(value)
                self.search = Search(tt_size_mb=hash_size, max_depth=64)
            except ValueError:
                pass
        elif name.lower() == "debug":
            self.debug = value.lower() == "true"
    
    def stop(self):
        """Stop searching."""
        self.search.stop_search = True
    
    def quit(self):
        """Quit the engine."""
        self.running = False
    
    def debug_mode(self, on: bool):
        """Toggle debug mode."""
        self.debug = on
    
    def run(self):
        """Main UCI loop."""
        while self.running:
            try:
                line = input().strip()
                
                if not line:
                    continue
                
                if self.debug:
                    print(f"[DEBUG] Received: {line}", file=sys.stderr, flush=True)
                
                parts = line.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command == "uci":
                    self.uci()
                elif command == "isready":
                    self.isready()
                elif command == "ucinewgame":
                    self.ucinewgame()
                elif command == "position":
                    self.position(args)
                elif command == "go":
                    self.go(args)
                elif command == "stop":
                    self.stop()
                elif command == "quit":
                    self.quit()
                elif command == "setoption":
                    self.setoption(args)
                elif command == "debug":
                    self.debug_mode(args[0].lower() == "on")
                elif command == "d":
                    # Display board (for debugging)
                    print(self.board.to_fen(), file=sys.stderr, flush=True)
                
            except EOFError:
                break
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Error: {e}", file=sys.stderr, flush=True)


def main():
    """Entry point for UCI engine."""
    engine = UCIEngine()
    engine.run()


if __name__ == "__main__":
    main()
