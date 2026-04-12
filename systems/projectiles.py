"""

projectile system for AETHER HARVEST
"""

import pygame 
import math 
import random 
from utils.math_utils import normalize, dist 

class Projectile:
    __slots__ = ("x", "y", "vx", "vy", "damage", "speed",
                 "color", "glow", "radius", "life", "alive", "pierce")
    
    def __init__(self, x, y, dx, dy, damage=10, speed=420,
                 color=(120, 60, 255), glow=(180, 100, 255),
                 radius=5, life=1.8, pierce=0):
        self.x = float(x)
        self.y = float(y)
        nx, ny = normalize(dx, dy)
        self.vx = nx * speed
        self.vy = ny * speed 
        self.color = color 
        self.speed  = speed 
        self.damage = damage 
        self.glow = glow 
        self.radius = radius 
        self.life = life 
        self.alive = True 
        self.pierce = pierce 

    
    def update(self, dt):
        self.x += self.vx * dt 
        self.y += self.vy * dt 
        self.life -= dt 
        if self.life <= 0:
            self.alive = False 

    def draw(self, surf, cam):
        if not self.alive:
            return 
        sx, sy  = cam.world_to_screen(self.x, self.y)

        
        trail_len = 3 
        for i in range(trail_len, 0, -1):
            tx = sx - int(self.vx * 0.003 * i)
            ty = sy - int(self.vy * 0.003 * i)
            a = int(120 // (i+1))
            r  = max(1, self.radius - i)
            gs = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.glow, a), (r + 1, r + 1), r)
            surf.blit(gs, (tx - r - 1, ty - r -1 ), special_flags=pygame.BLEND_ADD)

       
        pygame.draw.circle(surf, self.color, (sx, sy), self.radius)
        pygame.draw.circle(surf, (255, 255, 255), (sx, sy), max(1, self.radius -2 ))

class ProjectileSystem:
    def __init__(self):
        self.projectiles = []
        self.shoot_cd = 0.0
        self.shoot_range = 0.45  
        self.damage = 10
        self.pierce = 0 

    def try_shoot(self, player_x, player_y, target_x, target_y, dt, upgrades_lvl=0):
        """ call every frame with mouse world position. Fires if cooldown ready +. """
        self.shoot_cd = max(0, self.shoot_cd - dt)
       
        self.damage = 10 + upgrades_lvl * 5 
        self.pierce = upgrades_lvl // 3
        rate_mult = max(0.4, 1.0 - upgrades_lvl * 0.05)
        self.shoot_rate = 0.45 * rate_mult 

    def shoot(self, px, py, tx, ty, upgrades_lvl=0):
        """Immediately fire a bolt."""
        if self.shoot_cd > 0:
            return False 
        self.shoot_cd =  self.shoot_rate 
        dmg = 10 + upgrades_lvl * 5
        pierce = upgrades_lvl // 3
        self.projectiles.append(Projectile(
            px, py, tx - px, ty - py,
            damage=dmg, pierce=pierce,
            color=(120, 60, 255), glow=(200, 120, 255),
            radius=5, life=1.8
        ))
        return True 
    
    def shoot_spread(self, px, py, tx, ty, count=3, upgrades_lvl=0):
        """Fire a spread of bolts ( for charged shot). """
        if self.shoot_cd > 0:
            return False 
        self.shoot_cd  = self.shoot_rate * 1.5
        base_angle = math.atan2(ty - py, tx - px)
        spread = math.radians(20)
        dmg = 15 + upgrades_lvl * 7
        for i in range(count):
            offset = (i - count // 2) * spread / max(1, count - 1)
            angle = base_angle + offset 
            dx, dy = math.cos(angle), math.sin(angle)
            self.projectiles.append(Projectile(
                px, py, dx, dy,
                damage=dmg, color=(255, 140, 50),
                glow=(255, 200, 100), radius=6, life=1.5
            ))
        return True 
    
    def update(self, dt, enemies, boss_mgr, particles):
        """Move projectiles, check enemy hits. Returns total damage dealt."""
        total_dmg = 0
        dead = []
        for proj in self.projectiles:
            if not  proj.alive:
                dead.append(proj)
                continue 
            proj.update(dt)
            if not proj.alive:
                dead.append(proj)
                continue 

           
            hits =0 
            for enemy in enemies:
                if not enemy.alive:
                    continue 
                d = dist(proj.x, proj.y, enemy.x, enemy.y)
                if d < proj.radius + enemy.size:
                    killed = enemy.take_damage(proj.damage)
                    total_dmg += proj.damage 
                    particles.burst(proj.x, proj.y, proj.glow,
                                    count=6, speed=80, life=0.3, size=3)
                    hits += 1
                    if hits > proj.pierce:
                        proj.alive = False 
                        dead.append(proj)
                        break 

          
            if proj.alive and boss_mgr.boss and boss_mgr.boss.alive:
                b =  boss_mgr.boss
                d = dist(proj.x, proj.y, b.x, b.y)
                if d < proj.radius + b.size:
                    b.take_damage(proj.damage)
                    total_dmg += proj.damage 
                    particles.burst(proj.x, proj.y, proj.glow, count=10, speed=120, life=0.4, size=4)
                    proj.alive = False 
                    dead.append(proj)

        for p in dead:
            if p in self.projectiles:
                self.projectiles.remove(p)

        return total_dmg    
    
    def draw(self, surf, cam):
        for p in self.projectiles:
            p.draw(surf, cam)

