"""
Wave timer — shows countdown to next enemy wave and wave number.
"""
import pygame
import math
from utils.constants import C_DANGER, C_ACCENT, C_WHITE, C_GRAY, C_SUCCESS, WIDTH
from utils.math_utils import smooth_step
from engine.renderer import draw_panel


class WaveTimer:
    def __init__(self, font_md, font_sm, font_xs):
        self.font_md  = font_md
        self.font_sm  = font_sm
        self.font_xs  = font_xs
        self.pulse    = 0.0

    def draw(self, surf, enemies, boss_mgr):
        self.pulse += 0.05

        wave    = enemies.wave
        t_left  = enemies.spawn_timer
        t_total = enemies.spawn_interval
        ratio   = max(0.0, t_left / max(1, t_total))

        # Position: top-center, just below combo display
        from ui.layout import CX, WAVETIMER_Y
        bar_w  = 200
        bar_x  = CX - bar_w // 2
        bar_y  = WAVETIMER_Y

        panel = pygame.Rect(bar_x - 10, bar_y - 6, bar_w + 20, 36)
        draw_panel(surf, panel, alpha=190, radius=8)

        # Wave label
        wave_lbl = self.font_xs.render(f"WAVE  {wave}", True, C_GRAY)
        surf.blit(wave_lbl, (bar_x, bar_y - 2))

        # Next wave countdown
        if boss_mgr.intro_timer > 0:
            col  = (255, 100, 255)
            txt  = "BOSS"
        elif ratio < 0.2:
            col  = C_DANGER
            txt  = f"{t_left:.1f}s"
            # Urgent pulse
            a = int(abs(math.sin(self.pulse * 6)) * 60)
            urg = pygame.Surface((bar_w + 20, 36), pygame.SRCALPHA)
            pygame.draw.rect(urg, (*C_DANGER, a), (0, 0, bar_w + 20, 36),
                             border_radius=8)
            surf.blit(urg, panel.topleft)
        elif ratio < 0.5:
            col  = C_ACCENT
            txt  = f"{t_left:.1f}s"
        else:
            col  = C_SUCCESS
            txt  = f"{t_left:.0f}s"

        time_surf = self.font_xs.render(txt, True, col)
        surf.blit(time_surf, (bar_x + bar_w - time_surf.get_width(), bar_y - 2))

        # Progress bar
        pygame.draw.rect(surf, (30, 20, 50),
                         (bar_x, bar_y + 18, bar_w, 5), border_radius=2)
        fill_w = int(bar_w * (1.0 - ratio))   # fills as wave approaches
        if fill_w > 0:
            pygame.draw.rect(surf, col,
                             (bar_x, bar_y + 18, fill_w, 5), border_radius=2)

        # Enemy count on screen
        alive_count = sum(1 for e in enemies.enemies if e.alive)
        if alive_count > 0:
            ec = self.font_xs.render(f"☠ {alive_count} enemies", True, C_DANGER)
            surf.blit(ec, (WIDTH // 2 - ec.get_width() // 2, bar_y + 26))
