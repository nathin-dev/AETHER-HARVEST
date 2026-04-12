"""
Renderer for AETHER HARVEST - handles glow, vignette, scanlines
"""
import pygame
import math
from utils.constants import WIDTH, HEIGHT, C_BG, C_BG2


def draw_glow_circle(surf, color, center, radius, intensity=180, layers=4):
    """Draw a radial glow around a point."""
    for i in range(layers, 0, -1):
        r = radius * (1 + i * 0.6)
        a = intensity // (layers - i + 2)
        s = pygame.Surface((int(r * 2) + 4, int(r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (int(r) + 2, int(r) + 2), int(r))
        surf.blit(s, (center[0] - int(r) - 2, center[1] - int(r) - 2),
                  special_flags=pygame.BLEND_ADD)


def draw_glow_rect(surf, color, rect, radius=6, alpha=80):
    s = pygame.Surface((rect.width + radius * 4, rect.height + radius * 4), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (radius * 2, radius * 2,
                                           rect.width, rect.height), border_radius=8)
    surf.blit(s, (rect.x - radius * 2, rect.y - radius * 2),
              special_flags=pygame.BLEND_ADD)


def draw_panel(surf, rect, color=(18, 14, 42), border=(55, 40, 120),
               alpha=220, radius=10):
    """Draw a semi-transparent rounded panel."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha),   (0, 0, rect.width, rect.height), border_radius=radius)
    pygame.draw.rect(s, (*border, 180),    (0, 0, rect.width, rect.height), width=1, border_radius=radius)
    surf.blit(s, rect.topleft)


def draw_health_bar(surf, x, y, w, h, value, max_val,
                    fg_color=(80, 255, 140), bg_color=(30, 20, 50),
                    border_color=(55, 40, 120)):
    pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=4)
    fill_w = int(w * max(0, value / max_val))
    if fill_w > 0:
        pygame.draw.rect(surf, fg_color, (x, y, fill_w, h), border_radius=4)
    pygame.draw.rect(surf, border_color, (x, y, w, h), 1, border_radius=4)


_vignette_surf = None

def get_vignette(width, height):
    global _vignette_surf
    if _vignette_surf is None or _vignette_surf.get_size() != (width, height):
        _vignette_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        cx, cy = width // 2, height // 2
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                dist = math.hypot(x - cx, y - cy) / math.hypot(cx, cy)
                alpha = int(max(0, min(180, (dist - 0.45) * 400)))
                if alpha > 0:
                    _vignette_surf.set_at((x, y), (0, 0, 0, alpha))
                    if x + 1 < width:
                        _vignette_surf.set_at((x + 1, y), (0, 0, 0, alpha))
                    if y + 1 < height:
                        _vignette_surf.set_at((x, y + 1), (0, 0, 0, alpha))
                    if x + 1 < width and y + 1 < height:
                        _vignette_surf.set_at((x + 1, y + 1), (0, 0, 0, alpha))
    return _vignette_surf


def draw_star_field(surf, stars, cam_dx, cam_dy):
    """Draw parallax star field."""
    for (sx, sy, size, parallax, brightness) in stars:
        wx = int(sx - cam_dx * parallax) % WIDTH
        wy = int(sy - cam_dy * parallax) % HEIGHT
        c  = brightness
        if size <= 1:
            surf.set_at((wx, wy), (c, c, c + 30))
        else:
            pygame.draw.circle(surf, (c, c, c + 30), (wx, wy), size)

