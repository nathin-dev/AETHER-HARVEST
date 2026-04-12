"""
World / background for AETHER HARVEST
"""
import pygame
import math
import random
from utils.constants import WIDTH, HEIGHT, C_BG, C_BG2, C_PANEL_BORDER


WORLD_W = WIDTH  * 2
WORLD_H = HEIGHT * 2
GRID    = 96


def _make_star_field(n=300):
    stars = []
    for _ in range(n):
        x          = random.uniform(0, WORLD_W)
        y          = random.uniform(0, WORLD_H)
        size       = random.choices([0, 0, 1, 2], weights=[50, 30, 15, 5])[0]
        parallax   = random.uniform(0.05, 0.25)
        brightness = random.randint(60, 200)
        stars.append((x, y, size, parallax, brightness))
    return stars


def _make_nebula_patches(n=8):
    """Return list of (x, y, radius, color) for soft nebula blobs."""
    patches = []
    colors  = [
        (80, 30, 140, 12),
        (30, 80, 140, 10),
        (30, 140, 100, 8),
        (140, 60, 30, 8),
    ]
    for _ in range(n):
        x = random.randint(0, WORLD_W)
        y = random.randint(0, WORLD_H)
        r = random.randint(120, 300)
        c = random.choice(colors)
        patches.append((x, y, r, c))
    return patches


class World:
    def __init__(self):
        self.width  = WORLD_W
        self.height = WORLD_H

        self.stars   = _make_star_field(350)
        self.nebulae = _make_nebula_patches(12)

        
        self._bg_tile  = self._build_bg_tile()
        self._nebula_s = self._build_nebula_surface()

    def _build_bg_tile(self):
        tile = pygame.Surface((GRID, GRID))
        tile.fill(C_BG)
        
        pygame.draw.line(tile, (20, 16, 45), (0, 0), (GRID, 0), 1)
        pygame.draw.line(tile, (20, 16, 45), (0, 0), (0, GRID), 1)
        return tile

    def _build_nebula_surface(self):
        s = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        for (x, y, r, c) in self.nebulae:
            
            for layer in range(4, 0, -1):
                lr = r * layer // 4
                la = c[3] * (5 - layer) // 4
                pygame.draw.circle(s, (*c[:3], la), (x, y), lr)
        return s

    def draw(self, surf, cam):
        
        cam_x = int(cam.x)
        cam_y = int(cam.y)
        start_x = -(cam_x % GRID)
        start_y = -(cam_y % GRID)
        for ty in range(start_y, HEIGHT + GRID, GRID):
            for tx in range(start_x, WIDTH + GRID, GRID):
                surf.blit(self._bg_tile, (tx, ty))

        
        nbx = -int(cam_x * 0.6) % WORLD_W
        nby = -int(cam_y * 0.6) % WORLD_H
        surf.blit(self._nebula_s, (nbx - WORLD_W, nby - WORLD_H),
                  special_flags=pygame.BLEND_ADD)
        surf.blit(self._nebula_s, (nbx, nby - WORLD_H),
                  special_flags=pygame.BLEND_ADD)
        surf.blit(self._nebula_s, (nbx - WORLD_W, nby),
                  special_flags=pygame.BLEND_ADD)
        surf.blit(self._nebula_s, (nbx, nby),
                  special_flags=pygame.BLEND_ADD)

      
        for (sx, sy, size, parallax, brightness) in self.stars:
            wx = int(sx - cam_x * parallax) % WIDTH
            wy = int(sy - cam_y * parallax) % HEIGHT
            c  = brightness
            if size == 0:
                surf.set_at((wx, wy), (c, c, min(255, c + 40)))
            elif size == 1:
                pygame.draw.circle(surf, (c, c, min(255, c + 40)), (wx, wy), 1)
            else:
                pygame.draw.circle(surf, (c, c, min(255, c + 40)), (wx, wy), size)

        
        bx1, by1 = cam.world_to_screen(0,       0)
        bx2, by2 = cam.world_to_screen(WORLD_W, WORLD_H)
        pygame.draw.rect(surf, C_PANEL_BORDER,
                         (bx1, by1, bx2 - bx1, by2 - by1), 2)
