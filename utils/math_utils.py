"""
Math utilities for AETHER HARVEST
"""
import math
import random


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def dist2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


def normalize(dx, dy):
    d = math.hypot(dx, dy)
    if d == 0:
        return 0.0, 0.0
    return dx / d, dy / d


def angle_to(ax, ay, bx, by):
    return math.atan2(by - ay, bx - ax)


def polar(angle, radius):
    return math.cos(angle) * radius, math.sin(angle) * radius


def random_on_ring(cx, cy, r_min, r_max):
    angle  = random.uniform(0, math.tau)
    radius = random.uniform(r_min, r_max)
    return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius


def smooth_step(t):
    t = clamp(t, 0, 1)
    return t * t * (3 - 2 * t)


def ease_out(t):
    return 1 - (1 - t) ** 3


def format_number(n):
    """Format big numbers nicely: 1234 → 1.2K"""
    n = int(n)
    if n < 1_000:
        return str(n)
    elif n < 1_000_000:
        return f"{n/1_000:.1f}K"
    elif n < 1_000_000_000:
        return f"{n/1_000_000:.1f}M"
    else:
        return f"{n/1_000_000_000:.1f}B"
