"""
Menu screens for AETHER HARVEST v3
Main menu → Mode select → Difficulty → Game
"""
import pygame, math, random
from utils.constants import (WIDTH, HEIGHT, C_BG, C_PRIMARY, C_SECONDARY,
                              C_ACCENT, C_DANGER, C_WHITE, C_GRAY, C_SUCCESS)
from engine.renderer import draw_panel, draw_glow_rect
from utils.math_utils import lerp, smooth_step, format_number
from core.game_modes import MODES, DIFFICULTIES
from core.achievements import ACHIEVEMENTS


# ── Reusable star field ───────────────────────────────────────────────────────
class StarField:
    def __init__(self, n=200):
        self.stars = [(random.uniform(0,WIDTH), random.uniform(0,HEIGHT),
                       random.uniform(0.3,2.0), random.uniform(40,220))
                      for _ in range(n)]
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.stars = [((x + spd * 0.3) % WIDTH, y, spd, b)
                      for (x,y,spd,b) in self.stars]

    def draw(self, surf):
        for (x,y,spd,bright) in self.stars:
            b = int(bright * (0.7 + 0.3*math.sin(self.t * spd)))
            r = max(1, int(spd * 0.5))
            pygame.draw.circle(surf, (b, b, min(255,b+40)), (int(x),int(y)), r)


