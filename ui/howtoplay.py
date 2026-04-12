"""

How To Play screen for AETHER HARVEST.
Tabbed: Controls | Ores | Upgrades | Modes | Tips 
"""

import pygame, math 
from utils.constants import (WIDTH, HEIGHT, C_BG, C_PRIMARY, C_SECONDARY,
                             C_ACCENT, C_DANGER, C_SUCCESS, C_WHITE, C_GRAY,
                             ORE_TYPES, UPGRADES)

from engine.renderer import draw_panel, draw_glow_rect 
from utils.math_utils import lerp 

SECTIONS = ["Controls", "Ores", "Upgrades", "Modes & Diff", "Tips"]

CONTROLS = [
    ("Move", "WASD or Arrow Keys"),
    ("Dash", "Space (invincibility frames)"),
    ("Harvest ore", "Left Click on a crystal"),
    ("Shoot bolt", "Right Click (hold to auto-fire)"),
    ("Switch weapon", "Tab (3 weapon types)"),
    ("Ability 1", "Q - Nova Burst (explode all nearby ones)"),
    ("Ability 2", "E - Void Pulse (shockwave enemies)"),
    ("Save game", "S"),
    ("Quit", "Esc"),
]

TIPS  = [

    "🔮  Buy Aether Lens early — auto-collecting while moving is massive passive income.",
    "💎  Chain combos multiply your income. Collect ores as fast as you can!",
    "🧲  Void Magnet shifts spawn weights toward rare ores — stack it with Warp Field.",
    "🌀  Warp Field widens your click radius — even a small level is game-changing.",
    "⚡  Nova Burst (Q) during Ore Storm events = enormous income. Time it well.",
    "☠  When the Blood Moon event fires, kill enemies first — they drop 5× resources.",
    "★  Reach wave 20 then Prestige — you get a permanent bonus that carries forever.",
    "🛡  Void Shield upgrade + Aether Shield ability stacks — nearly unkillable.",
    "👑  Bosses spawn every 5 waves. Use your abilities just before they arrive.",
    "🚀  Phase Drive stacks with Speed Boost loot — you become extremely hard to hit.",
    "⏱  In Blitz mode, skip upgrades and just harvest — time is the only resource.",
    "◈  Crystal Echo + Void Magnet = chain reactions on rare ores = insane damage.",

]

MODES_INFO  = [
    ("◈ Classic", "Survive waves, buy upgrades. The full experience"),
    ("⚡ Blitz", "5 minutes. Ores worth 2x. Enemies 40% faster."),
    ("☠ Void Siege", "No upgrades. Pure skill. 4x ore value. Brutual."),
    ("💎 Crystal Rush", "No enemies. 2-minute harvest highscore sprint."),
    ("★ Prestige", "Unlocked after wave 20. All upgrades maxed. God enemies."),
    ("",           ""),
    ("☆ Easy", "60% enemy HP/DMG. Learn the game"),

]

