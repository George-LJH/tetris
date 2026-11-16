import pygame
import sys
import json
import js
import asyncio
import random
import time

def save(key, value):
    js.localStorage.setItem(str(key), str(value))

def load(key):
    val = js.localStorage.getItem(str(key))
    if val is None: 
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0

def font(size):
    return pygame.font.Font("spaceInvadersFont.ttf", size)


def renderSplitText(text, font, top_color, bottom_color):
    """
    Renders a text surface split horizontally into two colors.
    """
    # 1. Render both versions of the text fully
    top_surf = font.render(text, True, top_color)
    bottom_surf = font.render(text, True, bottom_color)
    
    # 2. Get the dimensions of the text
    width, height = top_surf.get_size()
    half_height = height // 2
    
    # 3. Create a clean transparent destination surface
    final_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # 4. Slice and paste the halves together
    # Top half: Draw from (0,0) to (width, half_height)
    final_surf.blit(top_surf, (0, 0), (0, 0, width, half_height))
    
    # Bottom half: Draw from (0, half_height) to the end
    final_surf.blit(bottom_surf, (0, half_height), (0, half_height, width, height - half_height))
    
    return final_surf
# Initialize Pygame
pygame.init()


# Game Constants
screenWidth = 1280
screenHeight = 720

# Setup window
window = pygame.Window(size=(screenWidth, screenHeight))
window.title = "Tetris - Game"
screen = window.get_surface()
fps = 60

running = True
playerX = screenWidth/2
playerY = screenHeight/2
player = pygame.Rect(playerX, playerY, 100, 100)
player.centerx = playerX

player.centery = playerY
while running:
    keys = pygame.key.get_pressed()

    pygame.draw.rect(screen, (255, 255, 255), player)
    
    playerX += (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
    await asyncio.sleep(1 / fps)

# Clean Up & Exit
pygame.quit()
sys.exit()