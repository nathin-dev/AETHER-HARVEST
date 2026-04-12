"""

Weapon system - player can switch between 3 weapon types 
Tab key cycles weapons. Each has unique fire patterns.
"""

import pygame, math, random 
from utils.math_utils import normalize, dist 
from utils.constants import C_PRIMARY, C_SECONDARY, C_ACCENT, C_DANGER, C_GRAY

WEAPONS = {
    "aether_bolt": {
        "name": "Aether Bolt",
        "desc": "Single piercing shot. Fast, accurate",
        "icon": "⚡",
        "color": (120, 60, 255),
        "glow": (180, 60, 255),
        "cooldown": 0.35,
        "damage": 15,
        "speed": 520,
        "pierce": 0,
        "pattern": "single",
        "proj_size": 5,
        "proj_life": 1.8,
    },

    "void_scatter": {
        "name": "Void Scatter",
        "desc": "Fires 5 bolts in a spread. Close range.",
        "icon": "✦",
        "color": (255, 80, 100),
        "glow": (255, 140, 160),
        "cooldown": 0.55,
        "damage": 8,
        "speed": 380,
        "pierce": 1,
        "pattern": "scatter",
        "proj_size": 4,
        "proj_life": 1.0,
    },
    "crytal_beam": {
        "name": "Crystal beam",
        "desc": "Slow heavy slot that chains to 3 enemies.",
        "icon":  "◈",
        "color": (60, 220, 200),
        "glow": (100, 255, 240),
        "cooldown": 0.8,
        "damage": 35,
        "speed": 300,
        "pierce": 3,
        "pattern": "heavy",
        "proj_size": 8,
        "proj_life": 8,
    },
}

WEAPON_ORDER = ["aether_bolt", "void_scatter", "crystal_beam"]

