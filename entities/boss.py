"""
Boss system for AETHER HARVEST
Epic boss encounters every 5 waves.
"""
import pygame
import math
import random
from utils.constants import C_DANGER, C_ACCENT, C_WHITE, WIDTH, HEIGHT
from utils.math_utils import normalize, dist, lerp
from engine.renderer import draw_glow_circle, draw_panel


BOSS_WAVE_INTERVAL = 5  

BOSS_TYPES = {
    "void_colossus": {
        "name":   "VOID COLOSSUS",
        "color":  (160,  50, 255),
        "glow":   (200, 100, 255),
        "size":   52,
        "hp":     500,
        "speed":  55,
        "damage": 25,
        "reward": 200,
        "phases": 3,
    },
    "crystal_titan": {
        "name":   "CRYSTAL TITAN",
        "color":  (50, 200, 180),
        "glow":   (100, 255, 230),
        "size":   48,
        "hp":     400,
        "speed":  40,
        "damage": 20,
        "reward": 160,
        "phases": 2,
    },
    "aether_wraith": {
        "name":   "AETHER WRAITH",
        "color":  (255,  80, 120),
        "glow":   (255, 150, 180),
        "size":   38,
        "hp":     280,
        "speed":  100,
        "damage": 15,
        "reward": 140,
        "phases": 2,
    },
}


