import atexit
import os
import random
import select
import shutil
import sys
import termios
import time
import tty
from typing import Any

import pyfiglet

bag = []
def getPiece():
    global bag
    if not bag:
        bag = list(range(1,8))
        random.shuffle(bag)
    return bag.pop()
paused = False
def hideCursor():
	sys.stdout.write("\033[?25l")
	sys.stdout.flush()
def showCursor():
	clearConsole()
	sys.stdout.write("\033[?25h")
	sys.stdout.flush()
atexit.register(showCursor)
hideCursor()
print('\033[2J\033[H', end='', flush=True)
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
	# print('\033[2J\033[H', end='', flush=True)
	print('\033[H', end='', flush=True)

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
cubeStr = "██"
clearConsole()

blankStr = "□"
blankStr = "  "
        #  ""
ghostPiece = "░░"
#            "🟪"
gamefield = [
	[blankStr for _ in range(10)]
	for _ in range(20)
]
pieceLoc: list[Any] = []
pieces: dict[int, list[list[int]]] = {
    1: [[0,3],[0,4],[0,5],[0,6]],  # I
    2: [[0,4],[0,5],[1,4],[1,5]],  # O
    3: [[0,4],[0,5],[0,6],[1,5]],  # T
    4: [[0,4],[0,5],[1,5],[1,6]],  # S
    5: [[0,5],[0,6],[1,4],[1,5]],  # Z
    6: [[0,4],[1,4],[1,5],[1,6]],  # J
    7: [[0,6],[1,4],[1,5],[1,6]],  # L
}
def spawnNewPiece():
	global pieceLoc, gamefield, gameOver, pivotOffset, pivots, current, nextPiece, pieces

	current = nextPiece
	nextPiece = getPiece()
	pieceLoc = pieces[current]
		# pieceLoc = [[0,4], [0,5]]


	pivotLocal: list[int] = pivots[current]
	pivotOffset = [
		pivotLocal[0] - pieceLoc[0][0],
		pivotLocal[1] - pieceLoc[0][1]
	]

	for row, col in pieceLoc:
		if gamefield[row][col] != blankStr:
			gameOver = True
			return

		
	# for r, c in pieceLoc:
	# 	gamefield[r][c] = cubeStr
	rotationState = 0
def type(text, delay=0.05):
	for char in text:
		print(char, end='', flush=True)
		time.sleep(delay)
	print()


def printCenterLargeReveal(text, font="standard", line_delay=0.05, **kwargs):
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
def getGhost():
	ghost = [list(p) for p in pieceLoc]  # copy
	while True:
		# check if ALL blocks can move down
		if not all(0 <= r+1 < 20 and gamefield[r+1][c] == blankStr for r, c in ghost):
			break
		ghost = [[r+1, c] for r, c in ghost]
	return ghost

# def getRotated(clockwise=True):
#     # pivot = first block (no offset)
#     pivotRow, pivotCol = pieceLoc[0]
    
#     if clockwise:
#         return [
#             [pivotRow + (col - pivotCol), pivotCol - (row - pivotRow)]
#             for row, col in pieceLoc
#         ]
#     else:
#         return [
#             [pivotRow - (col - pivotCol), pivotCol + (row - pivotRow)]
#             for row, col in pieceLoc
#         ]
def getRotated(clockwise=True):
    pivotRow, pivotCol = pieceLoc[0]
    if clockwise:
        return [[pivotRow + (c - pivotCol), pivotCol - (r - pivotRow)] for r, c in pieceLoc]
    else:
        return [[pivotRow - (c - pivotCol), pivotCol + (r - pivotRow)] for r, c in pieceLoc]


def gravity():
	global now, nextFallTime, pieceLoc, gamefield, cubeStr, rowsToClear, blankStr  # noqa: PLW0602
	global linesCleared, score, level, fallInterval, softdropCells  # noqa: PLW0602
	# remove ghost from globals
	
	if now >= nextFallTime and canMove(1, 0):
		pieceLoc = [[row + 1, col] for row, col in pieceLoc]
		nextFallTime = now + fallInterval
def lockPiece():
	global pieceLoc, gamefield, cubeStr, blankStr, canHold  # noqa: PLW0602
	global linesCleared, score, level, fallInterval, softdropCells
	global nextFallTime, current, nextPiece, pivotOffset, gameOver  # noqa: PLW0602
	


	for row, col in pieceLoc:
			gamefield[row][col] = cubeStr
		
	rowsToClear = []
	for rowIndex in range(19, -1, -1):
		if all(cell != blankStr for cell in gamefield[rowIndex]):
			rowsToClear.append(rowIndex)
	
	if rowsToClear:
		cleared = len(rowsToClear)
		linesCleared += cleared
		points = [0, 100, 300, 500, 800]
		score += points[cleared] * level
		score += softdropCells
		softdropCells = 0
		newLevel = linesCleared // 10 + 1
		if newLevel > level:
			level = newLevel
			fallInterval = max(0.05, 0.5 - (level - 1) * 0.05)
		gamefield = [row for i, row in enumerate(gamefield) if i not in rowsToClear]
		for _ in range(cleared):
			gamefield.insert(0, [blankStr] * 10)
	
	spawnNewPiece()
	nextFallTime = time.time() + fallInterval
	softdropCells = 0
	canHold = True