class HowToPlayScreen:
    def __init__(self, font_lg, font_md, font_sm, font_xs):
        self.fonts = (font_lg, font_md, font_sm, font_xs)
        self.done = False 
        self.tab = 0
        self.t = 0.0 
        self.tab_scales = [1.0] * len(SECTIONS)
        self.hover_tab = -1 

        TAB_W = WIDTH // len(SECTIONS)
        self.tab_rects = [
            pygame.Rect(i * TAB_W, 52, TAB_W, 36)
            for i in range(len(SECTIONS))
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.done = True 
            elif event.key == pygame.K_LEFT:
                self.tab = (self.tab - 1) % len(SECTIONS)
            elif event.key == pygame.K_RIGHT:
                self.tab = (self.tab + 1) % len(SECTIONS)

        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            for i, r in enumerate(self.tab_rects):
                if r.collidepoint(mp):
                    self.done = i 
            
            # Close button 
            close = pygame.Rect(WIDTH - 48, 8, 40, 36)
            if close.collidepoint(mp):
                self.done = True 

    
    def update(self, dt):
        self.t += dt 
        mp = pygame.mouse.get_pos()
        self.hover_tab = -1 
        for i, r in enumerate(self.tab_rects):
            if r.collidepoint(mp):
                self.hover_tab = i 
        for i in range(len(SECTIONS)):
            target = 1.05 if i == self.tab else (1.02 if i == self.hover_tab else 1.0)
            self.tab_scales[i] = lerp(self.tab_scales[i], target, 0.25)

    
    def draw(self, surf):
        font_lg, font_md, font_xs, font_sm = self.fonts
        surf.fill(C_BG)

        # Subtle animated bg dots 
        for i in range(0, WIDTH, 80):
            for j in range(0, HEIGHT, 80):
                r = int(abs(math.sin(self.t*0.5 + i*0.01 + j*0.01))*2)
                if r > 0:
                    pygame.draw.circle(surf, (25,18,55), (i,j), r)

        # Title bar
        pygame.draw.rect(surf, (14,10,32), (0,0, WIDTH, 52))
        title = font_lg.render("HOW TO PLAY", True, C_ACCENT)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 8))

        # Close button 
        close_rect = pygame.Rect(WIDTH-48, 8, 40,  36)
        draw_panel(surf, close_rect, color=(30,14,40), border=C_DANGER, alpha=200, radius=8)
        xs = font_md.render("x", True, C_DANGER)
        surf.blit(xs, (close_rect.centerx - xs.get_width()//2,
                       close_rect.centery - xs.get_height()//2))
        

        # Tab bar 
        for i, (label, rect) in enumerate(zip(SECTIONS, self.tab_rects)):
            active = i == self.tab 
            hovered = i == self.hover_tab 
            col = C_ACCENT if active else (C_WHITE if hovered else C_GRAY)
            bg = (22,16,52) if active else (14,10,32)
            pygame.draw.rect(surf, bg, rect)
            if active:
                pygame.draw.rect(surf, C_ACCENT, (rect.x, rect.bottom-2, rect.width, 2))

            sc = self.tab_scales[i]
            txt = font_sm.render(label, True, col)
            surf.blit(txt, (rect.centerx - txt.get_width()//2,
                                rect.centery - txt.get_height()//2))
            
        pygame.draw.line(surf, (40,30,80), (0,88), (WIDTH,88), 1)

        # Content area
        content_y = 100
        content_h = HEIGHT - 110
        clip = pygame.Rect(0, content_y, WIDTH, content_h)
        surf.set_clip(clip)

        if self.tab == 0: self._draw_controls(surf, font_md, font_sm, font_xs, content_y)
        elif self.tab == 1: self._draw_ores(surf, font_md, font_sm, font_xs, content_y)
        elif self.tab == 2: self._draw_upgrades(surf, font_md, font_sm, font_xs, content_y)
        elif self.tab == 3: self._draw_modes(surf, font_md, font_sm, font_xs, content_y)
        elif self.tab == 4: self._draw_tips(surf, font_md, font_sm, font_xs, content_y)


        surf.set_clip(None)

        # Bottom jint 
        hint = font_xs.render("<- -> Arrow keys to switch tabs . Esc to go back", True, C_GRAY)
        surf.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 20))

    def _draw_controls(self, surf, font_md, font_sm, font_xs, y0):
        col_x = [80, 400, 750]
        y= y0 + 16
        hdr = font_md.render("Key Bindings", True, C_WHITE)
        surf.blit(hdr, (col_x[0], y)); y+= 36

        for action, key in CONTROLS:
            pygame.draw.rect(surf, (18, 14, 42),
                             (col_x[0]-8, y-2, 720, 28), border_radius=4)
            act_s = font_sm.render(action, True, C_SECONDARY)
            surf.blit(act_s, (col_x[0], y))
            key_s = font_sm.render(key, True, C_ACCENT)
            surf.blit(key_s, (col_x[1], y))
            y += 32 

        y += 10
        hdr2 = font_md.render("Combat Tips", True, C_WHITE)
        surf.blit(hdr2, (col_x[0], y)); y += 30
        for tip in ["Dash gives invincibility frames - dash through enemies to avoid damage",
                    "Abilities recharge on cooldown - watch the  Q/E/F slots at the bottom",
                    "Your three weapons fire differently - Tab cycles between them"]:
            t_s = font_xs.render("• " + tip, True, C_GRAY)
            surf.blit(t_s, (col_x[0], y)); y += 22

            for ore_name, cfg in ORE_TYPES.items():
                card = pygame.Rect(80, y, 760, 72)
                draw_panel(surf, card, color=(16,12,36),
                           border=cfg["color"], alpha=210, radius=10)
                

                # ORE gem preview 
                pygame.draw.circle(surf, cfg["color"], (card.x+36, card.centery), 20)
                pygame.draw.circle(surf, cfg["glow"], (card.x+36, card.centery), 14)
                pygame.draw.circle(surf, (255,255,255), (card.x+29, card.centery-7), 5)

                # Info 
                name_s = font_md.render(ore_name.upper(), True, cfg["color"])
                surf.blit(name_s, (card.x+68, card.y+8))
                info = [
                    f"Value: x{cfg['Value']} per click",
                    f"Spawn chance: ~{cfg['rarity']}% base (Void Magnet raises this)",

                ]
                for i2,inf in enumerate(info):
                    s=font_xs.render(inf, True, C_GRAY)
                    surf.blit(s, (card.x+68, card.y+32+i2*16))
                # Special tag 
                if ore_name == "voidate":
                    tag = font_xs.render("⚡ Triggers Temporal Surge if unlocked!", True, C_ACCENT)
                    surf.blit(tag, (card.x+68, card.y+52))
                y += 82
    def _draw_upgrades(self, surf, font_md, font_sm, font_xs, y0):
        y = y0 + 10
        hdr = font_md.render("Upgrade Panel (right side of the screen - scroll to see all)", True, C_WHITE)
        surf.blit(hdr, (40, y)); y += 36 

        COL_W = (WIDTH - 80) // 2
        for i, u in enumerate(UPGRADES):
            col = i % 2
            row = i //2 
            cx = 40 + col * (COL_W + 8)
            cy = y + row * 80
            card = pygame.Rect(cx, cy, COL_W, 72) 
            draw_panel(surf, card, color=(16,12,36),
                               border=C_PRIMARY, alpha=200, radius=8) 
            icon_s = font_md.render(u["icon"], True, C_WHITE)
            surf.blit(icon_s, (cx+8, cy+22))
            name_s = font_sm.render(u["name"], True, C_ACCENT)
            surf.blit(name_s, (cx+38, cy+6))
            desc_s = font_xs.render(u["desc"], True, C_GRAY)
            surf.blit(desc_s, (cx+38, cy+26))
            eff_s = font_xs.render(u["effect"], True, C_SECONDARY)
            surf.blit(eff_s, (cx+38, cy+44))
            lv_s = font_xs.render(f"Max Lv {u['max_level']}", True, C_GRAY)
            surf.blit(lv_s, (card.right - lv_s.get_width()-8, cy+6))
            cost_s = font_xs.render(f"Start: {u['base_cost']}✦", True, C_GRAY)
            surf.blit(cost_s, (card.right - cost_s.get_width()-8, cy+22))

    def _draw_tips(self, surf, font_md, font_sm, font_xs, y0):
        y = y0 + 16
        hdr = font_md.render("Pro Tips", True, C_WHITE)
        surf.blit(hdr, (80, y)); y += 36
        for tip in TIPS:
            card = pygame.Rect(80, y, WIDTH-160, 36)
            draw_panel(surf, card, color=(14,10,30), border=(40,32,70),
                       alpha=190, radius=6)
            t_s = font_xs.render(tip, True, C_GRAY)
            # Truncate if too wide 
            while t_s.get_width() > WIDTH-200:
                tip= tip[:-4]+"..."
                t_s = font_xs.render(tip, True, C_GRAY)
            surf.blit(t_s, (card.x+10, card.y+10))
            y += 42
