import select
import sys
import termios
import tty
import os

# --- Module-level state (initialized on first call) ---
_fd = sys.stdin.fileno()
_old_settings = None
_initialized = False

# Escape sequence -> friendly name mapping
ESCAPE_MAP = {
    '\x1b[A': 'UP',
    '\x1b[B': 'DOWN',
    '\x1b[C': 'RIGHT',
    '\x1b[D': 'LEFT',
    '\x1bOA': 'UP',      # Some terminals send this variant
    '\x1bOB': 'DOWN',
    '\x1bOC': 'RIGHT',
    '\x1bOD': 'LEFT',
}

def _init():
    """Initialize terminal once (lazy)."""
    global _old_settings, _initialized
    if not _initialized:
        _old_settings = termios.tcgetattr(_fd)
        tty.setcbreak(_fd)
        _initialized = True

def _cleanup():
    """Restore terminal on exit."""
    global _initialized
    if _initialized:
        termios.tcsetattr(_fd, termios.TCSADRAIN, _old_settings)
        _initialized = False

# Register cleanup on normal exit
import atexit
atexit.register(_cleanup)


def getKey():
    """
    Returns:
      - 'UP', 'DOWN', 'LEFT', 'RIGHT' for arrows
      - Single character string for normal keys
      - '' (empty string) if no key pressed
    """
    _init()
    
    if select.select([_fd], [], [], 0)[0]:
        first = os.read(_fd, 1).decode('utf-8', errors='ignore')
        if first == '\x1b':
            seq = first
            while select.select([_fd], [], [], 0.01)[0]:
                seq += os.read(_fd, 1).decode('utf-8', errors='ignore')
            return ESCAPE_MAP.get(seq, seq)  # Return friendly name or raw seq
        return first
    return ''


# --- Example Usage ---
if __name__ == "__main__":
    print("Press keys (arrows work!), 'q' to quit...")
    try:
        while True:
            K = getKey()
            if K:
                print(K)
                if K == 'q':
                    break
    except (KeyboardInterrupt, termios.error):
        print("\nExiting...")