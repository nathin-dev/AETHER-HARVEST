"""

Enemy entities for Infinite Harvest
"""

import pygame
import math
import random
from utils.constants import ENEMY_TYPES, C_DANGER
from utils.math_utils import normalize, dist, lerp
from engine.renderer import draw_glow_circle

class Enemy:
    def __init__(self, x, y, enemy_type="void_wisp"):
        cfg = ENEMY_TYPES[enemy_type]
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.type = enemy_type
        self.color = cfg["color"]
        self.speed = cfg["speed"]
        self.hp = cfg["hp"]
        self.max_hp = cfg["hp"]
        self.dmg = cfg["damage"]
        self.reward = cfg["reward"]
        self.size = cfg["size"]

        self.alive = True 
        self.pulse = random.uniform(0, math.tau)
        self.angle = 0.0
        self.hit_flash = 0.0 # Seconds of white flash
        self.spawn_anim = 1.0  # scale up from 0

    def update(self, dt, target_x, target_y):
        self.pulse += dt * 2.5
        self.spawn_anim = min(1.0, self.spawn_anim + dt * 3)
        self.hit_flash = max(0.0, self.hit_flash - dt)

        # Chase player
        dx, dy = normalize(target_x - self.x, target_y - self.y)
        self.vx = lerp(self.vx, dx * self.speed, 0.1)
        self.vy = lerp(self.vy, dy * self.speed, 0.1)

        self.x += self.vx * dt 
        self.y += self.vy * dt

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 0.15
        if self.hp <= 0:
            self.alive = False 
            return True
        return False
    
    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        pulse = abs(math.sin(self.pulse))
        scale = self.spawn_anim
        radius = max(1, int(self.size * scale))

        # Glow
        glow_s = pygame.Surface((radius * 6, radius *6), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*self.color, 40),
                           (radius * 3, radius * 3), radius *3)
        surf.blit(glow_s, (sx - radius * 3, sy - radius * 3),
                  special_flags=pygame.BLEND_ADD)
        
        #Body
        color = (255, 255, 255) if self.hit_flash > 0 else self.color 
        pygame.draw.circle(surf, color, (sx, sy), radius)

        # Spike decoration for larger enemies
        if self.size >= 20:
            for i in range(6):
                a = self.pulse * 0.5 + i * math.tau / 6
                ex = sx + int(math.cos(a) * (radius + 5))
                ey = sy + int(math.sin(a) * (radius + 5))
                pygame.draw.line(surf, (*self.color, 180), (sx, sy), (ex, ey), 1)

        # HP BAR 
        bar_w = radius * 2
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surf, (40, 30, 60), (sx - radius, sy - radius - 8, bar_w, 4))
        pygame.draw.rect(surf, C_DANGER, (sx - radius, sy - radius - 8, int(bar_w * hp_ratio),4))


class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.wave = 0
        self.spawn_timer = 15.0 # First wave sonner
        self.spawn_interval = 18.0

    def update (self, dt, player, particles, floating_texts, font_sm):
        self.spawn_timer -= dt 
        if self.spawn_timer <= 0:
            self._spawn_wave(player.x, player.y)
            self.spawn_timer =  self.spawn_interval
            self.spawn_interval = max(8.0, self.spawn_interval - 0.5)

        reward_total = 0
        killed = []
        for enemy in self.enemies:
            if not enemy.alive:
                killed.append(enemy)
                continue
            enemy.update(dt, player.x, player.y)

            # Collsion With Player
            d = dist(enemy.x, enemy.y, player.x, player.y)
            if d < enemy.size + player.RADIUS:
                if player.take_damage(enemy.dmg):
                    particles.burst(player.x, player.y, (255, 80, 80), count=10)
                enemy.alive = False 
                killed.append(enemy)
            
            for e in killed:
                if e in self.enemies:
                    self.enemies.remove(e)
                    if not e.alive and e.hp <= 0:
                        reward_total += e.reward
                        particles.burst(e.x, e.y, e.color, count=15, speed=150)
                        floating_texts.add(e.x, e.y - 20, f"+{e.reward}✦",
                                        font_sm, (255, 220, 80))
            return reward_total 
        
    def _spawn_wave(self, px, py):
        self.wave +=1
        count = 2 + self.wave // 2
        from utils.math_utils import random_on_ring
        from utils.constants import WIDTH, HEIGHT, ENEMY_TYPES
        import random 

        weights  = list(ENEMY_TYPES.keys())
        for _ in range(count):
            ex, ey = random_on_ring(px, py, 300, 500)
            ex = max(30, min(HEIGHT *2 - 30, ex))
            ey = max(30, min(HEIGHT * 2 - 30, ey))
            if self.wave < 3:
                etype = "void_wisp"
            else:
                etype = random.choices(
                    ["void_wisp", "crystal_golem", "void_hunter"],
                    weights=[5, 2, 2]
                )[0]
            self.enemies.append(Enemy(ex, ey, etype))

    
    def draw(self, surf, cam):
        for e in self.enemies:
            if e.alive:
                e.draw(surf, cam)

                        
                    