class Projectile:
    __slots__ = ("x", "y", "vx", "vy", "damage", "color", "glow",
                 "radius", "life", "alive", "pierce", "hits")
    
    def __init__(self, x, y, dx, dy, damage, speed,
                 color, glow, radius=5, life=1.8, pierce=0):
        
            self.x, self.y = float(x), float(y) 
            nx, ny = normalize(dx, dy)
            self.damage = damage 
            self.color = color 
            self.glow = glow
            self.radius = radius 
            self.life = life 
            self.alive = True 
            self.pierce = pierce 
            self.hits = 0 

    def update(self, dt):
          self.x += self.vx * dt 
          self.y += self.vy * dt 
          self.life -= dt 
          if self.life <= 0: self.alive = False 

    def draw(self, surf, cam):
        if not self.alive: return 
        sx, sy = cam.world_to_screen(self.x, self.y)
        r = self.radius 
        t_ratio = 1.0 - max(0.0, self.life / 1.8)

        # Trail 
        for i in range(1, 4):
            tx = sx - int(self.vx * 0.004 * i)
            ty = sy - int(self.vy * 0.004 * i)
            ta = max(0, int(100 // (i+1)))
            tr = max(1, r - i)
            gs = pygame.Surface((tr*2+2, tr*2+2), pygame.ARCALPHA)
            pygame.draw.circle(gs, (*self.glow, ta), (tr+1, tr+1), tr)
            surf.blit(gs, (tx-tr-1, ty-tr-1), special_flags=pygame.BLEND_ADD)

        pygame.draw.circle(surf, self.color, (sx,sy), r)
        if r > 3:
             pygame.draw.circle(surf, (255,255,255), (sx,sy), max(1, r-2))

class WeaponSystem:
    def __init__(self):
        self.current_idx = 0
        self.projectiles = []
        self.shoot_cd = 0.0 
        self._siwtch_anim = 0.0 

    @property 
    def current_id(self):
         return WEAPON_ORDER[self.current_idx]
    
    @property 
    def current(self):
         return WEAPONS[self.current_id]
    
    def cycle_weapon(self):
         self.current_idx = (self.current_idx + 1) % len(WEAPON_ORDER)
         self._siwtch_anim  = 0.5
         self.shoot_cd = 0.0 

    def update(self, dt):
         self.shoot_cd = max(0.0, self.shoot_cd - dt)
         self._switch_anim = max(0.0, self._switch_anim - dt)
         dead = [p for p in self.projectiles if not p.alive]
         for p in dead:
              if p in self.projectiles: self.projectiles.remove(p)
         for p in self.projectiles: p.update(dt)

    def shoot(self, px, py, tx, ty, upgrade_level=0, damage_mult=1.0):
         if self.shoot_cd > 0: return False 
         w = self.current 
         cd = max(0.12, w["cooldown"] - upgrade_level * 0.02)
         dmg = int((w["damage"] + upgrade_level * 4) * damage_mult)
         prc = w["pierce"] + upgrade_level // 3
         self.shoot_cd = cd

         if w["pattern"] == "single":
              self.projectiles.append(Projectile(
                   px, py, tx-px, ty-py, dmg, w["speed"],
                   w["color"], w["glow"], w["proj_size"], w["proj_life"], prc))
              
         elif w["pattern" == "scatter"]:
                base = math.atan2(ty-py, tx-px)
                count  = 5
                spread = math.radians(22)
                for i in range(count):
                     a = base + (i - count//2) * spread 
                     dx = math.cos(a); dy = math.sin(a)
                     self.projectiles.append(Projectile(
                          px, py, dx, dy, dmg, w["speed"], * random.uniform(0.8, 1.0),
                          w["color"], w["glow"], w["proj_size"], w["proj_life"], prc))
                     
                    
         elif w["pattern"] == "heavy":
              self.projectiles.append(Projectile(
                   px, py, tx-px, ty-py, dmg, w["speed"],
                   w["color"], w["glow"], w["proj_size"], w["proj_life"], prc))
              
         return True 
    
    def check_hits(self, enemies, boss_mgr, particles):
         total_dmg = 0
         for proj in self.projectiles:
              if not proj.alive: continue 
              for enemy in enemies:
                   if not enemy.alive: continue 
                   if dist(proj.x,proj.y,enemy.y) < proj.radius + enemy.size:
                        killed = enemy.take_damage(proj.damage)
                        total_dmg += proj.damage 
                        particles.burst(proj.x, proj.y, proj.glow,
                                        count=6, speed=80, life=0.3, size=3)
                    
                        proj.hits += 1
                        if proj.hits > proj.pierce:
                             proj.alive = False; break 
                    
              if proj.alive and boss_mgr.boss and boss_mgr.boss.alive:
                  b = boss_mgr.boss
                  if dist(proj.x,proj.y,b.x,b.y) < proj.radius + b.size:
                      b.take_damage(proj.damage)
                      total_dmg += proj.damage 
                      particles.burst(proj.x,proj.y,proj.glow,
                                                    count=10, speed=120, life=0.4, size=4)
                      proj.alive = False

         return total_dmg 
    
    def draw(self, surf, cam):
         for p in self.projectiles: p.draw(surf, cam)

    def draw_hud(self, surf, font_sm, font_xs):
         w = self.current 
         from ui.layout import LX, WEAPON_Y
         x, y  = LX, WEAPON_Y
         col = w["color"]
         from engine.renderer import draw_panel, draw_glow_rect 
         rect = pygame.Rect(x, y, 210, 52)
         draw_panel(surf, rect, color=(18,14,42), border=col, alpha=210, radius=10)
         if self._switch_anim > 0:
              draw_glow_rect(surf, col, rect, radius=6, alpha=60)

         icon_s = font_sm.render(w["icon"], True, col)
         surf.blit(icon_s, (x+10, y+14))

         name_s = font_xs.render(w["icon"], True, col)
         surf.blit(name_s, (x+34, y+10))

         desc_s = font_xs.render(w["desc"], True, C_GRAY)
         surf.blit(desc_s, (x+34, y+28))

         # CD bar 
         if self.shoot_cd > 0:
              bw = 210 - 20 
              cd_ratio = self.shoot_cd / w["cooldown"]
              pygame.draw.rect(surf, (30,20,50), (x+10, y+46, bw, 3), border_radius=2)
              rem_w = int(bw * (1.0 - cd_ratio))
              if rem_w > 0:
                   pygame.draw.rect(surf, col, (x+10, y+46, rem_w, 3), border_radius=2)

        
         # Tab hint 
         tab_s = font_xs.render("Tab - switch", True, C_GRAY)
         surf.blit(tab_s, (x+10, y+54))


       
            
           
            



        