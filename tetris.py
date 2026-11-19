import os
import random
import sys
import time
import select
import termios
import tty
import pyfiglet
import shutil


fallInterval = 0.5
nextFallTime = time.time() + fallInterval
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
	global pieceLoc, gamefield, pieceLocations, blankStr
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
		if (gamefield[newRow][newCol] != blankStr):
			return False
	return True


cubeStr = "⯀"
clearConsole()

blankStr = "□"
gamefield = [
	[blankStr for _ in range(10)]
	for _ in range(20)
]
pieceLoc = []
def spawnNewPiece():
	global pieceLoc, gamefield, gameOver, pivotOffset, pivots, current
	pieces = {
		1: [[0,3],[0,4],[0,5],[0,6]],  # I
		2: [[0,4],[0,5],[1,4],[1,5]],  # O
		3: [[0,4],[0,5],[0,6],[1,5]],  # T
		4: [[0,5],[0,6],[1,4],[1,5]],  # S
		5: [[0,4],[0,5],[1,5],[1,6]],  # Z
		6: [[0,4],[1,4],[1,5],[1,6]],  # J
		7: [[0,6],[1,4],[1,5],[1,6]],  # L
	}
	current = random.randint(1,7)
	pieceLoc = pieces[current]
		# pieceLoc = [[0,4], [0,5]]


	pivotLocal = pivots[current]
	pivotOffset = [
		pivotLocal[0] - pieceLoc[0][0],
		pivotLocal[1] - pieceLoc[0][1]
	]

	for row, col in pieceLoc:
		if gamefield[row][col] != blankStr:
			gameOver = True
			return

		
	for r, c in pieceLoc:
		gamefield[r][c] = cubeStr

def type(text, delay=0.05):
	for char in text:
		print(char, end='', flush=True)
		time.sleep(delay)
	print()


def printCenterLargeReveal(text, font="standard", line_delay=0.05, **kwargs):
	import shutil, pyfiglet
	terminal_size = shutil.get_terminal_size()
	width = terminal_size.columns
	height = terminal_size.lines

	ascii_art = pyfiglet.figlet_format(text, font=font)
	lines = ascii_art.splitlines()

	top_padding = max(0, (height - len(lines)) // 2)
	print("\n" * top_padding, end="", **kwargs)

	for line in lines:
		print(line.center(width), **kwargs)
		time.sleep(line_delay)

# def rotatePiece(clockwise=False):
# 	global pieceLoc, gamefield, blankStr, pivotOffset
	
# 	pivotRow = pieceLoc[0][0] + pivotOffset[0]
# 	pivotCol = pieceLoc[0][1] + pivotOffset[1]
	
# 	candidate = []
# 	for row, col in pieceLoc:
# 		if clockwise:
# 			nr = pivotRow - (col - pivotCol)
# 			nc = pivotCol + (row - pivotRow)
# 		else:  # counter-clockwise
# 			nr = pivotRow + (col - pivotCol)
# 			nc = pivotCol - (row - pivotRow)
# 		candidate.append([nr, nc])
	
# 	# validation + commit same as before...
# 	for row, col in candidate:
# 		if row < 0 or row >= 20 or col < 0 or col >= 10:
# 			return
# 		if gamefield[row][col] != blankStr:
# 			return
# 	pieceLoc = candidate
def getRotated(clockwise=True):
    pivotRow = pieceLoc[0][0] + pivotOffset[0]
    pivotCol = pieceLoc[0][1] + pivotOffset[1]
    
    if clockwise:
        return [
            [pivotRow + (col - pivotCol), pivotCol - (row - pivotRow)]
            for row, col in pieceLoc
        ]
    else:
        return [
            [pivotRow - (col - pivotCol), pivotCol + (row - pivotRow)]
            for row, col in pieceLoc
        ]


pivots = {
    1: [0, 4],   # I - 2nd block (index 1)
    2: [0, 4],   # O - top-left (doesn't visually rotate)
    3: [0, 5],   # T - 2nd block (center of top row)
    4: [0, 5],   # S - 1st block (index 0)
    5: [0, 5],   # Z - 2nd block (index 1)
    6: [1, 5],   # J - 3rd block (center of bottom row)
    7: [1, 5],   # L - 3rd block (center of bottom row)
}
spawnNewPiece()
gameOver = False
while not gameOver:
	now = time.time()
	# Clear
	for row, col in pieceLoc:
		gamefield[row][col] = blankStr

	# Input
	K = getKey()
	if K == "LEFT" and canMove(0, -1):
		pieceLoc = [[row, col - 1] for row, col in pieceLoc]
	if K == "RIGHT" and canMove(0, 1):
		pieceLoc = [[row, col + 1] for row, col in pieceLoc]


	# if K == "UP":
		# rotatePiece()
		# pieceLoc = [list(row) for row in zip(*pieceLoc[::-1])]
		# candidate = getRotated()
		# while candidate[0][1]  > 10 or candidate[1][1] > 10 or candidate[2][1] > 10 or candidate[3][1] > 10:
		# 	for item in candidate:
		# 		item[1] += 1
		# pieceLoc = candidate

	if K == "UP" and current != 2:
		candidate = getRotated()
		for kick in [0, -1, 1, -2, 2]:      # tries: none, left, right, left2, right2
			kicked = [[r, c + kick] for r, c in candidate]
			if all(0 <= c < 10 and 0 <= r < 20 and gamefield[r][c] == blankStr for r, c in kicked):
				pieceLoc = kicked
				break
	if K == "DOWN":
		if canMove(1, 0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
	if K == " ":
		while canMove(1,0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
		for row, col in pieceLoc:
			gamefield[row][col] = cubeStr
			nextFallTime = now + fallInterval
	# Gravity
	if now >= nextFallTime:
		if canMove(1, 0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
		else:
			for row, col in pieceLoc:
				gamefield[row][col] = cubeStr
			for rowIndex in range(19, -1, -1):
				if all(cell != blankStr for cell in gamefield[rowIndex]):
					del gamefield[rowIndex]
					gamefield.insert(0, [blankStr]*10)	
			spawnNewPiece()
		nextFallTime = now + fallInterval

	# Draw
	for row, col in pieceLoc:
		gamefield[row][col] = cubeStr

	# Render
	clearConsole()
	for row in gamefield:
		print(*row)


	# time.sleep(0.016)
	time.sleep(.01)

# GAME OVER
clearConsole()
# time.sleep(0.5)
printCenterLargeReveal("GAME OVER", line_delay=0.09)