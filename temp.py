
import os
import random
import sys
import time
import select
import termios
import tty


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




def clearConsole():
	#   os.system('cls' if os.name == 'nt' else 'clear')
	print('\033[2J\033[H', end='', flush=True)

def canMove(rowDelta, colDelta):
	global pieceLoc, gamefield, pieceLocations
	newLoc = []
	for row, col in pieceLoc:
		newRow = row + rowDelta
		newCol = col + colDelta
		if newCol < 0:
			return False
		if newRow >= 20:
			return False
		if newCol >= 10:
			return False
# 	for blockRow, blockCol in 
	return True
	
		

	


	  






clearConsole()
gamefield = [
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
	  [0,0,0,0,0,0,0,0,0,0],
]
current = random.randint(1,7)
current = 1
if current == 1:
	  pieceLoc = [[0,4],[0,5],[0,6],[1,5]]

for r, c in pieceLoc:
	  gamefield[r][c] = "■"
	  # gamefield[0][4] = "■"
	  # gamefield[0][5] = "■"
	  # gamefield[0][6] = "■"
	  # gamefield[1][5] = "■"



while True:
    # Clear
    for row, col in pieceLoc:
        gamefield[row][col] = 0

    # Input
    K = getKey()
    if K == "LEFT" and canMove(0, -1):
        pieceLoc = [[row, col - 1] for row, col in pieceLoc]
    if K == "RIGHT" and canMove(0, 1):
        pieceLoc = [[row, col + 1] for row, col in pieceLoc]
    if K == "UP":
        rotate()
    # Gravity
    if canMove(1, 0):
        pieceLoc = [[row + 1, col] for row, col in pieceLoc]

    # Draw
    for row, col in pieceLoc:
        gamefield[row][col] = "■"

    # Render
    clearConsole()
    for row in gamefield:
        print(*row)

    time.sleep(0.016)