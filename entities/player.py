"""

Player entity for Infinite Harvest
"""
import pygame
import math
import random
from utils.constants import (WIDTH, HEIGHT, PLAYER_SPEED, PLAYER_DASH_SPEED,
                             DASH_DURATION, DASH_COOLDOWN, C_SECONDARY, C_PRIMARY)

from utils.math_utils import clamp, normalize, lerp

class Player:
    RADIUS = 16

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0

       
        self.max_hp  = 100
        self.hp  = 100
        self.invincible = 0.0 

      
        self.dash_time = 0.0
        self.dash_cd =  0.0
        self.dashing = False 
        self.dash_vx = 0.0 
        self.dash_vy = 0.0

        # Visual
        self.angle = 0.0
        self.pulse = 0.0 

       
        self.trail = []   
        self.trail_max = 18

       
        self.collect_range_bonus = 0 

    @property 
    def collect_radius(self):
        return 28 + self.collect_range_bonus 
    
    def take_damage(self, amount):
        if self.invincible > 0:
            return False 
        self.hp -= amount 
        self.invincible = 1.2
        self.hp = clamp(self.hp, 0, self.max_hp)
        return True 
    
    def heal(self, amount):
        self.hp = clamp(self.hp + amount, 0, self.max_hp)

    def update(self, dt, inp, world_w, world_h):
        self.pulse += dt * 3.0
        self.invincible = max(0, self.invincible - dt)
        self.dash_cd = max(0, self.dash_cd - dt)

       
        dx, dy = 0.0, 0.0
        if inp.key_held(pygame.K_w) or inp.key_held(pygame.K_UP): dy -= 1
        if inp.key_held(pygame.K_s) or inp.key_held(pygame.K_DOWN): dy+=1
        if inp.key_held(pygame.K_a) or inp.key_held(pygame.K_LEFT): dx -= 1
        if inp.key_held(pygame.K_d) or inp.key_held(pygame.K_RIGHT): dx += 1
        dx, dy = normalize(dx, dy)

        
        if inp.key_pressed(pygame.K_SPACE) and self.dash_cd <= 0 and (dx or dy):
            self.dashing = True 
            self.dash_time = DASH_DURATION
            self.dash_cd = DASH_COOLDOWN
            self.dash_vx = dx
            self.dash_vy = dy 


        if self.dashing:
            self.dash_time -= dt
            if self.dash_time <= 0:
                self.dashing = False 
            spd = PLAYER_DASH_SPEED 
            self.vx = self.dash_vx * spd
            self.vy = self.dash_vy * spd 
            self.invincible = max(self.invincible, self.dash_time)
        else:
            self.vx = dx * PLAYER_SPEED
            self.vy = dy * PLAYER_SPEED 
        
        self.x = clamp(self.x + self.vx * dt, self.RADIUS, world_w - self.RADIUS)
        self.y = clamp(self.y + self.vy * dt, self.RADIUS, world_h - self.RADIUS)

       
        if dx or dy:
            self.angle = math.atan2(dx, dy)

        
        speed = math.hypot(self.vx, self.vy)
        if speed > 20:
            self.trail.append([self.x, self.y, 1.0])
        if len(self.trail) > self.trail_max:
            self.trail.pop(0)
        for t in self.trail:
            t[2] -= dt * 3
        self.trail = [t for t in self.trail if t[2] > 0]

    def draw(self, surf, cam):
        sx, sy = cam.world_to_screen(self.x, self.y)
        pulse = abs(math.sin(self.pulse))

       
        for i, (tx, ty, age) in enumerate(self.trail):
            tsx, tsy = cam.world_to_screen(tx, ty)
            alpha = int(age * 180 * (i / max(1, len(self.trail))))
            radius = max(1, int(self.RADIUS * age * 0.6))
            color = C_SECONDARY if self.dashing else C_PRIMARY 
            s = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius + 1, radius + 1), radius)
            surf.blit(s, (tsx - radius - 1, tsy - radius - 1))

       
        if self.invincible > 0 and int(self.invincible * 10) % 2 ==0:
            from engine.renderer import draw_glow_circle 
            draw_glow_circle(surf, (255, 220, 80), (sx, sy), self.RADIUS + 6, intensity=120,
                             layers =2)
        
       
        glow_r = int(self.RADIUS * (1.4 + pulse * 0.2))
        glow_s = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*C_SECONDARY, 50), (glow_r + 2, glow_r + 2), glow_r)
        surf.blit(glow_s, (sx - glow_r -2, sy - glow_r - 2), special_flags=pygame.BLEND_ADD)

       
        pygame.draw.circle(surf, C_SECONDARY, (sx, sy), self.RADIUS)
        pygame.draw.circle(surf, (200, 255, 250), (sx, sy), self.RADIUS - 4)

       
        pip_x = sx + int(math.cos(self.angle) * (self.RADIUS - 4))
        pip_y = sy + int(math.sin(self.angle) * (self.RADIUS - 4))
        pygame.draw.circle(surf, C_PRIMARY, (pip_x, pip_y), 4)

       
        if self.dash_cd > 0:
            ratio = 1.0 - self.dash_cd / DASH_COOLDOWN
            angle_end = int(-90 + ratio * 360)
            rect = pygame.Rect(sx - self.Radius - 5, sy - self.Radius - 5,
            (self.RADIUS + 5) * 2, (self.RADIUS + 5) * 2)
            pygame.draw.arc(surf, (180, 100, 255), rect,
                            math.radians(-90), math.radians(angle_end), 2)
            