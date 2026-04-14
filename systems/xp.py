"""
XP and player level system for AETHER HARVEST.
"""
import math
from utils.math_utils import lerp
from utils.constants import C_ACCENT, C_SUCCESS, C_GRAY, WIDTH, HEIGHT


def xp_for_level(level):
    return int(80 * (level ** 1.5))


LEVEL_PERKS = {
    3:  ("⚡ Power Surge",    "Click power permanently +2"),
    5:  ("🛡 Iron Core",      "Max HP +25"),
    8:  ("🌀 Resonance",      "Collection radius +30px"),
    10: ("💥 Overcharge",     "Projectile damage +50%"),
    12: ("🔥 Chain Master",   "Chain chance +20%"),
    15: ("🌟 Void Walker",    "Dash cooldown -30%"),
    20: ("👑 Aether Lord",    "All income ×1.5"),
}


class XPSystem:
    def __init__(self):
        self.xp = 0
        self.level = 1
        self.xp_to_next = xp_for_level(2)
        self.display_xp = 0.0
        self.level_up_anim = 0.0
        self.pending_perks = []
        self.total_xp = 0
        self.kills = 0

        self.bonus_click = 0
        self.bonus_hp = 0
        self.bonus_range = 0
        self.bonus_dmg_pct = 0.0
        self.bonus_chain = 0.0
        self.bonus_dash_cd = 0.0
        self.income_mult = 1.0

    def add_xp(self, amount, from_boss=False):
        amount = max(0, int(amount))

        if from_boss:
            amount = int(amount * 3)

        self.xp += amount
        self.total_xp += amount

        levelled = False

        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = xp_for_level(self.level + 1)
            self.level_up_anim = 2.5
            levelled = True
            self._apply_perk(self.level)

        return levelled

    def register_kill(self, reward, is_boss=False):
        reward = max(0, int(reward))
        self.kills += 1

        xp = int(reward * (3 if is_boss else 1))
        self.add_xp(xp, from_boss=is_boss)

        return xp

    def _apply_perk(self, level):
        if level in LEVEL_PERKS:
            self.pending_perks.append(LEVEL_PERKS[level])

        if level % 2 == 0:
            self.bonus_click += 1

        if level % 5 == 0:
            self.bonus_hp += 25

        if level == 8:
            self.bonus_range += 30

        if level == 10:
            self.bonus_dmg_pct += 0.5

        if level == 12:
            self.bonus_chain += 0.20

        if level == 15:
            self.bonus_dash_cd += 0.30

        if level == 20:
            self.income_mult = 1.5

    def apply_to_player(self, player):
        if self.bonus_hp > 0:
            new_max = 100 + self.bonus_hp
            if player.max_hp != new_max:
                diff = new_max - player.max_hp
                player.max_hp = new_max
                player.hp = min(player.hp + diff, player.max_hp)

        if self.bonus_range > 0:
            player.collect_range_bonus = max(
                getattr(player, "collect_range_bonus", 0),
                self.bonus_range
            )

    @property
    def xp_ratio(self):
        return min(1.0, self.xp / max(1, self.xp_to_next))

    def update(self, dt):
        dt = max(0.0, min(dt, 0.05))
        self.display_xp = lerp(self.display_xp, self.xp_ratio, min(1.0, dt * 6))
        self.level_up_anim = max(0.0, self.level_up_anim - dt)

    def draw(self, surf, font_md, font_sm, font_xs):
        import pygame
        from utils.math_utils import smooth_step
        from ui.layout import XP_Y, LX, LW, RES_Y
        from engine.renderer import draw_panel

        bar_w = int(WIDTH * self.display_xp)

        pygame.draw.rect(surf, (20, 14, 40), (0, XP_Y, WIDTH, 5))
        if bar_w > 0:
            pygame.draw.rect(surf, C_ACCENT, (0, XP_Y, bar_w, 5))

        lv_txt = font_sm.render(f"Lv{self.level}", True, C_ACCENT)
        lv_x = LX + LW + 8

        lv_rect = pygame.Rect(lv_x, RES_Y + 8, lv_txt.get_width() + 16, 28)
        draw_panel(surf, lv_rect, color=(30, 20, 60), border=(180, 120, 50),
                   alpha=220, radius=6)

        surf.blit(lv_txt, (lv_rect.x + 8, lv_rect.y + 5))

        kill_txt = font_xs.render(f"☠ {self.kills}", True, C_GRAY)
        surf.blit(kill_txt, (lv_rect.right + 8, lv_rect.y + 8))

        if self.level_up_anim > 0:
            t = self.level_up_anim / 2.5
            alpha = int(220 * smooth_step(min(t * 4, 1.0)) * smooth_step(t))

            msg = font_md.render(f"✦  LEVEL {self.level}  ✦", True, C_ACCENT)
            msg.set_alpha(alpha)
            surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 100))

            if self.pending_perks:
                name, desc = self.pending_perks[0]

                p1 = font_sm.render(name, True, C_SUCCESS)
                p2 = font_xs.render(desc, True, C_GRAY)

                p1.set_alpha(alpha)
                p2.set_alpha(alpha)

                surf.blit(p1, (WIDTH // 2 - p1.get_width() // 2, HEIGHT // 2 - 72))
                surf.blit(p2, (WIDTH // 2 - p2.get_width() // 2, HEIGHT // 2 - 50))

                if self.level_up_anim < 0.1:
                    self.pending_perks.pop(0)