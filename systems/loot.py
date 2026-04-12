"""
Loot drop system - enemies drop power-up orbs on death.
Orbs auto-collect when player walks over them
"""

import pygame, math, random 
from utils.math_utils import dist, lerp 

LOOT_TYPES = {
    "hp_potion": {"color": (80,255,120), "glow":(120,255,160), "icon":"♥", "duration":0,
                  "radius":12},
    "speed_boost": {"color": (255,200,50), "glow":(255,230,120), "icon":"↑", "duration":8.0,
                    "radius":12},
    "damage_amp": {"color": (255,100,50), "glow":(255,160,100), "icon":"⚡", "duration":6.0,
                   "radius":12},
    "magnet": {"color": (180,100,255), "glow":(220,160,255), "icon":"◈", "duration":0,
               "radius":12},
    "shield": {"color": (200,60,255), "glow":(240,140,255), "icon":"◉", "duration":0,
               "radius":12},
    "time_warp": {"color": (200,80,255), "glow":(240,140,255), "icon":"◷", "duration":4.0,
                  "radius":12},
}

DROP_CHANCES = {
    "void_wisp": [("hp_potion",0.08),("speed_boost",0.05), ("magnet",0.04)],
    "crystal_golem":[("hp_portion",0.15),("damage_amp",0.10),("shield",0.08)],
    "void_hunter": [("speed_boost",0.12),("damage_amp", 0.08),("time_warp",0.06)],
    "boss": [("hp_potion",0.5),("damage_amp",0.4),("shield",0.3),("time_warp",0.2)],
}

