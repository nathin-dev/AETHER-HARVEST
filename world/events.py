"""
World events system — random dramatic events that change gameplay temporarily.
Events fire every few waves to keep the game fresh and unpredictable.
"""
import pygame, math, random
from utils.constants import (C_DANGER, C_ACCENT, C_SUCCESS, C_SECONDARY,
                              C_WHITE, C_GRAY, WIDTH, HEIGHT)
from utils.math_utils import smooth_step
from engine.renderer import draw_panel


EVENTS = {
    "ore_storm": {
        "name":     "ORE STORM",
        "desc":     "Crystals rain from the void for 20 seconds!",
        "color":    (120, 60, 255),
        "icon":     "💎",
        "duration": 20.0,
        "effect":   "triple_ore_spawn",
    },
    "void_surge": {
        "name":     "VOID SURGE",
        "desc":     "Enemy waves double in size for 30 seconds!",
        "color":    (255, 70, 90),
        "icon":     "☠",
        "duration": 30.0,
        "effect":   "double_enemies",
    },
    "aether_rain": {
        "name":     "AETHER RAIN",
        "desc":     "All resources doubled for 15 seconds!",
        "color":    (255, 200, 50),
        "icon":     "✦",
        "duration": 15.0,
        "effect":   "double_resources",
    },
    "crystal_nova": {
        "name":     "CRYSTAL NOVA",
        "desc":     "Every ore on the map explodes in value!",
        "color":    (60, 220, 200),
        "icon":     "⚡",
        "duration": 0.0,   
        "effect":   "instant_nova",
    },
    "gravity_well": {
        "name":     "GRAVITY WELL",
        "desc":     "All ores pulled toward you for 10 seconds!",
        "color":    (180, 100, 255),
        "icon":     "🌀",
        "duration": 10.0,
        "effect":   "ore_gravity",
    },
    "blood_moon": {
        "name":     "BLOOD MOON",
        "desc":     "Enemies are deadly but drop 5× resources!",
        "color":    (200, 30, 60),
        "icon":     "◉",
        "duration": 25.0,
        "effect":   "blood_moon",
    },
}

EVENT_WEIGHTS = {
    "ore_storm":   30,
    "void_surge":  20,
    "aether_rain": 25,
    "crystal_nova":15,
    "gravity_well":20,
    "blood_moon":  10,
}


class WorldEvent:
    def __init__(self, event_id):
        cfg           = EVENTS[event_id]
        self.id       = event_id
        self.name     = cfg["name"]
        self.desc     = cfg["desc"]
        self.color    = cfg["color"]
        self.icon     = cfg["icon"]
        self.duration = cfg["duration"]
        self.effect   = cfg["effect"]
        self.time_left= cfg["duration"]
        self.active   = True
        self.announce = 3.5  

    @property
    def ratio(self):
        if self.duration <= 0: return 0.0
        return max(0.0, self.time_left / self.duration)

    def tick(self, dt):
        self.announce = max(0.0, self.announce - dt)
        if self.duration > 0:
            self.time_left -= dt
            if self.time_left <= 0:
                self.active = False


class EventSystem:
    def __init__(self):
        self.current_event  = None
        self.event_timer    = random.uniform(45, 75)  # first event
        self.event_cooldown = 0.0
        self.history        = []

    def update(self, dt):
        self.event_timer    -= dt
        self.event_cooldown -= dt

        if self.current_event:
            self.current_event.tick(dt)
            if not self.current_event.active:
                self.history.append(self.current_event.id)
                self.current_event  = None
                self.event_cooldown = 20.0
                self.event_timer    = random.uniform(40, 80)

        if self.event_timer <= 0 and self.event_cooldown <= 0 and not self.current_event:
            self._trigger_random()

    def _trigger_random(self):
        ids     = list(EVENT_WEIGHTS.keys())
        weights = [EVENT_WEIGHTS[i] for i in ids]
        eid     = random.choices(ids, weights=weights)[0]
        self.current_event = WorldEvent(eid)
        self.event_timer   = random.uniform(50, 90)

    def _has(self, effect):
        return (self.current_event is not None and
                self.current_event.active and
                self.current_event.effect == effect)

    @property
    def triple_ore_spawn(self):   return self._has("triple_ore_spawn")
    @property
    def double_enemies(self):     return self._has("double_enemies")
    @property
    def double_resources(self):   return self._has("double_resources")
    @property
    def ore_gravity(self):        return self._has("ore_gravity")
    @property
    def blood_moon(self):         return self._has("blood_moon")

    def get_instant_nova(self):
        """Returns True once when crystal_nova triggers."""
        if self._has("instant_nova"):
            self.current_event.active = False
            return True
        return False

    def get_resource_mult(self):
        mult = 1.0
        if self.double_resources: mult *= 2.0
        if self.blood_moon:       mult *= 5.0
        return mult

    def get_enemy_dmg_mult(self):
        return 2.5 if self.blood_moon else 1.0

    def draw_announcement(self, surf, font_lg, font_md, font_xs):
        ev = self.current_event
        if not ev or ev.announce <= 0:
            return

        t     = ev.announce / 3.5
        alpha = int(255 * smooth_step(min(t*3, 1.0)) * smooth_step(t*1.5))

        bar_h = 90
        bar_y = HEIGHT//2 - bar_h//2 - 40

        bar = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
        bar.fill((*ev.color, min(60, alpha//3)))
        surf.blit(bar, (0, bar_y))

        for i in range(0, bar_h, 4):
            scan = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            scan.fill((*ev.color, min(20, alpha//6)))
            surf.blit(scan, (0, bar_y + i))

        icon_s = font_lg.render(ev.icon + "  " + ev.name, True, ev.color)
        icon_s.set_alpha(alpha)
        surf.blit(icon_s, (WIDTH//2 - icon_s.get_width()//2, bar_y + 10))

        desc_s = font_md.render(ev.desc, True, C_WHITE)
        desc_s.set_alpha(alpha)
        surf.blit(desc_s, (WIDTH//2 - desc_s.get_width()//2, bar_y + 50))

    def draw_active_banner(self, surf, font_xs):
        ev = self.current_event
        if not ev or not ev.active or ev.duration <= 0:
            return

        import pygame
        col  = ev.color
        x    = WIDTH//2
        y    = HEIGHT - 26

        bar_w = 200
        bx    = x - bar_w//2

        bg = pygame.Surface((bar_w + 24, 18), pygame.SRCALPHA)
        bg.fill((*col, 30))
        surf.blit(bg, (bx - 12, y - 2))

        pygame.draw.rect(surf, (20,14,42), (bx, y, bar_w, 8), border_radius=4)
        fill_w = int(bar_w * ev.ratio)
        if fill_w > 0:
            pygame.draw.rect(surf, col, (bx, y, fill_w, 8), border_radius=4)

        lbl = font_xs.render(f"{ev.icon} {ev.name}  {ev.time_left:.0f}s", True, col)
        surf.blit(lbl, (x - lbl.get_width()//2, y + 10))

