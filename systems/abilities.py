"""
Active ability system for AETHER HARVEST.
Player has 3 ability slots, triggered by Q / E / F keys.
"""
import pygame, math, random
from utils.math_utils import normalize, dist
from utils.constants import C_DANGER, C_SECONDARY, C_ACCENT, C_SUCCESS

ABILITIES = {
    "nova_burst": {
        "name":     "Nova Burst",
        "desc":     "Explodes all nearby ores simultaneously",
        "icon":     "💥",
        "color":    (255, 180, 50),
        "cooldown": 12.0,
        "key":      "Q",
    },
    "void_pulse": {
        "name":     "Void Pulse",
        "desc":     "Shockwave damages and knocks back all enemies",
        "icon":     "🌀",
        "color":    (120, 60, 255),
        "cooldown": 8.0,
        "key":      "E",
    },
    "aether_shield": {
        "name":     "Aether Shield",
        "desc":     "3 seconds of full invincibility + healing",
        "icon":     "🛡",
        "color":    (80, 255, 140),
        "cooldown": 20.0,
        "key":      "F",
    },
}


class Ability:
    def __init__(self, ability_id):
        cfg          = ABILITIES[ability_id]
        self.id      = ability_id
        self.name    = cfg["name"]
        self.desc    = cfg["desc"]
        self.icon    = cfg["icon"]
        self.color   = cfg["color"]
        self.max_cd  = cfg["cooldown"]
        self.cd      = 0.0
        self.key     = cfg["key"]

    @property
    def ready(self):
        return self.cd <= 0

    @property
    def cd_ratio(self):
        return max(0.0, self.cd / self.max_cd)

    def use(self):
        if not self.ready:
            return False
        self.cd = self.max_cd
        return True

    def update(self, dt):
        self.cd = max(0.0, self.cd - dt)


class AbilitySystem:
    def __init__(self):
        self.abilities = [
            Ability("nova_burst"),
            Ability("void_pulse"),
            Ability("aether_shield"),
        ]
        self.shield_active = 0.0  

    def update(self, dt):
        for a in self.abilities:
            a.update(dt)
        self.shield_active = max(0.0, self.shield_active - dt)

    def fire(self, idx, player, enemies, boss_mgr,
             res_sys, particles, floats, font_sm, cam):
        """Fire ability at index idx. Returns resources gained."""
        if idx >= len(self.abilities):
            return 0
        ab = self.abilities[idx]
        if not ab.use():
            return 0

        gained = 0
        if ab.id == "nova_burst":
            gained = self._nova_burst(player, res_sys, particles, floats, font_sm)
        elif ab.id == "void_pulse":
            self._void_pulse(player, enemies, boss_mgr, particles)
        elif ab.id == "aether_shield":
            self._aether_shield(player, particles)

        return gained

    def _nova_burst(self, player, res_sys, particles, floats, font_sm):
        """Detonate all ores on screen in a massive explosion."""
        gained  = 0
        to_kill = []
        for ore in res_sys.ores:
            d = dist(ore.x, ore.y, player.x, player.y)
            if d < 500:
                to_kill.append(ore)

        for ore in to_kill:
            ore.alive = False
            val = ore.value * 3   
            gained += val
            particles.burst(ore.x, ore.y, ore.color,
                            count=20, speed=200, life=1.0, size=7, glow=True)
            floats.add(ore.x, ore.y - 20, f"+{val}", font_sm, ore.glow)

        res_sys.ores = [o for o in res_sys.ores if o.alive]
        from systems.resource_system import WORLD_W, WORLD_H
        while len(res_sys.ores) < res_sys.total_ores:
            res_sys._spawn_ore(player.x, player.y)

       
        particles.burst(player.x, player.y, (255, 200, 80),
                        count=50, speed=300, life=1.5, size=8, glow=True)
        return gained

    def _void_pulse(self, player, enemies, boss_mgr, particles):
        """Shockwave pushes and damages all nearby enemies."""
        pulse_r = 350
        for enemy in enemies.enemies:
            if not enemy.alive:
                continue
            d = dist(enemy.x, enemy.y, player.x, player.y)
            if d < pulse_r:
                
                nx, ny = normalize(enemy.x - player.x, enemy.y - player.y)
                force  = (1.0 - d / pulse_r) * 600
                enemy.vx += nx * force
                enemy.vy += ny * force
               
                dmg = int(40 * (1.0 - d / pulse_r) + 15)
                enemy.take_damage(dmg)
                particles.burst(enemy.x, enemy.y, (120, 60, 255),
                                count=8, speed=100, life=0.4)

        if boss_mgr.boss and boss_mgr.boss.alive:
            b = boss_mgr.boss
            d = dist(b.x, b.y, player.x, player.y)
            if d < pulse_r:
                b.take_damage(80)

       
        for i in range(32):
            angle = i * math.tau / 32
            px = player.x + math.cos(angle) * pulse_r
            py = player.y + math.sin(angle) * pulse_r
            particles.emit(px, py,
                           math.cos(angle) * 80, math.sin(angle) * 80,
                           life=0.6, color=(120, 60, 255),
                           end_color=(40, 20, 80), size=5, glow=True)

    def _aether_shield(self, player, particles):
        """Full invincibility + heal."""
        self.shield_active = 3.0
        player.invincible  = 3.0
        player.heal(40)
        particles.burst(player.x, player.y, (80, 255, 140),
                        count=40, speed=150, life=1.2, size=6, glow=True)

    def draw_hud(self, surf, font_sm, font_xs):
        """Draw ability slots at bottom-center using layout constants."""
        import pygame
        from utils.constants import C_GRAY, C_WHITE
        from engine.renderer import draw_panel, draw_glow_rect
        from ui.layout import AB_X, AB_Y, AB_W, AB_H, AB_GAP

        slot_w, slot_h = AB_W, AB_H
        gap    = AB_GAP
        y      = AB_Y

        for i, ab in enumerate(self.abilities):
            x = AB_X + i * (slot_w + gap)
            rect = pygame.Rect(x, y, slot_w, slot_h)

            
            if ab.ready:
                bg = (25, 18, 55)
                border = ab.color
            else:
                bg = (15, 12, 35)
                border = (50, 40, 80)

            draw_panel(surf, rect, color=bg, border=border, alpha=220, radius=10)

            
            if not ab.ready:
                overlay_h = int(slot_h * ab.cd_ratio)
                ov = pygame.Surface((slot_w, overlay_h), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 140))
                surf.blit(ov, (x, y + slot_h - overlay_h))

                
                cd_txt = font_xs.render(f"{ab.cd:.1f}", True, (200, 180, 255))
                surf.blit(cd_txt, (x + slot_w//2 - cd_txt.get_width()//2,
                                   y + slot_h//2 - cd_txt.get_height()//2))
            else:
                draw_glow_rect(surf, ab.color, rect, radius=4, alpha=40)

           
            icon_s = font_sm.render(ab.icon, True,
                                    ab.color if ab.ready else (80, 70, 100))
            surf.blit(icon_s, (x + slot_w//2 - icon_s.get_width()//2,
                                y + 10))

           
            key_lbl = ["Q", "E", "F"][i]
            k_surf  = font_xs.render(key_lbl, True, C_GRAY)
            surf.blit(k_surf, (x + slot_w//2 - k_surf.get_width()//2,
                                y + slot_h - 14))
