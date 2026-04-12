"""
HUD for AETHER HARVEST — rebuilt with master layout, zero overlaps.
"""
import pygame, math
from utils.constants import (WIDTH, HEIGHT, UPGRADES, C_PRIMARY, C_SECONDARY,
                              C_ACCENT, C_DANGER, C_WHITE, C_GRAY, C_SUCCESS,
                              C_PANEL_BORDER)
from utils.math_utils import lerp, format_number, smooth_step
from engine.renderer import draw_panel, draw_glow_rect, draw_health_bar
from ui.layout import (LX, LW, RES_Y, HP_Y, BADGE_Y, MODE_Y, WEAPON_Y,
                       STATS_Y, FPS_Y, XP_Y, CX, COMBO_Y, WAVETIMER_Y,
                       PANEL_X, PANEL_Y, PANEL_W, PANEL_H,
                       PANEL_BTN_H, PANEL_BTN_GAP, PANEL_BTN_X, PANEL_BTN_W,
                       PANEL_SCROLL_TOP, PANEL_SCROLL_BOT,
                       MM_X, MM_Y, MM_W, MM_H)
from world.world import WORLD_W, WORLD_H


class UpgradePanel:
    """Right-side upgrade shop with scrolling and embedded minimap."""

    def __init__(self, font_md, font_sm, font_xs):
        self.font_md  = font_md
        self.font_sm  = font_sm
        self.font_xs  = font_xs
        self.hover_idx= -1
        self.scales   = [1.0] * len(UPGRADES)
        self.pulses   = [0.0] * len(UPGRADES)
        self.flash    = {}
        self.scroll_y = 0
        self.scroll_speed = 0

        self.panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
        n = len(UPGRADES)
        self.content_h = n * (PANEL_BTN_H + PANEL_BTN_GAP) - PANEL_BTN_GAP
        self.visible_h = PANEL_SCROLL_BOT - PANEL_SCROLL_TOP

    def _btn_rect(self, i):
        y = PANEL_SCROLL_TOP + i * (PANEL_BTN_H + PANEL_BTN_GAP) - int(self.scroll_y)
        return pygame.Rect(PANEL_BTN_X, y, PANEL_BTN_W, PANEL_BTN_H)

    def _max_scroll(self):
        return max(0, self.content_h - self.visible_h)

    def handle_scroll(self, delta):
        self.scroll_y = max(0, min(self._max_scroll(), self.scroll_y - delta * 25))

    def update(self, dt, mouse_pos, upgrades):
        mx, my = mouse_pos
        self.hover_idx = -1
        for i, u in enumerate(UPGRADES):
            rect = self._btn_rect(i)
            in_clip = PANEL_SCROLL_TOP <= my <= PANEL_SCROLL_BOT
            if rect.collidepoint(mx, my) and in_clip:
                self.hover_idx = i
                self.scales[i] = lerp(self.scales[i], 1.03, 0.2)
            else:
                self.scales[i] = lerp(self.scales[i], 1.0, 0.15)
            if upgrades.can_afford(u["id"], 999_999_999):
                self.pulses[i] += dt * 3
            else:
                self.pulses[i] = 0.0
        for k in list(self.flash):
            self.flash[k] = max(0, self.flash[k] - dt)
            if self.flash[k] == 0:
                del self.flash[k]
        self.scroll_y = max(0, min(self._max_scroll(), self.scroll_y))

    def handle_click(self, mouse_pos, resources, upgrades):
        mx, my = mouse_pos
        for i, u in enumerate(UPGRADES):
            rect = self._btn_rect(i)
            in_clip = PANEL_SCROLL_TOP <= my <= PANEL_SCROLL_BOT
            if rect.collidepoint(mx, my) and in_clip:
                resources, ok = upgrades.purchase(u["id"], resources)
                if ok:
                    self.scales[i] = 1.12
                    self.flash[u["id"]] = 0.5
                return resources
        return resources

    def draw(self, surf, resources, upgrades):
        draw_panel(surf, self.panel_rect,
                   color=(14, 10, 35), border=(55, 40, 120), alpha=230, radius=10)

        title = self.font_sm.render("UPGRADES", True, C_PRIMARY)
        surf.blit(title, (PANEL_X + PANEL_W//2 - title.get_width()//2, PANEL_Y + 10))

        if self._max_scroll() > 0:
            ratio = self.scroll_y / self._max_scroll()
            track_h = PANEL_SCROLL_BOT - PANEL_SCROLL_TOP
            thumb_h = max(20, int(track_h * self.visible_h / self.content_h))
            thumb_y = PANEL_SCROLL_TOP + int((track_h - thumb_h) * ratio)
            pygame.draw.rect(surf, (40, 30, 70),
                             (PANEL_X + PANEL_W - 6, PANEL_SCROLL_TOP, 4, track_h),
                             border_radius=2)
            pygame.draw.rect(surf, C_PRIMARY,
                             (PANEL_X + PANEL_W - 6, thumb_y, 4, thumb_h),
                             border_radius=2)
            hint = self.font_xs.render("scroll ↕", True, C_GRAY)
            surf.blit(hint, (PANEL_X + PANEL_W//2 - hint.get_width()//2,
                             PANEL_SCROLL_BOT + 2))

        clip = surf.get_clip()
        surf.set_clip(pygame.Rect(PANEL_X, PANEL_SCROLL_TOP,
                                  PANEL_W, PANEL_SCROLL_BOT - PANEL_SCROLL_TOP))

        for i, u in enumerate(UPGRADES):
            self._draw_btn(surf, i, u, resources, upgrades)

        surf.set_clip(clip)

        self._draw_minimap_stub(surf)

    def _draw_btn(self, surf, i, u, resources, upgrades):
        rect    = self._btn_rect(i)
        if rect.y + rect.height < PANEL_SCROLL_TOP: return
        if rect.y > PANEL_SCROLL_BOT: return

        level   = upgrades.level(u["id"])
        maxed   = upgrades.maxed(u["id"])
        cost    = upgrades.costs[u["id"]]
        afford  = resources >= cost and not maxed
        hover   = self.hover_idx == i
        flash   = self.flash.get(u["id"], 0) > 0
        pulse   = abs(math.sin(self.pulses[i])) * 0.25 if afford else 0

        scale = self.scales[i]
        if scale != 1.0:
            nw = int(rect.width  * scale)
            nh = int(rect.height * scale)
            rect = pygame.Rect(rect.centerx - nw//2, rect.centery - nh//2, nw, nh)

        if maxed:   bg,border=(25,50,25),C_SUCCESS
        elif flash: bg,border=(45,25,75),C_ACCENT
        elif hover and afford: bg,border=(32,22,65),C_PRIMARY
        elif afford:
            p=int(18*pulse)
            bg=(22+p,16+p//2,52+p); border=C_PRIMARY
        else:       bg,border=(16,12,36),(40,32,70)

        draw_panel(surf, rect, color=bg, border=border, alpha=215, radius=8)
        if afford and not maxed:
            draw_glow_rect(surf, C_PRIMARY, rect, radius=4, alpha=int(25+pulse*35))

        x,y = rect.x, rect.y

        icon_s = self.font_md.render(u["icon"], True, C_WHITE)
        surf.blit(icon_s, (x+6, y + rect.height//2 - icon_s.get_height()//2))

        name_col = C_SUCCESS if maxed else (C_ACCENT if flash else C_WHITE)
        name_s   = self.font_xs.render(u["name"], True, name_col)
        surf.blit(name_s, (x+36, y+6))

        desc_s = self.font_xs.render(u["desc"][:28], True, C_GRAY)
        surf.blit(desc_s, (x+36, y+20))

        max_lv = next(ug["max_level"] for ug in UPGRADES if ug["id"]==u["id"])
        bw = PANEL_BTN_W - 80
        draw_health_bar(surf, x+36, y+34, bw, 4,
                        level, max_lv,
                        fg_color=C_SUCCESS if maxed else C_PRIMARY)

        if maxed:
            tag = self.font_xs.render("MAX✓", True, C_SUCCESS)
        else:
            col = C_ACCENT if afford else C_GRAY
            tag = self.font_xs.render(f"{format_number(cost)}✦", True, col)
        surf.blit(tag, (rect.right - tag.get_width() - 6, y+6))

        lv_s = self.font_xs.render(f"Lv{level}", True, C_GRAY)
        surf.blit(lv_s, (rect.right - lv_s.get_width() - 6, y+22))

    def _draw_minimap_stub(self, surf):
        """Placeholder — real minimap drawn from main.py with world data."""
        mm_rect = pygame.Rect(MM_X, MM_Y, MM_W, MM_H)
        draw_panel(surf, mm_rect, color=(10,8,24), border=(40,30,80), alpha=210, radius=6)
        lbl = self.font_xs.render("MINIMAP", True, C_GRAY)
        surf.blit(lbl, (MM_X + 4, MM_Y + 2))


class HUD:
    """Main heads-up display using master layout constants."""

    def __init__(self, font_lg, font_md, font_sm, font_xs):
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self.font_xs = font_xs
        self.res_display = 0.0
        self.wave_announce = 0.0
        self.wave_num = 0

    def announce_wave(self, wave):
        self.wave_num = wave
        self.wave_announce = 3.0

    def update(self, dt, resources, time_slow):
        self.res_display = lerp(self.res_display, resources, min(1.0, dt*8))
        self.wave_announce = max(0.0, self.wave_announce - dt)

    def draw(self, surf, player, upgrades, wave, time_slow=False):
        self._draw_resource_bar(surf, self.res_display)
        self._draw_hp_bar(surf, player)
        self._draw_danger_badge(surf)    
        self._draw_wave_announce(surf)

    def _draw_resource_bar(self, surf, resources):
        rect = pygame.Rect(LX, RES_Y, LW, 44)
        draw_panel(surf, rect, alpha=210, radius=10)
        icon = self.font_md.render("✦", True, C_ACCENT)
        surf.blit(icon, (LX+12, RES_Y+10))
        val  = self.font_lg.render(format_number(int(resources)), True, C_ACCENT)
        surf.blit(val, (LX+38, RES_Y+6))
        draw_glow_rect(surf, C_ACCENT, rect, radius=4, alpha=25)

    def _draw_hp_bar(self, surf, player):
        rect = pygame.Rect(LX, HP_Y, 200, 24)
        draw_panel(surf, rect, alpha=200, radius=7)
        col = C_SUCCESS if player.hp > player.max_hp*0.5 else C_DANGER
        draw_health_bar(surf, LX+8, HP_Y+6, 184, 8,
                        player.hp, player.max_hp, fg_color=col)
        ht = self.font_xs.render(f"HP  {int(player.hp)}/{player.max_hp}",True,C_WHITE)
        surf.blit(ht, (LX+8, HP_Y+14))

    def _draw_danger_badge(self, surf):
        pass  
    def _draw_wave_announce(self, surf):
        t    = self.wave_announce / 3.0
        alpha= int(255 * smooth_step(min(t*3,1.0)) * smooth_step(t))
        txt  = self.font_lg.render(f"── WAVE  {self.wave_num} ──", True, C_DANGER)
        txt.set_alpha(alpha)
        surf.blit(txt, (CX - txt.get_width()//2, HEIGHT//2 - 80))

    def draw_stats(self, surf, upgrades, loot_sys=None):
        """Draw active upgrade stats panel bottom-left."""
        lines = []
        if upgrades.click_power > 1:
            lines.append((f"⚡ ×{upgrades.click_power} click power", C_SECONDARY))
        if upgrades.auto_income > 0:
            lines.append((f"🤖 {format_number(upgrades.auto_income)}/s auto", C_SECONDARY))
        if upgrades.rare_boost > 0:
            lines.append((f"🧲 +{int(upgrades.rare_boost*100)}% rare ores", (255,200,80)))
        if upgrades.collect_range_bonus > 0:
            lines.append((f"🌀 +{upgrades.collect_range_bonus}px range", (120,180,255)))
        if upgrades.chain_chance > 0:
            lines.append((f"💎 {int(upgrades.chain_chance*100)}% chain", (200,120,255)))
        if upgrades.hp_regen > 0:
            lines.append((f"🛡 {upgrades.hp_regen:.0f} HP/s regen", C_SUCCESS))
        if upgrades.speed_mult > 1.0:
            lines.append((f"🚀 ×{upgrades.speed_mult:.2f} speed", (255,140,80)))
        if upgrades.vacuum_radius > 0:
            lines.append((f"🔮 {upgrades.vacuum_radius}px vacuum", (100,220,255)))
        if not lines: return

        h = min(len(lines), 5) * 18 + 10
        rect = pygame.Rect(LX, STATS_Y, 220, h)
        draw_panel(surf, rect, alpha=190, radius=8)
        for j,(txt,col) in enumerate(lines[:5]):
            s = self.font_xs.render(txt, True, col)
            surf.blit(s, (LX+8, STATS_Y+6+j*18))

    def draw_xp_bar(self, surf, xp_sys):
        pygame.draw.rect(surf, (20,14,40), (0, XP_Y, WIDTH, 5))
        bw = int(WIDTH * xp_sys.display_xp)
        if bw > 0:
            pygame.draw.rect(surf, C_ACCENT, (0, XP_Y, bw, 5))

    def draw_fps(self, surf, fps):
        fps_s = self.font_xs.render(f"{int(fps)}fps", True, C_GRAY)
        surf.blit(fps_s, (LX, FPS_Y))
