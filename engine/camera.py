"""
Camera system with smooth follow and screen shake
"""
import random
from utils.math_utils import lerp


class Camera:
    def __init__(self, width, height, world_w, world_h):
        self.width   = width
        self.height  = height
        self.world_w = world_w
        self.world_h = world_h

        self.x = 0.0
        self.y = 0.0
        self._target_x = 0.0
        self._target_y = 0.0

        self._shake_time      = 0.0
        self._shake_intensity = 0.0
        self.offset_x = 0
        self.offset_y = 0

    def follow(self, target_x, target_y, dt, speed=6.0):
        self._target_x = target_x - self.width  / 2
        self._target_y = target_y - self.height / 2
        self.x = lerp(self.x, self._target_x, min(1.0, speed * dt))
        self.y = lerp(self.y, self._target_y, min(1.0, speed * dt))

       
        self.x = max(0, min(self.world_w - self.width,  self.x))
        self.y = max(0, min(self.world_h - self.height, self.y))

    def shake(self, intensity=8, duration=0.25):
        self._shake_intensity = max(self._shake_intensity, intensity)
        self._shake_time      = max(self._shake_time, duration)

    def update(self, dt):
        if self._shake_time > 0:
            self._shake_time -= dt
            t = self._shake_time / 0.25
            mag = self._shake_intensity * t
            self.offset_x = random.randint(-int(mag), int(mag))
            self.offset_y = random.randint(-int(mag), int(mag))
        else:
            self.offset_x = 0
            self.offset_y = 0
            self._shake_intensity = 0.0

    @property
    def dx(self):
        return int(self.x) + self.offset_x

    @property
    def dy(self):
        return int(self.y) + self.offset_y

    def world_to_screen(self, wx, wy):
        return wx - self.dx, wy - self.dy

    def screen_to_world(self, sx, sy):
        return sx + self.dx, sy + self.dy
