"""
Edge warning arrows for AETHER HARVEST.
Shows directional arrows on screen edges when enemies/boss are off-screen.
"""
import pygame
import math
from utils.constants import WIDTH, HEIGHT, C_DANGER, C_GRAY
from utils.math_utils import normalize


MARGIN  = 28    
MAX_ARR = 8    


def draw_warning_arrows(surf, player, enemies, boss_mgr, cam, font_xs):
    """Draw edge arrows pointing toward off-screen threats."""
    cx = WIDTH  // 2
    cy = HEIGHT // 2

    threats = []

    
    for e in enemies:
        if not e.alive:
            continue
        sx, sy = cam.world_to_screen(e.x, e.y)
        if 0 <= sx <= WIDTH and 0 <= sy <= HEIGHT:
            continue   
        threats.append((e.x, e.y, C_DANGER, e.size))

   
    if boss_mgr.boss and boss_mgr.boss.alive:
        b = boss_mgr.boss
        sx, sy = cam.world_to_screen(b.x, b.y)
        if not (0 <= sx <= WIDTH and 0 <= sy <= HEIGHT):
            threats.append((b.x, b.y, (255, 100, 255), b.size))

    if not threats:
        return

    
    threats.sort(key=lambda t: (t[0] - player.x)**2 + (t[1] - player.y)**2)
    threats = threats[:MAX_ARR]

    for (wx, wy, color, size) in threats:
       
        dx = wx - player.x
        dy = wy - player.y
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx, ny = dx / length, dy / length

        
       
        if nx != 0:
            t_x = ((WIDTH  - MARGIN) - cx) / nx if nx > 0 else (MARGIN - cx) / nx
        else:
            t_x = float('inf')
        if ny != 0:
            t_y = ((HEIGHT - MARGIN) - cy) / ny if ny > 0 else (MARGIN - cy) / ny
        else:
            t_y = float('inf')
        t   = min(abs(t_x), abs(t_y))
        ax  = int(cx + nx * t)
        ay  = int(cy + ny * t)
        ax  = max(MARGIN, min(WIDTH  - MARGIN, ax))
        ay  = max(MARGIN, min(HEIGHT - MARGIN, ay))

        
        dist_ratio = min(1.0, length / 600)
        alpha = int(200 * dist_ratio + 55)

        
        angle = math.atan2(ny, nx)
        _draw_arrow(surf, ax, ay, angle, color, alpha, size)

      
        dist_txt = font_xs.render(f"{int(length)}", True, (*color[:3],))
        surf.blit(dist_txt, (ax - dist_txt.get_width() // 2,
                              ay - dist_txt.get_height() // 2 - 16))


def _draw_arrow(surf, x, y, angle, color, alpha, enemy_size):
    """Draw a filled triangle arrow at (x,y) pointing in direction angle."""
    size  = 10 + min(8, enemy_size // 4)
    back  = size * 1.4

    tip_x  = x + math.cos(angle) * size
    tip_y  = y + math.sin(angle) * size
    left_x = x + math.cos(angle + 2.4) * back
    left_y = y + math.sin(angle + 2.4) * back
    right_x= x + math.cos(angle - 2.4) * back
    right_y= y + math.sin(angle - 2.4) * back

    pts = [(int(tip_x), int(tip_y)),
           (int(left_x), int(left_y)),
           (int(right_x), int(right_y))]

    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(s, (*color[:3], alpha), pts)
    pygame.draw.polygon(s, (255, 255, 255, alpha // 3), pts, 1)
    surf.blit(s, (0, 0))

