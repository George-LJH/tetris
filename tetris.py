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
pieceLoc = []
def spawnNewPiece():
	global pieceLoc, gamefield, gameOver, pivotOffset, pivots, current, nextPiece
	
	pieces = {
		1: [[0,3],[0,4],[0,5],[0,6]],  # I
		2: [[0,4],[0,5],[1,4],[1,5]],  # O
		3: [[0,4],[0,5],[0,6],[1,5]],  # T
		4: [[0,5],[0,6],[1,4],[1,5]],  # S
		5: [[0,4],[0,5],[1,5],[1,6]],  # Z
		6: [[0,4],[1,4],[1,5],[1,6]],  # J
		7: [[0,6],[1,4],[1,5],[1,6]],  # L
	}
	current = nextPiece
	nextPiece = random.randint(1,7)
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
def getGhost():
	ghost = [list(p) for p in pieceLoc]  # copy
	while True:
		# check if ALL blocks can move down
		if not all(0 <= r+1 < 20 and gamefield[r+1][c] == blankStr for r, c in ghost):
			break
		ghost = [[r+1, c] for r, c in ghost]
	return ghost

def getRotated(clockwise=True):
    # pivot = first block (no offset)
    pivotRow, pivotCol = pieceLoc[0]
    
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
def gravity():
	global now, nextFallTime, pieceLoc, gamefield, cubeStr, rowsToClear, blankStr
	global linesCleared, score, level, fallInterval, softdropCells
	# remove ghost from globals
	
	if now >= nextFallTime:
		if canMove(1, 0):
			pieceLoc = [[row + 1, col] for row, col in pieceLoc]
			nextFallTime = now + fallInterval
def lockPiece():
	global pieceLoc, gamefield, cubeStr, blankStr
	global linesCleared, score, level, fallInterval, softdropCells
	global nextFallTime, current, nextPiece, pivotOffset, gameOver
	


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
pivots = {
	1: [0, 4],   # I - 2nd block (index 1)
	2: [0, 4],   # O - top-left (doesn't visually rotate)
	3: [0, 5],   # T - 2nd block (center of top row)
	4: [0, 5],   # S - 1st block (index 0)
	5: [0, 5],   # Z - 2nd block (index 1)
	6: [1, 5],   # J - 3rd block (center of bottom row)
	7: [1, 5],   # L - 3rd block (center of bottom row)
}
nextPiece = random.randint(1,7)
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

	if K == "UP" and current != 2:
		candidate = getRotated()
		for kick in [0, -1, 1, -2, 2]:
			kicked = [[r, c + kick] for r, c in candidate]
			if all(0 <= c < 10 and 0 <= r < 20 and gamefield[r][c] == blankStr for r, c in kicked):
				pieceLoc = kicked
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
	nextShapes = {
		1: [[0,1],[0,2],[0,3],[0,4]],
		2: [[0,1],[0,2],[1,1],[1,2]],
		3: [[0,1],[0,2],[0,3],[1,2]],
		4: [[0,2],[0,3],[1,1],[1,2]],
		5: [[0,1],[0,2],[1,2],[1,3]],
		6: [[0,1],[1,1],[1,2],[1,3]],
		7: [[0,3],[1,1],[1,2],[1,3]],
	}
	print("NEXT: ")
	for r in range(2):
		line = ""
		for c in range(6):
			line += cubeStr if [r,c] in nextShapes[nextPiece] else " "
		print(line)

	# time.sleep(0.016)
	time.sleep(.01)

# GAME OVER
clearConsole()
# time.sleep(0.5)
printCenterLargeReveal("GAME OVER", line_delay=0.09)