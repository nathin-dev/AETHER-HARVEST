"""
Combo system for AETHER HARVEST
Rewards rapid collection with escalating multipliers.
"""
import math
from utils.math_utils import lerp, smooth_step


COMBO_DECAY    = 2.5   
COMBO_STEPS    = [1, 2, 3, 5, 8, 13, 20]   
COMBO_MULTS    = [1, 1.25, 1.5, 2.0, 3.0, 5.0, 8.0]


class ComboSystem:
    def __init__(self):
        self.count        = 0
        self.timer        = 0.0       
        self.multiplier   = 1.0
        self.display_mult = 1.0       
        self.flash        = 0.0       
        self._prev_tier   = 0

    @property
    def tier(self):
        for i, step in reversed(list(enumerate(COMBO_STEPS))):
            if self.count >= step:
                return i
        return 0

    def register_collect(self):
        """Call whenever player collects an ore. Returns current multiplier."""
        self.count  += 1
        self.timer   = 0.0
        new_tier = self.tier
        if new_tier > self._prev_tier:
            self.flash      = 0.6
            self._prev_tier = new_tier
        self.multiplier = COMBO_MULTS[min(self.tier, len(COMBO_MULTS) - 1)]
        return self.multiplier

    def update(self, dt):
        self.timer        += dt
        self.flash         = max(0.0, self.flash - dt)
        if self.timer >= COMBO_DECAY:
            self.count      = 0
            self.multiplier = 1.0
            self._prev_tier = 0
        self.display_mult   = lerp(self.display_mult, self.multiplier, min(1.0, dt * 8))

    def draw(self, surf, font_md, font_xs):
        import pygame
        from utils.constants import C_ACCENT, C_DANGER, C_WHITE, C_GRAY, WIDTH
        from utils.math_utils import format_number

        if self.count < 2:
            return

        cx = WIDTH // 2

       
        pulse = 1.0 + math.sin(self.timer * 12) * 0.06 * (1 if self.flash > 0 else 0)
        txt   = f"× {self.count}  COMBO"
        col   = C_DANGER if self.tier >= 4 else (C_ACCENT if self.tier >= 2 else C_WHITE)
        surf_t = font_md.render(txt, True, col)

        
        if pulse != 1.0:
            w = int(surf_t.get_width() * pulse)
            h = int(surf_t.get_height() * pulse)
            surf_t = pygame.transform.scale(surf_t, (max(1, w), max(1, h)))

        surf.blit(surf_t, (cx - surf_t.get_width() // 2, 54))

       
        mult_txt = f"✦ {self.display_mult:.2f}×"
        m_surf   = font_xs.render(mult_txt, True, col)
        surf.blit(m_surf, (cx - m_surf.get_width() // 2, 82))

      
        bar_w   = 160
        ratio   = max(0, 1.0 - self.timer / COMBO_DECAY)
        bar_x   = cx - bar_w // 2
        bar_y   = 98
        pygame.draw.rect(surf, (30, 20, 50), (bar_x, bar_y, bar_w, 4), border_radius=2)
        if ratio > 0:
            pygame.draw.rect(surf, col, (bar_x, bar_y, int(bar_w * ratio), 4), border_radius=2)

