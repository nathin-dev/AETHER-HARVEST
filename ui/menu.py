"""
Menu screens for AETHER HARVEST
"""
import pygame
import math
import random
from utils.constants import WIDTH, HEIGHT, C_BG, C_PRIMARY, C_SECONDARY, C_ACCENT, C_DANGER,  C_GRAY, C_SUCCESS
from engine.renderer import draw_panel, draw_glow_circle, draw_glow_rect


class StarField:
    """Animated star field for menu backgrounds."""
    def __init__(self, n=200):
        self.stars = [
            (random.uniform(0, WIDTH),
             random.uniform(0, HEIGHT),
             random.uniform(0.3, 2.0),
             random.uniform(40, 220))
            for _ in range(n)
        ]
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.stars = [
            (x, (y + speed * 0.4) % HEIGHT, speed, bright)
            for (x, y, speed, bright) in self.stars
        ]

    def draw(self, surf):
        for (x, y, speed, bright) in self.stars:
            b = int(bright * (0.7 + 0.3 * math.sin(self.t * speed)))
            r = max(1, int(speed * 0.5))
            pygame.draw.circle(surf, (b, b, min(255, b + 40)), (int(x), int(y)), r)


class Button:
    def __init__(self, rect, text, font, color=C_PRIMARY, hover_color=C_SECONDARY):
        self.rect        = pygame.Rect(rect)
        self.text        = text
        self.font        = font
        self.color       = color
        self.hover_color = hover_color
        self.scale       = 1.0
        self.hovered     = False

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.05 if self.hovered else 1.0
        self.scale += (target - self.scale) * min(1.0, dt * 12)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surf):
        col    = self.hover_color if self.hovered else self.color
        w      = int(self.rect.width  * self.scale)
        h      = int(self.rect.height * self.scale)
        r      = pygame.Rect(self.rect.centerx - w // 2,
                             self.rect.centery - h // 2, w, h)
        draw_panel(surf, r, color=(20, 14, 50), border=col, alpha=220, radius=10)
        if self.hovered:
            draw_glow_rect(surf, col, r, radius=6, alpha=50)
        txt = self.font.render(self.text, True, col)
        surf.blit(txt, (r.centerx - txt.get_width() // 2,
                        r.centery - txt.get_height() // 2))


class MainMenu:
    def __init__(self, font_lg, font_md, font_sm, font_xs, has_save=False):
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self.font_xs = font_xs
        self.stars   = StarField(250)
        self.t       = 0.0
        self.done    = False
        self.new_game= False

        cx = WIDTH // 2
        self.btns = [
            Button((cx - 130, 320, 260, 52), "NEW GAME",    font_md, C_SECONDARY),
            Button((cx - 130, 390, 260, 52), "CONTINUE",    font_md, C_PRIMARY) if has_save
            else Button((cx - 130, 390, 260, 52), "HOW TO PLAY", font_md, C_GRAY),
            Button((cx - 130, 460, 260, 52), "QUIT",        font_md, C_DANGER),
        ]
        self.has_save = has_save

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btns[0].clicked(mp):
                self.done     = True
                self.new_game = True
            elif self.btns[1].clicked(mp):
                self.done     = True
                self.new_game = not self.has_save
            elif self.btns[2].clicked(mp):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)
        mp = pygame.mouse.get_pos()
        for b in self.btns:
            b.update(mp, dt)

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)

        # Title glow
        cx = WIDTH // 2
        glow_y = 160 + int(math.sin(self.t * 1.5) * 8)

        # Animated hex ring behind title
        for i in range(12):
            angle  = self.t * 0.4 + i * math.tau / 12
            rx     = cx + int(math.cos(angle) * 140)
            ry     = glow_y + int(math.sin(angle) * 40)
            col    = C_PRIMARY if i % 3 != 0 else C_SECONDARY
            pygame.draw.circle(surf, col, (rx, ry), 3)

        # Title
        title = self.font_lg.render("AETHER  HARVEST", True, C_ACCENT)
        surf.blit(title, (cx - title.get_width() // 2, glow_y - 30))

        sub = self.font_sm.render("Crystal Mining · Wave Defense · Idle Upgrades", True, C_GRAY)
        surf.blit(sub, (cx - sub.get_width() // 2, glow_y + 20))

        # Version tag
        ver = self.font_xs.render("v2.0", True, C_GRAY)
        surf.blit(ver, (WIDTH - 50, HEIGHT - 22))

        for b in self.btns:
            b.draw(surf)

        # Controls hint at bottom
        hints = [
            "WASD / Arrows  –  Move",
            "Space  –  Dash (i-frames)",
            "Click  –  Harvest crystals / Buy upgrades",
            "S  –  Save game",
        ]
        panel = pygame.Rect(cx - 200, 530, 400, len(hints) * 20 + 16)
        draw_panel(surf, panel, alpha=160, radius=8)
        for j, h in enumerate(hints):
            hs = self.font_xs.render(h, True, C_GRAY)
            surf.blit(hs, (cx - hs.get_width() // 2, panel.y + 8 + j * 20))


class GameOverScreen:
    def __init__(self, font_lg, font_md, font_sm, font_xs,
                 resources, wave, play_time):
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self.font_xs = font_xs

        self.resources  = resources
        self.wave       = wave
        self.play_time  = play_time
        self.stars      = StarField(200)
        self.t          = 0.0
        self.restart    = False
        self.quit       = False

        from utils.math_utils import format_number
        self.fmt = format_number

        cx = WIDTH // 2
        self.btns = [
            Button((cx - 140, 460, 280, 52), "PLAY AGAIN", font_md, C_SUCCESS),
            Button((cx - 140, 528, 280, 52), "MAIN MENU",  font_md, C_PRIMARY),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btns[0].clicked(mp):
                self.restart = True
            elif self.btns[1].clicked(mp):
                self.quit    = True

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)
        mp = pygame.mouse.get_pos()
        for b in self.btns:
            b.update(mp, dt)

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)

        cx = WIDTH // 2
        cy = HEIGHT // 2

        panel = pygame.Rect(cx - 260, cy - 200, 520, 420)
        draw_panel(surf, panel, color=(25, 8, 50), border=C_DANGER, alpha=235, radius=16)
        draw_glow_rect(surf, C_DANGER, panel, radius=10, alpha=30)

        # Title
        t1 = self.font_lg.render("YOU HAVE FALLEN", True, C_DANGER)
        surf.blit(t1, (cx - t1.get_width() // 2, panel.y + 24))

        # Divider
        pygame.draw.line(surf, C_DANGER,
                         (panel.x + 30, panel.y + 74),
                         (panel.right - 30, panel.y + 74), 1)

        # Stats
        mins = int(self.play_time // 60)
        secs = int(self.play_time % 60)
        stats = [
            ("Crystals Harvested", f"{self.fmt(int(self.resources))} ✦"),
            ("Waves Survived",     str(self.wave)),
            ("Time Played",        f"{mins}m {secs:02d}s"),
        ]
        for j, (label, value) in enumerate(stats):
            y    = panel.y + 100 + j * 52
            lbl  = self.font_sm.render(label, True, C_GRAY)
            val  = self.font_md.render(value, True, C_ACCENT)
            surf.blit(lbl, (panel.x + 40, y))
            surf.blit(val, (panel.right - val.get_width() - 40, y))
            pygame.draw.line(surf, (40, 30, 70),
                             (panel.x + 30, y + 34),
                             (panel.right - 30, y + 34), 1)

        for b in self.btns:
            b.draw(surf)

        # Floating skull anim
        skull_y = panel.y - 20 + int(math.sin(self.t * 2) * 6)
        sk = self.font_lg.render("☠", True, C_DANGER)
        surf.blit(sk, (cx - sk.get_width() // 2, skull_y))