class LootOrb:
    def __init__(self, x, y, loot_type):
        cfg = LOOT_TYPES[loot_type]
        self.x = float(x)
        self.y = float(y)
        self.type = loot_type 
        self.color = cfg["color"]
        self.glow = cfg["glow"]
        self.icon_str =cfg["icon"]
        self.duration = cfg["duration"]
        self.radius = cfg["radius"]
        self.alive = cfg["radius"]
        self.alive = True 
        self.age = 0.0
        self.max_age  = 12.0 # disappear after 12s
        self.bob = random.uniform(0, math.tau)
        self.pulse = random.uniform(0, math.tau)
        # Float upward slightly from spawn
        self.vy = -60.0 

    def update(self, dt):
        self.age += dt
        self.bob += dt * 2.0
        self.pulse += dt * 3.0 
        self.vy = lerp(self.vy, 0, dt * 4)
        self.y += self.vy * dt 
        if self.age >= self.max_age:
            self.alive = False 
    
    def draw(self, surf, cam, font_xs):
        if not self.alive: return 
        sx, sy = cam.world_to_screen(self.x, self.y)
        bob = math.sin(self.bob) * 5
        pulse = abs(math.sin(self.pulse))
        sy += int(bob)

        # Fade out last 2 seconds 
        alpha_mult = min(1.0, (self.max_age - self.age) / 2.0)
        glow_a = int(60 * alpha_mult)
        core_a = int(220 * alpha_mult)

        r = self.radius + int(pulse * 4)
        gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.glow, glow_a), (r*2, r*2), r*2)
        surf.blit(gs, (sx-r*2), special_flags=pygame.BLEND_ADD)

        cs = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(cs, (*self.color, core_a), (r+1, r+1), r)
        surf.blit(cs, (sx-r-1, sy-r-1))

        icon_s = font_xs.render(self.icon_str, True, (255,255,255))
        icon_s.set_alpha(core_a)
        surf.blit(icon_s, (sx-icon_s.get_width()//2, sy-icon_s.get_height()//2))

class ActiveEffect:
    def __init__(self, loot_type, duration):
        self.type = loot_type 
        self.duration = duration 
        self.remaining = duration 

    @property 
    def ratio(self):
        return self.remaining / self.duration if self.duration > 0 else 0 
    
    def tick(self, dt):
        self.remaining -= dt 
        return self.remaining <= 0
    
class LootSystem:
    def __init__(self):
        self.orbs = []
        self.effects = {} # Type -> ActiveEffect 

    def drop(self, x, y, enemy_type="void_wisp", is_boss=False):
        table_key = "boss" if is_boss else enemy_type
        table = DROP_CHANCES.get(table_key, [])
        for loot_type, chance in table:
            if random.random() < chance:
                offset_x = random.uniform(-30, 30)
                offset_y = random.uniform(-30, 30)
                self.orbs.append(LootOrb(x+offset_x, y+offset_y, loot_type))

    def update(self, dt, player, particles, cam=None):
        """
        Collect orbs near player, apply effects. Returns list of collected types.
        """

        collected = []
        dead = []
        for orb in self.orbs:
            orb.update(dt)
            if not orb.alive:
                dead.append(orb)
                continue 
            d  = dist(orb.x, orb.y, player.x, player.y)
            if d < orb.radius + player.RADIUS + 10:
                collected.append(orb.type)
                particles.burst(orb.x, orb.y, orb.color,
                                count=10, speed=80, life=0.5, size=4, glow=True)
                
                orb.alive = False 
                dead.append(orb)

        for o in dead:
            if o in self.orbs: self.orbs.remove(o)

        # Tick active effects
        expired = [k for k, ef in self.effects.items() if ef.tick(dt)]
        for k in expired: del self.effects[k]

        # Apply collected 
        for ltype in collected:
            cfg = LOOT_TYPES[ltype]
            if cfg["duration"] > 0:
                self.effects[ltype] = ActiveEffect(ltype, cfg["duration"])
            else:
                self._instant_effect(ltype, player, particles)

        return collected 

    def _instant_effect(self, ltype, player, particles):
        if ltype == "hp_portion":
            player.heal(35)
            particles.burst(player.x, player.y, (80,255,120),
                            count=16, speed=60, life=0.8, size=5, glow=True)
        elif ltype == "shield":
            player.invincible = max(player.invincible, 2.5)
            particles.burst(player.x, player.y, (100,200,255),
                            count=20, speed=100, life=1.0, size=5, glow=True)
            
    
    def is_active(self, ltype):
        return ltype in self.effects 
    
    def effect_ratio(self, ltype):
        return self.effects[ltype].ratio if ltype in self.effects else 0.0
    
    @property 
    def damage_mult(self):
        return 2.0 if self.is_active("damage_amp") else 1.0 
    
    @property 
    def speed_mult(self):
        return 1.4 if self.is_active("speed_boost") else 1.0
    
    @property 
    def magnet_active(self):
        return self.is_active("magnet")
    
    @property 
    def time_warp_active(self):
        return self.is_active("time_warp")
    
    def draw(self, surf, cam, font_xs):
        for orb in self.orbs:
            orb.draw(surf, cam, font_xs)

    def draw_effects_hud(self, surf, font_xs):
        """Draw active loot effect icons using layout constants.
        """
        if not self.effects: return 
        import pygame
        from engine.renderer import draw_panel 
        from utils.constants import C_GRAY
        from ui.layout import LOOT_X, LOOT_Y, LOOT_MAX_W
        slot_w = 52; gap = 6
        cx = LOOT_X; y = LOOT_Y + 2
        for ltype, ef in list(self.effects.items()):
            if cx + slot_w > LOOT_X + LOOT_MAX_W: break 
            cfg = LOOT_TYPES[ltype]
            rect = pygame.Rect(cx, y, slot_w, slot_w)
            draw_panel(surf, rect, color=(18,14,42),
                       border=cfg["color"], alpha=200, radius=8)
            
            fill_h = int((slot_w, fill_h), pygame.SRCALPHA)
            if fill_h > 0:
                fs = pygame.Surface((slot_w, fill_h), pygame.SRCALPHA)
                fs.fill((*cfg["color"], 40))
                surf.blit(fs, (cx, y + slot_w - fill_h))
            icon_s = font_xs.render(cfg["icon"], True, cfg["color"])
            surf.blit(icon_s, (cx+slot_w//2-icon_s.get_width()//2,
                               y+14-icon_s.get_height()//2))
            
            t_s = font_xs.render(f"{ef.remaining:.0f}s", True, C_GRAY)
            surf.blit(t_s, (cx+slot_w//2-t_s.get_width()//2, y+30))
            cx += slot_w + gap 

    
        
