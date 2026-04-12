"""
Weather / atmosphere system for AETHER HARVEST.
Visual-only effects that react to game state — storm, pulse rings,
void rifts, crystal showers.
"""
import pygame, math, random
from utils.constants import C_BG, WIDTH, HEIGHT


class VoidRift:
    """A shimmering tear in space that appears near enemies."""
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.life      = random.uniform(3.0, 6.0)
        self.max_life  = self.life
        self.angle     = random.uniform(0, math.tau)
        self.w         = random.randint(6, 18)
        self.h         = random.randint(40, 100)
        self.pulse     = random.uniform(0, math.tau)

    def update(self, dt):
        self.life  -= dt
        self.pulse += dt * 2.0
        self.angle += dt * 0.3

    @property
    def alive(self): return self.life > 0

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        if sx < -100 or sx > WIDTH+100 or sy < -100 or sy > HEIGHT+100:
            return
        alpha  = int(180 * min(1.0, self.life/self.max_life)
                     * min(1.0, (self.max_life-self.life+0.5)/0.5))
        pulse  = abs(math.sin(self.pulse))
        w      = max(2, int(self.w * (0.6 + pulse*0.4)))

        s = pygame.Surface((w*2+4, self.h+4), pygame.SRCALPHA)
      
        pygame.draw.ellipse(s, (180,60,255,alpha//3), (0,0,w*2+4, self.h+4))
        pygame.draw.ellipse(s, (120,40,200,alpha), (w-2,2, 8, self.h))
        surf.blit(s, (sx-w-2, sy-self.h//2-2))


class CrystalShard:
    """Falling crystal particle from ore storms."""
    def __init__(self, cam_x, cam_y):
        self.x   = cam_x + random.uniform(0, WIDTH)
        self.y   = cam_y - 20
        self.vy  = random.uniform(80, 180)
        self.vx  = random.uniform(-30, 30)
        self.rot = random.uniform(0, math.tau)
        self.rot_spd = random.uniform(-3, 3)
        self.size= random.randint(4, 10)
        from utils.constants import ORE_TYPES
        ore = random.choice(list(ORE_TYPES.values()))
        self.color= ore["color"]
        self.glow = ore["glow"]
        self.life = random.uniform(1.5, 3.0)
        self.max_life = self.life

    @property
    def alive(self): return self.life > 0

    def update(self, dt):
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.rot += self.rot_spd * dt
        self.life -= dt

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        if sx < -20 or sx > WIDTH+20 or sy < -20 or sy > HEIGHT+20:
            return
        alpha = int(200 * (self.life / self.max_life))
        s = self.size
        pts = []
        for i in range(6):
            a  = self.rot + i * math.tau/6
            r  = s if i%2==0 else s//2
            pts.append((sx + int(math.cos(a)*r),
                        sy + int(math.sin(a)*r)))

        gs = pygame.Surface((s*4, s*4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.glow, alpha//4), (s*2,s*2), s*2)
        surf.blit(gs, (sx-s*2, sy-s*2), special_flags=pygame.BLEND_ADD)

        ps = pygame.Surface((s*2+2, s*2+2), pygame.SRCALPHA)
        if len(pts) >= 3:
            adj = [(p[0]-sx+s+1, p[1]-sy+s+1) for p in pts]
            pygame.draw.polygon(ps, (*self.color, alpha), adj)
        surf.blit(ps, (sx-s-1, sy-s-1))


class PulseRing:
    """Expanding ring used for shockwaves, level-ups, boss spawns."""
    def __init__(self, x, y, color, max_radius=300, speed=250, width=3):
        self.x, self.y   = float(x), float(y)
        self.color        = color
        self.radius       = 10.0
        self.max_radius   = max_radius
        self.speed        = speed
        self.width        = width
        self.alive        = True

    def update(self, dt):
        self.radius += self.speed * dt
        if self.radius >= self.max_radius:
            self.alive = False

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        r      = int(self.radius)
        alpha  = int(200 * (1.0 - self.radius/self.max_radius))
        if alpha < 4 or r <= 0: return
        s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha),
                           (r+2, r+2), r, self.width)
        surf.blit(s, (sx-r-2, sy-r-2))


class WeatherSystem:
    def __init__(self):
        self.rifts        = []
        self.shards       = []
        self.rings        = []
        self._rift_timer  = random.uniform(5, 15)
        self._shard_timer = 0.0
        self.storm_active = False  
        self._blood_overlay = 0.0

    def spawn_ring(self, x, y, color, max_radius=300, speed=250, width=3):
        self.rings.append(PulseRing(x,y,color,max_radius,speed,width))

    def set_storm(self, active):
        self.storm_active = active

    def set_blood_moon(self, active):
        self._blood_overlay = 1.0 if active else 0.0

    def update(self, dt, cam):
       
        self._rift_timer -= dt
        if self._rift_timer <= 0:
            cx, cy = cam.x + random.uniform(0, WIDTH), cam.y + random.uniform(0, HEIGHT)
            self.rifts.append(VoidRift(cx, cy))
            self._rift_timer = random.uniform(4, 12)

       
        if self.storm_active:
            self._shard_timer -= dt
            if self._shard_timer <= 0:
                self.shards.append(CrystalShard(cam.x, cam.y))
                self._shard_timer = random.uniform(0.03, 0.12)
        else:
            self._shard_timer = 0.0

        self.rifts  = [r for r in self.rifts  if r.alive]
        self.shards = [s for s in self.shards if s.alive]
        self.rings  = [r for r in self.rings  if r.alive]

        for r in self.rifts:  r.update(dt)
        for s in self.shards: s.update(dt)
        for r in self.rings:  r.update(dt)

    def draw(self, surf, cam):
        for r in self.rifts:  r.draw(surf, cam)
        for s in self.shards: s.draw(surf, cam)
        for r in self.rings:  r.draw(surf, cam)

    def draw_overlays(self, surf):
        if self._blood_overlay > 0:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((120, 0, 20, int(18 * self._blood_overlay)))
            surf.blit(ov, (0,0))

