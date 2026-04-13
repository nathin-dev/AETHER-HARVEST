"""
Particle system for AETHER HARVEST
"""
import pygame
import random
import math
from utils.math_utils import lerp, ease_out


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "color", "end_color", "size", "end_size",
                 "gravity", "fade", "glow")

    def __init__(self, x, y, vx, vy, life, color,
                 end_color=None, size=4, end_size=0,
                 gravity=0, fade=True, glow=False):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.life        = float(life)
        self.max_life    = float(life)
        self.color       = color
        self.end_color   = end_color or color
        self.size        = float(size)
        self.end_size    = float(end_size)
        self.gravity     = gravity
        self.fade        = fade
        self.glow        = glow

    @property
    def progress(self):
        return 1.0 - self.life / self.max_life

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= dt

    def draw(self, surf, cam_x=0, cam_y=0):
        if not self.alive:
            return
        t    = self.progress
        r    = int(lerp(self.color[0], self.end_color[0], t))
        g    = int(lerp(self.color[1], self.end_color[1], t))
        b    = int(lerp(self.color[2], self.end_color[2], t))
        a    = int(255 * (1 - ease_out(t))) if self.fade else 255
        size = max(1, int(lerp(self.size, self.end_size, t)))

        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        if self.glow:
            glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (r, g, b, a // 4), (size * 3, size * 3), size * 3)
            pygame.draw.circle(glow_surf, (r, g, b, a // 2), (size * 3, size * 3), size * 2)
            surf.blit(glow_surf, (sx - size * 3, sy - size * 3),
                      special_flags=pygame.BLEND_ADD)

        if a < 255:
            col_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(col_surf, (r, g, b, a), (size, size), size)
            surf.blit(col_surf, (sx - size, sy - size))
        else:
            pygame.draw.circle(surf, (r, g, b), (sx, sy), size)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, vx, vy, life, color, **kwargs):
        self.particles.append(Particle(x, y, vx, vy, life, color, **kwargs))

    def burst(self, x, y, color, count=12, speed=120,
              life=0.6, size=5, glow=True, spread=math.tau):
        for _ in range(count):
            angle = random.uniform(0, spread)
            spd   = random.uniform(speed * 0.4, speed)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd
            self.emit(x, y, vx, vy,
                      life=random.uniform(life * 0.5, life),
                      color=color,
                      end_color=(20, 10, 40),
                      size=random.uniform(size * 0.5, size),
                      end_size=0,
                      glow=glow)

    def trail(self, x, y, color, vx=0, vy=0, life=None):
        self.emit(
            x + random.uniform(-4, 4),
            y + random.uniform(-4, 4),
            vx * 0.1 + random.uniform(-20, 20),
            vy * 0.1 + random.uniform(-20, 20),
            life=random.uniform(0.2, 0.5) if life is None else life,
            color=color,
            end_color=(20, 10, 40),
            size=random.uniform(2, 5),
            glow=True
    )

    def text_pop(self, x, y, text, font, color, surf):
        pass

    def update(self, dt):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update(dt)

    def draw(self, surf, cam_x=0, cam_y=0):
        for p in self.particles:
            p.draw(surf, cam_x, cam_y)


class FloatingText:
    def __init__(self, x, y, text, font, color=(255, 255, 255), speed=-80, life=1.2):
        self.x, self.y  = float(x), float(y)
        self.text        = text
        self.font        = font
        self.color       = color
        self.speed       = speed
        self.life        = life
        self.max_life    = life

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.y   += self.speed * dt
        self.life -= dt

    def draw(self, surf, cam_x=0, cam_y=0):
        t     = 1.0 - self.life / self.max_life
        alpha = int(255 * (1 - ease_out(t)))
        label = self.font.render(self.text, True, self.color)
        label.set_alpha(alpha)
        surf.blit(label, (int(self.x - label.get_width() // 2 - cam_x),
                           int(self.y - cam_y)))


class FloatingTextManager:
    def __init__(self):
        self.texts = []

    def add(self, x, y, text, font, color=(255, 255, 255), speed=-80, life=1.2):
        self.texts.append(FloatingText(x, y, text, font, color, speed, life))

    def update(self, dt):
        self.texts = [t for t in self.texts if t.alive]
        for t in self.texts:
            t.update(dt)

    def draw(self, surf, cam_x=0, cam_y=0):
        for t in self.texts:
            t.draw(surf, cam_x, cam_y)