# ── Generic button ────────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, text, font, color=C_PRIMARY, hover_color=C_SECONDARY):
        self.rect        = pygame.Rect(rect)
        self.text        = text
        self.font        = font
        self.color       = color
        self.hover_color = hover_color
        self.scale       = 1.0
        self.hovered     = False

    def update(self, mp, dt):
        self.hovered = self.rect.collidepoint(mp)
        self.scale   = lerp(self.scale, 1.05 if self.hovered else 1.0,
                            min(1.0, dt*12))

    def clicked(self, mp):
        return self.rect.collidepoint(mp)

    def draw(self, surf):
        col = self.hover_color if self.hovered else self.color
        w   = int(self.rect.width  * self.scale)
        h   = int(self.rect.height * self.scale)
        r   = pygame.Rect(self.rect.centerx - w//2, self.rect.centery - h//2, w, h)
        draw_panel(surf, r, color=(20,14,50), border=col, alpha=220, radius=10)
        if self.hovered:
            draw_glow_rect(surf, col, r, radius=6, alpha=50)
        txt = self.font.render(self.text, True, col)
        surf.blit(txt, (r.centerx - txt.get_width()//2,
                        r.centery - txt.get_height()//2))


# ── Main menu (screen 1) ──────────────────────────────────────────────────────
class MainMenu:
    def __init__(self, font_lg, font_md, font_sm, font_xs,
                 has_save=False, achievements=None, highscores=None, prestige=None):
        self.fonts   = (font_lg, font_md, font_sm, font_xs)
        self.stars   = StarField(250)
        self.t       = 0.0
        self.done    = False
        self.to_mode_select = False
        self.to_achievements= False

        cx = WIDTH // 2
        self.btns = [
            Button((cx-130, 310, 260, 52), "PLAY",          font_md, C_SECONDARY),
            Button((cx-130, 374, 260, 52), "CONTINUE",      font_md, C_PRIMARY) if has_save
             else Button((cx-130, 374, 260, 52), "HOW TO PLAY", font_md, C_GRAY),
            Button((cx-130, 438, 260, 52), "ACHIEVEMENTS",  font_md, C_ACCENT),
            Button((cx-130, 502, 260, 52), "QUIT",          font_md, C_DANGER),
        ]
        self.has_save    = has_save
        self.new_game    = False
        self.achievements= achievements
        self.prestige    = prestige
        self.highscores  = highscores

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btns[0].clicked(mp):
                self.to_mode_select = True
                self.done = True
                self.new_game = True
            elif self.btns[1].clicked(mp):
                self.to_mode_select = True
                self.done = True
                self.new_game = not self.has_save
            elif self.btns[2].clicked(mp):
                self.to_achievements = True
                self.done = True
            elif self.btns[3].clicked(mp):
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
        font_lg, font_md, font_sm, font_xs = self.fonts
        cx = WIDTH // 2

        # Orbiting hex ring
        for i in range(16):
            a  = self.t * 0.3 + i * math.tau / 16
            rx = cx + int(math.cos(a) * 160)
            ry = 175 + int(math.sin(a) * 45)
            col = C_PRIMARY if i%4 != 0 else C_SECONDARY
            pygame.draw.circle(surf, col, (rx, ry), 2 + (i%3))

        # Title glow
        title_y = 145 + int(math.sin(self.t*1.2)*6)
        title   = font_lg.render("AETHER  HARVEST", True, C_ACCENT)
        surf.blit(title, (cx - title.get_width()//2, title_y))

        sub = font_sm.render("Crystal Mining  ·  Wave Defense  ·  Prestige Upgrades", True, C_GRAY)
        surf.blit(sub, (cx - sub.get_width()//2, title_y + 44))

        # Prestige badge
        if self.prestige and self.prestige.prestige_level > 0:
            p_txt = font_xs.render(f"★ Prestige {self.prestige.prestige_level}", True, (255,220,50))
            surf.blit(p_txt, (cx - p_txt.get_width()//2, title_y + 66))

        for b in self.btns:
            b.draw(surf)

        # Achievement progress bottom-left
        if self.achievements:
            ach_txt = font_xs.render(
                f"Achievements  {self.achievements.total_unlocked}/{self.achievements.total_count}",
                True, C_GRAY)
            surf.blit(ach_txt, (16, HEIGHT - 22))

        # High score blurb
        if self.highscores:
            best = self.highscores.get_best("classic")
            if best:
                hs = font_xs.render(
                    f"Best classic run:  {format_number(best['score'])} ✦  wave {best['wave']}",
                    True, C_GRAY)
                surf.blit(hs, (cx - hs.get_width()//2, HEIGHT - 22))

        ver = font_xs.render("v3.0", True, C_GRAY)
        surf.blit(ver, (WIDTH-44, HEIGHT-20))


# ── Mode select (screen 2) ────────────────────────────────────────────────────
class ModeSelectScreen:
    CARD_W, CARD_H = 240, 200
    COLS, ROWS     = 3, 2

    def __init__(self, font_lg, font_md, font_sm, font_xs,
                 prestige=None, highscores=None):
        self.fonts      = (font_lg, font_md, font_sm, font_xs)
        self.stars      = StarField(180)
        self.t          = 0.0
        self.done       = False
        self.back       = False
        self.selected_mode = None
        self.prestige   = prestige
        self.highscores = highscores
        self.hover_mode = None

        # Unlock prestige mode
        if prestige and prestige.total_prestiges > 0:
            MODES["prestige"]["unlocked"] = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            for mode_id, rect in self._card_rects():
                if rect.collidepoint(mp) and MODES[mode_id]["unlocked"]:
                    self.selected_mode = mode_id
                    self.done = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back = True
            self.done = True

    def _card_rects(self):
        mode_ids = list(MODES.keys())
        gap      = 20
        total_w  = self.COLS * self.CARD_W + (self.COLS-1) * gap
        sx       = WIDTH//2 - total_w//2
        sy       = 130
        out = []
        for i, mid in enumerate(mode_ids):
            col = i % self.COLS
            row = i // self.COLS
            x = sx + col * (self.CARD_W + gap)
            y = sy + row * (self.CARD_H + gap)
            out.append((mid, pygame.Rect(x, y, self.CARD_W, self.CARD_H)))
        return out

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)
        mp = pygame.mouse.get_pos()
        self.hover_mode = None
        for mode_id, rect in self._card_rects():
            if rect.collidepoint(mp):
                self.hover_mode = mode_id

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)
        font_lg, font_md, font_sm, font_xs = self.fonts

        title = font_lg.render("SELECT  MODE", True, C_WHITE)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 60))

        for mode_id, rect in self._card_rects():
            m       = MODES[mode_id]
            locked  = not m["unlocked"]
            hovered = self.hover_mode == mode_id
            col     = m["color"] if not locked else (50,40,70)

            # Card bg
            pulse = abs(math.sin(self.t*2)) * 0.3 if hovered and not locked else 0
            draw_panel(surf, rect,
                       color=(25+int(pulse*20),16+int(pulse*10),55+int(pulse*30)),
                       border=col, alpha=220, radius=14)
            if hovered and not locked:
                draw_glow_rect(surf, col, rect, radius=8, alpha=50)

            # Icon
            icon_s = font_lg.render(m["icon"], True, col)
            surf.blit(icon_s, (rect.centerx - icon_s.get_width()//2, rect.y+16))

            # Name
            name_s = font_md.render(m["name"], True,
                                    col if not locked else (70,60,90))
            surf.blit(name_s, (rect.centerx - name_s.get_width()//2, rect.y+62))

            # Subtitle
            sub_s = font_xs.render(m["subtitle"] if not locked else "— LOCKED —",
                                   True, (120,110,150) if locked else C_GRAY)
            surf.blit(sub_s, (rect.centerx - sub_s.get_width()//2, rect.y+90))

            # Description (wrap manually)
            if not locked:
                desc = m["description"]
                words = desc.split()
                lines, cur = [], ""
                for w in words:
                    test = cur + (" " if cur else "") + w
                    if font_xs.size(test)[0] > self.CARD_W - 20:
                        lines.append(cur)
                        cur = w
                    else:
                        cur = test
                if cur:
                    lines.append(cur)
                for li, line in enumerate(lines[:3]):
                    ls = font_xs.render(line, True, C_GRAY)
                    surf.blit(ls, (rect.centerx - ls.get_width()//2,
                                   rect.y + 112 + li*16))

            # Best score badge
            if self.highscores and not locked:
                best = self.highscores.get_best(mode_id)
                if best:
                    bs = font_xs.render(f"Best: {format_number(best['score'])}",
                                        True, C_ACCENT)
                    surf.blit(bs, (rect.x + 8, rect.bottom - 18))

            # Time limit tag
            if m["time_limit"] > 0 and not locked:
                mins = m["time_limit"]//60
                tl = font_xs.render(f"⏱ {mins}min", True, C_ACCENT)
                surf.blit(tl, (rect.right - tl.get_width() - 8, rect.bottom - 18))

        esc = font_xs.render("Esc — back", True, C_GRAY)
        surf.blit(esc, (16, HEIGHT-20))


# ── Difficulty select (screen 3) ──────────────────────────────────────────────
class DifficultyScreen:
    BTN_W, BTN_H = 280, 80

    def __init__(self, font_lg, font_md, font_sm, font_xs, mode_id):
        self.fonts     = (font_lg, font_md, font_sm, font_xs)
        self.stars     = StarField(150)
        self.t         = 0.0
        self.done      = False
        self.back      = False
        self.selected  = None
        self.mode_id   = mode_id
        self.hover_diff= None

    def _btn_rects(self):
        diff_ids = list(DIFFICULTIES.keys())
        gap      = 12
        total_h  = len(diff_ids) * self.BTN_H + (len(diff_ids)-1) * gap
        sx       = WIDTH//2 - self.BTN_W//2
        sy       = HEIGHT//2 - total_h//2 + 20
        return [(did, pygame.Rect(sx, sy + i*(self.BTN_H+gap), self.BTN_W, self.BTN_H))
                for i, did in enumerate(diff_ids)]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            for did, rect in self._btn_rects():
                if rect.collidepoint(mp):
                    self.selected = did
                    self.done = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back = True
            self.done = True

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)
        mp = pygame.mouse.get_pos()
        self.hover_diff = None
        for did, rect in self._btn_rects():
            if rect.collidepoint(mp):
                self.hover_diff = did

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)
        font_lg, font_md, font_sm, font_xs = self.fonts

        m     = MODES[self.mode_id]
        title = font_lg.render("SELECT  DIFFICULTY", True, C_WHITE)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 55))

        mode_lbl = font_sm.render(f"Mode:  {m['name']}", True, m["color"])
        surf.blit(mode_lbl, (WIDTH//2 - mode_lbl.get_width()//2, 100))

        for did, rect in self._btn_rects():
            d       = DIFFICULTIES[did]
            hovered = self.hover_diff == did
            col     = d["color"]

            pulse = abs(math.sin(self.t*3))*0.3 if hovered else 0
            draw_panel(surf, rect,
                       color=(22+int(pulse*15),16+int(pulse*8),52+int(pulse*20)),
                       border=col, alpha=220, radius=12)
            if hovered:
                draw_glow_rect(surf, col, rect, radius=6, alpha=50)

            # Icon + name
            icon_s = font_md.render(d["icon"]+"  "+d["name"], True, col)
            surf.blit(icon_s, (rect.x + 20, rect.y + 14))

            # Description
            desc_s = font_xs.render(d["description"], True, C_GRAY)
            surf.blit(desc_s, (rect.x + 20, rect.y + 42))

            # Multiplier tags right side
            tags = [
                f"Enemies ×{d['enemy_hp']:.1f}HP",
                f"XP ×{d['xp_mult']:.1f}",
            ]
            for ti, tag in enumerate(tags):
                ts = font_xs.render(tag, True, col)
                surf.blit(ts, (rect.right - ts.get_width() - 12,
                                rect.y + 14 + ti*18))

        esc = font_xs.render("Esc — back", True, C_GRAY)
        surf.blit(esc, (16, HEIGHT-20))


# ── Achievements screen ───────────────────────────────────────────────────────
class AchievementsScreen:
    def __init__(self, font_lg, font_md, font_sm, font_xs, achievements):
        self.fonts = (font_lg, font_md, font_sm, font_xs)
        self.stars = StarField(150)
        self.ach   = achievements
        self.done  = False
        self.scroll= 0
        self.t     = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.done = True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)
        font_lg, font_md, font_sm, font_xs = self.fonts

        title = font_lg.render("ACHIEVEMENTS", True, C_ACCENT)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 30))

        prog = font_sm.render(
            f"{self.ach.total_unlocked} / {self.ach.total_count}  unlocked",
            True, C_GRAY)
        surf.blit(prog, (WIDTH//2 - prog.get_width()//2, 72))

        # Grid layout
        COLS   = 3
        CELL_W = (WIDTH - 80) // COLS
        CELL_H = 72
        gap    = 8
        clip   = pygame.Rect(0, 110, WIDTH, HEIGHT-130)
        surf.set_clip(clip)

        for i, ach in enumerate(ACHIEVEMENTS):
            col  = i % COLS
            row  = i // COLS
            x    = 40 + col * (CELL_W)
            y    = 110 + row * (CELL_H + gap) - self.scroll
            rect = pygame.Rect(x, y, CELL_W - gap, CELL_H)

            if y + CELL_H < 110 or y > HEIGHT - 30:
                continue

            unlocked = ach["id"] in self.ach.unlocked
            col_c    = ach["color"] if unlocked else (50, 44, 70)

            draw_panel(surf, rect,
                       color=(20,14,42) if unlocked else (14,11,30),
                       border=col_c, alpha=200, radius=8)

            icon_s = font_md.render(ach["icon"] if unlocked else "?", True, col_c)
            surf.blit(icon_s, (x+10, y + CELL_H//2 - icon_s.get_height()//2))

            name_s = font_sm.render(ach["name"], True,
                                    (220,215,245) if unlocked else (60,54,80))
            surf.blit(name_s, (x+46, y+10))

            desc_s = font_xs.render(ach["desc"], True,
                                    C_GRAY if unlocked else (45,40,65))
            surf.blit(desc_s, (x+46, y+32))

            if unlocked:
                dot = pygame.Surface((8,8), pygame.SRCALPHA)
                pygame.draw.circle(dot, C_SUCCESS, (4,4), 4)
                surf.blit(dot, (rect.right-14, y+8))

        surf.set_clip(None)

        esc = font_xs.render("Esc — back   |   Scroll to see more", True, C_GRAY)
        surf.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT-20))


# ── Game over screen ──────────────────────────────────────────────────────────
class GameOverScreen:
    def __init__(self, font_lg, font_md, font_sm, font_xs,
                 resources, wave, play_time,
                 mode_id="classic", difficulty_id="normal",
                 rank=None, is_new_record=False, prestige_available=False):
        self.fonts            = (font_lg, font_md, font_sm, font_xs)
        self.resources        = resources
        self.wave             = wave
        self.play_time        = play_time
        self.mode_id          = mode_id
        self.difficulty_id    = difficulty_id
        self.rank             = rank
        self.is_new_record    = is_new_record
        self.prestige_available = prestige_available
        self.stars            = StarField(200)
        self.t                = 0.0
        self.restart          = False
        self.quit             = False
        self.prestige         = False

        cx = WIDTH // 2
        btns = [Button((cx-150, 460, 300, 52), "PLAY AGAIN", font_md, C_SUCCESS)]
        if prestige_available:
            btns.append(Button((cx-150, 524, 300, 52), "✦ PRESTIGE", font_md, (255,220,50)))
        btns.append(Button((cx-150, 588 if prestige_available else 524,
                             300, 52), "MAIN MENU",  font_md, C_PRIMARY))
        self.btns = btns

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btns[0].clicked(mp):
                self.restart = True
            elif len(self.btns) > 2 and self.btns[1].clicked(mp):
                self.prestige = True
            elif self.btns[-1].clicked(mp):
                self.quit = True

    def update(self, dt):
        self.t += dt
        self.stars.update(dt)
        mp = pygame.mouse.get_pos()
        for b in self.btns:
            b.update(mp, dt)

    def draw(self, surf):
        surf.fill(C_BG)
        self.stars.draw(surf)
        font_lg, font_md, font_sm, font_xs = self.fonts
        cx, cy = WIDTH//2, HEIGHT//2

        panel = pygame.Rect(cx-280, 80, 560, 360)
        draw_panel(surf, panel, color=(22,10,50), border=C_DANGER, alpha=240, radius=18)
        draw_glow_rect(surf, C_DANGER, panel, radius=10, alpha=25)

        skull_y = 70 + int(math.sin(self.t*2)*5)
        sk = font_lg.render("☠", True, C_DANGER)
        surf.blit(sk, (cx - sk.get_width()//2, skull_y))

        title = font_lg.render("YOU HAVE FALLEN", True, C_DANGER)
        surf.blit(title, (cx - title.get_width()//2, panel.y+24))

        # Mode / difficulty tag
        m = MODES.get(self.mode_id, MODES["classic"])
        d = DIFFICULTIES.get(self.difficulty_id, DIFFICULTIES["normal"])
        tag = font_xs.render(f"{m['name']}  ·  {d['name']}", True, C_GRAY)
        surf.blit(tag, (cx - tag.get_width()//2, panel.y+56))

        pygame.draw.line(surf, C_DANGER, (panel.x+30, panel.y+76),
                         (panel.right-30, panel.y+76), 1)

        mins = int(self.play_time//60)
        secs = int(self.play_time%60)
        stats = [
            ("Crystals Harvested", f"{format_number(int(self.resources))} ✦"),
            ("Waves Survived",     str(self.wave)),
            ("Time Played",        f"{mins}m {secs:02d}s"),
        ]
        for j, (label, value) in enumerate(stats):
            y    = panel.y + 96 + j*52
            lbl  = font_sm.render(label, True, C_GRAY)
            val  = font_md.render(value, True, C_ACCENT)
            surf.blit(lbl, (panel.x+40, y))
            surf.blit(val, (panel.right - val.get_width()-40, y))
            pygame.draw.line(surf, (40,30,70),
                             (panel.x+30,y+34),(panel.right-30,y+34), 1)

        # Rank / record badge
        if self.is_new_record:
            rec = font_sm.render("★ NEW RECORD!", True, (255,220,50))
            surf.blit(rec, (cx - rec.get_width()//2, panel.y+260))
        elif self.rank:
            rec = font_xs.render(f"Rank #{self.rank} on this mode", True, C_GRAY)
            surf.blit(rec, (cx - rec.get_width()//2, panel.y+260))

        if self.prestige_available:
            pt = font_xs.render("★ Prestige available! Reset for permanent bonuses.",
                                True, (255,220,50))
            surf.blit(pt, (cx - pt.get_width()//2, panel.y+282))

        for b in self.btns:
            b.draw(surf)