pivots = {
	1: [0, 4],   # I - 2nd block (index 1)
	2: [0, 4],   # O - top-left (doesn't visually rotate)
	3: [0, 5],   # T - 2nd block (center of top row)
	4: [0, 5],   # S - 1st block (index 0)
	5: [0, 5],   # Z - 2nd block (index 1)
	6: [1, 5],   # J - 3rd block (center of bottom row)
	7: [1, 5],   # L - 3rd block (center of bottom row)
}
nextPiece = getPiece()
spawnNewPiece()
gameOver = False
level = 1
score = 0
linesCleared = 0
softdropCells = 0
lockDelay = 0.5
maxMove = 15
floorTime = 0
floorMove = 0
onFloor = False
holdPiece = None
canHold = True
rotationState = 0

# SRS Wall Kick Data: piece -> (from_state, to_state) -> [(dr, dc), ...]
SRS_KICKS: dict[int | str, dict[tuple[int, int], list[tuple[int, int]]]] = {
    1: {  # I-piece
        (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    },
    # J, L, T, S, Z all share this table (pieces 2-7)
    'JLTSZ': {
        (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        (2, 3): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        (3, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        (3, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        (0, 3): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    }
}
while not gameOver:
	now = time.time()
	# Clear
	for row, col in pieceLoc:
		gamefield[row][col] = blankStr



	

	# Input
	K = getKey()
	if K == "LEFT" and canMove(0, -1):
		pieceLoc = [[row, col - 1] for row, col in pieceLoc]
		if onFloor:
			floorTime = time.time()  # reset delay
			floorMove += 1

	if K == "RIGHT" and canMove(0, 1):
		pieceLoc = [[row, col + 1] for row, col in pieceLoc]
		if onFloor:
			floorTime = time.time()
			floorMove += 1

	if K == "UP":
		candidate = getRotated()
		nextState = (rotationState + 1) % 4
		key = (rotationState, nextState)
		table = SRS_KICKS[1] if current == 1 else SRS_KICKS['JLTSZ']
		kicks = table[key]
		
		for dr, dc in kicks:
			kicked = [[r + dr, c + dc] for r, c in candidate]
			if all(0 <= c < 10 and 0 <= r < 20 and gamefield[r][c] == blankStr for r, c in kicked):
				pieceLoc = kicked
				rotationState = nextState
				if onFloor:
					floorTime = time.time()
					floorMove += 1
				break
	if K == "DOWN":
		if canMove(1, 0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
			softdropCells += 1
		else:
			# Don't lock instantly - let delay handle it
			pass

	if K == " ":
		harddropDist = 0
		while canMove(1, 0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
			harddropDist += 1
		score += harddropDist * 2
		lockPiece()


	if K == "s":
		linesCleared = int(input())
	if K in ("c", "z") and canHold:
		for row, col in pieceLoc:
			if gamefield[row][col] == cubeStr:
				gamefield[row][col] = blankStr
		if holdPiece is None:
			holdPiece = current
			spawnNewPiece()
		else:
			holdPiece, current = current, holdPiece
			pieceLoc = pieces[current]

		canHold = False
		floorTime: float = time.time()
		floorMove = 0
	if K == '\x1b':
		paused: bool = not paused
		continue
	if paused:
		time.sleep(0.1)
		continue
	# Gravity
	gravity()
	# Piece Lock
	touchingFloor = not canMove(1, 0)
	if touchingFloor:
		if not onFloor:
			onFloor = True
			floorTime = time.time()
			floorMove = 0
		elif time.time() - floorTime >= lockDelay:
			lockPiece()
			onFloor = False
	else:
		onFloor = False

	ghost = getGhost()
	for row, col in ghost:
		if gamefield[row][col] == blankStr:
			gamefield[row][col] = ghostPiece
	# Draw
	for row, col in pieceLoc:
		gamefield[row][col] = cubeStr

	# Render
	clearConsole()
	print("----------------------")
	for row in gamefield:
		# print(f"|{*row}|")
		print(f"|{''.join(map(str, row))}|")
	print("----------------------")
	for row, col in ghost:
		if gamefield[row][col] == ghostPiece: 
			gamefield[row][col] = blankStr
	print(f"Score: {score}  Lines: {linesCleared}  Level: {level}")	
	nextShapes: dict[int, list[list[int]]] = {
		1: [[0,1],[0,2],[0,3],[0,4]],      # I  (cols 1-4)
		2: [[0,2],[0,3],[1,2],[1,3]],      # O  (centered)
		3: [[0,1],[0,2],[0,3],[1,2]],      # T
		5: [[0,2],[0,3],[1,1],[1,2]],      # S
		4: [[0,1],[0,2],[1,2],[1,3]],      # Z
		6: [[0,1],[1,1],[1,2],[1,3]],      # J
		7: [[0,3],[1,1],[1,2],[1,3]],      # L
	}
	print("NEXT: ")
	for r in range(2):
		line = ""
		for c in range(6):
			line += cubeStr if [r,c] in nextShapes[nextPiece] else "  "
		print(line)
	print("HOLD: ")
	if holdPiece:
		for r in range(2):
			line = ""
			for c in range(6):
				line += cubeStr if [r,c] in nextShapes[holdPiece] else "  "
			print(line)
	else:
		print("      ")
		print("      ")
	# time.sleep(0.016)
	time.sleep(.01)

# GAME OVER
clearConsole()
# time.sleep(0.5)
printCenterLargeReveal("GAME OVER", line_delay=0.09)