class Boss:
    def __init__(self, x, y, boss_type):
        cfg = BOSS_TYPES[boss_type]
        self.x        = float(x)
        self.y        = float(y)
        self.vx = self.vy = 0.0
        self.type     = boss_type
        self.name     = cfg["name"]
        self.color    = cfg["color"]
        self.glow_col = cfg["glow"]
        self.size     = cfg["size"]
        self.max_hp   = cfg["hp"]
        self.hp       = float(cfg["hp"])
        self.speed    = cfg["speed"]
        self.dmg      = cfg["damage"]
        self.reward   = cfg["reward"]
        self.phases   = cfg["phases"]

        self.alive      = True
        self.pulse      = random.uniform(0, math.tau)
        self.angle      = 0.0
        self.hit_flash  = 0.0
        self.spawn_anim = 0.0    
        self.phase      = 1       
        self.orbit_ents = []      
        self.shoot_timer= 0.0
        self.rage_mode  = False

        
        self._dash_timer = 0.0
        self._dash_cd    = 3.0
        self._dashing    = False
        self._dash_vx = self._dash_vy = 0.0
        self._dash_dur   = 0.4

    @property
    def hp_ratio(self):
        return self.hp / self.max_hp

    def _update_phase(self):
        if self.phases >= 3:
            if self.hp_ratio < 0.33:
                self.phase = 3
            elif self.hp_ratio < 0.66:
                self.phase = 2
            else:
                self.phase = 1
        elif self.phases >= 2:
            self.phase = 1 if self.hp_ratio > 0.5 else 2
        self.rage_mode = self.phase >= 2

    def update(self, dt, player, particles):
        self.pulse      += dt * (2.0 + self.phase * 0.5)
        self.spawn_anim  = min(1.0, self.spawn_anim + dt * 1.5)
        self.hit_flash   = max(0.0, self.hit_flash - dt)
        self._update_phase()

        speed_mult = 1.0 + (self.phase - 1) * 0.4

        
        self._dash_cd = max(0, self._dash_cd - dt)
        if self._dashing:
            self._dash_timer -= dt
            self.x += self._dash_vx * BOSS_DASH_SPEED * dt
            self.y += self._dash_vy * BOSS_DASH_SPEED * dt
            if self._dash_timer <= 0:
                self._dashing = False
                self._dash_cd = max(1.5, 3.0 - self.phase * 0.5)
        else:
            if self._dash_cd <= 0:
                dx, dy = normalize(player.x - self.x, player.y - self.y)
                self._dash_vx  = dx
                self._dash_vy  = dy
                self._dash_timer = self._dash_dur
                self._dashing  = True
                particles.burst(self.x, self.y, self.glow_col, count=20, speed=150)
            else:
               
                dx, dy = normalize(player.x - self.x, player.y - self.y)
                self.vx = lerp(self.vx, dx * self.speed * speed_mult, 0.08)
                self.vy = lerp(self.vy, dy * self.speed * speed_mult, 0.08)
                self.x += self.vx * dt
                self.y += self.vy * dt

        if random.random() < 0.3:
            angle = random.uniform(0, math.tau)
            r     = self.size * self.spawn_anim
            particles.emit(
                self.x + math.cos(angle) * r,
                self.y + math.sin(angle) * r,
                math.cos(angle) * 30, math.sin(angle) * 30,
                life=0.5, color=self.glow_col,
                end_color=(20, 10, 40), size=3, glow=True
            )

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 0.1
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        scale  = self.spawn_anim
        radius = max(1, int(self.size * scale))
        pulse  = abs(math.sin(self.pulse))

      
        glow_r = radius + 24 + int(pulse * 10)
        gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.glow_col, 25), (glow_r, glow_r), glow_r)
        pygame.draw.circle(gs, (*self.glow_col, 50), (glow_r, glow_r), radius + 8)
        surf.blit(gs, (sx - glow_r, sy - glow_r), special_flags=pygame.BLEND_ADD)

        for ring_i in range(self.phase):
            ring_r = radius + 14 + ring_i * 10
            angle  = self.pulse * (0.5 + ring_i * 0.3)
            for j in range(6):
                a = angle + j * math.tau / 6
                ex = sx + int(math.cos(a) * ring_r)
                ey = sy + int(math.sin(a) * ring_r)
                col_a = 100 + ring_i * 40
                pygame.draw.circle(surf, (*self.glow_col, col_a), (ex, ey), 4)

        body_col = (255, 255, 255) if self.hit_flash > 0 else self.color
        pygame.draw.circle(surf, body_col, (sx, sy), radius)

        inner_r = radius - 8
        if inner_r > 2:
            pygame.draw.circle(surf, self.glow_col, (sx, sy), inner_r)

        self._draw_boss_bar(surf)

    def _draw_boss_bar(self, surf):
        bar_rect = pygame.Rect(WIDTH // 4, 12, WIDTH // 2, 22)
        draw_panel(surf, bar_rect, color=(20, 10, 40), border=self.color, alpha=220, radius=6)

        fill_w = int(bar_rect.width * self.hp_ratio)
        if fill_w > 0:
            if self.phase == 3:
                fill_col = C_DANGER
            elif self.phase == 2:
                fill_col = C_ACCENT
            else:
                fill_col = self.color
            pygame.draw.rect(surf, fill_col,
                             (bar_rect.x, bar_rect.y, fill_w, bar_rect.height),
                             border_radius=6)

        for p in range(1, self.phases):
            nx = bar_rect.x + int(bar_rect.width * p / self.phases)
            pygame.draw.line(surf, (255, 255, 255),
                             (nx, bar_rect.y), (nx, bar_rect.bottom), 2)

        pygame.draw.rect(surf, self.color, bar_rect, 1, border_radius=6)

        import pygame as _pg
        _pg_font = pygame.font.SysFont("Arial", 13)
        name_surf = _pg_font.render(f"  {self.name}   HP {int(self.hp)}/{int(self.max_hp)}", True, C_WHITE)
        surf.blit(name_surf, (bar_rect.x + 8, bar_rect.y + 4))


BOSS_DASH_SPEED = 400


class BossManager:
    def __init__(self):
        self.boss         = None
        self.intro_timer  = 0.0  
        self.pending_type = None

    def check_spawn(self, wave, player_x, player_y):
        """Call when a new wave starts. Returns True if a boss is being introduced."""
        if wave > 0 and wave % BOSS_WAVE_INTERVAL == 0 and self.boss is None:
            self.pending_type = random.choice(list(BOSS_TYPES.keys()))
            self.intro_timer  = 2.5
            return True
        return False

    def update(self, dt, player, particles, floating_texts, font_md):
        reward = 0

        if self.intro_timer > 0:
            self.intro_timer -= dt
            if self.intro_timer <= 0 and self.pending_type:
                angle = random.uniform(0, math.tau)
                bx = player.x + math.cos(angle) * 400
                by = player.y + math.sin(angle) * 400
                from systems.resource_system import WORLD_W, WORLD_H
                bx = max(80, min(WORLD_W - 80, bx))
                by = max(80, min(WORLD_H - 80, by))
                self.boss = Boss(bx, by, self.pending_type)
                self.pending_type = None
                particles.burst(bx, by, BOSS_TYPES[self.boss.type]["glow"],
                                count=50, speed=200, life=1.5)

        if self.boss and self.boss.alive:
            self.boss.update(dt, player, particles)

            d = dist(self.boss.x, self.boss.y, player.x, player.y)
            if d < self.boss.size + player.RADIUS:
                if player.take_damage(self.boss.dmg):
                    particles.burst(player.x, player.y, C_DANGER, count=15)

            if not self.boss.alive:
                reward = self.boss.reward
                particles.burst(self.boss.x, self.boss.y,
                                self.boss.glow_col, count=80, speed=250, life=2.0)
                floating_texts.add(self.boss.x, self.boss.y - 40,
                                   f"BOSS SLAIN  +{reward}✦",
                                   font_md, C_ACCENT, speed=-60, life=3.0)
                self.boss = None

        elif self.boss and not self.boss.alive:
            self.boss = None

        return reward

    def draw(self, surf, cam):
        if self.boss and self.boss.alive:
            self.boss.draw(surf, cam)

    def draw_intro(self, surf, font_lg, font_md):
        """Draw dramatic boss intro overlay."""
        if self.intro_timer <= 0 or not self.pending_type:
            return
        cfg   = BOSS_TYPES[self.pending_type]
        t     = self.intro_timer / 2.5
        alpha = int(200 * (1 - abs(t - 0.5) * 2))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(180, alpha * 2)))
        surf.blit(overlay, (0, 0))

        warn = font_lg.render("⚠  BOSS INCOMING  ⚠", True, C_DANGER)
        warn.set_alpha(alpha)
        surf.blit(warn, (WIDTH // 2 - warn.get_width() // 2, HEIGHT // 2 - 40))

        name = font_md.render(cfg["name"], True, cfg["glow"])
        name.set_alpha(alpha)
        surf.blit(name, (WIDTH // 2 - name.get_width() // 2, HEIGHT // 2 + 10))

