"""
Test UCI protocol implementation.
"""

import sys
import subprocess
import time

def send_command(process, command):
    """Send command to UCI engine."""
    print(f"> {command}")
    process.stdin.write(f"{command}\n")
    process.stdin.flush()
    time.sleep(0.1)

def read_output(process, timeout=5.0, wait_for=None):
    """Read output from UCI engine."""
    output = []
    start = time.time()
    while time.time() - start < timeout:
        line = process.stdout.readline()
        if line:
            line = line.strip()
            if line:  # Only print non-empty lines
                print(f"< {line}")
                output.append(line)
                if wait_for and wait_for in line:
                    break
                if line in ["uciok", "readyok"] or line.startswith("bestmove"):
                    break
        time.sleep(0.01)  # Small delay to prevent busy waiting
    return output

def test_uci():
    """Test basic UCI commands."""
    print("="*70)
    print("UCI PROTOCOL TEST")
    print("="*70)
    
    # Start engine
    process = subprocess.Popen(
        [sys.executable, "uci/uci.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        print("\n[TEST 1: UCI initialization]")
        send_command(process, "uci")
        output = read_output(process)
        assert "uciok" in output, "Engine didn't respond with uciok"
        print("✓ UCI initialization successful\n")
        
        print("[TEST 2: Is ready]")
        send_command(process, "isready")
        output = read_output(process)
        assert "readyok" in output, "Engine didn't respond with readyok"
        print("✓ Engine is ready\n")
        
        print("[TEST 3: New game]")
        send_command(process, "ucinewgame")
        send_command(process, "isready")
        output = read_output(process)
        print("✓ New game initialized\n")
        
        print("[TEST 4: Set starting position]")
        send_command(process, "position startpos")
        send_command(process, "isready")
        output = read_output(process)
        print("✓ Position set\n")
        
        print("[TEST 5: Search at depth 5]")
        send_command(process, "go depth 5")
        output = read_output(process, timeout=10.0)
        bestmove_line = [line for line in output if line.startswith("bestmove")]
        assert bestmove_line, "Engine didn't return bestmove"
        print(f"✓ Search completed: {bestmove_line[0]}\n")
        
        print("[TEST 6: Position with moves]")
        send_command(process, "position startpos moves e2e4 e7e5")
        send_command(process, "go depth 4")
        output = read_output(process, timeout=10.0)
        bestmove_line = [line for line in output if line.startswith("bestmove")]
        assert bestmove_line, "Engine didn't return bestmove"
        print(f"✓ Position with moves: {bestmove_line[0]}\n")
        
        print("[TEST 7: Set option]")
        send_command(process, "setoption name Hash value 128")
        send_command(process, "isready")
        output = read_output(process)
        print("✓ Options set\n")
        
        print("[TEST 8: Quit]")
        send_command(process, "quit")
        process.wait(timeout=2)
        print("✓ Engine quit successfully\n")
        
        print("="*70)
        print("✓ ALL UCI TESTS PASSED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        process.kill()
        raise
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()

if __name__ == "__main__":
    test_uci()
