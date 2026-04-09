"""

HUD and UI for Infinite Harvest
"""

import pygame
import  math
from utils.constants import (WIDTH, HEIGHT, UPGRADES, C_BG, C_PANEL, C_PANEL_BORDER,
                             C_PRIMARY, C_SECONDARY, C_ACCENT, C_DANGER, C_WHITE,
                             C_GRAY, C_SUCCESS, ORE_TYPES)

from utils.math_utils import lerp, format_number, smooth_step
from engine.renderer import draw_panel, draw_glow_circle, draw_health_bar, draw_glow_rect

PANEL_W = 280
PANEL_X = WIDTH - PANEL_W - 10

class UpgradePanel:
    """Right-side upgrade shop panel."""

    BTN_H = 62
    BTN_GAP = 8

    def __init__(self, font_md, font_sm, font_xs):
        self.font_md = font_md
        self.font_sm = font_sm
        self.font_xs = font_xs 

        self.visible = True 
        self.hover_idx = -1
        self.btn_scales = [1.0] * len(UPGRADES)
        self.btn_pulses = [0.0] * len(UPGRADES)
        self.scroll_y = 0
        self.panel_rect = pygame.Rect(PANEL_X, 100, PANEL_W, HEIGHT - 110)

        # Notofication flashes
        self.flash = {} # upgrade_id -> timer 
        self.lab = "upgrades" # upgrades | stats 

    def update(self, dt, mouse_pos, upgrades):
        mx, my = mouse_pos 
        self.hover_idx = -1
        for i, u in enumerate(UPGRADES):
            rect = self._btn_rect(i)
            if rect.collidepoint(mx, my):
                self.hover_idx = i 
                self.btn_scales[i] = lerp(self.btn_scales[i], 1.04, 0.2)
            else:
                self.btn_scales[i] = lerp(self.btn_scales[i], 1.0, 0.15)

            if upgrades.can_afford(u["id"], 9999):
                self.btn_pulses[i] += dt * 3
            else:
                self.btn_pulses[i] = 0.0 
        
        for k in list(self.flash.keys()):
            self.flash[k] = max(0, self.flash[k] - dt)
            if self.flash[k] == 0:
                del self.flash[k]
    
    def handle_click(self, mouse_pos, resources, upgrades):
        mx, my = mouse_pos 
        for i, u in enumerate(UPGRADES):
            rect = self._btn_rect(i)
            if rect.collidepoint(mx, my):
                resources, ok = upgrades.purchase(u["id"], resources)
                if ok:
                    self.btn_scales[i] = 1.15
                    self.flash[u["id"]] = 0.4
                return resources
        return resources 

    def _btn_rect(self, i):
        y = self.panel_rect.y + 10 + i * (self.BTN_H + self.BTN_GAP) - self.scroll_y
        return pygame.Rect(self.panel_rect.x, y, PANEL_W -16, self.BTN_H)
    
    def draw(self, surf, resources, upgrades):
        # Panel background
        draw_panel(surf, self.panel_rect, alpha=200, radius=12)

        # title
        title = self.font_md.render("UPGRADES", True, C_PRIMARY)
        surf.blit(title, (self.panel_rect.x + (PANEL_W - title.get_width()) // 2,
                          self.panel_rect.y - 28))
        
        # Clip region
        clip = surf.get_clip()
        surf.set_clip(self.panel_rect)

        for i, u in enumerate(UPGRADES):
            self._draw_btn(surf, i, u, resources, upgrades)

        surf.set_clip(clip)

    def _draw_btn(self, surf, i, u, resources, upgrades):
        rect = self._btn_rect(i)
        level = upgrades.level(u["id"])
        maxed  = upgrades.maxed(u["id"])
        cost = upgrades.costs[u["id"]]
        afford = resources >= cost and not maxed 
        hover = self.hover_idx == i
        flash  = self.flash.get(u["id"], 0) >0 
        pulse = abs(math.sin(self.btn_pulses[i])) * 0.3 if afford else 0


        # Scale tarnsform
        scale = self.btn_scales[i]
        if scale != 1.0:
            new_w = int(rect.width * scale)
            new_h = int(rect.height * scale)
            rect = pygame.Rect(
                rect.centerx - new_w // 2,
                rect.centery - new_h // 2,
                new_w, new_h
            )

        # background 
        if maxed:
            bg = (30, 60,30)
            border = C_SUCCESS
        elif flash:
            bg = (50, 30, 80)
            border = C_ACCENT
        elif hover and afford:
            bg = (35, 25, 70)
            border = C_PRIMARY
        elif afford:
            bg_pulse = int(20 * pulse)
            bg = ( 25 + bg_pulse // 2, 55 + bg_pulse)
            border = (*C_PRIMARY[:2], 150)
        else:
            bg  = (18, 14, 38)
            border = C_PANEL_BORDER
        
        draw_panel(surf, rect, color=bg, border=border, alpha=210, radius=8)

        if afford and not maxed:
             draw_glow_rect(surf, C_PRIMARY, rect, radius=4, alpha=int(30 + pulse * 40))

        #Icon
        icon_surf = self.font_md.render(u["icon"], True, C_WHITE)
        surf.blit(icon_surf, (rect.x + 8, rect.centery - icon_surf.get_height() // 2))


        # Name
        name_color = C_SUCCESS if maxed else(C_ACCENT if flash else C_WHITE)
        name_surf = self.font_sm.render(u["name"], True, name_color)
        surf.blit(name_surf, (rect.x + 46, rect.y + 8))

        # Description
        desc_surf = self.font_xs.render(u["desc"][:32], True, C_GRAY)
        surf.blit(desc_surf, (rect.x + 46, rect.y + 8))

        # Level bar
        max_level = [ug["max_level"] for ug in UPGRADES if ug["id"] == u["id"]][0]
        bar_w = PANEL_W - 100
        draw_health_bar(surf, rect.x + 46, rect.y + 44, bar_w, 5,
                        level, max_level,
                        fg_color=C_SUCCESS if maxed else C_PRIMARY)

        # Cost / MAXED
        if maxed:
            tag = self.font_xs.render("MAXED ✓", True, C_SUCCESS)
        else:
            col = C_ACCENT if afford else C_GRAY
            tag = self.font_xs.render(f"{format_number(cost)} ✦", True, col)
        surf.blit(tag, (rect.right - tag.get_width() - 8, rect.y + 8))

        # Level number
        lv_surf = self.font_xs.render(f"Lv{level}", True, C_GRAY)
        surf.blit(lv_surf, (rect.right - lv_surf.get_width() - 8, rect.y + 44))


class HUD:
    """Main heads-up display: resources, HP, wave info, minimap."""

    def __init__(self, font_lg, font_md, font_sm, font_xs):
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self.font_xs = font_xs

        self.res_display    = 0.0   # smooth display value
        self.time_slow_anim = 0.0
        self.wave_announce  = 0.0
        self.wave_num       = 0

    def announce_wave(self, wave):
        self.wave_num    = wave
        self.wave_announce = 3.0

    def update(self, dt, resources, time_slow):
        self.res_display  = lerp(self.res_display, resources, min(1.0, dt * 8))
        if time_slow:
            self.time_slow_anim = min(1.0, self.time_slow_anim + dt * 4)
        else:
            self.time_slow_anim = max(0.0, self.time_slow_anim - dt * 4)
        self.wave_announce = max(0, self.wave_announce - dt)

    def draw(self, surf, player, upgrades, wave, time_slow=False):
        self._draw_resource_bar(surf, self.res_display)
        self._draw_hp_bar(surf, player)
        self._draw_stats(surf, upgrades)
        if self.wave_announce > 0:
            self._draw_wave_announce(surf, self.wave_num)
        if self.time_slow_anim > 0:
            self._draw_time_slow_overlay(surf)
        self._draw_controls(surf)

    def _draw_resource_bar(self, surf, resources):
        # Top bar
        bar_rect = pygame.Rect(10, 10, 300, 50)
        draw_panel(surf, bar_rect, alpha=200, radius=10)

        icon = self.font_md.render("✦", True, C_ACCENT)
        surf.blit(icon, (24, 20))

        val  = self.font_lg.render(format_number(int(resources)), True, C_ACCENT)
        surf.blit(val, (50, 14))

        draw_glow_rect(surf, C_ACCENT, bar_rect, radius=4, alpha=30)

    def _draw_hp_bar(self, surf, player):
        bar_rect = pygame.Rect(10, 68, 200, 28)
        draw_panel(surf, bar_rect, alpha=200, radius=8)
        draw_health_bar(surf, 16, 76, 188, 12,
                        player.hp, player.max_hp,
                        fg_color=C_SUCCESS if player.hp > 50 else C_DANGER)
        hp_txt = self.font_xs.render(f"HP  {int(player.hp)}/{player.max_hp}", True, C_WHITE)
        surf.blit(hp_txt, (16, 90))

    def _draw_stats(self, surf, upgrades):
        y  = HEIGHT - 110
        stats = [
            (f"⚡ Click Power  ×{upgrades.click_power}", C_SECONDARY),
            (f"🤖 Auto Income  {format_number(upgrades.auto_income)}/s", C_SECONDARY),
            (f"🧲 Rare Boost   +{int(upgrades.rare_boost*100)}%", C_SECONDARY),
        ]
        rect = pygame.Rect(10, y, 220, len(stats) * 22 + 14)
        draw_panel(surf, rect, alpha=180, radius=8)
        for j, (txt, col) in enumerate(stats):
            s = self.font_xs.render(txt, True, col)
            surf.blit(s, (18, y + 8 + j * 22))

    def _draw_wave_announce(self, surf, wave):
        t      = self.wave_announce / 3.0
        alpha  = int(255 * smooth_step(min(t * 3, 1.0) * smooth_step(t)))
        txt    = self.font_lg.render(f"── WAVE  {wave} ──", True, C_DANGER)
        txt.set_alpha(alpha)
        x = WIDTH // 2 - txt.get_width() // 2
        y = HEIGHT // 2 - 60
        surf.blit(txt, (x, y))

    def _draw_time_slow_overlay(self, surf):
        a    = int(self.time_slow_anim * 60)
        over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        over.fill((60, 30, 120, a))
        surf.blit(over, (0, 0))
        txt = self.font_sm.render("◈  TEMPORAL SURGE  ◈", True, (200, 150, 255))
        surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 20))

    def _draw_controls(self, surf):
        hints = ["WASD Move", "Space Dash", "Click Collect"]
        x = WIDTH // 2 - 140
        for i, h in enumerate(hints):
            s = self.font_xs.render(h, True, C_GRAY)
            surf.blit(s, (x + i * 95, HEIGHT - 22))

