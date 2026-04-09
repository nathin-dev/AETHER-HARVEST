"""

resource / Ore system for Infinite Harvest
"""

import pygame
import math
import random 
from utils.constants import ORE_TYPES, WIDTH, HEIGHT
from utils.math_utils import dist, lerp, random_on_ring

WORLD_W = WIDTH * 2
WORLD_H = HEIGHT * 2
MAX_ORES = 18

class Ore:
    def __init__(self,x ,y, ore_type):
        cfg = ORE_TYPES[ore_type]
        self.x = float(x)
        self.y = float(y)
        self.type = ore_type 
        self.color = cfg["color"]
        self.glow = cfg["glow"]
        self.value = cfg["value"]
        self.radius  = 16 + (cfg["value"] - 1) * 2
        self.radius = min(self.radius, 8)

        self.alive = True 
        self.pulse = random.uniform(0, math.tau)
        self.scale  = 0.0 # spawn animation
        self.bob_phase = random.uniform(0, math.tau)
        self.collected = False 

    def update(self, dt):
        self.pulse += dt * 2.0 
        self.bob_phase += dt * 1.5 
        self.scale = min(1.0, self.scale + dt * 4 )

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        bob    = math.sin(self.bob_phase) * 4
        pulse  = abs(math.sin(self.pulse)) * 0.15
        scale  = self.scale * (1.0 + pulse)
        radius = max(1, int(self.radius * scale))

        sy_draw = sy + int(bob)

        # Outer glow
        glow_r = radius + 12
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*self.glow, 35),
                           (glow_r, glow_r), glow_r)
        surf.blit(glow_s, (sx - glow_r, sy_draw - glow_r),
                  special_flags=pygame.BLEND_ADD)

        # Gem shape (hexagon approximation via circle + facets)
        pygame.draw.circle(surf, self.color, (sx, sy_draw), radius)

        # Facet highlight
        facet_r = radius - 4
        if facet_r > 2:
            hx = sx - radius // 4
            hy = sy_draw - radius // 3
            pygame.draw.circle(surf, (255, 255, 255), (hx, hy), max(1, facet_r // 3))

        # Crystal edges
        n_edges = 6 if self.value < 8 else 8
        for i in range(n_edges):
            angle = self.pulse * 0.3 + i * math.tau / n_edges
            ex = sx + int(math.cos(angle) * radius)
            ey = sy_draw + int(math.sin(angle) * radius)
            ex2 = sx + int(math.cos(angle + math.tau / n_edges) * radius)
            ey2 = sy_draw + int(math.sin(angle + math.tau / n_edges) * radius)
            pygame.draw.line(surf, (*self.glow, 160), (ex, ey), (ex2, ey2), 1)

        # Rarity ring for rare ores
        if self.value >= 8:
            ring_r = radius + 6
            pygame.draw.circle(surf, self.glow, (sx, sy_draw), ring_r, 1)

    @staticmethod
    def random_position():
        return (random.randint(40, WORLD_W - 40),
                random.randint(40, WORLD_H - 40))


class ResourceSystem:
    def __init__(self):
        self.ores       = []
        self.total_ores = MAX_ORES
        self._spawn_initial()

    def _spawn_initial(self):
        for _ in range(self.total_ores):
            self._spawn_ore()

    def _spawn_ore(self, near_x=None, near_y=None):
        # Weighted random type
        types   = list(ORE_TYPES.keys())
        weights = [ORE_TYPES[t]["rarity"] for t in types]
        ore_type = random.choices(types, weights=weights)[0]

        if near_x and near_y:
            x, y = random_on_ring(near_x, near_y, 150, 400)
            x = max(40, min(WORLD_W - 40, x))
            y = max(40, min(WORLD_H - 40, y))
        else:
            x, y = Ore.random_position()

        self.ores.append(Ore(x, y, ore_type))

    def update(self, dt, player, particles, floating_texts,
               font_sm, click_power, rare_boost=0, chain_chance=0,
               time_slow_cb=None):
        """Returns (resources_gained, voidite_collected)."""
        resources_gained = 0
        voidite = False

        for ore in self.ores:
            ore.update(dt)

        # Check collection (proximity or click handled via external click)
        return resources_gained, voidite

    def try_collect(self, wx, wy, player, particles, floating_texts,
                    font_sm, click_power, rare_boost=0, chain_chance=0,
                    time_slow_cb=None, cam=None):
        """Called when player clicks. Returns resources gained."""
        resources_gained = 0
        to_remove = []

        for ore in self.ores:
            if not ore.alive:
                continue
            d = ((ore.x - wx) ** 2 + (ore.y - wy) ** 2) ** 0.5
            if d < ore.radius + player.collect_radius:
                to_remove.append(ore)

        # Chain reaction
        if to_remove:
            import random as _rng
            for ore in to_remove:
                ore.alive = False
                val = ore.value * click_power
                # Chain bonus
                chain_rolls = 0
                while _rng.random() < chain_chance and chain_rolls < 5:
                    val = int(val * 1.5)
                    chain_rolls += 1
                    particles.burst(ore.x, ore.y, ore.glow, count=6, speed=100)

                resources_gained += val
                particles.burst(ore.x, ore.y, ore.color, count=16,
                                speed=140, life=0.8, size=6, glow=True)
                floating_texts.add(ore.x, ore.y - 30,
                                   f"+{val}{'!' * chain_rolls}",
                                   font_sm, ore.glow)

                if ore.type == "voidite" and time_slow_cb:
                    time_slow_cb()

        self.ores = [o for o in self.ores if o.alive]

        # Replenish
        while len(self.ores) < self.total_ores:
            self._spawn_ore(player.x, player.y)

        return resources_gained

    def auto_collect(self, dt, player, auto_income):
        """Passive income tick."""
        return auto_income * dt

    def draw(self, surf, cam):
        for ore in self.ores:
            ore.draw(surf, cam)



